#!/usr/bin/env python3
"""Verify one employee's remote Teedy login and reader access."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import httpx

from mcp_server.teedy import TeedyError, user_client


def main() -> int:
    client = None
    try:
        client = user_client()
        identity = client.whoami()
        groups = identity.get("groups") or []
        if "readers" not in groups:
            raise TeedyError("account is valid but is not in the Teedy readers group; ask the Teedy administrator to add it")

        tags = client.list_tags()
        docs = client.search_documents("", limit=10)
        total_docs = int(docs.get("total") or 0)
        download_probe = "pending_no_files"
        for doc in docs.get("documents") or []:
            files = client.list_files(doc["id"])
            if not files:
                continue
            data, _, _ = client.get_bytes(f"/api/file/{files[0]['id']}/data", params={"size": "thumb"})
            if data:
                download_probe = "ok"
                break
            download_probe = "failed"

        print(
            f"Teedy login=ok user={identity.get('username')} readers_group=ok "
            f"tags={len(tags)} documents={total_docs} preview_download={download_probe}"
        )
        if download_probe == "pending_no_files":
            print("No indexed files are available for a download probe yet; login and group access are valid.")
        return 0
    except (TeedyError, httpx.HTTPError, OSError) as exc:
        print(f"Teedy account verification failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
