# CNL (Cisco Neural Language) - Flow Architecture

> **Version:** 1.0
> **Last Updated:** 2026-02-08
> **Tip:** Install a Mermaid preview extension in VS Code (e.g., "Markdown Preview Mermaid Support") to render the diagrams inline.

---

## 1. High-Level Architecture Overview

CNL is a conversational interface that translates natural language into Meraki Dashboard API operations. The system is composed of a React frontend, a FastAPI backend with WebSocket support, an LLM-powered agent router, and the Meraki cloud API.

```mermaid
graph TB
    subgraph Browser["Browser (React on :5173)"]
        UI[ChatView / ChatInput]
        WS_CLIENT[useWebSocket Hook]
        STORE[Zustand chatStore]
    end

    subgraph Backend["FastAPI Backend (:3141)"]
        SERVER[server.py<br/>WebSocket /ws/chat]
        ROUTER[agent_router.py<br/>classify_intent + process_message]
        TASK_EXEC[task_executor.py<br/>Deterministic Steps]
        SAFETY[safety.py<br/>SafetyLevel Check]
        REGISTRY[FUNCTION_REGISTRY<br/>40+ callables]
    end

    subgraph Modules["Python Modules"]
        DISCOVERY[discovery.py]
        CONFIG[config.py]
        WORKFLOW[workflow.py]
        REPORT[report.py]
    end

    subgraph External["External Services"]
        AI_ENGINE[ai_engine.py<br/>LiteLLM Wrapper]
        LLM[LLM Provider<br/>OpenAI / Anthropic / Google / Ollama]
        MERAKI[Meraki Dashboard API<br/>api.meraki.com/api/v1]
    end

    subgraph Storage["File System"]
        SNAPSHOTS[clients/NAME/discovery/]
        CONFIGS[clients/NAME/workflows/]
        REPORTS[clients/NAME/reports/]
        CREDS[~/.meraki/credentials]
    end

    UI -->|user types message| WS_CLIENT
    WS_CLIENT <-->|WebSocket JSON| SERVER
    WS_CLIENT -->|updates| STORE
    STORE -->|renders| UI

    SERVER -->|process_message()| ROUTER
    ROUTER -->|task_definition?| TASK_EXEC
    ROUTER -->|legacy LLM flow| AI_ENGINE
    TASK_EXEC -->|tool steps| REGISTRY
    TASK_EXEC -->|agent steps| AI_ENGINE
    TASK_EXEC -->|gate steps| SERVER

    AI_ENGINE <-->|acompletion()| LLM
    ROUTER -->|safety check| SAFETY

    REGISTRY --> DISCOVERY
    REGISTRY --> CONFIG
    REGISTRY --> WORKFLOW
    REGISTRY --> REPORT

    DISCOVERY -->|Meraki SDK| MERAKI
    CONFIG -->|Meraki SDK| MERAKI

    DISCOVERY -->|save_snapshot| SNAPSHOTS
    WORKFLOW -->|save_workflow| CONFIGS
    REPORT -->|generate_report| REPORTS
    CONFIG -->|backup_config| SNAPSHOTS
```

**Key design decisions:**

- **BYOK (Bring Your Own Key):** Users supply their own LLM API key via settings. LiteLLM abstracts the provider (`scripts/ai_engine.py`).
- **Dual execution paths:** Messages can flow through the legacy LLM tool-call loop or the deterministic Task Executor (Epic 7), controlled by the `use_modular_tasks` feature flag.
- **File-based storage:** No database. Snapshots, workflows, and reports are stored as JSON/HTML files under `clients/{name}/`.

---

## 2. Message Flow: User Question to Natural Language Answer

This diagram traces the full lifecycle of a read-only question like **"which device is consuming more bandwidth?"** through the legacy LLM path.

