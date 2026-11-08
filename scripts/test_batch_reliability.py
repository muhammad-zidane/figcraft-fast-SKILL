"""
test_batch_reliability.py - Unit tests for Stage 3.2: Batch Queue Reliability Hardening.
Tests batch queue failure semantics, failed batch diagnostics, reference consistency,
result validation, and context manager safety using mock sockets without FigCraft Engine.
"""

import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import figcraft_ui
from figcraft_ui import FigCraftClient, FigCraftError


class TestBatchReliability(unittest.TestCase):

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

    def test_01_pre_send_failure_records_failed_batch(self):
        """Test 1: PRE_SEND failure preserves the queued batch in last_failed_batch without loss."""
        client, mock_sock = self._create_client(strict=True)
        client.create_frame(name="Header", width=800, height=100)
        self.assertEqual(len(client._batch_queue), 1)
        expected_cmd = client._batch_queue[0]["command"]

        # Simulate PRE_SEND failure: disconnected socket where connect() fails
        client.sock = None
        with patch.object(client, "connect", side_effect=ConnectionError("Cannot connect")):
            with self.assertRaises(ConnectionError):
                client.flush()

        self.assertIn("Gagal menghubungkan soket sebelum mengirim", client.last_error)
        self.assertEqual(client.last_failure_stage, "PRE_SEND")
        self.assertIsNotNone(client.last_failed_batch)
        self.assertEqual(len(client.last_failed_batch), 1)
        self.assertEqual(client.last_failed_batch[0]["command"], expected_cmd)
        # Ensure _batch_queue was cleared to prevent automatic retry on close
        self.assertEqual(client._batch_queue, [])

    def test_02_ambiguous_failure_does_not_resend_on_close(self):
        """Test 2: Ambiguous in-flight failure does not cause batch to be resent when close() is called."""
        client, mock_sock = self._create_client(strict=True)
        client.create_frame(name="Card", width=300, height=200)

        # Mock execute to raise TimeoutError (RECV_AMBIGUOUS)
        with patch.object(client, "execute", side_effect=TimeoutError("recv timed out")) as mock_exec:
            with self.assertRaises(TimeoutError):
                client.flush()

            self.assertIsNotNone(client.last_failed_batch)
            self.assertEqual(client._batch_queue, [])

            # Reset execute mock to observe close() behavior
            mock_exec.reset_mock()
            mock_exec.side_effect = None

            client.close()
            # close() must NOT flush or execute any batch commands because queue was empty
            mock_exec.assert_not_called()
            self.assertIsNone(client.sock)

    def test_03_failed_step_with_id_does_not_populate_resolved_refs(self):
        """Test 3: Step with ok=False containing an id key is NOT committed to _resolved_refs."""
        # 3a. strict=True
        client, mock_sock = self._create_client(strict=True)
        ref = client.create_frame(name="Button", width=100, height=40)
        as_name = ref["$ref"]

        fake_results = [{"ok": False, "id": 999, "error": "Invalid bounds"}]
        with patch.object(client, "execute", return_value=fake_results):
            with self.assertRaises(FigCraftError) as ctx:
                client.flush()

            self.assertIn("Invalid bounds", str(ctx.exception))
            self.assertNotIn(as_name, client._resolved_refs)
            self.assertNotIn(999, client._resolved_refs.values())
            self.assertEqual(client.last_error, f"Batch step '{as_name}' (node.create) failed: Invalid bounds")
            self.assertIsNotNone(client.last_failed_batch)

        # 3b. strict=False
        client_loose, _ = self._create_client(strict=False)
        ref_loose = client_loose.create_frame(name="Button", width=100, height=40)
        as_loose = ref_loose["$ref"]
        with patch.object(client_loose, "execute", return_value=fake_results):
            res = client_loose.flush()
            self.assertEqual(res, fake_results)
            self.assertNotIn(as_loose, client_loose._resolved_refs)
            self.assertNotIn(999, client_loose._resolved_refs.values())
            self.assertEqual(client_loose.last_error, f"Batch step '{as_loose}' (node.create) failed: Invalid bounds")
            self.assertIsNotNone(client_loose.last_failed_batch)

    def test_04_strict_true_atomic_staging_drops_refs_on_partial_failure(self):
        """Test 4: In strict=True, partial batch failure commits NO staged refs to _resolved_refs."""
        client, mock_sock = self._create_client(strict=True)
        ref1 = client.create_frame(name="Box1", width=100, height=100)
        ref2 = client.create_frame(name="Box2", width=100, height=100)

        # Step 1 succeeds, Step 2 fails
        fake_results = [
            {"ok": True, "result": {"id": 101}},
            {"ok": False, "error": "Out of memory"}
        ]
        with patch.object(client, "execute", return_value=fake_results):
            with self.assertRaises(FigCraftError):
                client.flush()

            # Neither ref1 nor ref2 should be in _resolved_refs
            self.assertEqual(client._resolved_refs, {})
            self.assertIsNotNone(client.last_failed_batch)
            self.assertEqual(len(client.last_failed_batch), 2)

    def test_05_strict_false_commits_only_successful_step_refs(self):
        """Test 5: In strict=False, only refs from proven successful steps are committed."""
        client, mock_sock = self._create_client(strict=False)
        ref1 = client.create_frame(name="Box1", width=100, height=100)
        ref2 = client.create_frame(name="Box2", width=100, height=100)
        ref3 = client.create_frame(name="Box3", width=100, height=100)

        # Step 1 ok, Step 2 fails, Step 3 ok
        fake_results = [
            {"ok": True, "result": {"id": 101}},
            {"ok": False, "error": "Component syntax error"},
            {"ok": True, "result": {"id": 103}}
        ]
        with patch.object(client, "execute", return_value=fake_results):
            res = client.flush()

            self.assertEqual(res, fake_results)
            self.assertEqual(client._resolved_refs.get(ref1["$ref"]), 101)
            self.assertNotIn(ref2["$ref"], client._resolved_refs)
            self.assertEqual(client._resolved_refs.get(ref3["$ref"]), 103)
            self.assertIsNotNone(client.last_failed_batch)
            self.assertIn("Component syntax error", client.last_error)

    def test_06_result_length_mismatch_detected(self):
        """Test 6: Truncated or mismatched result list is detected and does NOT commit refs in either mode."""
        # 6a. strict=True raises FigCraftError and commits no refs
        client, mock_sock = self._create_client(strict=True)
        client.create_frame(name="Box1", width=100, height=100)
        client.create_frame(name="Box2", width=100, height=100)

        fake_results = [{"ok": True, "result": {"id": 101}}]
        with patch.object(client, "execute", return_value=fake_results):
            with self.assertRaises(FigCraftError) as ctx:
                client.flush()

            self.assertIn("Batch result count mismatch: expected 2, got 1", str(ctx.exception))
            self.assertEqual(client.last_error, "Batch result count mismatch: expected 2, got 1")
            self.assertIsNotNone(client.last_failed_batch)
            self.assertEqual(client._resolved_refs, {})

        # 6b. strict=False returns results without raising, but commits NO refs on structural mismatch
        client_loose, _ = self._create_client(strict=False)
        client_loose.create_frame(name="Box1", width=100, height=100)
        client_loose.create_frame(name="Box2", width=100, height=100)

        with patch.object(client_loose, "execute", return_value=fake_results):
            res = client_loose.flush()

            self.assertEqual(res, fake_results)
            self.assertEqual(client_loose.last_error, "Batch result count mismatch: expected 2, got 1")
            self.assertIsNotNone(client_loose.last_failed_batch)
            self.assertEqual(client_loose._resolved_refs, {})  # No refs committed!

    def test_07_non_list_result_detected(self):
        """Test 7: Non-list batch result is rejected and not disguised as an empty queue."""
        # 7a. strict=True raises FigCraftError
        client, mock_sock = self._create_client(strict=True)
        client.create_frame(name="Box1", width=100, height=100)

        with patch.object(client, "execute", return_value={"unexpected": "dict"}):
            with self.assertRaises(FigCraftError) as ctx:
                client.flush()

            self.assertIn("Invalid batch response: expected list of results, got dict", str(ctx.exception))
            self.assertIsNotNone(client.last_failed_batch)

        # 7b. strict=False returns [] and sets last_error & last_failed_batch
        client_loose, _ = self._create_client(strict=False)
        client_loose.create_frame(name="Box1", width=100, height=100)
        with patch.object(client_loose, "execute", return_value={"unexpected": "dict"}):
            res = client_loose.flush()
            self.assertEqual(res, [])
            self.assertIsNotNone(client_loose.last_failed_batch)
            self.assertIn("Invalid batch response", client_loose.last_error)

    def test_08_dangling_ref_rejected(self):
        """Test 8: Dangling $ref is rejected on both strict=True and strict=False."""
        # 8a. strict=True
        client, mock_sock = self._create_client(strict=True)
        with self.assertRaises(FigCraftError) as ctx:
            client.create_text(parent={"$ref": "nonexistent_ref"}, text="Hello World")

        self.assertIn("Dangling reference detected", str(ctx.exception))
        self.assertIn("nonexistent_ref", str(ctx.exception))
        self.assertIn("Dangling reference detected", client.last_error)
        self.assertEqual(client._batch_queue, [])

        # 8b. strict=False also rejects dangling $ref without passing to engine
        client_loose, _ = self._create_client(strict=False)
        with self.assertRaises(FigCraftError) as ctx_loose:
            client_loose.create_text(parent={"$ref": "nonexistent_ref"}, text="Hello World")

        self.assertIn("Dangling reference detected", str(ctx_loose.exception))
        self.assertIn("Dangling reference detected", client_loose.last_error)
        self.assertEqual(client_loose._batch_queue, [])

    def test_09_old_ref_after_clear_canvas_rejected(self):
        """Test 9: Reference created before clear_canvas() is rejected as dangling after clear_canvas()."""
        client, mock_sock = self._create_client(strict=True)
        old_ref = client.create_frame(name="OldBox", width=100, height=100)

        # Mock clear_canvas commands
        with patch.object(client, "execute", return_value={"ok": True}):
            client.clear_canvas()

        # Attempting to use old_ref should be rejected
        with self.assertRaises(FigCraftError) as ctx:
            client.create_text(parent=old_ref, text="Child of wiped node")

        self.assertIn("Dangling reference detected", str(ctx.exception))
        self.assertIn(old_ref["$ref"], str(ctx.exception))

    def test_10_auto_batch_false_rejects_unresolved_ref(self):
        """Test 10: In auto_batch=False, unresolved $ref is rejected on both strict=True and strict=False."""
        # 10a. strict=True
        client, mock_sock = self._create_client(strict=True, auto_batch=False)
        with self.assertRaises(FigCraftError) as ctx:
            client.create_frame(name="Child", parent={"$ref": "unresolved_ref"})

        self.assertIn("Unresolved reference '$ref': 'unresolved_ref' cannot be used when auto_batch=False", str(ctx.exception))
        self.assertIn("Unresolved reference", client.last_error)

        # 10b. strict=False
        client_loose, _ = self._create_client(strict=False, auto_batch=False)
        with self.assertRaises(FigCraftError) as ctx_loose:
            client_loose.create_frame(name="Child", parent={"$ref": "unresolved_ref"})

        self.assertIn("Unresolved reference '$ref': 'unresolved_ref' cannot be used when auto_batch=False", str(ctx_loose.exception))
        self.assertIn("Unresolved reference", client_loose.last_error)

    def test_11_normal_close_performs_final_flush_once(self):
        """Test 11: Normal close() flushes pending batch queue exactly once and closes socket."""
        client, mock_sock = self._create_client(strict=True)
        client.create_frame(name="BoxToFlush", width=200, height=200)
        self.assertEqual(len(client._batch_queue), 1)

        fake_results = [{"ok": True, "result": {"id": 555}}]
        with patch.object(client, "execute", return_value=fake_results) as mock_exec:
            client.close()

            mock_exec.assert_called_once()
            self.assertEqual(mock_exec.call_args[0][0], "command.batch")
            self.assertEqual(client._resolved_refs.get("frame_1"), 555)
            self.assertEqual(client._batch_queue, [])
            self.assertIsNone(client.sock)
            mock_sock.close.assert_called_once()

    def test_12_context_manager_exception_cleans_socket_without_resending_failed_batch(self):
        """Test 12: Context manager with exception cleans socket and does not re-send failed batch on exit."""
        mock_sock = MagicMock()
        with patch.object(figcraft_ui.socket, "socket", return_value=mock_sock):
            client = FigCraftClient(host="127.0.0.1", port=7979, strict=True)

            with patch.object(client, "execute", side_effect=TimeoutError("Timeout in flush")) as mock_exec:
                with self.assertRaises(TimeoutError):
                    with client:
                        client.create_frame(name="Card", width=300, height=200)
                        client.flush()

                # Inside flush, execute was called once and threw
                mock_exec.assert_called_once()

                # On exit, socket was cleaned up via _close_socket
                self.assertIsNone(client.sock)
                mock_sock.close.assert_called_once()

                # Failed batch was recorded and queue is empty
                self.assertIsNotNone(client.last_failed_batch)
                self.assertEqual(client._batch_queue, [])

    def test_13_last_error_diagnostics_retained_on_all_failures(self):
        """Test 13: last_error remains set and diagnostic info is not lost across failures."""
        client, mock_sock = self._create_client(strict=False)

        # 1. Structural mismatch failure sets last_error
        client.create_frame(name="A", width=100, height=100)
        client.create_frame(name="B", width=100, height=100)
        with patch.object(client, "execute", return_value=[{"ok": True, "result": {"id": 1}}]):
            client.flush()
            self.assertIsNotNone(client.last_error)
            self.assertIn("Batch result count mismatch", client.last_error)

        # 2. Step failure sets last_error
        client.create_frame(name="C", width=100, height=100)
        with patch.object(client, "execute", return_value=[{"ok": False, "error": "Step error"}]):
            client.flush()
            self.assertIsNotNone(client.last_error)
            self.assertIn("Step error", client.last_error)

        # 3. Dangling ref sets last_error
        with self.assertRaises(FigCraftError):
            client.create_text(parent={"$ref": "nonexistent"}, text="Test")
        self.assertIsNotNone(client.last_error)
        self.assertIn("Dangling reference detected", client.last_error)

    def test_14_strict_true_accepts_list_result(self):
        """Test 14 (Stage 3.3.1): strict=True (abort mode) accepts raw list results (e.g. doc.list)."""
        client, _ = self._create_client(strict=True)
        client._batch_queue.append({"command": "doc.list", "as": "docs_1", "params": {}})

        raw_batch_results = [[{"id": 1, "dirty": False, "active": True}]]
        with patch.object(client, "execute", return_value=raw_batch_results):
            res = client.flush()

        self.assertEqual(res, raw_batch_results)
        self.assertIsNone(client.last_error)
        self.assertIsNone(client.last_failed_batch)
        self.assertEqual(client._resolved_refs, {})

    def test_15_strict_true_accepts_null_result(self):
        """Test 15 (Stage 3.3.1): strict=True (abort mode) accepts raw null/None results (e.g. missing node.get)."""
        client, _ = self._create_client(strict=True)
        client._batch_queue.append({"command": "node.get", "as": "missing_1", "params": {"id": 999999}})

        raw_batch_results = [None]
        with patch.object(client, "execute", return_value=raw_batch_results):
            res = client.flush()

        self.assertEqual(res, [None])
        self.assertIsNone(client.last_error)
        self.assertIsNone(client.last_failed_batch)
        self.assertEqual(client._resolved_refs, {})

    def test_16_strict_true_mixed_dict_list_null_and_scalar_results(self):
        """Test 16 (Stage 3.3.1): strict=True handles mixed raw dict, list, null, and scalar results."""
        client, _ = self._create_client(strict=True)
        client._batch_queue.append({"command": "doc.list", "as": "step_list", "params": {}})
        client._batch_queue.append({"command": "node.create", "as": "step_dict_id", "params": {"type": "frame"}})
        client._batch_queue.append({"command": "node.get", "as": "step_null", "params": {"id": 999999}})
        client._batch_queue.append({"command": "node.find", "as": "step_dict_no_id", "params": {"limit": 2}})
        client._batch_queue.append({"command": "custom.scalar", "as": "step_scalar", "params": {}})

        raw_batch_results = [
            [{"id": 1, "dirty": False}],
            {"id": 1903, "type": "FRAME"},
            None,
            {"ids": [1903, 1904], "total": 2},
            42
        ]
        with patch.object(client, "execute", return_value=raw_batch_results):
            res = client.flush()

        self.assertEqual(res, raw_batch_results)
        self.assertIsNone(client.last_error)
        self.assertIsNone(client.last_failed_batch)
        # Only step_dict_id had a top-level integer 'id' in its dict result
        self.assertEqual(client._resolved_refs, {"step_dict_id": 1903})

    def test_17_strict_true_extracts_valid_id_from_raw_dict_result(self):
        """Test 17 (Stage 3.3.1): strict=True extracts integer IDs from raw dict results and ignores non-int IDs."""
        client, _ = self._create_client(strict=True)
        ref1 = client.create_frame(name="ValidFrame", width=400, height=300)
        client._batch_queue.append({"command": "node.get", "as": "null_id_node", "params": {"id": 1}})
        client._batch_queue.append({"command": "node.get", "as": "bool_id_node", "params": {"id": 2}})

        raw_batch_results = [
            {"id": 2048, "type": "FRAME"},
            {"id": None, "type": "NONE"},
            {"id": True, "type": "BOOL"}
        ]
        with patch.object(client, "execute", return_value=raw_batch_results):
            client.flush()

        self.assertEqual(client._resolved_refs, {ref1["$ref"]: 2048})

    def test_18_strict_false_accepts_successful_null_result(self):
        """Test 18 (Stage 3.3.1): strict=False (continue mode) accepts wrapper with ok=True and result=None."""
        client, _ = self._create_client(strict=False)
        ref1 = client.create_frame(name="Frame1", width=200, height=200)
        client._batch_queue.append({"command": "node.get", "as": "missing_get", "params": {"id": 999999}})

        live_continue_results = [
            {"step": 0, "command": "node.create", "ok": True, "result": {"id": 301, "type": "FRAME"}},
            {"step": 1, "command": "node.get", "ok": True, "result": None}
        ]
        with patch.object(client, "execute", return_value=live_continue_results):
            res = client.flush()

        self.assertEqual(res, live_continue_results)
        self.assertIsNone(client.last_error)
        self.assertIsNone(client.last_failed_batch)
        self.assertEqual(client._resolved_refs, {ref1["$ref"]: 301})

    def test_19_strict_false_live_wrapper_partial_failure(self):
        """Test 19 (Stage 3.3.1): strict=False with full live wrapper {step, command, ok, result|error} commits only ok=True steps."""
        client, _ = self._create_client(strict=False)
        ref1 = client.create_frame(name="F1", width=100, height=100)
        ref2 = client.create_frame(name="F2", width=100, height=100)
        ref3 = client.create_frame(name="F3", width=100, height=100)

        live_continue_results = [
            {"step": 0, "command": "node.create", "ok": True, "result": {"id": 401}},
            {"step": 1, "command": "node.create", "ok": False, "error": "invalid parent"},
            {"step": 2, "command": "node.create", "ok": True, "result": {"id": 403}}
        ]
        with patch.object(client, "execute", return_value=live_continue_results):
            res = client.flush()

        self.assertEqual(res, live_continue_results)
        self.assertEqual(client._resolved_refs, {ref1["$ref"]: 401, ref3["$ref"]: 403})
        self.assertIsNotNone(client.last_error)
        self.assertIn("invalid parent", client.last_error)
        self.assertIsNotNone(client.last_failed_batch)

    def test_20_strict_false_malformed_wrapper_never_commits_refs(self):
        """Test 20 (Stage 3.3.1): Malformed wrappers in strict=False never commit any references."""
        # Case A: Non-dict element in continue results
        client_a, _ = self._create_client(strict=False)
        client_a.create_frame(name="F1", width=100, height=100)
        client_a.create_frame(name="F2", width=100, height=100)
        with patch.object(client_a, "execute", return_value=[{"ok": True, "result": {"id": 501}}, None]):
            client_a.flush()
        self.assertEqual(client_a._resolved_refs, {})
        self.assertIn("Malformed batch step wrapper at index 1: expected dict", client_a.last_error)
        self.assertIsNotNone(client_a.last_failed_batch)

        # Case B: Missing 'ok' boolean field in continue wrapper
        client_b, _ = self._create_client(strict=False)
        client_b.create_frame(name="F1", width=100, height=100)
        client_b.create_frame(name="F2", width=100, height=100)
        with patch.object(client_b, "execute", return_value=[{"ok": True, "result": {"id": 502}}, {"id": 503}]):
            client_b.flush()
        self.assertEqual(client_b._resolved_refs, {})
        self.assertIn("missing or non-boolean 'ok' field", client_b.last_error)
        self.assertIsNotNone(client_b.last_failed_batch)

        # Case C: Missing 'result' key when ok=True
        client_c, _ = self._create_client(strict=False)
        client_c.create_frame(name="F1", width=100, height=100)
        client_c.create_frame(name="F2", width=100, height=100)
        with patch.object(client_c, "execute", return_value=[{"ok": True, "result": {"id": 504}}, {"ok": True}]):
            client_c.flush()
        self.assertEqual(client_c._resolved_refs, {})
        self.assertIn("missing 'result' field for ok=True step", client_c.last_error)
        self.assertIsNotNone(client_c.last_failed_batch)

    def test_21_strict_false_wrong_step_index_or_command_mapping_never_commits_refs(self):
        """Test 21 (Stage 3.3.1): Wrong step index or command name in continue wrapper rejects commit of all refs."""
        # Case A: Wrong step index (e.g. out-of-order step: 5 at index 1)
        client_idx, _ = self._create_client(strict=False)
        client_idx.create_frame(name="F1", width=100, height=100)
        client_idx.create_frame(name="F2", width=100, height=100)
        mismatched_step_results = [
            {"step": 0, "command": "node.create", "ok": True, "result": {"id": 601}},
            {"step": 5, "command": "node.create", "ok": True, "result": {"id": 602}}
        ]
        with patch.object(client_idx, "execute", return_value=mismatched_step_results):
            client_idx.flush()
        self.assertEqual(client_idx._resolved_refs, {})
        self.assertIn("expected step 1, got 5", client_idx.last_error)
        self.assertIsNotNone(client_idx.last_failed_batch)

        # Case B: Wrong command mapping (e.g. 'node.delete' returned for 'node.create' step)
        client_cmd, _ = self._create_client(strict=False)
        client_cmd.create_frame(name="F1", width=100, height=100)
        client_cmd.create_frame(name="F2", width=100, height=100)
        mismatched_cmd_results = [
            {"step": 0, "command": "node.create", "ok": True, "result": {"id": 701}},
            {"step": 1, "command": "node.delete", "ok": True, "result": {"id": 702}}
        ]
        with patch.object(client_cmd, "execute", return_value=mismatched_cmd_results):
            client_cmd.flush()
        self.assertEqual(client_cmd._resolved_refs, {})
        self.assertIn("expected command 'node.create', got 'node.delete'", client_cmd.last_error)
        self.assertIsNotNone(client_cmd.last_failed_batch)


if __name__ == "__main__":
    unittest.main()
