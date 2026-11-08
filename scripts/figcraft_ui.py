"""
figcraft_ui.py (v3.0) - Production Batch UI Automation Library for FigCraft.
Communicates with FigCraft Engine over TCP JSON-RPC (engine.execute).
"""

import socket
import json
import os
import time
import re
from typing import Union, List, Dict, Optional, Any

NodeRef = Union[int, str, Dict[str, str]]


class FigCraftError(RuntimeError):
    """Raised when a FigCraft RPC command or batch step fails in strict mode."""
    pass


class FigCraftClient:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7979,
        auto_batch: bool = True,
        strict: bool = True
    ):
        self.host = host
        self.port = port
        self.auto_batch = auto_batch
        self.strict = strict
        self.sock: Optional[socket.socket] = None
        self._req_id = 0
        self._step_counter = 0
        self._buffer = ""
        self._batch_queue: List[Dict[str, Any]] = []
        self._resolved_refs: Dict[str, int] = {}
        self.total_rpc_ms: float = 0.0
        self.last_flush_ms: float = 0.0
        self.connect()

    def connect(self):
        """Connects strictly to the configured host:port (no silent port switching)."""
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(20.0)
            s.connect((self.host, self.port))
            self.sock = s
        except Exception as e:
            raise ConnectionError(
                f"[figcraft_ui] Gagal terhubung ke FigCraft di {self.host}:{self.port}. "
                f"Pastikan aplikasi FigCraft berjalan dengan `--control {self.port}`. Detail: {e}"
            ) from e

    def close(self):
        """Flushes pending batch commands and closes the TCP socket."""
        if self._batch_queue:
            self.flush()
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def execute(self, command: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Executes a single engine command immediately over TCP JSON-RPC and measures latency."""
        if params is None:
            params = {}
        self._req_id += 1
        req = {
            "jsonrpc": "2.0",
            "id": self._req_id,
            "method": "engine.execute",
            "params": {
                "command": command,
                "params": params
            }
        }
        payload = (json.dumps(req) + "\n").encode("utf-8")

        t0 = time.perf_counter()
        try:
            self.sock.sendall(payload)
        except (socket.error, BrokenPipeError, AttributeError):
            self.connect()
            self.sock.sendall(payload)

        buf = self._buffer
        while True:
            if "\n" in buf:
                line, rest = buf.split("\n", 1)
                self._buffer = rest
                if line.strip():
                    elapsed_ms = (time.perf_counter() - t0) * 1000.0
                    self.total_rpc_ms += elapsed_ms
                    resp = json.loads(line)
                    if not resp.get("ok", False):
                        err_msg = resp.get("error", "Unknown error")
                        if self.strict:
                            raise FigCraftError(f"Command `{command}` gagal: {err_msg} | Params: {params}")
                        print(f"[figcraft_ui Warning] `{command}` failed: {err_msg}")
                    return resp.get("result", {})
            try:
                chunk = self.sock.recv(65536).decode("utf-8")
                if not chunk:
                    break
                buf += chunk
            except socket.timeout as e:
                if self.strict:
                    raise FigCraftError(f"Timeout saat menunggu respons `{command}`") from e
                break

        if buf.strip():
            resp = json.loads(buf)
            self._buffer = ""
            if not resp.get("ok", False) and self.strict:
                raise FigCraftError(f"Command `{command}` gagal: {resp.get('error')}")
            return resp.get("result", {})
        return {}

    def _resolve_param_refs(self, obj: Any) -> Any:
        """Recursively substitutes already-flushed `$ref` dicts with their integer IDs."""
        if isinstance(obj, dict):
            if "$ref" in obj and len(obj) == 1:
                ref_key = obj["$ref"]
                if ref_key in self._resolved_refs:
                    return self._resolved_refs[ref_key]
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
            return res.get("id") if isinstance(res, dict) else res

    def flush(self, label: str = "Fast UI Batch") -> List[Dict[str, Any]]:
        """Flushes all queued commands in one atomic `command.batch` call."""
        if not self._batch_queue:
            return []
        commands = self._batch_queue
        self._batch_queue = []
        t0 = time.perf_counter()
        results = self.execute("command.batch", {
            "label": label,
            "onError": "abort" if self.strict else "continue",
            "commands": commands
        })
        self.last_flush_ms = (time.perf_counter() - t0) * 1000.0

        if isinstance(results, list):
            for cmd_item, res_item in zip(commands, results):
                as_name = cmd_item.get("as")
                if as_name and isinstance(res_item, dict):
                    inner = res_item.get("result", res_item) if "ok" in res_item else res_item
                    if isinstance(inner, dict) and "id" in inner:
                        self._resolved_refs[as_name] = inner["id"]
                    elif isinstance(res_item, dict) and not res_item.get("ok", True):
                        err = res_item.get("error", "Unknown batch step error")
                        if self.strict:
                            raise FigCraftError(f"Batch step `{as_name}` ({cmd_item.get('command')}) gagal: {err}")
                        print(f"[figcraft_ui Batch Error] Step `{as_name}`: {err}")
        return results if isinstance(results, list) else []

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
            "select": False,
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
            "select": False,
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
            "select": False,
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
            "select": False,
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
            "select": False,
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
            "select": False,
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
        if self._batch_queue:
            self.flush(label="Pre-Verify Flush")

        target_ids: List[int] = []
        if frame_refs:
            for ref in frame_refs:
                rid = self.resolve_id(ref)
                if rid is not None:
                    target_ids.append(rid)
        else:
            found = self.execute("node.find", {"type": "FRAME", "limit": 500})
            if isinstance(found, dict) and "ids" in found:
                target_ids = found["ids"][:20]

        violations: List[Dict[str, Any]] = []

        audit_fields = [
            "id", "name", "type", "absoluteBounds", "clip",
            "absolute", "layout", "fills", "strokes", "strokeWeight", "children"
        ]

        def _audit_node(node: Dict[str, Any], screen_name: str, depth: int = 0):
            p_bounds = node.get("absoluteBounds")
            p_name = node.get("name", f"id:{node.get('id')}")
            p_type = node.get("type", "")
            children = node.get("children", [])
            if not children and node.get("childCount", 0) > 0 and node.get("id") is not None:
                fetched = self.execute("node.get", {"id": node["id"], "fields": audit_fields})
                if isinstance(fetched, dict):
                    children = fetched.get("children", [])

            if p_bounds:
                pw = float(p_bounds.get("width", 0))
                ph = float(p_bounds.get("height", 0))
                if pw <= 0 or ph <= 0:
                    violations.append({
                        "screen": screen_name,
                        "kind": "zero_size",
                        "node_id": node.get("id"),
                        "node_name": p_name,
                        "detail": f"Layer memiliki ukuran tidak valid ({pw}x{ph})"
                    })

            if p_bounds and children and p_type in ("FRAME", "COMPONENT", "INSTANCE"):
                px = float(p_bounds["x"])
                py = float(p_bounds["y"])
                pr = px + float(p_bounds["width"])
                pb = py + float(p_bounds["height"])

                has_visible_box = bool(node.get("fills")) or (
                    bool(node.get("strokes")) and float(node.get("strokeWeight") or 0) > 0
                )

                flow_children: List[Dict[str, Any]] = []

                for child in children:
                    c_bounds = child.get("absoluteBounds")
                    c_name = child.get("name", f"id:{child.get('id')}")
                    c_type = child.get("type", "")
                    if c_bounds:
                        cx = float(c_bounds["x"])
                        cy = float(c_bounds["y"])
                        cr = cx + float(c_bounds["width"])
                        cb = cy + float(c_bounds["height"])

                        over_r = cr - pr
                        over_b = cb - pb
                        over_l = px - cx
                        over_t = py - cy

                        if max(over_r, over_b, over_l, over_t) > tolerance:
                            violations.append({
                                "screen": screen_name,
                                "kind": "child_overflow",
                                "parent_id": node.get("id"),
                                "parent_name": p_name,
                                "child_id": child.get("id"),
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
                                    "parent_id": node.get("id"),
                                    "parent_name": p_name,
                                    "child_id": child.get("id"),
                                    "child_name": c_name,
                                    "detail": f"Teks `{c_name}` menempel (0px padding) ke tepi container berwarna/berborder `{p_name}`"
                                })

                        if not child.get("absolute"):
                            flow_children.append(child)

                    _audit_node(child, screen_name, depth + 1)

                # Check 3: Sibling Overlap inside Auto-Layout containers
                if node.get("layout") and len(flow_children) > 1:
                    for i in range(len(flow_children)):
                        b1 = flow_children[i].get("absoluteBounds")
                        if not b1:
                            continue
                        x1, y1 = float(b1["x"]), float(b1["y"])
                        r1, bot1 = x1 + float(b1["width"]), y1 + float(b1["height"])
                        for j in range(i + 1, len(flow_children)):
                            b2 = flow_children[j].get("absoluteBounds")
                            if not b2:
                                continue
                            x2, y2 = float(b2["x"]), float(b2["y"])
                            r2, bot2 = x2 + float(b2["width"]), y2 + float(b2["height"])
                            ix = min(r1, r2) - max(x1, x2)
                            iy = min(bot1, bot2) - max(y1, y2)
                            if ix > tolerance and iy > tolerance:
                                violations.append({
                                    "screen": screen_name,
                                    "kind": "sibling_overlap",
                                    "parent_id": node.get("id"),
                                    "parent_name": p_name,
                                    "child_a": flow_children[i].get("name"),
                                    "child_b": flow_children[j].get("name"),
                                    "overlap_px": {"x": round(ix, 1), "y": round(iy, 1)}
                                })

        for fid in target_ids:
            tree = self.execute("node.get", {
                "id": fid,
                "fields": [
                    "id", "name", "type", "absoluteBounds", "clip",
                    "absolute", "layout", "fills", "strokes", "strokeWeight", "children"
                ]
            })
            if isinstance(tree, dict) and "id" in tree:
                _audit_node(tree, tree.get("name", f"Frame_{fid}"), depth=0)

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
