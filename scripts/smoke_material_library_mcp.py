#!/usr/bin/env python3
"""Verify a configured Reader/Admin can search/download and MCP exposes no write tools."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcp_server.teedy import TeedyError, load_user_env, user_client

PYTHON = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
SERVER = ROOT / "mcp_server" / "server.py"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def smoke_permissions() -> None:
    creds = load_user_env()
    client = user_client()
    try:
        me = client.whoami()
        if me.get("username") != creds["YUKI_TEEDY_USERNAME"]:
            fail(f"logged in as {me.get('username')}")
        is_admin = "ADMIN" in (me.get("base_functions") or [])
        if not (is_admin or "READ" in (me.get("base_functions") or []) or "readers" in (me.get("groups") or [])):
            fail("configured account has neither ADMIN nor Teedy READ access")
        docs = client.search_documents("", limit=20)
        if int(docs.get("total") or 0) < 1:
            fail("configured account cannot see any documents")
        tags = client.list_tags()
        if len(tags) < 1:
            fail("configured account cannot see tags")
        first = (docs.get("documents") or [])[0]
        files = client.list_files(first["id"])
        if not files:
            fail("configured account cannot list files")
        data, _, _ = client.get_bytes(f"/api/file/{files[0]['id']}/data")
        if not data:
            fail("configured account download empty")
        role = "admin" if is_admin else "reader"
        print(f"OK {role} user {me['username']} sees {docs['total']} docs, {len(tags)} tags, downloaded {len(data)} bytes")
    finally:
        client.close()

    try:
        client = user_client()
        client.json("PUT", "/api/document", {"title": "blocked-by-client", "language": "chi_sim"})
        fail("readonly client allowed PUT")
    except PermissionError:
        print("OK MCP TeedyClient blocks PUT")
    except TeedyError as exc:
        fail(f"expected PermissionError, got TeedyError {exc}")
    finally:
        try:
            client.close()
        except Exception:
            pass


async def smoke_mcp() -> None:
    params = StdioServerParameters(command=str(PYTHON), args=[str(SERVER)], cwd=str(ROOT))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = {t.name for t in (await session.list_tools()).tools}
            expected = {"list_tags", "search_materials", "get_material", "download_file"}
            if tools != expected:
                fail(f"MCP tools should be read/download only; missing={expected - tools}, extra={tools - expected}")
            tags_raw = await session.call_tool("list_tags", {})
            tags = json.loads(tags_raw.content[0].text) if tags_raw.content else {}
            names = [t["name"] for t in tags.get("tags") or []]
            if not {"KET", "PET", "FCE"}.issubset(set(names)):
                fail(f"missing Cambridge exam tags: {[name for name in ('KET', 'PET', 'FCE') if name not in names]}")
            search_raw = await session.call_tool("search_materials", {"tags": ["KET"], "query": "考试时间"})
            search = json.loads(search_raw.content[0].text)
            if search.get("error"):
                fail(f"search error {search}")
            if not search.get("items"):
                fail(f"empty search {search}")
            doc_id = search["items"][0]["id"]
            detail_raw = await session.call_tool("get_material", {"document_id": doc_id})
            detail = json.loads(detail_raw.content[0].text)
            if not detail.get("zip_url"):
                fail(f"missing zip_url {detail}")
            if not detail.get("previews"):
                fail("detail has no previews")
            if not detail.get("files") or not detail["files"][0].get("download_url"):
                fail("detail missing file download_url")
            file_id = detail["files"][0]["id"]
            down_raw = await session.call_tool("download_file", {"file_id": file_id, "filename": detail["files"][0]["name"]})
            down = json.loads(down_raw.content[0].text)
            path = Path(down["path"])
            if not path.exists() or path.stat().st_size < 1:
                fail(f"download missing {down}")
            print(f"OK MCP search {search['used_tags']} -> {len(search['items'])} hits, downloaded {path}")


def main() -> int:
    smoke_permissions()
    asyncio.run(smoke_mcp())
    print("ALL SMOKE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
