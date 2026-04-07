# Building CHATSEC-SOC-Agent as a Standalone Windows .EXE

This document explains how to package the CHATSEC-SOC-Agent Streamlit application
into a self-contained Windows executable (`.exe`) that end-users can run without
installing Python.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (One-Click Build)](#quick-start-one-click-build)
3. [Manual Build Steps](#manual-build-steps)
4. [Build Script Options](#build-script-options)
5. [Distributing the Application](#distributing-the-application)
6. [Running the Executable](#running-the-executable)
7. [Configuration (.env)](#configuration-env)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Customisation](#advanced-customisation)

---

## Prerequisites

| Requirement | Minimum Version | Notes |
|---|---|---|
| Windows | 10 / 11 (64-bit) | Build machine only – the output runs on any supported Windows version |
| Python | 3.10+ | Must be on the system `PATH` |
| Internet access | – | Required to download PyInstaller and project dependencies |
| Disk space | ~2 GB free | PyInstaller and dependencies can be large |

> **Tip:** Install Python from <https://www.python.org/downloads/windows/> and
> check **"Add Python to PATH"** during installation.

---

## Quick Start (One-Click Build)

1. Open **Command Prompt** or **PowerShell** in the project root directory.
2. Double-click **`build_exe.bat`**, or run it from the command line:

   ```bat
   build_exe.bat
   ```

3. Wait for the build to finish (typically 2–5 minutes on first run).
4. The finished executable is placed in:

   ```
   dist\CHATSEC-SOC-Agent\CHATSEC-SOC-Agent.exe
   ```

---

## Manual Build Steps

If you prefer a step-by-step approach, or if `build_exe.bat` is not suitable for
your environment:

### Step 1 – Install Python dependencies

```bat
pip install -r requirements.txt
pip install pyinstaller
```

### Step 2 – (Optional) Clean previous build artefacts

```bat
rmdir /S /Q build dist
```

### Step 3 – Run PyInstaller

```bat
pyinstaller build.spec --noconfirm
```

Alternatively, delegate to the Python helper script:

```bat
python build_exe.py
python build_exe.py --clean        # clean build
python build_exe.py --upx-dir C:\upx  # compress with UPX
```

### Step 4 – Verify the output

```
dist\
└── CHATSEC-SOC-Agent\
    ├── CHATSEC-SOC-Agent.exe   ← main executable
    ├── .env                    ← configuration template
    ├── README.md
    └── ...                     ← bundled libraries & assets
```

---

## Build Script Options

### `build_exe.bat`

```
build_exe.bat [options]

Options forwarded to build_exe.py:
  --clean          Remove build/ and dist/ before building
  --upx-dir PATH   Path to a directory containing the UPX binary
  --icon PATH      Path to a .ico file to embed in the executable
  --help           Show all available options
```

### `build_exe.py`

```
python build_exe.py [--clean] [--upx-dir PATH] [--icon PATH]
```

| Flag | Description |
|---|---|
| `--clean` | Delete previous `build/` and `dist/` directories first |
| `--upx-dir PATH` | Use [UPX](https://upx.github.io/) to compress the bundled binaries (reduces `.exe` size by ~30–50%) |
| `--icon PATH` | Path to a `.ico` file to use as the application icon |

---

## Distributing the Application

The build produces a **one-folder distribution** inside `dist\CHATSEC-SOC-Agent\`.
Distribute the **entire folder** to end-users; the `.exe` alone will not work.

Recommended distribution options:

* **ZIP archive** – Zip the entire `dist\CHATSEC-SOC-Agent\` folder.
* **Installer** – Use [Inno Setup](https://jrsoftware.org/isinfo.php) or
  [NSIS](https://nsis.sourceforge.io/) to wrap the folder in a proper installer.
* **Network share** – Copy the folder to a shared drive that users can access.

---

## Running the Executable

1. Extract / copy the `CHATSEC-SOC-Agent\` folder to the target machine.
2. **Edit `.env`** with the required credentials (see [Configuration](#configuration-env)).
3. Double-click **`CHATSEC-SOC-Agent.exe`** or run it from Command Prompt:

   ```bat
   CHATSEC-SOC-Agent.exe
   ```

4. The application starts a local web server. Open a browser and navigate to:

   ```
   http://localhost:8501
   ```

> A console window will remain open showing log output. Close it to stop the
> application.

---

## Configuration (.env)

The application reads settings from a `.env` file located in the **same
directory as the executable**. A template is created automatically during the
build; fill it in before running the application:

```dotenv
# ── LLM ────────────────────────────────────────────────────────────────────
GROQ_API_KEY=<your Groq API key>
GROQ_MODEL=mixtral-8x7b-32768

# ── Wazuh API ───────────────────────────────────────────────────────────────
WAZUH_API_HOST=<wazuh-manager-hostname-or-ip>
WAZUH_API_PORT=55000
WAZUH_API_USERNAME=admin
WAZUH_API_PASSWORD=<wazuh-api-password>

# ── Wazuh Indexer ───────────────────────────────────────────────────────────
WAZUH_INDEXER_HOST=<indexer-hostname-or-ip>
WAZUH_INDEXER_PORT=9200
WAZUH_INDEXER_USERNAME=admin
WAZUH_INDEXER_PASSWORD=<indexer-password>

# ── Optional ────────────────────────────────────────────────────────────────
WAZUH_VERIFY_SSL=false
WAZUH_TEST_PROTOCOL=https
MAX_AGENT_STEPS=10
DEFAULT_PROACTIVE_INTERVAL=60
```

> **Security note:** Never commit a `.env` file with real credentials to a
> public repository.

---

## Troubleshooting

### Application fails to start / shows a configuration error

* Ensure the `.env` file exists in the same folder as the `.exe` and all
  required keys (`GROQ_API_KEY`, `WAZUH_API_PASSWORD`, `WAZUH_INDEXER_PASSWORD`)
  are set.

### `ModuleNotFoundError` in the console

* Rebuild with `--clean` to ensure a fresh bundle.
* Open an issue with the full traceback so a hidden import can be added to
  `build.spec`.

### Antivirus flags the executable

* This is a known false positive with PyInstaller-generated binaries.
* Sign the executable with a code-signing certificate to reduce false positives.
* Add an exclusion for the `CHATSEC-SOC-Agent\` folder in your antivirus software.

### The browser does not open automatically

* Navigate manually to `http://localhost:8501`.
* If port 8501 is already in use, the application will fail to start. Stop the
  conflicting process or change the port by editing `launcher.py` before
  rebuilding.

### Build fails with `FileNotFoundError: launcher.py`

* Ensure `launcher.py` is present in the project root alongside `build.spec`.

### Build fails on a non-Windows machine

* The `.exe` format is Windows-specific. To build for Windows from Linux/macOS,
  use a Windows virtual machine or a GitHub Actions Windows runner.

---

## Advanced Customisation

### Adding a custom application icon

1. Place a `.ico` file in the project root (e.g., `icon.ico`).
2. Build with the `--icon` flag:

   ```bat
   build_exe.bat --icon icon.ico
   ```

   Or edit `build.spec` directly and set the `icon` parameter in the `EXE` block.

### Compressing with UPX

[UPX](https://upx.github.io/) can reduce the size of native libraries in the
bundle by ~30–50%:

1. Download UPX and extract it (e.g., to `C:\upx\`).
2. Build with:

   ```bat
   build_exe.bat --upx-dir C:\upx
   ```

### Changing the default port

Edit the `_run_streamlit` function in `launcher.py` and change the `port`
default value, then rebuild.

### One-file executable

Edit `build.spec` and replace the `COLLECT` block with a `onefile=True` EXE
(remove `exclude_binaries=True` from the `EXE` call and add `a.binaries`,
`a.zipfiles`, `a.datas` directly). Be aware that one-file builds have a slower
startup time because they unpack to a temp directory on each launch.