```mermaid
sequenceDiagram
    actor User
    participant ChatInput as ChatInput.tsx
    participant WS as useWebSocket.ts
    participant Server as server.py<br/>/ws/chat
    participant Session as SessionManager
    participant Router as agent_router.py<br/>process_message()
    participant Classify as classify_intent()
    participant AIEngine as ai_engine.py<br/>chat_completion()
    participant LLM as LLM Provider
    participant Registry as FUNCTION_REGISTRY
    participant Discovery as discovery.py
    participant API as api.py<br/>Meraki SDK
    participant Meraki as Meraki Cloud

    User->>ChatInput: Types "which device is consuming more bandwidth?"
    ChatInput->>WS: send({type:"message", content:"...", session_id:"abc"})
    WS->>Server: WebSocket JSON frame

    Note over Server: Validate session_id (regex: ^[a-zA-Z0-9-]{1,64}$)
    Note over Server: Check content length <= 5000 chars

    Server->>Session: get_session("abc") / create_session("abc")
    Session-->>Server: ChatSession object
    Server->>Session: add_message(role="user", content="...")

    Server->>Server: send {type:"agent_status", status:"thinking"}
    Server->>Router: process_message(message, session_id, ai_engine, context)

    Router->>Classify: classify_intent(message, ai_engine, settings)

    Note over Classify: 1. Check explicit prefix (@analyst) -> No<br/>2. Check task registry -> No match<br/>3. Quick regex classify -> "network-analyst" (0.85)<br/>4. Score >= 0.9? No -> try LLM

    Classify->>AIEngine: classify(message, agents_list)
    AIEngine->>LLM: acompletion() with route_to_agent tool
    LLM-->>AIEngine: tool_call: route_to_agent(agent="network-analyst", confidence=0.95)
    AIEngine-->>Classify: {agent:"network-analyst", confidence:0.95}
    Classify-->>Router: ClassificationResult(agent="network-analyst", confidence=0.95)

    Router-->>Server: yield {type:"classification", agent:"network-analyst", confidence:0.95}
    Server-->>WS: send_json(classification)

    Note over Router: No task_definition -> Legacy LLM Flow

    Router->>Router: Build messages: [system_prompt, context[-20:], user_msg]
    Router->>Router: tools = get_agent_tools("network-analyst")

    loop Tool-call loop (max 5 rounds)
        Router->>AIEngine: chat_completion(messages, tools, stream=True)
        AIEngine->>LLM: acompletion(stream=True)
        LLM-->>AIEngine: streaming chunks with tool_call: discover_clients(network_id="L_123")

        Note over Router: Accumulate tool_call chunks (id, name, arguments)

        Router->>Registry: _execute_function("discover_clients", {network_id:"L_123"})
        Registry->>Discovery: discover_clients(network_id="L_123")
        Discovery->>API: dashboard.networks.getNetworkClients(network_id)
        API->>Meraki: GET /api/v1/networks/L_123/clients
        Meraki-->>API: JSON response (client list with usage)
        API-->>Discovery: Client data
        Discovery-->>Registry: [{mac:"...", usage:{sent:1024, recv:2048}}, ...]
        Registry-->>Router: (True, result_dict, None)

        Router-->>Server: yield {type:"tool_status", function:"discover_clients", status:"ok"}
        Server-->>WS: send_json(tool_status)

        Note over Router: Append tool result to messages as role:"tool"<br/>Loop continues - LLM sees tool result

        Router->>AIEngine: chat_completion(messages_with_tool_result, tools, stream=True)
        AIEngine->>LLM: acompletion(stream=True)
        LLM-->>AIEngine: streaming text: "The top 3 devices by bandwidth..."
    end

    loop Streaming text chunks
        AIEngine-->>Router: chunk.delta.content = "The top..."
        Router-->>Server: yield {type:"stream", chunk:"The top...", agent:"network-analyst"}
        Server-->>WS: send_json(stream chunk)
        WS->>WS: appendToLastAssistant(sessionId, chunk)
    end

    Note over Router: No more tool_calls -> break loop

    Server-->>WS: send_json({type:"done", agent:"system", session_id:"abc"})
    WS->>WS: setStreaming(false)
    WS-->>User: Chat bubble renders complete response
```

