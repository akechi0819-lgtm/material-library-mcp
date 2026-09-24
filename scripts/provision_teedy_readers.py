#!/usr/bin/env python3
"""Ensure the readers group can read all existing Teedy tags and documents."""
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp_server.teedy import TeedyClient, TeedyError

PAGE_SIZE = 100
GROUP = "readers"


def ensure_group(client: TeedyClient) -> None:
    try:
        client.json("GET", f"/api/group/{GROUP}")
    except TeedyError as exc:
        if "HTTP 404" not in str(exc):
            raise
        client.json("PUT", "/api/group", {"name": GROUP})
        print(f"created group {GROUP}", flush=True)


def list_all_documents(client: TeedyClient) -> list[dict]:
    documents = []
    offset = 0
    while True:
        page = client.json("GET", "/api/document/list", params={"limit": PAGE_SIZE, "offset": offset})
        batch = page.get("documents") or []
        documents.extend(batch)
        offset += len(batch)
        if not batch or offset >= int(page.get("total") or 0):
            break
    return documents


def ensure_read_acl(client: TeedyClient, source_id: str, *, kind: str) -> bool:
    path = f"/api/tag/{source_id}" if kind == "tag" else f"/api/document/{source_id}"
    detail = client.json("GET", path)
    if any(
        acl.get("type") == "GROUP" and acl.get("name") == GROUP and acl.get("perm") == "READ"
        for acl in detail.get("acls") or []
    ):
        return False
    client.json(
        "PUT",
        "/api/acl",
        {"source": source_id, "perm": "READ", "target": GROUP, "type": "GROUP"},
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="Remote Teedy HTTPS base URL")
    args = parser.parse_args()

    parsed = urlsplit(args.base_url)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    ):
        parser.error("--base-url must be the remote Teedy server's HTTPS URL")

    username = input("Teedy admin username: ").strip()
    password = getpass.getpass("Teedy admin password: ")
    client = TeedyClient(args.base_url, username, password, readonly=False)
    try:
        client.login()
        identity = client.whoami()
        if "ADMIN" not in (identity.get("base_functions") or []):
            raise TeedyError("readers group provisioning requires a Teedy ADMIN account")
        ensure_group(client)
        tags = client.list_tags()
        documents = list_all_documents(client)
        tag_updates = sum(ensure_read_acl(client, tag["id"], kind="tag") for tag in tags)
        document_updates = sum(ensure_read_acl(client, doc["id"], kind="document") for doc in documents)
        print(
            f"readers_group={GROUP} tags={len(tags)} documents={len(documents)} "
            f"new_tag_acls={tag_updates} new_document_acls={document_updates}",
            flush=True,
        )
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
