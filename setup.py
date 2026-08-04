#!/usr/bin/env python3
"""Register the climate logger as a systemd service."""

from __future__ import annotations

import os
import pwd
import subprocess
import sys
from pathlib import Path


SERVICE_NAME = "environment-logger.service"
PROJECT_ROOT = Path(__file__).resolve().parent
PYTHON_PATH = PROJECT_ROOT / "env" / "bin" / "python"
RUN_PATH = PROJECT_ROOT / "run.py"
SERVICE_PATH = Path("/etc/systemd/system") / SERVICE_NAME
SYSTEMD_RUNTIME_PATH = Path("/run/systemd/system")


def _quote_systemd_path(path: Path) -> str:
    escaped_path = str(path).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped_path}"'


def _service_unit(user: str) -> str:
    return f"""[Unit]
Description=AM2302 Environment Logger
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User={user}
WorkingDirectory={_quote_systemd_path(PROJECT_ROOT)}
ExecStart={_quote_systemd_path(PYTHON_PATH)} -u {_quote_systemd_path(RUN_PATH)}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""


def register_service() -> None:
    """Install, enable, and start the systemd service for this checkout."""
    if sys.platform != "linux":
        raise RuntimeError("Service registration requires Linux with systemd")
    if not SYSTEMD_RUNTIME_PATH.is_dir():
        raise RuntimeError("systemd is not running on this system")
    if os.geteuid() != 0:
        raise PermissionError(f"Run with sudo: sudo {sys.executable} {__file__}")
    if not PYTHON_PATH.is_file():
        raise FileNotFoundError(
            f"Virtual environment Python not found at {PYTHON_PATH}"
        )
    if not RUN_PATH.is_file():
        raise FileNotFoundError(f"Application launcher not found at {RUN_PATH}")

    service_user = pwd.getpwuid(PROJECT_ROOT.stat().st_uid).pw_name
    service_unit = _service_unit(service_user)
    if not SERVICE_PATH.exists() or SERVICE_PATH.read_text(encoding="utf-8") != service_unit:
        SERVICE_PATH.write_text(service_unit, encoding="utf-8")

    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", "--now", SERVICE_NAME], check=True)
    print(f"Registered and started {SERVICE_NAME}")


if __name__ == "__main__":
    register_service()
