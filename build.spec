# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for CHATSEC-SOC-Agent Streamlit application.

Build with:
    pyinstaller build.spec
"""

import os
import sys
from pathlib import Path

# Resolve the project root (directory containing this spec file)
spec_root = os.path.dirname(os.path.abspath(SPEC))

# ---------------------------------------------------------------------------
# Helper: collect all data files from a package directory
# ---------------------------------------------------------------------------
def collect_pkg_data(pkg_name):
    """Return (src, dest) tuples for every non-.py file inside a package."""
    try:
        import importlib
        mod = importlib.import_module(pkg_name)
        pkg_dir = Path(mod.__file__).parent
        pairs = []
        for path in pkg_dir.rglob("*"):
            if path.is_file() and path.suffix not in (".py", ".pyc"):
                rel = path.relative_to(pkg_dir.parent)
                pairs.append((str(path), str(rel.parent)))
        return pairs
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Streamlit static assets and metadata
# ---------------------------------------------------------------------------
import streamlit
streamlit_dir = Path(streamlit.__file__).parent

streamlit_datas = [
    (str(streamlit_dir / "static"),       "streamlit/static"),
    (str(streamlit_dir / "runtime"),      "streamlit/runtime"),
    (str(streamlit_dir / "web"),          "streamlit/web"),
    (str(streamlit_dir / "components"),   "streamlit/components"),
]

# Only include paths that actually exist in this Streamlit version
streamlit_datas = [(src, dst) for src, dst in streamlit_datas if Path(src).exists()]

# ---------------------------------------------------------------------------
# Application source and config files
# ---------------------------------------------------------------------------
app_datas = [
    # Application source packages
    (os.path.join(spec_root, "src"),    "src"),
    (os.path.join(spec_root, "config"), "config"),
]

# Include .env if it exists (users can also supply it next to the .exe)
env_file = os.path.join(spec_root, ".env")
if os.path.exists(env_file):
    app_datas.append((env_file, "."))

# MCP server script (launched as a subprocess at runtime)
mcp_script = os.path.join(spec_root, "src", "mcp", "wazuh_mcp_server.py")
if os.path.exists(mcp_script):
    app_datas.append((mcp_script, os.path.join("src", "mcp")))

# ---------------------------------------------------------------------------
# Hidden imports – modules discovered only at runtime
# ---------------------------------------------------------------------------
hidden_imports = [
    # Streamlit internals
    "streamlit",
    "streamlit.web.cli",
    "streamlit.web.server",
    "streamlit.runtime.scriptrunner",
    "streamlit.runtime.state",
    "streamlit.components.v1",
    # Altair / Vega (pulled in by Streamlit)
    "altair",
    "altair.vegalite.v5",
    # Data / async
    "pandas",
    "pandas._libs.tslibs.timedeltas",
    "pandas._libs.tslibs.np_datetime",
    "pandas._libs.tslibs.nattype",
    "pandas._libs.skiplist",
    "numpy",
    "asyncio",
    # LangChain / Groq
    "langchain_groq",
    "langchain_core",
    "langchain_core.messages",
    "langchain_core.prompts",
    "langchain_core.output_parsers",
    # Scheduling
    "apscheduler",
    "apscheduler.schedulers.background",
    "apscheduler.triggers.interval",
    # HTTP / networking
    "requests",
    "httpx",
    "urllib3",
    # MCP
    "fastmcp",
    "mcp",
    # Env / config
    "dotenv",
    "python_dotenv",
    # Database
    "sqlite3",
    # Misc standard-library helpers used by the app
    "email.mime.text",
    "email.mime.multipart",
    "logging.handlers",
    "json",
    "pathlib",
    "typing",
    "importlib.metadata",
    "pkg_resources",
    "pkg_resources.extern",
    # Application packages
    "src",
    "src.core",
    "src.core.agent",
    "src.core.proactive_agents",
    "src.core.wazuh_client",
    "src.database",
    "src.database.models",
    "src.mcp",
    "src.mcp.wazuh_mcp_server",
    "src.ui",
    "src.ui.dashboard",
    "src.ui.chat",
    "src.utils",
    "config",
    "config.settings",
]

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
a = Analysis(
    [os.path.join(spec_root, "launcher.py")],
    pathex=[spec_root],
    binaries=[],
    datas=streamlit_datas + app_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Development-only packages – not needed at runtime
        "pytest",
        "pytest_asyncio",
        "black",
        "flake8",
        "mypy",
        "pre_commit",
        "sphinx",
        "IPython",
        "ipykernel",
        "notebook",
        "matplotlib",
        "tkinter",
        "_tkinter",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# ---------------------------------------------------------------------------
# PYZ archive
# ---------------------------------------------------------------------------
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# ---------------------------------------------------------------------------
# EXE
# ---------------------------------------------------------------------------
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,          # Use COLLECT for a one-folder build
    name="CHATSEC-SOC-Agent",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                       # Compress binaries with UPX if available
    upx_exclude=[],
    console=True,                   # Keep console window for log output
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,                      # Set to an .ico path to add a custom icon
)

# ---------------------------------------------------------------------------
# COLLECT – assemble the one-folder distribution
# ---------------------------------------------------------------------------
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="CHATSEC-SOC-Agent",
)