---

## 3. Agent Classification Flow

The `classify_intent()` function in `agent_router.py` uses a multi-tier pipeline to determine which agent should handle a message.

```mermaid
flowchart TD
    START([User message arrives]) --> SANITIZE[_sanitize_input<br/>Truncate to 500 chars<br/>Remove control characters]

    SANITIZE --> PREFIX{Explicit prefix?<br/>@analyst / @specialist / @workflow}
    PREFIX -->|Yes| RETURN_100[Return agent<br/>confidence = 1.0]

    PREFIX -->|No| TASK_FLAG{use_modular_tasks<br/>enabled?}
    TASK_FLAG -->|Yes| TASK_MATCH[TaskRegistry.find_matching_task<br/>YAML pattern + verb check]
    TASK_FLAG -->|No| REGEX

    TASK_MATCH --> TASK_HIT{Task matched?}
    TASK_HIT -->|Yes| RETURN_TASK[Return agent + task_definition<br/>confidence = 1.0]
    TASK_HIT -->|No| REGEX

    REGEX[_quick_classify<br/>Regex patterns + verb-aware boost] --> REGEX_SCORE{Score >= 0.9?}
    REGEX_SCORE -->|Yes| RETURN_REGEX[Return agent<br/>confidence = 0.6 + score * 0.1]

    REGEX_SCORE -->|No| AI_CHECK{AIEngine available?}
    AI_CHECK -->|Yes| LLM_CLASSIFY[_llm_classify<br/>ai_engine.classify with<br/>route_to_agent tool]
    AI_CHECK -->|No| FALLBACK_REGEX

    LLM_CLASSIFY --> LLM_OK{Success?}
    LLM_OK -->|Yes| RETURN_LLM[Return agent<br/>confidence from LLM]
    LLM_OK -->|No| FALLBACK_REGEX

    FALLBACK_REGEX{Regex result<br/>exists?}
    FALLBACK_REGEX -->|Yes| RETURN_FALLBACK[Return regex result<br/>confidence * 0.8]
    FALLBACK_REGEX -->|No| RETURN_DEFAULT[Return network-analyst<br/>confidence = 0.3<br/>requires_confirmation = true]

    style RETURN_100 fill:#2d6a2d,color:#fff
    style RETURN_TASK fill:#2d6a2d,color:#fff
    style RETURN_REGEX fill:#2d6a2d,color:#fff
    style RETURN_LLM fill:#2d6a2d,color:#fff
    style RETURN_FALLBACK fill:#8a6d2b,color:#fff
    style RETURN_DEFAULT fill:#8b3a3a,color:#fff
```

**Verb-aware scoring** (`verb_utils.py`): When `workflow-creator` has zero keyword matches, the router applies a +2.0 boost to `meraki-specialist` for action verbs (configure, create, add, block, delete) or to `network-analyst` for analysis nouns/verbs (discover, analyze, audit, investigate). This prevents ambiguous messages like "check the firewall" from misrouting.

---

## 4. Tool Execution Flow (Legacy LLM Path)

When no `task_definition` is matched, the router enters the legacy LLM flow in `process_message()`. This uses a conversation loop where the LLM can make tool calls, the system executes them, and feeds results back.

