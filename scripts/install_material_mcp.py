#!/usr/bin/env python3
"""Install 素材库MCP locally, collect Teedy credentials safely, and register Codex."""
from __future__ import annotations

import argparse
import getpass
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp_server.settings import credentials_file_path, installation_dir

MCP_ID = "material-library"
LEGACY_MCP_IDS = ("yuki_materials", "yuki-materials")
SKILL_SOURCE = ROOT / "skills" / "material-library"
SKILL_DESTINATION = Path.home() / ".agents" / "skills" / MCP_ID
SERVER = ROOT / "mcp_server" / "server.py"
VERIFY = ROOT / "scripts" / "verify_teedy_account.py"


def python_in_venv() -> Path:
    if os.name == "nt":
        return ROOT / ".venv" / "Scripts" / "python.exe"
    return ROOT / ".venv" / "bin" / "python"


def copy_managed_install() -> Path:
    destination = installation_dir()
    if ROOT.resolve() == destination.resolve():
        return ROOT

    destination.mkdir(parents=True, exist_ok=True)
    for directory in ("mcp_server", "skills/material-library"):
        shutil.copytree(
            ROOT / directory,
            destination / directory,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
        )
    for file_name in ("requirements-mcp.txt", "scripts/install_material_mcp.py", "scripts/verify_teedy_account.py"):
        target = destination / file_name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / file_name, target)
    return destination


def prepare_runtime() -> Path:
    venv_python = python_in_venv()
    if not venv_python.exists():
        subprocess.run([sys.executable, "-m", "venv", str(ROOT / ".venv")], check=True)
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "-r", str(ROOT / "requirements-mcp.txt")],
        check=True,
    )
    return venv_python


def write_pending_credentials(base_url: str, username: str, password: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        path.parent.chmod(0o700)
    data = "\n".join([
        f"YUKI_TEEDY_BASE_URL={base_url}",
        f"YUKI_TEEDY_USERNAME={username}",
        f"YUKI_TEEDY_PASSWORD={password}",
        "",
    ])
    file_descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(file_descriptor, "w", encoding="utf-8") as credentials_file:
        credentials_file.write(data)
    if os.name != "nt":
        path.chmod(0o600)


def verify_credentials(venv_python: Path, path: Path) -> bool:
    child_env = dict(os.environ)
    for name in ("YUKI_TEEDY_BASE_URL", "YUKI_TEEDY_USERNAME", "YUKI_TEEDY_PASSWORD"):
        child_env.pop(name, None)
    child_env["YUKI_TEEDY_CREDENTIALS_FILE"] = str(path)
    result = subprocess.run([str(venv_python), str(VERIFY)], cwd=ROOT, env=child_env, check=False)
    return result.returncode == 0


def install_skill() -> None:
    SKILL_DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SKILL_SOURCE, SKILL_DESTINATION, dirs_exist_ok=True)


def register_codex(venv_python: Path, credentials_path: Path) -> bool:
    codex = shutil.which("codex")
    if not codex:
        return False

    for name in (*LEGACY_MCP_IDS, MCP_ID):
        subprocess.run(
            [codex, "mcp", "remove", name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    subprocess.run(
        [
            codex,
            "mcp",
            "add",
            MCP_ID,
            "--env",
            f"YUKI_TEEDY_CREDENTIALS_FILE={credentials_path}",
            "--",
            str(venv_python),
            str(SERVER),
        ],
        check=True,
    )
    subprocess.run([codex, "mcp", "list"], check=True)
    return True


def register_workbuddy(venv_python: Path, credentials_path: Path) -> Path:
    config_path = Path.home() / ".workbuddy" / "mcp.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"WorkBuddy MCP config is not valid JSON: {config_path}") from exc
    else:
        config = {}

    servers = config.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        raise RuntimeError(f"mcpServers must be a JSON object in {config_path}")
    for name in LEGACY_MCP_IDS:
        servers.pop(name, None)
    servers[MCP_ID] = {
        "type": "stdio",
        "command": str(venv_python),
        "args": [str(SERVER)],
        "env": {"YUKI_TEEDY_CREDENTIALS_FILE": str(credentials_path)},
        "description": "素材库MCP",
    }
    pending = config_path.with_name("mcp.json.pending")
    pending.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(pending, config_path)
    return config_path


def print_manual_config(venv_python: Path, credentials_path: Path) -> None:
    print("Add this stdio server in your MCP client settings:")
    print("  name: material-library")
    print(f'  command: "{venv_python}"')
    print(f'  args: ["{SERVER}"]')
    print(f'  env: {{ "YUKI_TEEDY_CREDENTIALS_FILE": "{credentials_path}" }}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", choices=("auto", "codex", "workbuddy", "manual"), default="auto")
    parser.add_argument("--installed-copy", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if not sys.stdin.isatty():
        parser.error("run this installer in an interactive terminal; the Teedy password is entered without echo")

    client_mode = args.client
    if client_mode == "auto":
        default_choice = "1" if shutil.which("codex") else "3"
        choice = input(f"MCP client: [1] Codex [2] WorkBuddy [3] other client [{default_choice}]: ").strip() or default_choice
        client_mode = {"1": "codex", "2": "workbuddy", "3": "manual"}.get(choice, "manual")

    if not args.installed_copy:
        destination = copy_managed_install()
        if destination.resolve() != ROOT.resolve():
            result = subprocess.run(
                [sys.executable, str(destination / "scripts" / "install_material_mcp.py"), "--installed-copy", "--client", client_mode],
                check=False,
            )
            return result.returncode

    print("Installing 素材库MCP. You will enter your own Teedy account; never use an admin account.")
    venv_python = prepare_runtime()
    base_url = input("Remote Teedy HTTPS URL: ").strip()
    username = input("Your Teedy username: ").strip()
    password = getpass.getpass("Your Teedy password (hidden): ")

    credentials_path = credentials_file_path()
    pending_path = credentials_path.with_name("teedy.env.pending")
    write_pending_credentials(base_url, username, password, pending_path)
    del password
    try:
        verified = verify_credentials(venv_python, pending_path)
    except BaseException:
        pending_path.unlink(missing_ok=True)
        raise
    if not verified:
        pending_path.unlink(missing_ok=True)
        print("Credentials were not installed. Ask the Teedy administrator to confirm the account and readers group.", file=sys.stderr)
        return 1

    try:
        os.replace(pending_path, credentials_path)
    except OSError:
        pending_path.unlink(missing_ok=True)
        raise
    install_skill()
    if client_mode == "codex":
        try:
            registered = register_codex(venv_python, credentials_path)
        except subprocess.CalledProcessError:
            registered = False
        if not registered:
            print("Codex CLI was not found; use the manual MCP settings below.", file=sys.stderr)
            print_manual_config(venv_python, credentials_path)
            return 2
        print(f"Installed skill to {SKILL_DESTINATION}. Start a new Codex thread and type $素材库MCP to search.")
    elif client_mode == "workbuddy":
        config_path = register_workbuddy(venv_python, credentials_path)
        print(f"Registered 素材库MCP in {config_path}. Reload MCP settings in WorkBuddy and type $素材库MCP to search.")
    else:
        print_manual_config(venv_python, credentials_path)
        print(f"Skill source: {SKILL_SOURCE}")
        print("After adding the server and skill, type $素材库MCP to search.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
