"""
figcraft_ui.py (v4.0) - Live Streaming & Batch UI Automation Library for FigCraft.
Communicates with FigCraft Engine over TCP JSON-RPC (engine.execute).
"""

import socket
import json
import os
import time
import re
import copy
import math
import subprocess
import shutil
from typing import Union, List, Dict, Optional, Any

NodeRef = Union[int, str, Dict[str, str]]
DEFAULT_FIGCRAFT_APP = r"C:\Program Files\FigCraft\figcraft.exe"


class FigCraftError(RuntimeError):
    """Raised when a FigCraft RPC command or batch step fails in strict mode."""
    pass


class FigCraftClient:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7979,
        auto_batch: bool = False,
        strict: bool = True,
        live_select: bool = True,
        step_delay_ms: float = 50.0,
        auto_launch: bool = True,
        app_path: Optional[str] = None
    ):
        self.host = host
        self.port = port
        self.auto_batch = auto_batch
        self.strict = strict
        self.live_select = live_select
        self.step_delay_ms = step_delay_ms
        self.auto_launch = auto_launch
        self.app_path = app_path
        self.sock: Optional[socket.socket] = None
        self._req_id = 0
        self._step_counter = 0
        self._buffer = ""
        self._batch_queue: List[Dict[str, Any]] = []
        self._resolved_refs: Dict[str, int] = {}
        self.total_rpc_ms: float = 0.0
        self.last_flush_ms: float = 0.0
        self.last_error: Optional[str] = None
        self.last_failure_stage: Optional[str] = None
        self.last_failed_batch: Optional[List[Dict[str, Any]]] = None
        self.connect()

    def _close_socket(self):
        """Closes the underlying TCP socket and resets the stream buffer."""
        self._buffer = ""
        if self.sock is not None:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def _find_figcraft_binary(self) -> Optional[str]:
        """Finds the figcraft.exe executable on the host machine."""
        if self.app_path and os.path.exists(self.app_path):
            return self.app_path
        candidates = [
            DEFAULT_FIGCRAFT_APP,
            r"C:\Program Files (x86)\FigCraft\figcraft.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\FigCraft\figcraft.exe"),
        ]
        for cand in candidates:
            if cand and os.path.exists(cand):
                return cand
        which_path = shutil.which("figcraft") or shutil.which("figcraft.exe")
        if which_path and os.path.exists(which_path):
            return which_path
        return None

    def _try_socket_connect(self) -> bool:
        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
            s.connect((self.host, self.port))
            self.sock = s
            self.sock.settimeout(20.0)
            return True
        except Exception:
            if s is not None:
                try:
                    s.close()
                except Exception:
                    pass
            return False

    def connect(self):
        """Connects to FigCraft engine. If auto_launch is True and connection fails, attempts to launch FigCraft."""
        self._close_socket()
        if self._try_socket_connect():
            return

        # If direct connection fails and auto_launch is enabled
        if self.auto_launch:
            bin_path = self._find_figcraft_binary()
            if bin_path:
                try:
                    print(f"[figcraft_ui] FigCraft belum aktif di {self.host}:{self.port}. Meluncurkan: {bin_path} --control {self.port} ...")
                    subprocess.Popen(
                        [bin_path, "--control", str(self.port)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        close_fds=(os.name != "nt")
                    )
                    start_time = time.time()
                    timeout = 15.0
                    while time.time() - start_time < timeout:
                        time.sleep(0.3)
                        if self._try_socket_connect():
                            print(f"[figcraft_ui] Berhasil terhubung ke FigCraft di {self.host}:{self.port}!")
                            return
                except Exception as e:
                    print(f"[figcraft_ui Warning] Gagal meluncurkan FigCraft secara otomatis: {e}")

        raise ConnectionError(
            f"[figcraft_ui] Gagal terhubung ke FigCraft di {self.host}:{self.port}. "
            f"Pastikan aplikasi FigCraft berjalan dengan `--control {self.port}`."
        )

    def close(self):
        """Flushes pending batch commands and closes the TCP socket."""
        try:
            if self._batch_queue:
                self.flush()
        finally:
            self._close_socket()

    def __enter__(self):
        if not self.sock:
            self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._close_socket()
            return False
        self.close()
        return False

    def execute(self, command: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Executes a single engine command immediately over TCP JSON-RPC and measures latency."""
        if params is None:
            params = {}
        self.last_error = None
        self.last_failure_stage = None

        self._req_id += 1
        current_req_id = self._req_id
        req = {
            "jsonrpc": "2.0",
            "id": current_req_id,
            "method": "engine.execute",
            "params": {
                "command": command,
                "params": params
            }
        }
        try:
            payload = (json.dumps(req) + "\n").encode("utf-8")
        except (TypeError, ValueError) as e:
            self.last_failure_stage = "PRE_SEND"
            self.last_error = f"Gagal serialisasi JSON untuk `{command}`: {e}"
            if self.strict:
                raise FigCraftError(self.last_error) from e
            print(f"[figcraft_ui Warning] {self.last_error}")
            return {}

        if not self.sock:
            try:
                self.connect()
            except ConnectionError as e:
                self.last_failure_stage = "PRE_SEND"
                self.last_error = f"Gagal menghubungkan soket sebelum mengirim `{command}`: {e}"
                if self.strict:
                    raise
                print(f"[figcraft_ui Warning] {self.last_error}")
                return {}

        if self._buffer.strip():
            stale_data = self._buffer
            self._close_socket()
            self.last_failure_stage = "INVALID_RESPONSE"
            self.last_error = f"Buffer stream TCP tidak kosong sebelum pengiriman `{command}`: {stale_data!r}"
            if self.strict:
                raise FigCraftError(self.last_error)
            print(f"[figcraft_ui Warning] {self.last_error}")
            return {}
        self._buffer = ""

        t0 = time.perf_counter()
        try:
            self.sock.sendall(payload)
        except (socket.error, BrokenPipeError, OSError) as e:
            self._close_socket()
            self.last_failure_stage = "SEND_AMBIGUOUS"
            self.last_error = f"Transmisi TCP gagal saat mengirim `{command}`: {e}"
            if self.strict:
                raise ConnectionError(f"[figcraft_ui] {self.last_error}") from e
            print(f"[figcraft_ui Warning] {self.last_error}")
            return {}

        buf = self._buffer
        while True:
            if "\n" in buf:
                line, rest = buf.split("\n", 1)
                self._buffer = rest
                if line.strip():
                    elapsed_ms = (time.perf_counter() - t0) * 1000.0
                    self.total_rpc_ms += elapsed_ms
                    try:
                        resp = json.loads(line)
                    except json.JSONDecodeError as e:
                        self._close_socket()
                        self.last_failure_stage = "INVALID_RESPONSE"
                        self.last_error = f"Respons JSON tidak valid untuk `{command}`: {e}"
                        if self.strict:
                            raise FigCraftError(self.last_error) from e
                        print(f"[figcraft_ui Warning] {self.last_error}")
                        return {}

                    if not isinstance(resp, dict):
                        self._close_socket()
                        self.last_failure_stage = "INVALID_RESPONSE"
                        self.last_error = f"Format respons bukan objek JSON untuk `{command}`: {resp}"
                        if self.strict:
                            raise FigCraftError(self.last_error)
                        print(f"[figcraft_ui Warning] {self.last_error}")
                        return {}

                    resp_id = resp.get("id")
                    if resp_id is not None and resp_id != current_req_id:
                        self._close_socket()
                        self.last_failure_stage = "INVALID_RESPONSE"
                        self.last_error = f"Mismatch ID respons pada `{command}`: dikirim {current_req_id}, diterima {resp_id}"
                        if self.strict:
                            raise FigCraftError(self.last_error)
                        print(f"[figcraft_ui Warning] {self.last_error}")
                        return {}

                    if "ok" not in resp:
                        self._close_socket()
                        self.last_failure_stage = "INVALID_RESPONSE"
                        self.last_error = f"Format respons tidak memiliki field 'ok' untuk `{command}`: {resp}"
                        if self.strict:
                            raise FigCraftError(self.last_error)
                        print(f"[figcraft_ui Warning] {self.last_error}")
                        return {}

                    # Reject unexpected extra responses in buffer for synchronous 1:1 RPC
                    if self._buffer.strip():
                        extra_data = self._buffer
                        self._close_socket()
                        self.last_failure_stage = "INVALID_RESPONSE"
                        self.last_error = f"Menerima respons/data ekstra yang tidak terduga pada `{command}`: {extra_data!r}"
                        if self.strict:
                            raise FigCraftError(self.last_error)
                        print(f"[figcraft_ui Warning] {self.last_error}")
                        return {}

                    self._buffer = ""

                    if not resp.get("ok", False):
                        err_msg = resp.get("error", "Unknown error")
                        self.last_failure_stage = None
                        self.last_error = f"Command `{command}` gagal: {err_msg}"
                        if self.strict:
                            raise FigCraftError(f"{self.last_error} | Params: {params}")
                        print(f"[figcraft_ui Warning] `{command}` failed: {err_msg}")
                        return {}

                    return resp.get("result", {})
                buf = self._buffer

            try:
                chunk = self.sock.recv(65536).decode("utf-8")
                if not chunk:
                    is_incomplete = bool(buf.strip())
                    self._close_socket()
                    self.last_failure_stage = "RECV_AMBIGUOUS"
                    if is_incomplete:
                        self.last_error = f"Koneksi terputus dengan respons tidak lengkap untuk `{command}`: {buf!r}"
                    else:
                        self.last_error = f"Koneksi ditutup oleh FigCraft Engine tanpa respons untuk `{command}`."
                    if self.strict:
                        raise ConnectionError(f"[figcraft_ui] {self.last_error}")
                    print(f"[figcraft_ui Warning] {self.last_error}")
                    return {}
                buf += chunk
                self._buffer = buf
            except socket.timeout as e:
                self._close_socket()
                self.last_failure_stage = "RECV_AMBIGUOUS"
                self.last_error = f"Timeout saat menunggu respons `{command}`"
                if self.strict:
                    raise FigCraftError(self.last_error) from e
                print(f"[figcraft_ui Warning] {self.last_error}")
                return {}
            except (socket.error, OSError, UnicodeDecodeError) as e:
                self._close_socket()
                self.last_failure_stage = "RECV_AMBIGUOUS"
                self.last_error = f"Kesalahan soket saat membaca respons `{command}`: {e}"
                if self.strict:
                    raise ConnectionError(f"[figcraft_ui] {self.last_error}") from e
                print(f"[figcraft_ui Warning] {self.last_error}")
                return {}

    def _resolve_param_refs(self, obj: Any) -> Any:
        """Recursively substitutes already-flushed `$ref` dicts with their integer IDs,
        and validates that unresolved `$ref` references exist in the active batch queue."""
        if isinstance(obj, dict):
            if "$ref" in obj and len(obj) == 1:
                ref_key = obj["$ref"]
                if ref_key in self._resolved_refs:
                    return self._resolved_refs[ref_key]
                if not self.auto_batch:
                    err_msg = f"Unresolved reference '$ref': '{ref_key}' cannot be used when auto_batch=False"
                    self.last_error = err_msg
                    raise FigCraftError(err_msg)
                in_active_queue = any(cmd.get("as") == ref_key for cmd in self._batch_queue)
                if not in_active_queue:
                    err_msg = f"Dangling reference detected: '$ref': '{ref_key}' is neither resolved nor in the active batch queue"
                    self.last_error = err_msg
                    raise FigCraftError(err_msg)
                return obj
            return {k: self._resolve_param_refs(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._resolve_param_refs(item) for item in obj]
        return obj

    def _enqueue_or_run(self, command: str, params: Dict[str, Any], as_prefix: str = "node") -> NodeRef:
        """Queues a command into the active batch or executes immediately."""
        clean_params = self._resolve_param_refs(params)
        if self.auto_batch:
            self._step_counter += 1
            step_name = f"{as_prefix}_{self._step_counter}"
            self._batch_queue.append({
                "command": command,
                "as": step_name,
                "params": clean_params
            })
            return {"$ref": step_name}
        else:
            res = self.execute(command, clean_params)
            if self.step_delay_ms > 0:
                time.sleep(self.step_delay_ms / 1000.0)
            return res.get("id") if isinstance(res, dict) else res

    def flush(self, label: str = "Fast UI Batch") -> List[Dict[str, Any]]:
        """Flushes all queued commands in one atomic `command.batch` call."""
        if not self._batch_queue:
            return []
        commands = list(self._batch_queue)
        self._batch_queue = []
        t0 = time.perf_counter()
        results = None
        try:
            results = self.execute("command.batch", {
                "label": label,
                "onError": "abort" if self.strict else "continue",
                "commands": commands
            })
        except Exception as e:
            self.last_failed_batch = copy.deepcopy(commands)
            if not self.last_error:
                self.last_error = str(e)
            raise

        self.last_flush_ms = (time.perf_counter() - t0) * 1000.0

        if not isinstance(results, list):
            self.last_failed_batch = copy.deepcopy(commands)
            err_msg = self.last_error or f"Invalid batch response: expected list of results, got {type(results).__name__}"
            self.last_error = err_msg
            if self.strict:
                raise FigCraftError(err_msg)
            return []

        if len(results) != len(commands):
            self.last_failed_batch = copy.deepcopy(commands)
            mismatch_msg = f"Batch result count mismatch: expected {len(commands)}, got {len(results)}"
            self.last_error = mismatch_msg
            if self.strict:
                raise FigCraftError(mismatch_msg)
            return results

        staged_refs: Dict[str, int] = {}
        has_structural_failure = False
        has_step_failure = False
        first_error_msg: Optional[str] = None

        if self.strict:
            # Abort mode (strict=True): Engine returns raw command results in order
            # (dict, list, scalar, or None), or a step error dict in mocked unit tests.
            for idx, (cmd_item, res_item) in enumerate(zip(commands, results)):
                as_name = cmd_item.get("as")
                cmd_name = cmd_item.get("command")

                if isinstance(res_item, dict):
                    is_ok = res_item.get("ok")
                    if is_ok is False or (is_ok is None and "error" in res_item):
                        has_step_failure = True
                        step_err = res_item.get("error", "Unknown batch step error")
                        err_text = f"Batch step '{as_name}' ({cmd_name}) failed: {step_err}"
                        if not first_error_msg:
                            first_error_msg = err_text
                            self.last_error = err_text
                        continue

                    inner = res_item.get("result", res_item) if "ok" in res_item else res_item
                    if (
                        as_name
                        and isinstance(inner, dict)
                        and isinstance(inner.get("id"), int)
                        and not isinstance(inner.get("id"), bool)
                    ):
                        staged_refs[as_name] = inner["id"]
                elif res_item is not None and not isinstance(res_item, (list, int, float, str, bool)):
                    has_structural_failure = True
                    err_text = f"Invalid batch step result format at index {idx}: unexpected type {type(res_item).__name__}"
                    if not first_error_msg:
                        first_error_msg = err_text
                        self.last_error = err_text
        else:
            # Continue mode (strict=False): Engine returns per-step wrapper dicts
            # {command, ok, result|error, step}.
            for idx, (cmd_item, res_item) in enumerate(zip(commands, results)):
                as_name = cmd_item.get("as")
                cmd_name = cmd_item.get("command")

                if not isinstance(res_item, dict):
                    has_structural_failure = True
                    err_text = f"Malformed batch step wrapper at index {idx}: expected dict, got {type(res_item).__name__}"
                    if not first_error_msg:
                        first_error_msg = err_text
                        self.last_error = err_text
                    continue

                is_ok = res_item.get("ok")
                if not isinstance(is_ok, bool):
                    has_structural_failure = True
                    err_text = f"Malformed batch step wrapper at index {idx}: missing or non-boolean 'ok' field"
                    if not first_error_msg:
                        first_error_msg = err_text
                        self.last_error = err_text
                    continue

                if "step" in res_item and res_item["step"] != idx:
                    has_structural_failure = True
                    err_text = f"Malformed batch step wrapper at index {idx}: expected step {idx}, got {res_item['step']!r}"
                    if not first_error_msg:
                        first_error_msg = err_text
                        self.last_error = err_text
                    continue

                if "command" in res_item and res_item["command"] != cmd_name:
                    has_structural_failure = True
                    err_text = (
                        f"Malformed batch step wrapper at index {idx}: "
                        f"expected command '{cmd_name}', got {res_item['command']!r}"
                    )
                    if not first_error_msg:
                        first_error_msg = err_text
                        self.last_error = err_text
                    continue

                if not is_ok:
                    has_step_failure = True
                    step_err = res_item.get("error", "Unknown batch step error")
                    err_text = f"Batch step '{as_name}' ({cmd_name}) failed: {step_err}"
                    if not first_error_msg:
                        first_error_msg = err_text
                        self.last_error = err_text
                    print(f"[figcraft_ui Batch Error] Step '{as_name}': {step_err}")
                    continue

                if "result" not in res_item:
                    has_structural_failure = True
                    err_text = f"Malformed batch step wrapper at index {idx}: missing 'result' field for ok=True step"
                    if not first_error_msg:
                        first_error_msg = err_text
                        self.last_error = err_text
                    continue

                inner = res_item["result"]
                if (
                    as_name
                    and isinstance(inner, dict)
                    and isinstance(inner.get("id"), int)
                    and not isinstance(inner.get("id"), bool)
                ):
                    staged_refs[as_name] = inner["id"]

        if has_structural_failure:
            self.last_failed_batch = copy.deepcopy(commands)
            if self.strict:
                raise FigCraftError(first_error_msg or "Invalid batch response structure")
            return results

        if has_step_failure:
            self.last_failed_batch = copy.deepcopy(commands)
            if self.strict:
                raise FigCraftError(first_error_msg or "Batch execution failed")
            self._resolved_refs.update(staged_refs)
            return results

        self._resolved_refs.update(staged_refs)
        self.last_failed_batch = None
        return results

    def resolve_id(self, ref: NodeRef) -> Optional[int]:
        """Resolves a `$ref` dictionary or integer ID into a concrete integer layer ID."""
        if isinstance(ref, int):
            return ref
        if isinstance(ref, dict) and "$ref" in ref:
            ref_name = ref["$ref"]
            if ref_name not in self._resolved_refs and self._batch_queue:
                self.flush()
            return self._resolved_refs.get(ref_name)
        return None

    def clear_canvas(self):
        """Clears queue, selects all layers on current page, and deletes them safely."""
        self._batch_queue.clear()
        self._resolved_refs.clear()
        self.execute("select.all")
        # If nothing is on the canvas, select.all selects nothing and edit.delete would fail in strict mode
        try:
            self.execute("edit.delete")
        except FigCraftError:
            pass

    # ==========================================================================
    # CORE LAYER BUILDERS
    # ==========================================================================

    def create_frame(
        self,
        name: str,
        x: float = 0,
        y: float = 0,
        width: float = 1440,
        height: float = 900,
        fill: str = "#FFF8F0",
        clip: bool = True,
        props: Optional[Dict[str, Any]] = None,
        parent: Optional[NodeRef] = None
    ) -> NodeRef:
        p: Dict[str, Any] = {"fill": fill, "clip": clip}
        if props:
            p.update(props)
        params: Dict[str, Any] = {
            "type": "frame",
            "name": name,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "select": self.live_select,
            "props": p
        }
        if parent is not None:
            params["parent"] = parent
        return self._enqueue_or_run("node.create", params, as_prefix="frame")

    def box(
        self,
        parent: Optional[NodeRef] = None,
        name: str = "Box",
        layout: Optional[str] = "vertical",
        x: float = 0,
        y: float = 0,
        width: Optional[float] = None,
        height: Optional[float] = None,
        gap: float = 0,
        padding: Union[float, List[float]] = 0,
        mainAlign: str = "min",
        crossAlign: str = "min",
        fill: Optional[str] = None,
        stroke: Optional[str] = None,
        strokeWeight: float = 1,
        cornerRadius: Union[float, List[float]] = 0,
        sizingH: Optional[str] = None,
        sizingV: Optional[str] = None,
        wrap: bool = False,
        effects: Optional[List[Dict[str, Any]]] = None,
        clip: bool = False,
        absolute: bool = False,
        props: Optional[Dict[str, Any]] = None
    ) -> NodeRef:
        resolved_sizing_h = sizingH or ("fixed" if width is not None else "hug")
        resolved_sizing_v = sizingV or ("fixed" if height is not None else "hug")

        p: Dict[str, Any] = {
            "clip": clip,
            "sizingH": resolved_sizing_h,
            "sizingV": resolved_sizing_v
        }
        if layout is not None:
            p["layout"] = layout
            p["gap"] = gap
            p["padding"] = padding
            p["mainAlign"] = mainAlign
            p["crossAlign"] = crossAlign
            p["wrap"] = wrap

        if fill is not None:
            p["fill"] = fill
        else:
            p["fills"] = []
        if stroke is not None:
            p["stroke"] = stroke
            p["strokeWeight"] = strokeWeight
        if cornerRadius:
            p["cornerRadius"] = cornerRadius
        if effects:
            p["effects"] = effects
        if absolute:
            p["absolute"] = True
        if props:
            p.update(props)

        params: Dict[str, Any] = {
            "type": "frame",
            "name": name,
            "x": x,
            "y": y,
            "select": self.live_select,
            "props": p
        }
        if width is not None:
            params["width"] = width
        if height is not None:
            params["height"] = height
        if parent is not None:
            params["parent"] = parent

        return self._enqueue_or_run("node.create", params, as_prefix="box")

    def create_rect(
        self,
        parent: NodeRef,
        name: str = "Rect",
        x: float = 0,
        y: float = 0,
        width: float = 100,
        height: float = 100,
        fill: Optional[str] = None,
        stroke: Optional[str] = None,
        strokeWeight: float = 1,
        cornerRadius: Union[float, List[float]] = 0,
        effects: Optional[List[Dict[str, Any]]] = None,
        absolute: bool = False,
        sizingH: Optional[str] = None,
        sizingV: Optional[str] = None
    ) -> NodeRef:
        p: Dict[str, Any] = {}
        if fill is not None:
            p["fill"] = fill
        else:
            p["fills"] = []
        if stroke is not None:
            p["stroke"] = stroke
            p["strokeWeight"] = strokeWeight
        if cornerRadius:
            p["cornerRadius"] = cornerRadius
        if effects:
            p["effects"] = effects
        if absolute:
            p["absolute"] = True
        if sizingH:
            p["sizingH"] = sizingH
        if sizingV:
            p["sizingV"] = sizingV

        params: Dict[str, Any] = {
            "type": "rectangle",
            "name": name,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "parent": parent,
            "select": self.live_select,
            "props": p
        }
        return self._enqueue_or_run("node.create", params, as_prefix="rect")

    def create_text(
        self,
        parent: NodeRef,
        text: str,
        name: Optional[str] = None,
        x: float = 0,
        y: float = 0,
        width: Optional[float] = None,
        fontSize: float = 14,
        fontFamily: str = "Plus Jakarta Sans",
        fontStyle: str = "Regular",
        fill: str = "#3B2219",
        textAlign: str = "left",
        lineHeight: Optional[Union[float, str]] = None,
        letterSpacing: Optional[Union[float, str]] = None,
        sizingH: Optional[str] = None,
        absolute: bool = False
    ) -> NodeRef:
        p: Dict[str, Any] = {
            "fontSize": fontSize,
            "fontFamily": fontFamily,
            "fontStyle": fontStyle,
            "fill": fill,
            "textAlign": textAlign
        }
        if lineHeight is not None:
            p["lineHeight"] = lineHeight
        if letterSpacing is not None:
            p["letterSpacing"] = letterSpacing
        if sizingH is not None:
            p["sizingH"] = sizingH
        if absolute:
            p["absolute"] = True

        params: Dict[str, Any] = {
            "type": "text",
            "name": name or (text[:24] + "..." if len(text) > 24 else text),
            "text": text,
            "x": x,
            "y": y,
            "parent": parent,
            "select": self.live_select,
            "props": p
        }
        if width is not None:
            params["width"] = width
        return self._enqueue_or_run("node.create", params, as_prefix="txt")

    def circle_arc(
        self,
        parent: NodeRef,
        name: str = "CircleArc",
        cx: float = 20,
        cy: float = 20,
        r: float = 20,
        fill: Optional[str] = "#E04D68",
        stroke: Optional[str] = None,
        strokeWeight: float = 1,
        absolute: bool = False
    ) -> NodeRef:
        d = r * 2.0
        path = (
            f"M 0 {r:.2f} "
            f"A {r:.2f} {r:.2f} 0 1 0 {d:.2f} {r:.2f} "
            f"A {r:.2f} {r:.2f} 0 1 0 0 {r:.2f} Z"
        )
        p: Dict[str, Any] = {}
        if fill is not None:
            p["fill"] = fill
        else:
            p["fills"] = []
        if stroke is not None:
            p["stroke"] = stroke
        if stroke is not None:
            p["strokeWeight"] = strokeWeight
        if absolute:
            p["absolute"] = True

        params: Dict[str, Any] = {
            "type": "vector",
            "name": name,
            "x": cx - r,
            "y": cy - r,
            "width": d,
            "height": d,
            "path": path,
            "closed": True,
            "parent": parent,
            "select": self.live_select,
            "props": p
        }
        return self._enqueue_or_run("node.create", params, as_prefix="circ")

    # ==========================================================================
    # NATIVE FIGCRAFT STYLES & COMPONENTS (Fitur #7 & #8)
    # ==========================================================================

    def create_color_style(self, name: str, color_hex: str, description: str = "") -> NodeRef:
        """Creates a native FigCraft Paint Style."""
        params: Dict[str, Any] = {
            "type": "paint",
            "name": name,
            "description": description,
            "value": [{"type": "solid", "color": color_hex}]
        }
        return self._enqueue_or_run("style.create", params, as_prefix="style")

    def create_text_style(
        self,
        name: str,
        fontFamily: str = "Plus Jakarta Sans",
        fontStyle: str = "Regular",
        fontSize: float = 14,
        lineHeight: Optional[float] = None
    ) -> NodeRef:
        """Creates a native FigCraft Text Style."""
        val: Dict[str, Any] = {
            "fontFamily": fontFamily,
            "fontStyle": fontStyle,
            "fontSize": fontSize
        }
        if lineHeight is not None:
            val["lineHeight"] = lineHeight
        params: Dict[str, Any] = {
            "type": "text",
            "name": name,
            "value": val
        }
        return self._enqueue_or_run("style.create", params, as_prefix="tstyle")

    def apply_style(self, node_refs: List[NodeRef], style_name_or_id: Union[str, int], target: str = "fill"):
        """Applies a registered Paint or Text style to one or more layers."""
        if self._batch_queue:
            self.flush(label="Pre-Style Flush")
        ids = [self.resolve_id(r) for r in node_refs]
        valid_ids = [i for i in ids if i is not None]
        if valid_ids:
            self.execute("style.apply", {
                "ids": valid_ids,
                "style": style_name_or_id,
                "target": target
            })

    def create_component(
        self,
        name: str,
        x: float = 0,
        y: float = -500,
        width: Optional[float] = None,
        height: Optional[float] = None,
        layout: Optional[str] = "horizontal",
        gap: float = 0,
        padding: Union[float, List[float]] = 0,
        mainAlign: str = "min",
        crossAlign: str = "center",
        fill: Optional[str] = None,
        stroke: Optional[str] = None,
        strokeWeight: float = 1,
        cornerRadius: Union[float, List[float]] = 0,
        parent: Optional[NodeRef] = None
    ) -> NodeRef:
        """Creates a reusable Main Component (`type='component'`)."""
        p: Dict[str, Any] = {
            "sizingH": "fixed" if width is not None else "hug",
            "sizingV": "fixed" if height is not None else "hug"
        }
        if layout is not None:
            p["layout"] = layout
            p["gap"] = gap
            p["padding"] = padding
            p["mainAlign"] = mainAlign
            p["crossAlign"] = crossAlign
        if fill is not None:
            p["fill"] = fill
        else:
            p["fills"] = []
        if stroke is not None:
            p["stroke"] = stroke
            p["strokeWeight"] = strokeWeight
        if cornerRadius:
            p["cornerRadius"] = cornerRadius

        params: Dict[str, Any] = {
            "type": "component",
            "name": name,
            "x": x,
            "y": y,
            "select": self.live_select,
            "props": p
        }
        if width is not None:
            params["width"] = width
        if height is not None:
            params["height"] = height
        if parent is not None:
            params["parent"] = parent
        return self._enqueue_or_run("node.create", params, as_prefix="comp")

    def create_instance(
        self,
        component: NodeRef,
        parent: Optional[NodeRef] = None,
        x: float = 0,
        y: float = 0
    ) -> NodeRef:
        """Creates an Instance linked to a Main Component."""
        params: Dict[str, Any] = {
            "component": component,
            "x": x,
            "y": y
        }
        if parent is not None:
            params["parent"] = parent
        return self._enqueue_or_run("instance.create", params, as_prefix="inst")

    # ==========================================================================
    # ANTI-GLITCH & VERIFICATION HELPERS (Fitur #1, #3, #4)
    # ==========================================================================

    def equasize_heights(self, node_refs: List[NodeRef], target_height: Optional[float] = None) -> float:
        """
        Equalizes vertical height across a list of cards.
        When `target_height` is None, queries `node.get` on each card and equalizes to `max(height)`.
        Returns the applied height.
        """
        if self._batch_queue:
            self.flush(label="Pre-Equasize Flush")

        resolved_ids = [self.resolve_id(ref) for ref in node_refs]
        valid_ids = [nid for nid in resolved_ids if nid is not None]
        if not valid_ids:
            return 0.0

        if target_height is None:
            heights = []
            for nid in valid_ids:
                info = self.execute("node.get", {"id": nid, "fields": ["height"]})
                if isinstance(info, dict) and "height" in info:
                    heights.append(float(info["height"]))
            target_height = max(heights) if heights else 200.0

        self.execute("node.set", {
            "ids": valid_ids,
            "props": {
                "height": target_height,
                "sizingV": "fixed"
            }
        })
        return float(target_height)

    equalize_heights = equasize_heights

    def verify_layout(
        self,
        frame_refs: Optional[List[NodeRef]] = None,
        tolerance: float = 2.0
    ) -> Dict[str, Any]:
        """
        Automated layout auditor (Fitur #3 - v3.1).
        Inspects layer subtrees via `node.get` to detect:
        1. Child Overflow (child `absoluteBounds` exceeding parent `absoluteBounds` by > `tolerance` px)
        2. Zero-Size Layers (`width <= 0` or `height <= 0`)
        3. Sibling Overlap (flow children inside an auto-layout frame overlapping by > `tolerance` px)
        4. Unpadded Visual Box (text flush at 0px top-left of a visibly filled/stroked container)
        Returns `{"ok": bool, "violation_count": int, "violations": [...]}`.
        """
        violations: List[Dict[str, Any]] = []

        def _fail_audit(err_msg: str) -> Dict[str, Any]:
            self.last_error = err_msg
            if self.strict:
                raise FigCraftError(err_msg)
            return {
                "ok": False,
                "error": err_msg,
                "violation_count": len(violations),
                "violations": violations
            }

        if self._batch_queue:
            self.flush(label="Pre-Verify Flush")
            if self.last_error is not None or self.last_failed_batch is not None:
                return _fail_audit(self.last_error or "Pre-verify batch flush failed")

        target_ids: List[int] = []
        if frame_refs is not None:
            if not isinstance(frame_refs, list) or len(frame_refs) == 0:
                return _fail_audit("verify_layout requires a non-empty list when frame_refs is provided")
            for idx, ref in enumerate(frame_refs):
                if isinstance(ref, bool):
                    return _fail_audit(f"Unresolved or invalid frame reference at index {idx}: {ref!r}")
                rid = self.resolve_id(ref)
                if rid is None or not isinstance(rid, int) or isinstance(rid, bool):
                    return _fail_audit(f"Unresolved or invalid frame reference at index {idx}: {ref!r}")
                target_ids.append(rid)
        else:
            found = self.execute("node.find", {"type": "FRAME", "limit": 500})
            if self.last_error is not None:
                return _fail_audit(self.last_error)
            if not isinstance(found, dict) or "ids" not in found or not isinstance(found["ids"], list):
                return _fail_audit(
                    f"Invalid response from node.find during verify_layout: expected dict with 'ids' list, got {type(found).__name__}"
                )
            raw_ids = found["ids"][:20]
            for idx, fid in enumerate(raw_ids):
                if not isinstance(fid, int) or isinstance(fid, bool):
                    return _fail_audit(f"Invalid frame ID in node.find response at index {idx}: {fid!r}")
                target_ids.append(fid)
            if not target_ids:
                return _fail_audit("No target frames found on canvas to audit")

        audit_fields = [
            "id", "name", "type", "absoluteBounds", "clip",
            "absolute", "layout", "fills", "strokes", "strokeWeight", "children"
        ]

        class _AuditAbort(Exception):
            pass

        fetched_node_ids = set()
        visited_node_ids = set()

        def _abort_or_fail(err_msg: str):
            self.last_error = err_msg
            if self.strict:
                raise FigCraftError(err_msg)
            raise _AuditAbort(err_msg)

        def _validate_bounds(bounds: Any, node_id: Any, node_name: str) -> Dict[str, float]:
            if not isinstance(bounds, dict):
                _abort_or_fail(
                    f"Invalid or missing absoluteBounds for node {node_name!r} (id={node_id!r}): "
                    f"expected dict, got {type(bounds).__name__}"
                )
            required_keys = ("x", "y", "width", "height")
            missing_keys = [k for k in required_keys if k not in bounds]
            if missing_keys:
                _abort_or_fail(
                    f"Incomplete absoluteBounds for node {node_name!r} (id={node_id!r}): "
                    f"missing keys {missing_keys}"
                )
            validated: Dict[str, float] = {}
            for k in required_keys:
                val = bounds[k]
                if isinstance(val, bool) or not isinstance(val, (int, float)):
                    _abort_or_fail(
                        f"Invalid absoluteBounds[{k!r}] for node {node_name!r} (id={node_id!r}): "
                        f"expected finite number, got {val!r} ({type(val).__name__})"
                    )
                fval = float(val)
                if not math.isfinite(fval):
                    _abort_or_fail(
                        f"Non-finite absoluteBounds[{k!r}] for node {node_name!r} (id={node_id!r}): "
                        f"got {val!r}"
                    )
                validated[k] = fval
            return validated

        def _prepare_node(node_obj: Dict[str, Any]) -> Dict[str, Any]:
            raw_children = node_obj.get("children")
            child_count = node_obj.get("childCount", 0)
            needs_fetch = (
                not raw_children
                and isinstance(child_count, int)
                and not isinstance(child_count, bool)
                and child_count > 0
            )
            if not needs_fetch:
                return node_obj

            req_id = node_obj.get("id")
            if not isinstance(req_id, int) or isinstance(req_id, bool):
                _abort_or_fail(f"Cannot lazy-fetch subtree in verify_layout: invalid node id {req_id!r}")

            if req_id in fetched_node_ids:
                return node_obj
            fetched_node_ids.add(req_id)

            fetched = self.execute("node.get", {"id": req_id, "fields": audit_fields})
            if self.last_error is not None:
                _abort_or_fail(self.last_error)
            if not isinstance(fetched, dict):
                _abort_or_fail(
                    f"Lazy fetch for node {req_id} in verify_layout failed: expected dict, got {type(fetched).__name__}"
                )
            fetched_id = fetched.get("id")
            if not isinstance(fetched_id, int) or isinstance(fetched_id, bool) or fetched_id != req_id:
                _abort_or_fail(
                    f"Invalid lazy-fetch response for node {req_id} in verify_layout: mismatched or invalid id {fetched_id!r}"
                )
            fetched_children = fetched.get("children")
            if not isinstance(fetched_children, list) or len(fetched_children) == 0:
                _abort_or_fail(
                    f"Inconsistent lazy-fetch response for node {req_id} in verify_layout: "
                    f"childCount={child_count} but children is empty or invalid"
                )
            return fetched

        def _audit_node(node: Dict[str, Any], screen_name: str, depth: int = 0):
            node = _prepare_node(node)
            node_id = node.get("id")
            if isinstance(node_id, int) and not isinstance(node_id, bool):
                if node_id in visited_node_ids:
                    return
                visited_node_ids.add(node_id)

            p_name = node.get("name", f"id:{node_id}")
            p_bounds = _validate_bounds(node.get("absoluteBounds"), node_id, p_name)
            p_type = node.get("type", "")
            p_layout = node.get("layout")
            p_fills = node.get("fills")
            p_strokes = node.get("strokes")
            p_stroke_weight = node.get("strokeWeight")
            raw_children = node.get("children", [])
            _ = node.get("childCount", len(raw_children) if isinstance(raw_children, list) else 0)

            pw = p_bounds["width"]
            ph = p_bounds["height"]
            if pw <= 0 or ph <= 0:
                violations.append({
                    "screen": screen_name,
                    "kind": "zero_size",
                    "node_id": node_id,
                    "node_name": p_name,
                    "detail": f"Layer memiliki ukuran tidak valid ({pw}x{ph})"
                })

            children: List[Dict[str, Any]] = []
            if isinstance(raw_children, list):
                for raw_child in raw_children:
                    if not isinstance(raw_child, dict):
                        _abort_or_fail(
                            f"Invalid child entry in node {p_name!r} (id={node_id!r}): "
                            f"expected dict, got {type(raw_child).__name__}"
                        )
                    children.append(_prepare_node(raw_child))

            if children and p_type in ("FRAME", "COMPONENT", "INSTANCE"):
                px = p_bounds["x"]
                py = p_bounds["y"]
                pr = px + pw
                pb = py + ph

                has_visible_box = bool(p_fills) or (
                    bool(p_strokes)
                    and isinstance(p_stroke_weight, (int, float))
                    and not isinstance(p_stroke_weight, bool)
                    and float(p_stroke_weight) > 0
                )

                flow_children: List[Dict[str, Any]] = []

                for child in children:
                    c_id = child.get("id")
                    c_name = child.get("name", f"id:{c_id}")
                    c_type = child.get("type", "")
                    c_bounds = _validate_bounds(child.get("absoluteBounds"), c_id, c_name)
                    cx = c_bounds["x"]
                    cy = c_bounds["y"]
                    cr = cx + c_bounds["width"]
                    cb = cy + c_bounds["height"]

                    over_r = cr - pr
                    over_b = cb - pb
                    over_l = px - cx
                    over_t = py - cy

                    if max(over_r, over_b, over_l, over_t) > tolerance:
                        violations.append({
                            "screen": screen_name,
                            "kind": "child_overflow",
                            "parent_id": node_id,
                            "parent_name": p_name,
                            "child_id": c_id,
                            "child_name": c_name,
                            "overflow_px": {
                                "right": round(max(0.0, over_r), 1),
                                "bottom": round(max(0.0, over_b), 1),
                                "left": round(max(0.0, over_l), 1),
                                "top": round(max(0.0, over_t), 1)
                            }
                        })

                    # Check 4: Unpadded Visual Box (text flush at 0px against a visibly filled/bordered container)
                    if depth > 0 and has_visible_box and c_type == "TEXT" and not child.get("absolute"):
                        if (cx - px) < 1.0 and (cy - py) < 1.0:
                            violations.append({
                                "screen": screen_name,
                                "kind": "unpadded_visual_box",
                                "parent_id": node_id,
                                "parent_name": p_name,
                                "child_id": c_id,
                                "child_name": c_name,
                                "detail": f"Teks `{c_name}` menempel (0px padding) ke tepi container berwarna/berborder `{p_name}`"
                            })

                    if not child.get("absolute"):
                        flow_children.append(child)

                # Check 3: Sibling Overlap inside Auto-Layout containers
                if p_layout and len(flow_children) > 1:
                    for i in range(len(flow_children)):
                        c1 = flow_children[i]
                        b1 = _validate_bounds(
                            c1.get("absoluteBounds"),
                            c1.get("id"),
                            c1.get("name", f"id:{c1.get('id')}")
                        )
                        x1, y1 = b1["x"], b1["y"]
                        r1, bot1 = x1 + b1["width"], y1 + b1["height"]
                        for j in range(i + 1, len(flow_children)):
                            c2 = flow_children[j]
                            b2 = _validate_bounds(
                                c2.get("absoluteBounds"),
                                c2.get("id"),
                                c2.get("name", f"id:{c2.get('id')}")
                            )
                            x2, y2 = b2["x"], b2["y"]
                            r2, bot2 = x2 + b2["width"], y2 + b2["height"]
                            ix = min(r1, r2) - max(x1, x2)
                            iy = min(bot1, bot2) - max(y1, y2)
                            if ix > tolerance and iy > tolerance:
                                violations.append({
                                    "screen": screen_name,
                                    "kind": "sibling_overlap",
                                    "parent_id": node_id,
                                    "parent_name": p_name,
                                    "child_a": c1.get("name"),
                                    "child_b": c2.get("name"),
                                    "overlap_px": {"x": round(ix, 1), "y": round(iy, 1)}
                                })

            # Separated child subtree traversal: executes for all container types (including GROUP and SECTION)
            for child in children:
                _audit_node(child, screen_name, depth + 1)

        audited_frames = 0
        try:
            for fid in target_ids:
                fetched_node_ids.add(fid)
                tree = self.execute("node.get", {
                    "id": fid,
                    "fields": audit_fields
                })
                if self.last_error is not None:
                    return _fail_audit(self.last_error)
                if not isinstance(tree, dict):
                    return _fail_audit(
                        f"Failed to fetch frame {fid} in verify_layout: expected dict, got {type(tree).__name__}"
                    )
                tree_id = tree.get("id")
                if not isinstance(tree_id, int) or isinstance(tree_id, bool) or tree_id != fid:
                    return _fail_audit(
                        f"Invalid frame response for target {fid} in verify_layout: mismatched or invalid id {tree_id!r}"
                    )
                _audit_node(tree, tree.get("name", f"Frame_{fid}"), depth=0)
                audited_frames += 1
        except _AuditAbort as abort_exc:
            return _fail_audit(str(abort_exc))

        if audited_frames == 0:
            return _fail_audit("No frames were audited in verify_layout")

        return {
            "ok": len(violations) == 0,
            "violation_count": len(violations),
            "violations": violations
        }

    def save_file(self, output_path: str) -> Dict[str, Any]:
        """Flushes pending batch commands and saves the document to a `.figcraft` file (Fitur #1)."""
        if self._batch_queue:
            self.flush(label="Pre-Save Flush")
        if not output_path.endswith(".figcraft"):
            output_path += ".figcraft"
        abs_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        res = self.execute("file.save", {
            "path": abs_path,
            "overwrite": True
        })
        return {"path": abs_path, "result": res}

    def export_page(self, output_path: str = "./preview.png", scale: float = 1) -> Dict[str, Any]:
        """Flushes pending batch, deselects all layers, and exports the full canvas to PNG."""
        if self._batch_queue:
            self.flush(label="Final Render Batch")
        abs_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        self.execute("select.none")
        res = self.execute("file.export", {
            "format": "png",
            "path": abs_path,
            "scale": scale
        })
        return res if isinstance(res, dict) else {}

    def export_frames(
        self,
        frame_refs: List[NodeRef],
        output_dir: str = "./exports",
        scale: float = 1
    ) -> List[Dict[str, Any]]:
        """Exports each top-level screen frame into its own individual PNG file (Fitur #4)."""
        if self._batch_queue:
            self.flush(label="Pre-Export Frames Flush")
        abs_dir = os.path.abspath(output_dir)
        os.makedirs(abs_dir, exist_ok=True)

        exported_files: List[Dict[str, Any]] = []
        for idx, ref in enumerate(frame_refs, start=1):
            fid = self.resolve_id(ref)
            if fid is None:
                continue
            info = self.execute("node.get", {"id": fid, "fields": ["name"]})
            raw_name = info.get("name", f"frame_{fid}") if isinstance(info, dict) else f"frame_{fid}"
            safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", raw_name).strip("_")
            file_path = os.path.join(abs_dir, f"{idx:02d}_{safe_name}.png")
            res = self.execute("file.export", {
                "ids": [fid],
                "format": "png",
                "path": file_path,
                "scale": scale
            })
            exported_files.append({
                "id": fid,
                "name": raw_name,
                "path": file_path,
                "bytes": res.get("bytes", 0) if isinstance(res, dict) else 0
            })
        return exported_files


fcclient = FigCraftClient
