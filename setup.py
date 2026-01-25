"""Setup script for Meraki Workflow CLI."""

from pathlib import Path

from setuptools import find_packages, setup

# Read long description from README if available
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

setup(
    name="meraki-workflow",
    version="1.0.0",
    author="josdasil",
    description="Meraki Workflow - Automacao de redes via linguagem natural",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/josdasil/meraki-workflow",
    packages=find_packages(exclude=["tests", "tests.*", "docs", "examples"]),
    python_requires=">=3.10",
    install_requires=[
        "meraki>=1.53.0",
        "click>=8.0",
        "rich>=13.0",
        "python-dotenv>=1.0",
        "pydantic>=2.0",
        "jinja2>=3.1",
    ],
    extras_require={
        "pdf": ["weasyprint>=60.0"],
        "dev": [
            "pytest>=7.0",
            "pytest-mock>=3.0",
            "pytest-cov>=4.0",
            "ruff>=0.1.0",
            "black>=23.0",
            "mypy>=1.0",
        ],
        "all": [
            "weasyprint>=60.0",
            "pytest>=7.0",
            "pytest-mock>=3.0",
            "pytest-cov>=4.0",
            "ruff>=0.1.0",
            "black>=23.0",
            "mypy>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "meraki=scripts.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Networking",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="meraki cisco networking automation workflow",
    project_urls={
        "Documentation": "https://github.com/josdasil/meraki-workflow/docs",
        "Source": "https://github.com/josdasil/meraki-workflow",
        "Tracker": "https://github.com/josdasil/meraki-workflow/issues",
    },
)
