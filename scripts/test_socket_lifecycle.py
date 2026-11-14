"""
test_socket_lifecycle.py - Unit tests for Stage 1: Socket Lifecycle Hardening.
Tests socket lifecycle behaviors using mock socket objects without connecting to a real FigCraft Engine.
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add scripts directory to path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import figcraft_ui
from figcraft_ui import FigCraftClient, FigCraftError


class TestSocketLifecycle(unittest.TestCase):

    @patch.object(figcraft_ui.socket, "socket")
    def test_01_successful_connection(self, mock_socket_factory):
        """Test 1: Successful connection initializes socket and sets timeout."""
        mock_sock = MagicMock()
        mock_socket_factory.return_value = mock_sock

        client = FigCraftClient(host="127.0.0.1", port=7979)

        mock_socket_factory.assert_called_once_with(figcraft_ui.socket.AF_INET, figcraft_ui.socket.SOCK_STREAM)
        mock_sock.settimeout.assert_called_once_with(20.0)
        mock_sock.connect.assert_called_once_with(("127.0.0.1", 7979))
        self.assertEqual(client.sock, mock_sock)
        self.assertEqual(client._buffer, "")

    @patch.object(figcraft_ui.socket, "socket")
    def test_02_failed_connection_closes_local_socket(self, mock_socket_factory):
        """Test 2: Failed connection closes local socket and raises ConnectionError."""
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = OSError("Connection refused")
        mock_socket_factory.return_value = mock_sock

        with self.assertRaises(ConnectionError) as ctx:
            FigCraftClient(host="127.0.0.1", port=7979)

        self.assertIn("Gagal terhubung ke FigCraft", str(ctx.exception))
        # Ensure the local socket instance that failed to connect was closed
        mock_sock.close.assert_called_once()

    @patch.object(figcraft_ui.socket, "socket")
    def test_03_close_socket_idempotent(self, mock_socket_factory):
        """Test 3: _close_socket() can be safely called repeatedly."""
        mock_sock = MagicMock()
        mock_socket_factory.return_value = mock_sock

        client = FigCraftClient(host="127.0.0.1", port=7979)
        client._buffer = "residual_data"

        # First call
        client._close_socket()
        self.assertIsNone(client.sock)
        self.assertEqual(client._buffer, "")
        mock_sock.close.assert_called_once()

        # Second call
        client._close_socket()
        self.assertIsNone(client.sock)
        self.assertEqual(client._buffer, "")
        # close() should still have only been called once on the mock
        mock_sock.close.assert_called_once()

    @patch.object(figcraft_ui.socket, "socket")
    def test_04_close_always_closes_socket_when_flush_fails(self, mock_socket_factory):
        """Test 4: close() guarantees socket closure even when flush() raises an exception."""
        mock_sock = MagicMock()
        mock_socket_factory.return_value = mock_sock

        client = FigCraftClient(host="127.0.0.1", port=7979)
        client._batch_queue = [{"command": "node.create", "as": "f1", "params": {}}]

        # Mock flush to raise an exception
        client.flush = MagicMock(side_effect=FigCraftError("Batch execution failed"))

        with self.assertRaises(FigCraftError) as ctx:
            client.close()

        self.assertIn("Batch execution failed", str(ctx.exception))
        self.assertIsNone(client.sock)
        self.assertEqual(client._buffer, "")
        mock_sock.close.assert_called_once()

    @patch.object(figcraft_ui.socket, "socket")
    def test_05_context_manager_normal_exit_closes_socket(self, mock_socket_factory):
        """Test 5: Context manager cleanly closes socket after a normal block."""
        mock_sock = MagicMock()
        mock_socket_factory.return_value = mock_sock

        client_ref = None
        with FigCraftClient(host="127.0.0.1", port=7979) as client:
            client_ref = client
            self.assertIsNotNone(client.sock)

        self.assertIsNone(client_ref.sock)
        self.assertEqual(client_ref._buffer, "")
        mock_sock.close.assert_called_once()

    @patch.object(figcraft_ui.socket, "socket")
    def test_06_context_manager_exception_does_not_flush(self, mock_socket_factory):
        """Test 6: Context manager does NOT call flush() when an exception occurs inside the block."""
        mock_sock = MagicMock()
        mock_socket_factory.return_value = mock_sock

        client_ref = None
        with self.assertRaises(ValueError):
            with FigCraftClient(host="127.0.0.1", port=7979) as client:
                client_ref = client
                client._batch_queue.append({"command": "node.create", "as": "f1", "params": {}})
                client.flush = MagicMock()
                raise ValueError("Error inside context block")

        # flush should NOT have been called
        client_ref.flush.assert_not_called()
        # Socket must still be closed
        self.assertIsNone(client_ref.sock)
        self.assertEqual(client_ref._buffer, "")
        mock_sock.close.assert_called_once()

    @patch.object(figcraft_ui.socket, "socket")
    def test_07_context_manager_preserves_original_exception(self, mock_socket_factory):
        """Test 7: Original exception in context block is preserved and not masked by cleanup."""
        mock_sock = MagicMock()
        # Mock close to raise an exception during cleanup
        mock_sock.close.side_effect = RuntimeError("Error during socket close")
        mock_socket_factory.return_value = mock_sock

        with self.assertRaises(KeyError) as ctx:
            with FigCraftClient(host="127.0.0.1", port=7979) as client:
                raise KeyError("Original domain error")

        self.assertIn("Original domain error", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