```mermaid
flowchart TD
    START([Legacy LLM Flow]) --> BUILD[Build messages array:<br/>1. system_prompt from .claude/agents/NAME.md<br/>2. session_context last 20 msgs<br/>3. current user message]

    BUILD --> GET_TOOLS[tools = get_agent_tools agent_name<br/>from agent_tools.py schemas]

    GET_TOOLS --> LOOP_START{Round < MAX_TOOL_ROUNDS?<br/>MAX = 5}
    LOOP_START -->|No| EXIT_MAX([Exit: max rounds reached])

    LOOP_START -->|Yes| CALL_LLM[ai_engine.chat_completion<br/>messages, tools, stream=True]

    CALL_LLM --> STREAM[Stream response chunks]

    STREAM --> CHECK_CONTENT{delta.content?}
    CHECK_CONTENT -->|Yes| YIELD_STREAM[yield type:stream chunk<br/>Accumulate assistant_content]
    YIELD_STREAM --> STREAM

    CHECK_CONTENT -->|No| CHECK_TC{delta.tool_calls?}
    CHECK_TC -->|Yes| ACCUMULATE[Accumulate tool_call<br/>id, name, arguments<br/>in pending_tool_calls dict]
    ACCUMULATE --> STREAM

    CHECK_TC -->|No| STREAM_END{Stream ended}

    STREAM_END --> HAS_TC{pending_tool_calls<br/>empty?}
    HAS_TC -->|Yes| DONE([Break loop<br/>LLM responded with text])

    HAS_TC -->|No| EXEC_TOOLS[For each tool_call:<br/>1. Parse JSON args<br/>2. _execute_function via FUNCTION_REGISTRY<br/>3. Collect results]

    EXEC_TOOLS --> YIELD_STATUS[yield type:tool_status<br/>or type:function_error<br/>per tool]

    YIELD_STATUS --> APPEND[Append to messages:<br/>1. assistant msg with tool_calls<br/>2. tool role messages with results]

    APPEND --> LOOP_START

    style DONE fill:#2d6a2d,color:#fff
    style EXIT_MAX fill:#8b3a3a,color:#fff
```

**Key details:**
- Tool call chunks arrive incrementally during streaming. The router accumulates `id`, `name`, and `arguments` across multiple chunks before execution.
- `_execute_function()` delegates to `executor_utils.execute_function()`, which runs sync functions via `asyncio.to_thread()`.
- After tool results are appended to the conversation, the loop repeats so the LLM can generate a natural language interpretation of the raw data.

---

## 5. Modular Task Executor Flow

The Task Executor (`task_executor.py`) provides a deterministic alternative to the LLM tool-call loop. Tasks are defined as YAML files in `tasks/` and matched by the `TaskRegistry` during classification.

```mermaid
flowchart TD
    START([task_definition matched<br/>in classify_intent]) --> INIT[Create TaskRunState<br/>status = RUNNING]

    INIT --> PRE_HOOKS[Run pre-task hooks<br/>e.g., validate credentials]

    PRE_HOOKS --> STEP_LOOP{Next step?}
    STEP_LOOP -->|No more steps| POST_HOOKS[Run post-task hooks]
    POST_HOOKS --> COMPLETE([yield type:task_complete<br/>status: completed])

    STEP_LOOP -->|Yes| CONDITION{step.condition<br/>evaluates true?}
    CONDITION -->|No| SKIP[yield type:step_skipped<br/>Record in state] --> STEP_LOOP
    CONDITION -->|Yes| STEP_TYPE{step.type?}

    STEP_TYPE -->|TOOL| TOOL_STEP[_execute_tool_step<br/>1. Resolve args_from previous results<br/>2. Safety check via classify_operation<br/>3. Call execute_function]
    TOOL_STEP --> TOOL_RESULT[yield type:function_result<br/>Store in step_results dict]
    TOOL_RESULT --> STEP_LOOP

    STEP_TYPE -->|AGENT| AGENT_STEP[_execute_agent_step<br/>1. Build prompt with step context<br/>2. ai_engine.chat_completion stream<br/>3. Yield stream chunks]
    AGENT_STEP --> AGENT_DONE[Collect streamed text<br/>Store in step_results]
    AGENT_DONE --> STEP_LOOP

    STEP_TYPE -->|GATE| GATE_STEP[_execute_gate_step<br/>1. yield type:confirmation_required<br/>with _event = asyncio.Event<br/>2. await event.wait with 300s timeout]

    GATE_STEP --> GATE_RESULT{User approved?}
    GATE_RESULT -->|Yes| GATE_OK[yield type:gate_result confirmed=true]
    GATE_OK --> STEP_LOOP
    GATE_RESULT -->|No / Timeout| ABORT([yield type:task_complete<br/>status: aborted])

    style COMPLETE fill:#2d6a2d,color:#fff
    style ABORT fill:#8b3a3a,color:#fff
```

