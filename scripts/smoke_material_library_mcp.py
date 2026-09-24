#!/usr/bin/env python3
"""Verify the configured Teedy user can search/download and MCP writes are blocked."""
from __future__ import annotations

import asyncio
import json
import os
import sys
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
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


def expect_http_error(method: str, path: str, form=None) -> int:
    creds = load_user_env()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
    login = urllib.parse.urlencode({
        "username": creds["YUKI_TEEDY_USERNAME"],
        "password": creds["YUKI_TEEDY_PASSWORD"],
    }).encode()
    opener.open(urllib.request.Request(creds["YUKI_TEEDY_BASE_URL"] + "/api/user/login", data=login, method="POST")).read()
    data = None
    headers = {}
    if form is not None:
        data = urllib.parse.urlencode(form, doseq=True).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(creds["YUKI_TEEDY_BASE_URL"] + path, data=data, headers=headers, method=method)
    try:
        with opener.open(req, timeout=20) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


def smoke_permissions() -> None:
    creds = load_user_env()
    client = user_client()
    try:
        me = client.whoami()
        if me.get("username") != creds["YUKI_TEEDY_USERNAME"]:
            fail(f"logged in as {me.get('username')}")
        if "ADMIN" in (me.get("base_functions") or []):
            fail("configured MCP user must not have ADMIN")
        docs = client.search_documents("", limit=20)
        if int(docs.get("total") or 0) < 1:
            fail("reader cannot see any documents")
        tags = client.list_tags()
        if len(tags) < 1:
            fail("reader cannot see tags")
        first = (docs.get("documents") or [])[0]
        files = client.list_files(first["id"])
        if not files:
            fail("reader cannot list files")
        data, _, _ = client.get_bytes(f"/api/file/{files[0]['id']}/data")
        if not data:
            fail("reader download empty")
        print(f"OK user {me['username']} sees {docs['total']} docs, {len(tags)} tags, downloaded {len(data)} bytes")
    finally:
        client.close()

    write_existing = expect_http_error(
        "POST",
        f"/api/document/{first_doc_id()}",
        {"title": "should-not-edit", "language": "chi_sim"},
    )
    if write_existing < 400:
        fail(f"reader edited existing document HTTP {write_existing}")
    print(f"OK reader cannot edit existing documents HTTP {write_existing}")
    print("NOTE Teedy's READ permission includes file downloads; only MCP tools are read-only")

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


def first_doc_id() -> str:
    client = user_client()
    try:
        docs = client.search_documents("", limit=1)
        return docs["documents"][0]["id"]
    finally:
        client.close()


async def smoke_mcp() -> None:
    params = StdioServerParameters(command=str(PYTHON), args=[str(SERVER)], cwd=str(ROOT))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = {t.name for t in (await session.list_tools()).tools}
            expected = {"list_tags", "search_materials", "get_material", "download_file"}
            if not expected.issubset(tools):
                fail(f"missing tools {expected - tools}")
            tags_raw = await session.call_tool("list_tags", {})
            tags = json.loads(tags_raw.content[0].text) if tags_raw.content else {}
            names = [t["name"] for t in tags.get("tags") or []]
            if "KETPET" not in names:
                fail(f"KETPET not in reader tags: {names}")
            search_raw = await session.call_tool("search_materials", {"tags": ["KET"], "query": "家长"})
            search = json.loads(search_raw.content[0].text)
            if search.get("error"):
                fail(f"search error {search}")
            if not search.get("items"):
                fail(f"empty search {search}")
            doc_id = search["items"][0]["id"]
            detail_raw = await session.call_tool("get_material", {"document_id": doc_id})
            detail = json.loads(detail_raw.content[0].text)
            if detail.get("writable"):
                fail("reader document is writable")
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
