"""
Public execution utilities for the CNL Task Executor.

Extracts `_execute_function` and `_serialize_result` from agent_router.py
as public API so task_executor.py can call them directly.

Created: Story 7.1 (CRITICAL-1 amendment)
"""

import asyncio
import dataclasses
import inspect
import logging
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def serialize_result(obj):
    """
    Recursively serialize a function return value to JSON-safe types.

    Handles dataclasses, Path, Enum, objects with to_dict(), and
    nested lists/dicts.

    Args:
        obj: Any Python object to serialize

    Returns:
        JSON-serializable Python object
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "to_dict"):
        return serialize_result(obj.to_dict())
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return serialize_result(dataclasses.asdict(obj))
    if isinstance(obj, dict):
        return {str(k): serialize_result(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [serialize_result(item) for item in obj]
    return str(obj)


async def execute_function(
    func_name: str, args: dict, function_registry: dict
) -> tuple[bool, Optional[dict], Optional[str]]:
    """
    Execute a function from the registry via asyncio.to_thread().

    Auto-injects ``client``, ``client_name``, and ``org_id`` when the
    target function accepts them and they are not already provided by
    the caller.

    Args:
        func_name: Name of the function to execute
        args: Arguments to pass to the function
        function_registry: The function registry dict

    Returns:
        Tuple of (success: bool, result: dict | None, error: str | None)
    """
    func = function_registry.get(func_name)
    if not func:
        error = f"Function '{func_name}' not found in registry"
        logger.error(error)
        return False, None, error

    try:
        sig = inspect.signature(func)
        params = sig.parameters

        # Auto-inject client if the function accepts it and it wasn't provided
        if "client" in params and "client" not in args:
            try:
                from scripts.api import get_client
                from scripts.settings import SettingsManager

                settings = SettingsManager.load()
                profile = settings.meraki_profile or "default"
                args["client"] = get_client(profile=profile)
            except Exception as exc:
                logger.warning(f"Could not auto-inject client: {exc}")

        # Auto-inject client_name from settings
        if "client_name" in params and "client_name" not in args:
            try:
                from scripts.settings import SettingsManager

                settings = SettingsManager.load()
                if settings.meraki_profile:
                    args["client_name"] = settings.meraki_profile
            except Exception as exc:
                logger.warning(f"Could not auto-inject client_name: {exc}")

        # Auto-inject org_id from client
        if "org_id" in params and "org_id" not in args:
            client = args.get("client")
            if client and hasattr(client, "org_id"):
                args["org_id"] = client.org_id

        # Execute via asyncio.to_thread() to avoid blocking
        logger.debug(f"Executing function: {func_name} with args: {list(args.keys())}")
        result = await asyncio.to_thread(func, **args)

        logger.info(f"Function {func_name} executed successfully")
        return True, {"result": serialize_result(result)}, None

    except Exception as exc:
        error = f"Function {func_name} failed: {type(exc).__name__}: {exc}"
        logger.error(error)
        return False, None, error
