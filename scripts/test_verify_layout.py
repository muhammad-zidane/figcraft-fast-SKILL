"""
test_verify_layout.py - Unit tests for Stage 3.4.1: Verify Layout Audit Integrity.
Tests verify_layout() against false-positives on pre-verify flush failure, RPC failure,
unresolved frame_refs, empty targets, null node.get, ID mismatch, and clean/violating trees.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import figcraft_ui
from figcraft_ui import FigCraftClient, FigCraftError


class TestVerifyLayoutIntegrity(unittest.TestCase):

    def _create_client(self, strict=True, auto_batch=True):
        with patch.object(figcraft_ui.socket, "socket") as mock_sock_cls:
            mock_sock = MagicMock()
            mock_sock_cls.return_value = mock_sock
            client = FigCraftClient(
                host="127.0.0.1",
                port=7979,
                auto_batch=auto_batch,
                strict=strict
            )
            return client, mock_sock

    def test_01_strict_false_pre_verify_flush_failure_aborts_audit(self):
        """Test 1 (VL-01): strict=False pre-verify flush failure returns ok=False without running node.find/node.get."""
        client, _ = self._create_client(strict=False)
        client.create_frame(name="PendingFrame", width=400, height=300)

        # Simulate flush failure in strict=False (e.g. non-list or step failure)
        with patch.object(client, "execute", return_value=[{"step": 0, "command": "node.create", "ok": False, "error": "create failed"}]) as mock_exec:
            res = client.verify_layout()

            # execute was only called once for command.batch, NOT for node.find or node.get
            mock_exec.assert_called_once()
            self.assertEqual(mock_exec.call_args[0][0], "command.batch")
            self.assertFalse(res["ok"])
            self.assertIn("create failed", res["error"])
            self.assertIn("create failed", client.last_error)
            self.assertIsNotNone(client.last_failed_batch)

    def test_02_strict_false_node_find_failure_returns_not_ok(self):
        """Test 2 (VL-01): strict=False node.find failure or malformed response returns ok=False."""
        client, mock_sock = self._create_client(strict=False)
        # Simulate socket timeout during node.find in strict=False
        mock_sock.recv.side_effect = figcraft_ui.socket.timeout("recv timed out")

        res = client.verify_layout()

        self.assertFalse(res["ok"])
        self.assertIn("Timeout", res["error"])
        self.assertEqual(client.last_failure_stage, "RECV_AMBIGUOUS")

        # Also test malformed node.find response (missing 'ids' list)
        client2, _ = self._create_client(strict=False)
        with patch.object(client2, "execute", return_value={"unexpected": "payload"}):
            res2 = client2.verify_layout()
            self.assertFalse(res2["ok"])
            self.assertIn("expected dict with 'ids' list", res2["error"])

    def test_03_unresolved_or_dangling_frame_references_rejected(self):
        """Test 3 (VL-03): Unresolved or invalid frame_refs are rejected on both strict=True and strict=False."""
        # 3a. strict=True raises FigCraftError
        client_strict, _ = self._create_client(strict=True)
        with self.assertRaises(FigCraftError) as ctx:
            client_strict.verify_layout(frame_refs=[{"$ref": "nonexistent_frame"}])
        self.assertIn("Unresolved or invalid frame reference at index 0", str(ctx.exception))
        self.assertIn("Unresolved or invalid frame reference", client_strict.last_error)

        # Invalid boolean ref in strict=True
        with self.assertRaises(FigCraftError):
            client_strict.verify_layout(frame_refs=[True])

        # 3b. strict=False returns ok=False
        client_loose, _ = self._create_client(strict=False)
        res = client_loose.verify_layout(frame_refs=[{"$ref": "nonexistent_frame"}])
        self.assertFalse(res["ok"])
        self.assertIn("Unresolved or invalid frame reference at index 0", res["error"])
        self.assertEqual(client_loose.last_error, res["error"])

    def test_04_empty_frame_refs_rejected(self):
        """Test 4 (VL-06): Passing explicit empty frame_refs=[] is rejected and does not fall back to node.find."""
        # 4a. strict=True raises FigCraftError
        client_strict, _ = self._create_client(strict=True)
        with patch.object(client_strict, "execute") as mock_exec:
            with self.assertRaises(FigCraftError) as ctx:
                client_strict.verify_layout(frame_refs=[])
            mock_exec.assert_not_called()
            self.assertIn("non-empty list", str(ctx.exception))

        # 4b. strict=False returns ok=False
        client_loose, _ = self._create_client(strict=False)
        with patch.object(client_loose, "execute") as mock_exec_loose:
            res = client_loose.verify_layout(frame_refs=[])
            mock_exec_loose.assert_not_called()
            self.assertFalse(res["ok"])
            self.assertIn("non-empty list", res["error"])

    def test_05_node_find_returning_empty_ids_fails_audit(self):
        """Test 5 (VL-06): When node.find returns {'ids': []}, verify_layout fails instead of returning ok=True."""
        # 5a. strict=True raises FigCraftError
        client_strict, _ = self._create_client(strict=True)
        with patch.object(client_strict, "execute", return_value={"ids": [], "total": 0}):
            with self.assertRaises(FigCraftError) as ctx:
                client_strict.verify_layout()
            self.assertIn("No target frames found on canvas to audit", str(ctx.exception))

        # 5b. strict=False returns ok=False
        client_loose, _ = self._create_client(strict=False)
        with patch.object(client_loose, "execute", return_value={"ids": [], "total": 0}):
            res = client_loose.verify_layout()
            self.assertFalse(res["ok"])
            self.assertIn("No target frames found on canvas to audit", res["error"])

    def test_06_node_get_returning_null_fails_audit(self):
        """Test 6 (VL-02): When root node.get returns None (null), verify_layout fails on both modes."""
        # 6a. strict=True raises FigCraftError
        client_strict, _ = self._create_client(strict=True)
        with patch.object(client_strict, "execute", return_value=None):
            with self.assertRaises(FigCraftError) as ctx:
                client_strict.verify_layout(frame_refs=[999999])
            self.assertIn("Failed to fetch frame 999999 in verify_layout: expected dict, got NoneType", str(ctx.exception))

        # 6b. strict=False returns ok=False
        client_loose, _ = self._create_client(strict=False)
        with patch.object(client_loose, "execute", return_value=None):
            res = client_loose.verify_layout(frame_refs=[999999])
            self.assertFalse(res["ok"])
            self.assertIn("Failed to fetch frame 999999 in verify_layout: expected dict, got NoneType", res["error"])

    def test_07_node_get_returning_mismatched_id_fails_audit(self):
        """Test 7 (VL-02): When root node.get returns a dict with mismatched or non-int ID, verify_layout fails."""
        # 7a. strict=True raises FigCraftError
        client_strict, _ = self._create_client(strict=True)
        with patch.object(client_strict, "execute", return_value={"id": 202, "name": "WrongFrame", "type": "FRAME"}):
            with self.assertRaises(FigCraftError) as ctx:
                client_strict.verify_layout(frame_refs=[101])
            self.assertIn("mismatched or invalid id 202", str(ctx.exception))

        # 7b. strict=False returns ok=False
        client_loose, _ = self._create_client(strict=False)
        with patch.object(client_loose, "execute", return_value={"id": 202, "name": "WrongFrame", "type": "FRAME"}):
            res = client_loose.verify_layout(frame_refs=[101])
            self.assertFalse(res["ok"])
            self.assertIn("mismatched or invalid id 202", res["error"])

    def test_08_regression_clean_and_violating_trees(self):
        """Test 8: Clean trees return ok=True and violating trees accurately report violations."""
        client, _ = self._create_client(strict=True)

        # 8a. Clean tree -> ok=True, violation_count=0
        clean_tree = {
            "id": 100,
            "name": "CleanDashboard",
            "type": "FRAME",
            "absoluteBounds": {"x": 0, "y": 0, "width": 1440, "height": 900},
            "layout": "vertical",
            "fills": [{"color": "#FFFFFF"}],
            "children": [
                {
                    "id": 101,
                    "name": "HeaderCard",
                    "type": "FRAME",
                    "absoluteBounds": {"x": 24, "y": 24, "width": 1392, "height": 80},
                    "layout": "horizontal",
                    "fills": [{"color": "#F5F5F5"}],
                    "children": [
                        {
                            "id": 102,
                            "name": "TitleText",
                            "type": "TEXT",
                            "absoluteBounds": {"x": 40, "y": 40, "width": 200, "height": 24},
                            "children": []
                        }
                    ]
                }
            ]
        }
        with patch.object(client, "execute", return_value=clean_tree):
            res_clean = client.verify_layout(frame_refs=[100])
            self.assertTrue(res_clean["ok"])
            self.assertEqual(res_clean["violation_count"], 0)
            self.assertEqual(res_clean["violations"], [])

        # 8b. Violating tree -> ok=False with child_overflow and zero_size violations
        violating_tree = {
            "id": 200,
            "name": "BrokenScreen",
            "type": "FRAME",
            "absoluteBounds": {"x": 0, "y": 0, "width": 400, "height": 300},
            "layout": "vertical",
            "fills": [{"color": "#FFFFFF"}],
            "children": [
                {
                    "id": 201,
                    "name": "OverflowBox",
                    "type": "FRAME",
                    "absoluteBounds": {"x": 0, "y": 0, "width": 500, "height": 300},
                    "children": []
                },
                {
                    "id": 202,
                    "name": "ZeroSizeBox",
                    "type": "FRAME",
                    "absoluteBounds": {"x": 10, "y": 10, "width": 0, "height": 50},
                    "children": []
                }
            ]
        }
        with patch.object(client, "execute", return_value=violating_tree):
            res_bad = client.verify_layout(frame_refs=[200])
            self.assertFalse(res_bad["ok"])
            self.assertEqual(res_bad["violation_count"], 2)
            kinds = {v["kind"] for v in res_bad["violations"]}
            self.assertEqual(kinds, {"child_overflow", "zero_size"})

    def test_09_lazy_fetch_updates_absolute_bounds(self):
        """Test 9 (Stage 3.4.2): Lazy fetch updates absoluteBounds so zero_size and child_overflow are detected."""
        client, _ = self._create_client(strict=True)

        root_tree = {
            "id": 300,
            "name": "RootScreen",
            "type": "FRAME",
            "absoluteBounds": {"x": 0, "y": 0, "width": 400, "height": 300},
            "children": [
                # Shallow summary lacking absoluteBounds and children, with childCount=1
                {"id": 301, "type": "FRAME", "childCount": 1}
            ]
        }
        lazy_301 = {
            "id": 301,
            "name": "LazyOverflowZeroCard",
            "type": "FRAME",
            "absoluteBounds": {"x": 0, "y": 0, "width": 450, "height": 0},
            "childCount": 1,
            "children": [
                {
                    "id": 302,
                    "name": "InnerLeaf",
                    "type": "RECT",
                    "absoluteBounds": {"x": 10, "y": 10, "width": 50, "height": 50},
                    "children": []
                }
            ]
        }

        def fake_exec(cmd, params=None):
            if cmd == "node.get" and params["id"] == 300:
                return root_tree
            if cmd == "node.get" and params["id"] == 301:
                return lazy_301
            raise AssertionError(f"Unexpected execute call: {cmd} {params}")

        with patch.object(client, "execute", side_effect=fake_exec):
            res = client.verify_layout(frame_refs=[300])
            self.assertFalse(res["ok"])
            kinds = {v["kind"] for v in res["violations"]}
            self.assertIn("child_overflow", kinds)
            self.assertIn("zero_size", kinds)

    def test_10_lazy_fetch_updates_layout_and_visual_properties(self):
        """Test 10 (Stage 3.4.2): Lazy fetch updates layout, fills, strokes, strokeWeight for sibling_overlap & unpadded_visual_box."""
        client, _ = self._create_client(strict=True)

        root_tree = {
            "id": 400,
            "name": "RootScreen",
            "type": "FRAME",
            "absoluteBounds": {"x": 0, "y": 0, "width": 800, "height": 600},
            "children": [
                # Shallow summary without layout, fills, strokes, or bounds
                {"id": 401, "type": "FRAME", "childCount": 2}
            ]
        }
        lazy_401 = {
            "id": 401,
            "name": "LazyVisualContainer",
            "type": "FRAME",
            "absoluteBounds": {"x": 20, "y": 20, "width": 300, "height": 200},
            "layout": "vertical",
            "fills": [{"color": "#FFFFFF"}],
            "strokes": [{"color": "#000000"}],
            "strokeWeight": 2,
            "childCount": 2,
            "children": [
                {
                    "id": 402,
                    "name": "FlushText",
                    "type": "TEXT",
                    # Flush at (20, 20) -> triggers unpadded_visual_box; overlaps with 403 -> triggers sibling_overlap
                    "absoluteBounds": {"x": 20, "y": 20, "width": 100, "height": 40},
                    "children": []
                },
                {
                    "id": 403,
                    "name": "OverlappingSibling",
                    "type": "FRAME",
                    "absoluteBounds": {"x": 25, "y": 25, "width": 100, "height": 40},
                    "children": []
                }
            ]
        }

        def fake_exec(cmd, params=None):
            if cmd == "node.get" and params["id"] == 400:
                return root_tree
            if cmd == "node.get" and params["id"] == 401:
                return lazy_401
            raise AssertionError(f"Unexpected execute call: {cmd} {params}")

        with patch.object(client, "execute", side_effect=fake_exec):
            res = client.verify_layout(frame_refs=[400])
            self.assertFalse(res["ok"])
            kinds = {v["kind"] for v in res["violations"]}
            self.assertIn("unpadded_visual_box", kinds)
            self.assertIn("sibling_overlap", kinds)

    def test_11_child_subtree_audited_after_lazy_fetch(self):
        """Test 11 (Stage 3.4.2): Grandchildren inside a lazy-fetched child subtree are recursively audited."""
        client, _ = self._create_client(strict=True)

        root_tree = {
            "id": 500,
            "name": "RootScreen",
            "type": "FRAME",
            "absoluteBounds": {"x": 0, "y": 0, "width": 800, "height": 600},
            "children": [
                {"id": 501, "type": "FRAME", "childCount": 1}
            ]
        }
        lazy_501 = {
            "id": 501,
            "name": "MidContainer",
            "type": "FRAME",
            "absoluteBounds": {"x": 10, "y": 10, "width": 400, "height": 300},
            "childCount": 1,
            "children": [
                {
                    "id": 502,
                    "name": "DeepNestedZero",
                    "type": "FRAME",
                    "absoluteBounds": {"x": 20, "y": 20, "width": 0, "height": 50},
                    "children": []
                }
            ]
        }

        with patch.object(client, "execute", side_effect=[root_tree, lazy_501]):
            res = client.verify_layout(frame_refs=[500])
            self.assertFalse(res["ok"])
            self.assertEqual(res["violation_count"], 1)
            self.assertEqual(res["violations"][0]["node_id"], 502)
            self.assertEqual(res["violations"][0]["kind"], "zero_size")

    def test_12_group_children_are_traversed(self):
        """Test 12 (Stage 3.4.2): GROUP node does not block traversal of its children subtree."""
        client, _ = self._create_client(strict=True)

        root_tree = {
            "id": 600,
            "name": "RootScreen",
            "type": "FRAME",
            "absoluteBounds": {"x": 0, "y": 0, "width": 800, "height": 600},
            "children": [
                {
                    "id": 601,
                    "name": "WrapperGroup",
                    "type": "GROUP",
                    "absoluteBounds": {"x": 10, "y": 10, "width": 400, "height": 300},
                    "children": [
                        {
                            "id": 602,
                            "name": "InnerFrameInsideGroup",
                            "type": "FRAME",
                            "absoluteBounds": {"x": 20, "y": 20, "width": 200, "height": 100},
                            "children": [
                                {
                                    "id": 603,
                                    "name": "OverflowChildInGroup",
                                    "type": "RECT",
                                    "absoluteBounds": {"x": 20, "y": 20, "width": 350, "height": 100},
                                    "children": []
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        with patch.object(client, "execute", return_value=root_tree):
            res = client.verify_layout(frame_refs=[600])
            self.assertFalse(res["ok"])
            self.assertEqual(res["violation_count"], 1)
            self.assertEqual(res["violations"][0]["child_id"], 603)
            self.assertEqual(res["violations"][0]["kind"], "child_overflow")

    def test_13_section_children_are_traversed(self):
        """Test 13 (Stage 3.4.2): SECTION node does not block traversal of its children subtree."""
        client, _ = self._create_client(strict=True)

        root_tree = {
            "id": 700,
            "name": "RootScreen",
            "type": "FRAME",
            "absoluteBounds": {"x": 0, "y": 0, "width": 800, "height": 600},
            "children": [
                {
                    "id": 701,
                    "name": "MainSection",
                    "type": "SECTION",
                    "absoluteBounds": {"x": 10, "y": 10, "width": 500, "height": 400},
                    "children": [
                        {
                            "id": 702,
                            "name": "ZeroFrameInsideSection",
                            "type": "FRAME",
                            "absoluteBounds": {"x": 20, "y": 20, "width": 100, "height": 0},
                            "children": []
                        }
                    ]
                }
            ]
        }

        with patch.object(client, "execute", return_value=root_tree):
            res = client.verify_layout(frame_refs=[700])
            self.assertFalse(res["ok"])
            self.assertEqual(res["violation_count"], 1)
            self.assertEqual(res["violations"][0]["node_id"], 702)
            self.assertEqual(res["violations"][0]["kind"], "zero_size")

    def test_14_lazy_fetch_returning_null_fails_audit(self):
        """Test 14 (Stage 3.4.2): Lazy fetch returning None fails the audit on both strict=True and strict=False."""
        root_tree = {
            "id": 800,
            "name": "RootScreen",
            "type": "FRAME",
            "absoluteBounds": {"x": 0, "y": 0, "width": 800, "height": 600},
            "children": [
                {"id": 801, "type": "FRAME", "childCount": 2}
            ]
        }

        # strict=True
        client_strict, _ = self._create_client(strict=True)
        with patch.object(client_strict, "execute", side_effect=[root_tree, None]):
            with self.assertRaises(FigCraftError) as ctx:
                client_strict.verify_layout(frame_refs=[800])
            self.assertIn("Lazy fetch for node 801 in verify_layout failed: expected dict, got NoneType", str(ctx.exception))

        # strict=False
        client_loose, _ = self._create_client(strict=False)
        with patch.object(client_loose, "execute", side_effect=[root_tree, None]):
            res = client_loose.verify_layout(frame_refs=[800])
            self.assertFalse(res["ok"])
            self.assertIn("Lazy fetch for node 801 in verify_layout failed", res["error"])

    def test_15_lazy_fetch_returning_mismatched_id_fails_audit(self):
        """Test 15 (Stage 3.4.2): Lazy fetch returning a dict with mismatched ID fails the audit."""
        root_tree = {
            "id": 900,
            "name": "RootScreen",
            "type": "FRAME",
            "absoluteBounds": {"x": 0, "y": 0, "width": 800, "height": 600},
            "children": [
                {"id": 901, "type": "FRAME", "childCount": 1}
            ]
        }
        wrong_lazy = {
            "id": 999,
            "name": "WrongNode",
            "type": "FRAME",
            "children": [{"id": 902, "type": "RECT", "children": []}]
        }

        # strict=True
        client_strict, _ = self._create_client(strict=True)
        with patch.object(client_strict, "execute", side_effect=[root_tree, wrong_lazy]):
            with self.assertRaises(FigCraftError) as ctx:
                client_strict.verify_layout(frame_refs=[900])
            self.assertIn("Invalid lazy-fetch response for node 901", str(ctx.exception))

        # strict=False
        client_loose, _ = self._create_client(strict=False)
        with patch.object(client_loose, "execute", side_effect=[root_tree, wrong_lazy]):
            res = client_loose.verify_layout(frame_refs=[900])
            self.assertFalse(res["ok"])
            self.assertIn("Invalid lazy-fetch response for node 901", res["error"])

    def test_16_child_count_positive_but_fetched_children_empty_fails_audit(self):
        """Test 16 (Stage 3.4.2): When childCount > 0 but lazy fetch returns empty or missing children, audit fails."""
        root_tree = {
            "id": 1000,
            "name": "RootScreen",
            "type": "FRAME",
            "absoluteBounds": {"x": 0, "y": 0, "width": 800, "height": 600},
            "children": [
                {"id": 1001, "type": "FRAME", "childCount": 3}
            ]
        }
        inconsistent_lazy = {
            "id": 1001,
            "name": "EmptyChildrenCard",
            "type": "FRAME",
            "absoluteBounds": {"x": 10, "y": 10, "width": 200, "height": 200},
            "childCount": 3,
            "children": []
        }

        # strict=True
        client_strict, _ = self._create_client(strict=True)
        with patch.object(client_strict, "execute", side_effect=[root_tree, inconsistent_lazy]):
            with self.assertRaises(FigCraftError) as ctx:
                client_strict.verify_layout(frame_refs=[1000])
            self.assertIn("Inconsistent lazy-fetch response for node 1001", str(ctx.exception))

        # strict=False
        client_loose, _ = self._create_client(strict=False)
        with patch.object(client_loose, "execute", side_effect=[root_tree, inconsistent_lazy]):
            res = client_loose.verify_layout(frame_refs=[1000])
            self.assertFalse(res["ok"])
            self.assertIn("Inconsistent lazy-fetch response for node 1001", res["error"])

    def test_17_no_redundant_fetches_or_infinite_loops(self):
        """Test 17 (Stage 3.4.2): Each lazy node is fetched at most once, and cyclic references terminate safely."""
        client, _ = self._create_client(strict=True)

        root_tree = {
            "id": 1100,
            "name": "RootScreen",
            "type": "FRAME",
            "absoluteBounds": {"x": 0, "y": 0, "width": 800, "height": 600},
            "children": [
                {"id": 1101, "type": "FRAME", "childCount": 1}
            ]
        }
        # 1101 references 1100 (cycle) as a child
        lazy_1101 = {
            "id": 1101,
            "name": "ChildCard",
            "type": "FRAME",
            "absoluteBounds": {"x": 20, "y": 20, "width": 200, "height": 200},
            "childCount": 1,
            "children": [
                {
                    "id": 1100,
                    "name": "CyclicRefToRoot",
                    "type": "FRAME",
                    "absoluteBounds": {"x": 20, "y": 20, "width": 100, "height": 100},
                    "childCount": 1
                }
            ]
        }

        with patch.object(client, "execute", side_effect=[root_tree, lazy_1101]) as mock_exec:
            res = client.verify_layout(frame_refs=[1100])
            self.assertTrue(res["ok"])
            # Exactly 2 calls: 1 for root 1100, 1 for lazy child 1101 (never re-fetches 1100 or 1101)
            self.assertEqual(mock_exec.call_count, 2)

    def test_18_regression_all_four_visual_checks(self):
        """Test 18 (Stage 3.4.2): Regression verifying all 4 visual checks (overflow, zero_size, overlap, unpadded_visual_box)."""
        client, _ = self._create_client(strict=True)

        tree_all_4 = {
            "id": 1200,
            "name": "AllFourViolationsScreen",
            "type": "FRAME",
            "absoluteBounds": {"x": 0, "y": 0, "width": 500, "height": 400},
            "layout": "vertical",
            "fills": [{"color": "#FFFFFF"}],
            "children": [
                {
                    "id": 1201,
                    "name": "CardContainer",
                    "type": "FRAME",
                    # Overflows right (x=0, width=550 > 500) -> 1. child_overflow
                    "absoluteBounds": {"x": 0, "y": 0, "width": 550, "height": 200},
                    "layout": "vertical",
                    "fills": [{"color": "#EEEEEE"}],
                    "children": [
                        {
                            "id": 1202,
                            "name": "FlushTextItem",
                            "type": "TEXT",
                            # At (0, 0) inside CardContainer (0, 0) with depth=1 -> 4. unpadded_visual_box
                            # Also overlaps with 1203 -> 3. sibling_overlap
                            "absoluteBounds": {"x": 0, "y": 0, "width": 120, "height": 30},
                            "children": []
                        },
                        {
                            "id": 1203,
                            "name": "OverlappingBox",
                            "type": "FRAME",
                            "absoluteBounds": {"x": 10, "y": 10, "width": 120, "height": 30},
                            "children": []
                        },
                        {
                            "id": 1204,
                            "name": "ZeroHeightDivider",
                            "type": "RECT",
                            # height=0 -> 2. zero_size
                            "absoluteBounds": {"x": 10, "y": 60, "width": 100, "height": 0},
                            "children": []
                        }
                    ]
                }
            ]
        }

        with patch.object(client, "execute", return_value=tree_all_4):
            res = client.verify_layout(frame_refs=[1200])
            self.assertFalse(res["ok"])
            kinds = {v["kind"] for v in res["violations"]}
            self.assertEqual(
                kinds,
                {"child_overflow", "zero_size", "sibling_overlap", "unpadded_visual_box"}
            )

    def test_19_missing_or_null_absolute_bounds_fails_audit(self):
        """Test 19 (Stage 3.4.3 / VL-05): absoluteBounds=None or missing fails audit on strict=True and strict=False."""
        for invalid_tree in (
            {"id": 1300, "name": "NullBoundsFrame", "type": "FRAME", "absoluteBounds": None, "children": []},
            {"id": 1300, "name": "MissingBoundsFrame", "type": "FRAME", "children": []},
        ):
            client_strict, _ = self._create_client(strict=True)
            with patch.object(client_strict, "execute", return_value=invalid_tree):
                with self.assertRaises(FigCraftError) as ctx:
                    client_strict.verify_layout(frame_refs=[1300])
                self.assertIn("Invalid or missing absoluteBounds", str(ctx.exception))
                self.assertIn("expected dict, got NoneType", str(ctx.exception))

            client_loose, _ = self._create_client(strict=False)
            with patch.object(client_loose, "execute", return_value=invalid_tree):
                res = client_loose.verify_layout(frame_refs=[1300])
                self.assertFalse(res["ok"])
                self.assertIn("Invalid or missing absoluteBounds", res["error"])
                self.assertEqual(client_loose.last_error, res["error"])

    def test_20_empty_dict_absolute_bounds_fails_audit(self):
        """Test 20 (Stage 3.4.3 / VL-05): absoluteBounds={} fails audit on strict=True and strict=False."""
        empty_bounds_tree = {
            "id": 1400,
            "name": "EmptyBoundsFrame",
            "type": "FRAME",
            "absoluteBounds": {},
            "children": []
        }

        client_strict, _ = self._create_client(strict=True)
        with patch.object(client_strict, "execute", return_value=empty_bounds_tree):
            with self.assertRaises(FigCraftError) as ctx:
                client_strict.verify_layout(frame_refs=[1400])
            self.assertIn("Incomplete absoluteBounds", str(ctx.exception))
            self.assertIn("missing keys ['x', 'y', 'width', 'height']", str(ctx.exception))

        client_loose, _ = self._create_client(strict=False)
        with patch.object(client_loose, "execute", return_value=empty_bounds_tree):
            res = client_loose.verify_layout(frame_refs=[1400])
            self.assertFalse(res["ok"])
            self.assertIn("Incomplete absoluteBounds", res["error"])
            self.assertIn("missing keys ['x', 'y', 'width', 'height']", res["error"])

    def test_21_missing_individual_keys_x_y_width_height_fails_audit(self):
        """Test 21 (Stage 3.4.3 / VL-05): Missing x, y, width, or height fails cleanly without raw KeyError."""
        full_bounds = {"x": 0, "y": 0, "width": 400, "height": 300}
        for missing_key in ("x", "y", "width", "height"):
            partial_bounds = {k: v for k, v in full_bounds.items() if k != missing_key}
            tree = {
                "id": 1500,
                "name": f"Missing_{missing_key}_Frame",
                "type": "FRAME",
                "absoluteBounds": partial_bounds,
                "children": []
            }

            client_strict, _ = self._create_client(strict=True)
            with patch.object(client_strict, "execute", return_value=tree):
                with self.assertRaises(FigCraftError) as ctx:
                    client_strict.verify_layout(frame_refs=[1500])
                self.assertIn(f"missing keys ['{missing_key}']", str(ctx.exception))

            client_loose, _ = self._create_client(strict=False)
            with patch.object(client_loose, "execute", return_value=tree):
                res = client_loose.verify_layout(frame_refs=[1500])
                self.assertFalse(res["ok"])
                self.assertIn(f"missing keys ['{missing_key}']", res["error"])

    def test_22_string_values_in_absolute_bounds_rejected(self):
        """Test 22 (Stage 3.4.3 / VL-05): String values in absoluteBounds are rejected on both modes."""
        for key in ("x", "y", "width", "height"):
            bad_bounds = {"x": 0, "y": 0, "width": 400, "height": 300}
            bad_bounds[key] = "100"
            tree = {
                "id": 1600,
                "name": "StringBoundsFrame",
                "type": "FRAME",
                "absoluteBounds": bad_bounds,
                "children": []
            }

            client_strict, _ = self._create_client(strict=True)
            with patch.object(client_strict, "execute", return_value=tree):
                with self.assertRaises(FigCraftError) as ctx:
                    client_strict.verify_layout(frame_refs=[1600])
                self.assertIn(f"Invalid absoluteBounds['{key}']", str(ctx.exception))
                self.assertIn("str", str(ctx.exception))

            client_loose, _ = self._create_client(strict=False)
            with patch.object(client_loose, "execute", return_value=tree):
                res = client_loose.verify_layout(frame_refs=[1600])
                self.assertFalse(res["ok"])
                self.assertIn(f"Invalid absoluteBounds['{key}']", res["error"])

    def test_23_boolean_values_in_absolute_bounds_rejected(self):
        """Test 23 (Stage 3.4.3 / VL-05): Boolean values in absoluteBounds are rejected despite bool subclassing int."""
        for key, bval in (("x", True), ("y", False), ("width", True), ("height", False)):
            bad_bounds = {"x": 0, "y": 0, "width": 400, "height": 300}
            bad_bounds[key] = bval
            tree = {
                "id": 1700,
                "name": "BoolBoundsFrame",
                "type": "FRAME",
                "absoluteBounds": bad_bounds,
                "children": []
            }

            client_strict, _ = self._create_client(strict=True)
            with patch.object(client_strict, "execute", return_value=tree):
                with self.assertRaises(FigCraftError) as ctx:
                    client_strict.verify_layout(frame_refs=[1700])
                self.assertIn(f"Invalid absoluteBounds['{key}']", str(ctx.exception))
                self.assertIn("bool", str(ctx.exception))

            client_loose, _ = self._create_client(strict=False)
            with patch.object(client_loose, "execute", return_value=tree):
                res = client_loose.verify_layout(frame_refs=[1700])
                self.assertFalse(res["ok"])
                self.assertIn(f"Invalid absoluteBounds['{key}']", res["error"])

    def test_24_nan_values_in_absolute_bounds_rejected(self):
        """Test 24 (Stage 3.4.3 / VL-05): NaN values in absoluteBounds are rejected on both modes."""
        for key in ("x", "y", "width", "height"):
            bad_bounds = {"x": 0.0, "y": 0.0, "width": 400.0, "height": 300.0}
            bad_bounds[key] = float("nan")
            tree = {
                "id": 1800,
                "name": "NaNBoundsFrame",
                "type": "FRAME",
                "absoluteBounds": bad_bounds,
                "children": []
            }

            client_strict, _ = self._create_client(strict=True)
            with patch.object(client_strict, "execute", return_value=tree):
                with self.assertRaises(FigCraftError) as ctx:
                    client_strict.verify_layout(frame_refs=[1800])
                self.assertIn(f"Non-finite absoluteBounds['{key}']", str(ctx.exception))

            client_loose, _ = self._create_client(strict=False)
            with patch.object(client_loose, "execute", return_value=tree):
                res = client_loose.verify_layout(frame_refs=[1800])
                self.assertFalse(res["ok"])
                self.assertIn(f"Non-finite absoluteBounds['{key}']", res["error"])

    def test_25_positive_and_negative_infinity_in_absolute_bounds_rejected(self):
        """Test 25 (Stage 3.4.3 / VL-05): Positive and negative infinity in absoluteBounds are rejected."""
        for inf_val in (float("inf"), float("-inf")):
            for key in ("x", "y", "width", "height"):
                bad_bounds = {"x": 0.0, "y": 0.0, "width": 400.0, "height": 300.0}
                bad_bounds[key] = inf_val
                tree = {
                    "id": 1900,
                    "name": "InfBoundsFrame",
                    "type": "FRAME",
                    "absoluteBounds": bad_bounds,
                    "children": []
                }

                client_strict, _ = self._create_client(strict=True)
                with patch.object(client_strict, "execute", return_value=tree):
                    with self.assertRaises(FigCraftError) as ctx:
                        client_strict.verify_layout(frame_refs=[1900])
                    self.assertIn(f"Non-finite absoluteBounds['{key}']", str(ctx.exception))

                client_loose, _ = self._create_client(strict=False)
                with patch.object(client_loose, "execute", return_value=tree):
                    res = client_loose.verify_layout(frame_refs=[1900])
                    self.assertFalse(res["ok"])
                    self.assertIn(f"Non-finite absoluteBounds['{key}']", res["error"])

    def test_26_child_with_invalid_or_missing_bounds_fails_audit(self):
        """Test 26 (Stage 3.4.3 / VL-05): Child node with invalid/missing bounds fails audit instead of being skipped."""
        for bad_child_bounds, expected_err in (
            (None, "Invalid or missing absoluteBounds"),
            ({"x": 10, "y": 10, "width": 100}, "Incomplete absoluteBounds"),
            ({"x": 10, "y": 10, "width": True, "height": 50}, "Invalid absoluteBounds['width']"),
            ({"x": 10, "y": float("nan"), "width": 100, "height": 50}, "Non-finite absoluteBounds['y']"),
        ):
            tree = {
                "id": 2000,
                "name": "ValidParent",
                "type": "FRAME",
                "absoluteBounds": {"x": 0, "y": 0, "width": 500, "height": 400},
                "children": [
                    {
                        "id": 2001,
                        "name": "BadChildNode",
                        "type": "RECT",
                        "absoluteBounds": bad_child_bounds,
                        "children": []
                    }
                ]
            }

            client_strict, _ = self._create_client(strict=True)
            with patch.object(client_strict, "execute", return_value=tree):
                with self.assertRaises(FigCraftError) as ctx:
                    client_strict.verify_layout(frame_refs=[2000])
                self.assertIn(expected_err, str(ctx.exception))
                self.assertIn("BadChildNode", str(ctx.exception))

            client_loose, _ = self._create_client(strict=False)
            with patch.object(client_loose, "execute", return_value=tree):
                res = client_loose.verify_layout(frame_refs=[2000])
                self.assertFalse(res["ok"])
                self.assertIn(expected_err, res["error"])
                self.assertIn("BadChildNode", res["error"])

    def test_27_valid_int_and_float_bounds_and_all_four_visual_checks_preserved(self):
        """Test 27 (Stage 3.4.3 / VL-05): Valid int/float bounds pass and all 4 visual checks work on strict=True/False."""
        valid_tree = {
            "id": 2100,
            "name": "ValidFloatBoundsScreen",
            "type": "FRAME",
            "absoluteBounds": {"x": -120.5, "y": 45.25, "width": 800.0, "height": 600},
            "layout": "vertical",
            "fills": [{"color": "#FFFFFF"}],
            "children": [
                {
                    "id": 2101,
                    "name": "InnerChild",
                    "type": "RECT",
                    "absoluteBounds": {"x": -100.0, "y": 60.5, "width": 250.75, "height": 120.25},
                    "children": []
                }
            ]
        }

        for strict_mode in (True, False):
            client, _ = self._create_client(strict=strict_mode)
            with patch.object(client, "execute", return_value=valid_tree):
                res = client.verify_layout(frame_refs=[2100])
                self.assertTrue(res["ok"])
                self.assertEqual(res["violation_count"], 0)
                self.assertNotIn("error", res)
                self.assertIsNone(client.last_error)


if __name__ == "__main__":
    unittest.main()