**Gate confirmation protocol:** The executor yields a `confirmation_required` message containing a hidden `_event` (an `asyncio.Event`). The WebSocket handler in `server.py` intercepts this, stores the event in `pending_confirmations[request_id]`, and strips the internal `_event` field before sending to the client. When the client sends `{type: "confirm_response", request_id, approved}`, the handler calls `event.set()` to unblock the executor.

---

## 6. Safety Layer

The safety system (`safety.py`) classifies every function call into one of three risk levels and enforces appropriate guardrails.

```mermaid
flowchart LR
    subgraph Classification
        FN[Function name] --> LOOKUP[SAFETY_CLASSIFICATION dict]
        LOOKUP --> LEVEL{SafetyLevel?}
    end

    subgraph SAFE_PATH["SAFE (Read-Only)"]
        S1[discover_*, find_issues<br/>generate_suggestions<br/>save_snapshot, list_*<br/>create_*_handler]
        S2[backup_required = false<br/>confirmation_type = none]
    end

    subgraph MOD_PATH["MODERATE (Low-Risk Write)"]
        M1[configure_ssid, enable_ssid<br/>disable_ssid, create_vlan<br/>update_vlan, backup_config]
        M2[backup_required = true<br/>confirmation_type = confirm<br/>Preview shown to user]
    end

    subgraph DANGER_PATH["DANGEROUS (High-Risk Write)"]
        D1[add_firewall_rule<br/>remove_firewall_rule<br/>add_switch_acl<br/>delete_vlan<br/>rollback_config]
        D2[backup_required = true<br/>confirmation_type = type_confirm<br/>Dry-run first recommended]
    end

    LEVEL -->|SAFE| S1
    S1 --> S2
    LEVEL -->|MODERATE| M1
    M1 --> M2
    LEVEL -->|DANGEROUS| D1
    D1 --> D2

    S2 --> EXEC_DIRECT[Execute immediately]
    M2 --> CONFIRM_WS[Send confirmation via WebSocket<br/>Wait for user approval]
    D2 --> CONFIRM_TYPE[Send typed CONFIRM prompt<br/>Backup current state first]

    CONFIRM_WS --> EXEC_BACKUP[Backup then execute]
    CONFIRM_TYPE --> EXEC_BACKUP

    style S2 fill:#2d6a2d,color:#fff
    style M2 fill:#8a6d2b,color:#fff
    style D2 fill:#8b3a3a,color:#fff
```

**Unclassified functions** default to `DANGEROUS` -- this is a fail-safe that prevents new functions from bypassing safety checks.

Additional safety features in `safety.py`:
- **Rate limiter:** Limits write operations per time window to prevent accidental mass changes.
- **Dry-run mode:** Operations can be previewed without actually applying changes.
- **Undo/rollback:** `execute_undo()` can revert the last operation using backed-up state.

---

## 7. Configuration Write Flow

This diagram shows what happens when a user says **"block telnet on all switches"** -- a DANGEROUS operation that requires confirmation and backup.

