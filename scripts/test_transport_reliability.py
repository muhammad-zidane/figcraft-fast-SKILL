"""
test_transport_reliability.py - Unit tests for Stage 2: TCP Response Validation & Transport Reliability.
Tests transport reliability, response validation, failure stages, and stream consistency using mock sockets.
"""

import json
import socket
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import figcraft_ui
from figcraft_ui import FigCraftClient, FigCraftError


class TestTransportReliability(unittest.TestCase):

    def _create_client_with_mock_sock(self, mock_socket_factory):
        mock_sock = MagicMock()
        mock_socket_factory.return_value = mock_sock
        client = FigCraftClient(host="127.0.0.1", port=7979, strict=True)
        return client, mock_sock

    @patch.object(figcraft_ui.socket, "socket")
    def test_01_successful_connection_and_valid_response(self, mock_socket_factory):
        """Test 1: Normal command execution with valid JSON-RPC response."""
        client, mock_sock = self._create_client_with_mock_sock(mock_socket_factory)
        # Mock engine response with matching ID
        mock_sock.recv.return_value = b'{"id": 1, "ok": true, "result": {"node_id": 42}}\n'

        res = client.execute("node.get", {"id": 10})

        self.assertEqual(res, {"node_id": 42})
        self.assertIsNone(client.last_error)
        self.assertIsNone(client.last_failure_stage)
        mock_sock.sendall.assert_called_once()

    @patch.object(figcraft_ui.socket, "socket")
    def test_02_sendall_fails_without_blind_retry(self, mock_socket_factory):
        """Test 2: sendall failure closes socket, sets SEND_AMBIGUOUS, and does NOT retry."""
        client, mock_sock = self._create_client_with_mock_sock(mock_socket_factory)
        mock_sock.sendall.side_effect = BrokenPipeError("Broken pipe during send")

        with self.assertRaises(ConnectionError) as ctx:
            client.execute("node.create", {"type": "frame"})

        self.assertIn("Transmisi TCP gagal saat mengirim", str(ctx.exception))
        self.assertEqual(client.last_failure_stage, "SEND_AMBIGUOUS")
        self.assertIn("Broken pipe", client.last_error)
        # sendall must have only been called once (NO blind retry)
        mock_sock.sendall.assert_called_once()
        self.assertIsNone(client.sock)

    @patch.object(figcraft_ui.socket, "socket")
    def test_03_eof_with_empty_buffer(self, mock_socket_factory):
        """Test 3: EOF (server closed connection) with empty buffer triggers ConnectionError."""
        client, mock_sock = self._create_client_with_mock_sock(mock_socket_factory)
        mock_sock.recv.return_value = b""  # Immediate EOF

        with self.assertRaises(ConnectionError) as ctx:
            client.execute("node.get", {"id": 1})

        self.assertIn("tanpa respons", str(ctx.exception))
        self.assertEqual(client.last_failure_stage, "RECV_AMBIGUOUS")
        self.assertIsNone(client.sock)
        self.assertEqual(client._buffer, "")

    @patch.object(figcraft_ui.socket, "socket")
    def test_04_eof_with_incomplete_response(self, mock_socket_factory):
        """Test 4: EOF with partial data before newline is detected as incomplete response."""
        client, mock_sock = self._create_client_with_mock_sock(mock_socket_factory)
        # First chunk is partial, second chunk is EOF
        mock_sock.recv.side_effect = [b'{"id": 1, "ok": tr', b""]

        with self.assertRaises(ConnectionError) as ctx:
            client.execute("node.get", {"id": 1})

        self.assertIn("respons tidak lengkap", str(ctx.exception))
        self.assertEqual(client.last_failure_stage, "RECV_AMBIGUOUS")
        self.assertIsNone(client.sock)
        self.assertEqual(client._buffer, "")

    @patch.object(figcraft_ui.socket, "socket")
    def test_05_timeout_closes_socket_and_resets_buffer(self, mock_socket_factory):
        """Test 5: Socket timeout closes connection and clears buffer."""
        client, mock_sock = self._create_client_with_mock_sock(mock_socket_factory)
        mock_sock.recv.side_effect = socket.timeout("timed out")

        with self.assertRaises(FigCraftError) as ctx:
            client.execute("node.get", {"id": 1})

        self.assertIn("Timeout saat menunggu respons", str(ctx.exception))
        self.assertEqual(client.last_failure_stage, "RECV_AMBIGUOUS")
        self.assertIsNone(client.sock)
        self.assertEqual(client._buffer, "")

    @patch.object(figcraft_ui.socket, "socket")
    def test_06_connection_reset_closes_socket(self, mock_socket_factory):
        """Test 6: ConnectionResetError during recv closes socket and raises ConnectionError."""
        client, mock_sock = self._create_client_with_mock_sock(mock_socket_factory)
        mock_sock.recv.side_effect = ConnectionResetError("Connection reset by peer")

        with self.assertRaises(ConnectionError) as ctx:
            client.execute("node.get", {"id": 1})

        self.assertIn("Kesalahan soket saat membaca respons", str(ctx.exception))
        self.assertEqual(client.last_failure_stage, "RECV_AMBIGUOUS")
        self.assertIsNone(client.sock)
        self.assertEqual(client._buffer, "")

    @patch.object(figcraft_ui.socket, "socket")
    def test_07_malformed_json_response(self, mock_socket_factory):
        """Test 7: Malformed JSON response line closes socket and raises FigCraftError."""
        client, mock_sock = self._create_client_with_mock_sock(mock_socket_factory)
        mock_sock.recv.return_value = b'{"bad_json": \n'

        with self.assertRaises(FigCraftError) as ctx:
            client.execute("node.get", {"id": 1})

        self.assertIn("Respons JSON tidak valid", str(ctx.exception))
        self.assertEqual(client.last_failure_stage, "INVALID_RESPONSE")
        self.assertIsNone(client.sock)
        self.assertEqual(client._buffer, "")

    @patch.object(figcraft_ui.socket, "socket")
    def test_08_response_id_mismatch(self, mock_socket_factory):
        """Test 8: Response with mismatched ID raises FigCraftError and closes socket."""
        client, mock_sock = self._create_client_with_mock_sock(mock_socket_factory)
        # Expected req_id is 1, but engine sent id 99
        mock_sock.recv.return_value = b'{"id": 99, "ok": true, "result": {}}\n'

        with self.assertRaises(FigCraftError) as ctx:
            client.execute("node.get", {"id": 1})

        self.assertIn("Mismatch ID respons", str(ctx.exception))
        self.assertEqual(client.last_failure_stage, "INVALID_RESPONSE")
        self.assertIsNone(client.sock)
        self.assertEqual(client._buffer, "")

    @patch.object(figcraft_ui.socket, "socket")
    def test_09_response_without_id(self, mock_socket_factory):
        """Test 9: Response without ID (flat format {"ok": true, "result": {...}}) is accepted."""
        client, mock_sock = self._create_client_with_mock_sock(mock_socket_factory)
        mock_sock.recv.return_value = b'{"ok": true, "result": {"name": "Canvas"}}\n'

        res = client.execute("node.get", {"id": 1})

        self.assertEqual(res, {"name": "Canvas"})
        self.assertIsNone(client.last_error)
        self.assertIsNone(client.last_failure_stage)

    @patch.object(figcraft_ui.socket, "socket")
    def test_10_response_flat_error_format(self, mock_socket_factory):
        """Test 10: Response with flat error format {"ok": false, "error": "Node not found"}."""
        client, mock_sock = self._create_client_with_mock_sock(mock_socket_factory)
        mock_sock.recv.return_value = b'{"ok": false, "error": "Node not found"}\n'

        with self.assertRaises(FigCraftError) as ctx:
            client.execute("node.get", {"id": 999})

        self.assertIn("Node not found", str(ctx.exception))
        # Engine rejected explicitly, socket remains healthy
        self.assertIsNotNone(client.sock)

    @patch.object(figcraft_ui.socket, "socket")
    def test_11_socket_and_buffer_cleaned_up_after_transport_failure(self, mock_socket_factory):
        """Test 11: After transport failure, socket is None and buffer is empty."""
        client, mock_sock = self._create_client_with_mock_sock(mock_socket_factory)
        mock_sock.recv.side_effect = OSError("Network unreachable")

        with self.assertRaises(ConnectionError):
            client.execute("node.get", {"id": 1})

        self.assertIsNone(client.sock)
        self.assertEqual(client._buffer, "")
        mock_sock.close.assert_called_once()

    @patch.object(figcraft_ui.socket, "socket")
    def test_12_next_request_does_not_use_stale_response(self, mock_socket_factory):
        """Test 12: Subsequent request after failure reconnects cleanly without reading old buffer."""
        mock_sock1 = MagicMock()
        mock_sock2 = MagicMock()
        mock_socket_factory.side_effect = [mock_sock1, mock_sock2]

        client = FigCraftClient(host="127.0.0.1", port=7979, strict=True)
        # First request times out
        mock_sock1.recv.side_effect = socket.timeout("timeout")
        with self.assertRaises(FigCraftError):
            client.execute("node.get", {"id": 1})

        self.assertIsNone(client.sock)
        self.assertEqual(client._buffer, "")

        # Second request succeeds on fresh socket (id=2)
        mock_sock2.recv.return_value = b'{"id": 2, "ok": true, "result": {"fresh": true}}\n'
        res2 = client.execute("node.get", {"id": 2})

        self.assertEqual(res2, {"fresh": True})
        self.assertEqual(client.sock, mock_sock2)

    @patch.object(figcraft_ui.socket, "socket")
    def test_13_non_strict_returns_empty_dict_and_sets_last_error(self, mock_socket_factory):
        """Test 13: In strict=False mode, transport failure returns {} without raising, but sets last_error and closes socket."""
        mock_sock = MagicMock()
        mock_socket_factory.return_value = mock_sock
        client = FigCraftClient(host="127.0.0.1", port=7979, strict=False)

        # Simulate timeout on recv
        mock_sock.recv.side_effect = socket.timeout("timed out")
        res = client.execute("node.get", {"id": 1})

        self.assertEqual(res, {})
        self.assertIn("Timeout saat menunggu respons", client.last_error)
        self.assertEqual(client.last_failure_stage, "RECV_AMBIGUOUS")
        self.assertIsNone(client.sock)
        self.assertEqual(client._buffer, "")

    @patch.object(figcraft_ui.socket, "socket")
    def test_14_non_object_response_raises_or_warns(self, mock_socket_factory):
        """Test 14: Response that is valid JSON but not a JSON object (e.g. integer or list) raises FigCraftError."""
        client, mock_sock = self._create_client_with_mock_sock(mock_socket_factory)
        mock_sock.recv.return_value = b'[1, 2, 3]\n'

        with self.assertRaises(FigCraftError) as ctx:
            client.execute("node.get", {"id": 1})

        self.assertIn("Format respons bukan objek JSON", str(ctx.exception))
        self.assertEqual(client.last_failure_stage, "INVALID_RESPONSE")
        self.assertIsNone(client.sock)
        self.assertEqual(client._buffer, "")

    @patch.object(figcraft_ui.socket, "socket")
    def test_15_unexpected_extra_response_in_chunk_is_rejected(self, mock_socket_factory):
        """Test 15: Two responses arrived in one chunk; synchronous RPC rejects unexpected extra response."""
        client, mock_sock = self._create_client_with_mock_sock(mock_socket_factory)
        # Server sends two response lines together in one chunk
        mock_sock.recv.return_value = (
            b'{"id": 1, "ok": true, "result": {"call": 1}}\n'
            b'{"id": 2, "ok": true, "result": {"call": 2}}\n'
        )

        with self.assertRaises(FigCraftError) as ctx:
            client.execute("node.get", {"id": 1})

        self.assertIn("Menerima respons/data ekstra yang tidak terduga", str(ctx.exception))
        self.assertEqual(client.last_failure_stage, "INVALID_RESPONSE")
        self.assertIsNone(client.sock)
        self.assertEqual(client._buffer, "")

    @patch.object(figcraft_ui.socket, "socket")
    def test_16_stale_buffer_before_sendall_rejected(self, mock_socket_factory):
        """Test 16: If buffer contains unconsumed stale response data before sendall, it is rejected and not sent."""
        client, mock_sock = self._create_client_with_mock_sock(mock_socket_factory)
        # Pre-populate buffer with unconsumed leftover data
        client._buffer = '{"ok": true, "result": {"stale": true}}\n'

        with self.assertRaises(FigCraftError) as ctx:
            client.execute("node.get", {"id": 2})

        self.assertIn("Buffer stream TCP tidak kosong sebelum pengiriman", str(ctx.exception))
        self.assertEqual(client.last_failure_stage, "INVALID_RESPONSE")
        self.assertIsNone(client.sock)
        self.assertEqual(client._buffer, "")
        # sendall should NOT have been called because stale data aborted execution before send
        mock_sock.sendall.assert_not_called()

    @patch.object(figcraft_ui.socket, "socket")
    def test_17_stale_response_without_id_cannot_satisfy_subsequent_request(self, mock_socket_factory):
        """Test 17: Stale response without ID cannot be consumed to satisfy a subsequent request."""
        client, mock_sock = self._create_client_with_mock_sock(mock_socket_factory)
        # Stale response has no ID
        client._buffer = '{"ok": true, "result": {"stale_node": 999}}\n'

        with self.assertRaises(FigCraftError) as ctx:
            client.execute("node.get", {"id": 10})

        self.assertIn("Buffer stream TCP tidak kosong", str(ctx.exception))
        self.assertEqual(client.last_failure_stage, "INVALID_RESPONSE")
        self.assertIsNone(client.sock)
        mock_sock.sendall.assert_not_called()


if __name__ == "__main__":
    unittest.main()
