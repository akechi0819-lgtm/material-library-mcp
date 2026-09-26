import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from mcp_server import server
from mcp_server.teedy import TeedyClient, user_client
from mcp_server.vocab import build_lookup, extract_tags_from_query, remaining_keywords
from scripts import install_material_mcp, verify_teedy_account


class FakeClient:
    base = "https://teedy.example"

    def __init__(self, search_results=None, tags=None):
        self.search_results = search_results or {}
        self.tags = tags or ["KET", "PET", "FCE", "考试", "考试时间", "小红书", "家长"]
        self.searches = []

    def list_tags(self):
        return [{"name": name, "id": name} for name in self.tags]

    def search_documents(self, search, limit=10):
        self.searches.append(search)
        return self.search_results.get(search, {"total": 0, "documents": []})

    def list_files(self, document_id):
        return []

    def close(self):
        pass


class MaterialMcpTests(unittest.TestCase):
    def test_missing_alias_target_does_not_override_real_tags(self):
        lookup = build_lookup(
            ["KET", "PET", "FCE"],
            {"KETPET": ["KET", "PET", "FCE"]},
        )
        self.assertEqual(lookup["ket"], "KET")
        self.assertEqual(lookup["pet"], "PET")
        self.assertEqual(lookup["fce"], "FCE")

    def test_query_tag_inference_drops_nested_terms_and_caps_results(self):
        inferred = extract_tags_from_query(
            "家长了解 KET 考试时间的小红书素材",
            ["考试", "考试时间", "KET", "小红书", "家长"],
        )
        self.assertEqual(inferred, ["考试时间", "KET", "小红书"])

    def test_remaining_keywords_removes_ascii_tags_case_insensitively(self):
        leftover = remaining_keywords("Get KET 考试时间", ["KET", "考试时间"], ["KET", "考试时间"])
        self.assertEqual(leftover, "Get")

    def test_search_drops_zero_hit_tags_and_retries_tag_and_only(self):
        document = {"id": "doc-1", "title": "KET 考试时间", "tags": [], "description": ""}
        client = FakeClient({
            "tag:KET": {"total": 39, "documents": []},
            "tag:考试时间": {"total": 1, "documents": []},
            "tag:家长": {"total": 0, "documents": []},
            "tag:KET tag:考试时间 家长": {"total": 0, "documents": []},
            "tag:KET tag:考试时间": {"total": 1, "documents": [document]},
        })
        with patch.object(server, "_client", return_value=client):
            result = server.search_materials(tags=["KET"], query="家长考试时间")

        self.assertEqual(result["used_tags"], ["KET", "考试时间"])
        self.assertEqual(result["empty_tags"], ["家长"])
        self.assertEqual(result["match"], "tag_and")
        self.assertEqual([item["id"] for item in result["items"]], ["doc-1"])
        self.assertNotIn("tag_or", client.searches)

    def test_failed_tag_and_does_not_fallback_to_or_or_keyword_search(self):
        client = FakeClient({
            "tag:KET": {"total": 39, "documents": []},
            "tag:PET": {"total": 28, "documents": []},
            "tag:KET tag:PET": {"total": 0, "documents": []},
        })
        with patch.object(server, "_client", return_value=client):
            result = server.search_materials(tags=["KET", "PET"])

        self.assertEqual(result["items"], [])
        self.assertEqual(result["match"], "tag_and")
        self.assertEqual(client.searches, ["tag:KET", "tag:PET", "tag:KET tag:PET"])

    def test_admin_login_is_accepted_but_mcp_client_still_blocks_writes(self):
        class LoggedInAdmin:
            def __init__(self, *args, **kwargs):
                self.readonly = kwargs["readonly"]

            def login(self):
                pass

            def close(self):
                pass

        with patch("mcp_server.teedy.load_user_env", return_value={
            "YUKI_TEEDY_BASE_URL": "https://teedy.example",
            "YUKI_TEEDY_USERNAME": "admin",
            "YUKI_TEEDY_PASSWORD": "secret",
        }), patch("mcp_server.teedy.TeedyClient", LoggedInAdmin):
            client = user_client()
        self.assertTrue(client.readonly)
        with self.assertRaises(PermissionError):
            TeedyClient._check(client, "POST", "/api/document")

    def test_verify_accepts_admin_and_reader(self):
        class IdentityClient:
            identity = {}

            def whoami(self):
                return self.identity

            def close(self):
                pass

        client = IdentityClient()
        for identity in (
            {"username": "admin", "base_functions": ["ADMIN"], "groups": ["administrators"]},
            {"username": "reader", "base_functions": [], "groups": ["readers"]},
            {"username": "reader-function", "base_functions": ["READ"], "groups": []},
        ):
            client.identity = identity
            with patch.object(verify_teedy_account, "user_client", return_value=client), redirect_stdout(io.StringIO()):
                self.assertEqual(verify_teedy_account.main(), 0)

    def test_installer_reads_credentials_as_json_without_echoing(self):
        secret = {"base_url": "https://teedy.example", "username": "employee", "password": "not-for-logs"}
        with patch.object(install_material_mcp.sys, "stdin", io.StringIO(json.dumps(secret))):
            self.assertEqual(install_material_mcp.read_chat_credentials(), secret)


if __name__ == "__main__":
    unittest.main()