```mermaid
sequenceDiagram
    actor User
    participant WS as useWebSocket.ts
    participant Server as server.py
    participant Router as agent_router.py
    participant AIEngine as ai_engine.py
    participant LLM as LLM Provider
    participant Safety as safety.py
    participant Config as config.py
    participant API as api.py
    participant Meraki as Meraki Cloud

    User->>WS: "block telnet on all switches"
    WS->>Server: {type:"message", content:"block telnet on all switches"}

    Server->>Router: process_message(...)
    Router->>Router: classify_intent -> meraki-specialist (0.95)
    Router-->>Server: yield {type:"classification", agent:"meraki-specialist"}

    Note over Router: Legacy LLM Flow (no task_definition)

    Router->>AIEngine: chat_completion(messages, tools, stream=True)
    AIEngine->>LLM: acompletion with meraki-specialist tools
    LLM-->>AIEngine: tool_call: add_switch_acl(network_id="L_123",<br/>policy="deny", protocol="tcp", dst_port="23")

    Router->>Router: _execute_function("add_switch_acl", args)

    Note over Router: executor_utils.execute_function() called

    Router->>Safety: classify_operation("add_switch_acl", args)
    Safety-->>Router: SafetyCheck(level=DANGEROUS,<br/>confirmation_type="type_confirm",<br/>backup_required=true)

    Router->>Safety: before_operation(safety_check)
    Safety->>Config: backup_current_state(network_id)
    Config->>API: GET current ACL state
    API->>Meraki: GET /api/v1/.../switchAccessControlLists
    Meraki-->>API: Current ACL rules
    API-->>Config: ACL snapshot
    Config-->>Safety: Backup saved to clients/NAME/discovery/

    Router-->>Server: yield {type:"confirmation_required",<br/>action:"Add Switch ACL",<br/>preview:"Deny TCP port 23 on network L_123",<br/>danger_level:"high"}

    Server-->>WS: send_json(confirmation_required)
    WS-->>User: ConfirmDialog renders with action preview

    User->>WS: Click "Confirm"
    WS->>Server: {type:"confirm_response", request_id:"r1", approved:true}

    Note over Server: pending_confirmations["r1"].set()

    Router->>Config: add_switch_acl(network_id, policy, protocol, port)
    Config->>API: dashboard.switch.updateNetworkSwitchAccessControlLists(...)
    API->>Meraki: PUT /api/v1/networks/L_123/switch/accessControlLists
    Meraki-->>API: 200 OK
    API-->>Config: Updated ACL
    Config-->>Router: {success: true, rules_applied: 1}

    Router-->>Server: yield {type:"tool_status", function:"add_switch_acl", status:"ok"}

    Note over Router: Feed result back to LLM for NL interpretation

    Router->>AIEngine: chat_completion(messages + tool_result)
    AIEngine->>LLM: acompletion(stream=True)
    LLM-->>AIEngine: "Done. Telnet (TCP/23) is now blocked on..."

    loop Stream response
        AIEngine-->>Router: chunk
        Router-->>Server: yield {type:"stream", chunk:"...", agent:"meraki-specialist"}
        Server-->>WS: send_json(stream)
    end

    Server-->>WS: {type:"done"}
    WS-->>User: Response rendered in chat
```

---

## 8. Component Reference

### Frontend Files

| File | Purpose |
|------|---------|
| `frontend/src/hooks/useWebSocket.ts` | WebSocket connection, reconnect, message dispatch |
| `frontend/src/stores/chatStore.ts` | Zustand store: sessions, messages, streaming state |
| `frontend/src/stores/settingsStore.ts` | Zustand store: app settings, AI provider config |
| `frontend/src/stores/agentStore.ts` | Zustand store: agent list and selection |
| `frontend/src/components/chat/ChatView.tsx` | Main chat view with message list |
| `frontend/src/components/chat/ChatInput.tsx` | Text input with send button |
| `frontend/src/components/chat/MessageBubble.tsx` | Individual message rendering |
| `frontend/src/components/chat/StreamingText.tsx` | Animated streaming text display |
| `frontend/src/components/chat/DataRenderer.tsx` | Structured data (JSON/table) rendering |
| `frontend/src/components/chat/ConfirmDialog.tsx` | Safety confirmation dialog for MODERATE/DANGEROUS ops |
| `frontend/src/components/sidebar/Sidebar.tsx` | Session list + agent indicators |
| `frontend/src/components/onboarding/OnboardingWizard.tsx` | First-run setup wizard |
| `frontend/src/components/settings/SettingsPanel.tsx` | Settings modal with tabs |

