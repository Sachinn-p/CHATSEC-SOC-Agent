#!/usr/bin/env python3
"""
Launcher entry point for the CHATSEC-SOC-Agent executable.

PyInstaller bundles this file as the top-level script.  It locates the
correct Streamlit runtime and the bundled ``main.py``, then boots the
Streamlit web server in-process.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging – write to both console and a rotating log file next to the .exe
# ---------------------------------------------------------------------------
_log_dir = (
    os.path.dirname(sys.executable)      # next to the .exe when frozen
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(__file__))  # project root in dev
)
LOG_FILE = os.path.join(_log_dir, "chatsec_soc_agent.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("launcher")


def _get_base_dir() -> Path:
    """Return the directory that contains the bundled application files."""
    if getattr(sys, "frozen", False):
        # sys._MEIPASS is PyInstaller's temporary extraction directory where
        # all bundled files are unpacked at runtime.
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # Running as a plain Python script (development mode)
    return Path(__file__).parent.resolve()


def _setup_environment(base_dir: Path) -> None:
    """Configure sys.path and load the .env file."""
    # Ensure the bundled package root is first on sys.path
    base_str = str(base_dir)
    if base_str not in sys.path:
        sys.path.insert(0, base_str)

    # Also add the directory that contains the .exe / this script so that
    # a .env file placed alongside the executable is found automatically.
    exe_dir = str(Path(sys.executable).parent if getattr(sys, "frozen", False)
                  else Path(__file__).parent)
    if exe_dir not in sys.path:
        sys.path.insert(0, exe_dir)

    # Load .env – look next to the .exe first, then inside the bundle
    _load_dotenv(Path(exe_dir) / ".env")
    _load_dotenv(base_dir / ".env")


def _load_dotenv(env_path: Path) -> None:
    """Load a .env file if it exists."""
    if env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=str(env_path), override=False)
            logger.info("Loaded environment variables from %s", env_path)
        except ImportError:
            # Fallback: parse manually
            with open(env_path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        os.environ.setdefault(key.strip(), value.strip())
            logger.info("Loaded environment variables (manual) from %s", env_path)


def _find_main_script(base_dir: Path) -> Path:
    """Return the path to the bundled ``main.py``."""
    candidate = base_dir / "main.py"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(
        f"Could not locate main.py inside the bundle at {base_dir}"
    )


def _run_streamlit(main_script: Path, port: int = 8501) -> None:
    """
    Launch Streamlit with the given script.

    Uses ``streamlit.web.cli`` when running inside a frozen bundle so that
    Streamlit can find its own static assets.
    """
    logger.info("Starting CHATSEC-SOC-Agent on http://localhost:%d …", port)
    logger.info("Press Ctrl+C to stop.")

    # Build the argument list that streamlit expects
    streamlit_args = [
        "streamlit",
        "run",
        str(main_script),
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
    ]

    if getattr(sys, "frozen", False):
        # Inside a PyInstaller bundle: invoke the Streamlit CLI directly so
        # that it picks up its bundled static files correctly.
        try:
            from streamlit.web import cli as stcli
            sys.argv = streamlit_args
            sys.exit(stcli.main())
        except SystemExit:
            raise
        except Exception as exc:
            logger.error("Streamlit internal launch failed: %s", exc)
            raise
    else:
        # Development: delegate to the system ``streamlit`` command
        result = subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(main_script),
             "--server.port", str(port),
             "--server.headless", "true",
             "--browser.gatherUsageStats", "false"],
            check=False,
        )
        sys.exit(result.returncode)


def main() -> None:
    """Entry point."""
    logger.info("=" * 60)
    logger.info("CHATSEC-SOC-Agent launcher starting")
    logger.info("Python %s | frozen=%s", sys.version.split()[0],
                getattr(sys, "frozen", False))

    base_dir = _get_base_dir()
    logger.info("Base directory: %s", base_dir)

    _setup_environment(base_dir)

    try:
        main_script = _find_main_script(base_dir)
        logger.info("Launching main script: %s", main_script)
        _run_streamlit(main_script)
    except FileNotFoundError as exc:
        logger.critical("%s", exc)
        input("Press Enter to exit…")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down (KeyboardInterrupt).")
        sys.exit(0)
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        input("Press Enter to exit…")
        sys.exit(1)


if __name__ == "__main__":
    main()
