#!/usr/bin/env python3
"""
build_exe.py – Automated build script for the CHATSEC-SOC-Agent Windows .EXE

Usage:
    python build_exe.py [--clean] [--upx-dir PATH] [--icon PATH]

Options:
    --clean          Remove previous build/dist directories before building.
    --upx-dir PATH   Path to the directory containing UPX (optional).
    --icon PATH      Path to a .ico file to embed in the executable (optional).
"""

import argparse
import logging
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("build_exe")

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.resolve()
SPEC_FILE = PROJECT_ROOT / "build.spec"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
OUTPUT_DIR = DIST_DIR / "CHATSEC-SOC-Agent"

# Minimum Python version required
MIN_PYTHON = (3, 10)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        logger.error(
            "Python %d.%d or later is required (found %s).",
            *MIN_PYTHON,
            platform.python_version(),
        )
        sys.exit(1)
    logger.info("Python version OK: %s", platform.python_version())


def _check_platform() -> None:
    if platform.system() != "Windows":
        logger.warning(
            "This build script is designed for Windows.  "
            "Building on %s may produce a non-functional Windows .exe.",
            platform.system(),
        )


def _ensure_pyinstaller() -> str:
    """Return the path to the PyInstaller executable, installing if needed."""
    pyinstaller = shutil.which("pyinstaller")
    if pyinstaller:
        logger.info("Found PyInstaller: %s", pyinstaller)
        return pyinstaller

    logger.info("PyInstaller not found – installing via pip…")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"],
        check=True,
    )
    pyinstaller = shutil.which("pyinstaller")
    if not pyinstaller:
        # Try locating via the current interpreter's Scripts directory
        scripts_dir = Path(sys.executable).parent / "Scripts"
        candidate = scripts_dir / "pyinstaller.exe"
        if candidate.exists():
            pyinstaller = str(candidate)

    if not pyinstaller:
        logger.error("Could not locate PyInstaller after installation.")
        sys.exit(1)

    logger.info("PyInstaller installed: %s", pyinstaller)
    return pyinstaller


def _ensure_requirements() -> None:
    """Install project requirements if requirements.txt exists."""
    req_file = PROJECT_ROOT / "requirements.txt"
    if not req_file.exists():
        logger.warning("requirements.txt not found – skipping dependency install.")
        return

    logger.info("Installing project requirements…")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
        check=True,
    )
    logger.info("Requirements installed.")


def _clean_build_dirs() -> None:
    """Remove previous build and dist directories."""
    for directory in (BUILD_DIR, DIST_DIR):
        if directory.exists():
            logger.info("Removing %s …", directory)
            shutil.rmtree(directory)
    logger.info("Clean complete.")


def _run_pyinstaller(
    pyinstaller_path: str,
    upx_dir: str | None,
    icon_path: str | None,
) -> None:
    """Invoke PyInstaller with the project spec file."""
    cmd = [
        pyinstaller_path,
        str(SPEC_FILE),
        "--noconfirm",
        "--log-level", "WARN",
    ]

    if upx_dir:
        cmd += ["--upx-dir", upx_dir]

    if icon_path:
        # The --icon flag is accepted by PyInstaller at the CLI level;
        # it overrides the value defined in the spec file.
        cmd += ["--icon", icon_path]

    logger.info("Running: %s", " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

    if result.returncode != 0:
        logger.error("PyInstaller exited with code %d.", result.returncode)
        sys.exit(result.returncode)


def _copy_runtime_files() -> None:
    """
    Copy files that must sit next to the .exe at runtime but are NOT bundled
    inside the executable (e.g., the .env template, README).
    """
    if not OUTPUT_DIR.exists():
        logger.warning("Output directory not found: %s", OUTPUT_DIR)
        return

    files_to_copy = [
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "README_BUILD.md",
    ]

    # Copy .env.example as a template so users know what to configure
    env_example = PROJECT_ROOT / ".env.example"
    if env_example.exists():
        files_to_copy.append(env_example)

    for src in files_to_copy:
        if src.exists():
            dest = OUTPUT_DIR / src.name
            shutil.copy2(str(src), str(dest))
            logger.info("Copied %s → %s", src.name, dest)

    # Create a blank .env placeholder if none exists in the output directory
    env_dest = OUTPUT_DIR / ".env"
    if not env_dest.exists():
        env_template = OUTPUT_DIR / ".env.example"
        if env_template.exists():
            shutil.copy2(str(env_template), str(env_dest))
            logger.info("Created .env from .env.example template.")
        else:
            env_dest.write_text(
                "# CHATSEC-SOC-Agent environment configuration\n"
                "# Fill in the values below before running the application.\n\n"
                "GROQ_API_KEY=\n"
                "GROQ_MODEL=mixtral-8x7b-32768\n\n"
                "# Wazuh API\n"
                "WAZUH_API_HOST=127.0.0.1\n"
                "WAZUH_API_PORT=55000\n"
                "WAZUH_API_USERNAME=admin\n"
                "WAZUH_API_PASSWORD=\n\n"
                "# Wazuh Indexer\n"
                "WAZUH_INDEXER_HOST=127.0.0.1\n"
                "WAZUH_INDEXER_PORT=9200\n"
                "WAZUH_INDEXER_USERNAME=admin\n"
                "WAZUH_INDEXER_PASSWORD=\n\n"
                "# Optional\n"
                "WAZUH_VERIFY_SSL=false\n"
                "WAZUH_TEST_PROTOCOL=https\n"
                "MAX_AGENT_STEPS=10\n"
                "DEFAULT_PROACTIVE_INTERVAL=60\n",
                encoding="utf-8",
            )
            logger.info("Created blank .env template in output directory.")


def _print_summary() -> None:
    """Print a human-readable build summary."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("Build complete!")
    logger.info("Output directory : %s", OUTPUT_DIR)

    exe_path = OUTPUT_DIR / "CHATSEC-SOC-Agent.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        logger.info("Executable       : %s (%.1f MB)", exe_path, size_mb)
    else:
        logger.warning(
            "Executable not found at expected path %s – "
            "check PyInstaller output above for errors.",
            exe_path,
        )

    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Edit %s\\.env with your API keys and Wazuh credentials.", OUTPUT_DIR)
    logger.info("  2. Run CHATSEC-SOC-Agent.exe to start the application.")
    logger.info(
        "  3. Open http://localhost:8501 in your browser (the app opens "
        "automatically if not headless)."
    )
    logger.info("=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build CHATSEC-SOC-Agent as a standalone Windows .EXE"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        default=False,
        help="Remove previous build/dist directories before building.",
    )
    parser.add_argument(
        "--upx-dir",
        metavar="PATH",
        default=None,
        help="Path to the directory containing the UPX executable.",
    )
    parser.add_argument(
        "--icon",
        metavar="PATH",
        default=None,
        help="Path to a .ico file to embed in the executable.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logger.info("CHATSEC-SOC-Agent – EXE build started")
    logger.info("Project root: %s", PROJECT_ROOT)

    _check_python_version()
    _check_platform()
    _ensure_requirements()

    pyinstaller_path = _ensure_pyinstaller()

    if args.clean:
        _clean_build_dirs()

    _run_pyinstaller(pyinstaller_path, args.upx_dir, args.icon)
    _copy_runtime_files()
    _print_summary()


if __name__ == "__main__":
    main()