### Backend Files

| File | Purpose |
|------|---------|
| `scripts/server.py` | FastAPI app, WebSocket `/ws/chat`, router mounts, CORS |
| `scripts/agent_router.py` | Intent classification, process_message, FUNCTION_REGISTRY |
| `scripts/ai_engine.py` | LiteLLM wrapper: chat_completion, classify, token tracking |
| `scripts/safety.py` | Safety classification, confirmation flows, backup, undo, rate limit |
| `scripts/task_executor.py` | Deterministic step executor (TOOL / AGENT / GATE steps) |
| `scripts/task_registry.py` | YAML task loader and pattern matcher |
| `scripts/task_models.py` | Pydantic/dataclass models for task definitions and run state |
| `scripts/verb_utils.py` | Verb/noun detection for classification boosting |
| `scripts/executor_utils.py` | Shared execute_function and serialize_result helpers |
| `scripts/agent_tools.py` | OpenAI-format tool schemas per agent |
| `scripts/discovery.py` | Network discovery functions (clients, devices, SSIDs, etc.) |
| `scripts/config.py` | Configuration write functions (SSID, VLAN, firewall, ACL) |
| `scripts/workflow.py` | Workflow JSON generation (offline handler, compliance, etc.) |
| `scripts/report.py` | HTML/PDF report generation |
| `scripts/api.py` | Meraki SDK wrapper with rate limiting |
| `scripts/auth.py` | Credential management from `~/.meraki/credentials` |
| `scripts/settings.py` | SettingsManager with encryption |
| `scripts/chat_session.py` | In-memory session/context management |
| `scripts/path_validation.py` | Path traversal protection for file operations |

### Key Data Flows

| Flow | Path |
|------|------|
| User message in | Browser -> WebSocket -> `server.py` -> `agent_router.process_message()` |
| Classification | `classify_intent()` -> prefix / task registry / regex / LLM |
| Read operation | `FUNCTION_REGISTRY` -> `discovery.py` -> `api.py` -> Meraki SDK -> Cloud |
| Write operation | `FUNCTION_REGISTRY` -> `safety.py` check -> `config.py` -> `api.py` -> Meraki SDK |
| LLM interaction | `agent_router.py` -> `ai_engine.chat_completion()` -> LiteLLM -> Provider API |
| Streaming response | `ai_engine.py` yields chunks -> `agent_router.py` yields -> `server.py` sends via WS |
| Task execution | `task_executor.py` steps -> TOOL/AGENT/GATE -> results streamed via WS |
| Confirmation gate | Server stores `asyncio.Event` -> Client sends `confirm_response` -> Event unblocked |

### WebSocket Protocol Summary

| Direction | Message Type | Purpose |
|-----------|-------------|---------|
| Client -> Server | `message` | User chat message with `content` and `session_id` |
| Client -> Server | `confirm_response` | User approval/denial with `request_id` and `approved` |
| Client -> Server | `cancel` | Cancel current operation |
| Client -> Server | `ping` | Keepalive (every 30s) |
| Server -> Client | `stream` | Text chunk with `chunk` and `agent` |
| Server -> Client | `data` | Structured data with `format` and `data` |
| Server -> Client | `classification` | Agent routing result with `agent` and `confidence` |
| Server -> Client | `agent_status` | Agent state: `thinking`, `executing`, `done` |
| Server -> Client | `tool_status` | Tool execution success notification |
| Server -> Client | `function_error` | Tool execution failure |
| Server -> Client | `confirmation_required` | Safety confirmation request with `preview` |
| Server -> Client | `task_start` / `step_start` | Task executor progress |
| Server -> Client | `error` | Error with `message` and `code` |
| Server -> Client | `done` | Message processing complete |
| Server -> Client | `pong` | Keepalive response |
