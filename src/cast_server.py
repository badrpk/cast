from __future__ import annotations
"""Cast v3 — Chromecast parity gaps + Pro undercut billing."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from http_util import JsonAPI, serve, uid, iso
import payments as pay
import auth as authmod

DEVICES = [
    {"id": "tv1", "name": "Living Room TV", "protocol": "chromecast", "ip": "192.168.1.20", "online": True, "model": "Chromecast HD"},
    {"id": "tv2", "name": "Bedroom Fire", "protocol": "dlna", "ip": "192.168.1.21", "online": True, "model": "Fire TV"},
    {"id": "tv3", "name": "Office Projector", "protocol": "miracast", "ip": "192.168.1.22", "online": False, "model": "Epson"},
    {"id": "tv4", "name": "Mac AirPlay", "protocol": "airplay", "ip": "192.168.1.23", "online": True, "model": "Apple TV"},
]
SESSIONS, GROUPS, QUEUES = {}, {}, {}

class H(JsonAPI):
    def do_GET(self):
        _path_early = (self.path.split("?")[0].rstrip("/") or "/")
        if _path_early.startswith("/auth"):
            hdrs = {k: v for k, v in self.headers.items()}
            code, body = authmod.handle_auth_request("GET", _path_early, {}, hdrs, product="cast")
            return self._send(code, body)
        path, q = self.parse()
        if path in ("/", "/health"):
            return self._send(200, {"ok": True, "service": "cast", "version": "3.0.0",
                "gaps_closed": ["multi_room_groups", "queue", "pro_billing", "stripe", "signup", "login", "otp", "oauth_google", "oauth_facebook"]})
        if path == "/capabilities":
            return self._send(200, {"ok": True, "competitor": "Google Cast / AirPlay",
                "features": ["discovery","session","media","queue","groups","mirror","billing","stripe"]})
        if path == "/pricing": return self._send(200, {"ok": True, **pay.pricing_for("cast")})
        if path == "/payments/rails": return self._send(200, {"ok": True, "rails": pay.list_rails()})
        if path == "/gap-analysis":
            return self._send(200, {"ok": True, "added": ["multi-room groups", "queue", "Cast Pro $1.99 vs ~$4.99"]})
        if path == "/devices":
            proto = (q.get("protocol") or [None])[0]
            rows = [d for d in DEVICES if not proto or d["protocol"]==proto]
            if (q.get("online") or [None])[0]=="1": rows = [d for d in rows if d["online"]]
            return self._send(200, {"ok": True, "devices": rows})
        if path == "/sessions": return self._send(200, {"ok": True, "sessions": list(SESSIONS.values())})
        if path == "/groups": return self._send(200, {"ok": True, "groups": list(GROUPS.values())})
        if path.startswith("/sessions/"):
            s = SESSIONS.get(path.split("/")[2])
            return self._send(200 if s else 404, {"ok": bool(s), "session": s})
        self._send(404, {"ok": False})

    def do_POST(self):
        _path_early = (self.path.split("?")[0].rstrip("/") or "/")
        if _path_early.startswith("/auth"):
            hdrs = {k: v for k, v in self.headers.items()}
            body = self._read_json() if hasattr(self, "_read_json") else self._read()
            code, resp = authmod.handle_auth_request("POST", _path_early, body if isinstance(body, dict) else {}, hdrs, product="cast")
            return self._send(code, resp)
        path, _ = self.parse()
        body = self._read_json()
        if path == "/sessions":
            dev = next((d for d in DEVICES if d["id"]==body.get("device_id")), None)
            if not dev: return self._send(400, {"ok": False, "error": "unknown_device"})
            if not dev["online"]: return self._send(400, {"ok": False, "error": "device_offline"})
            sid = uid("sess")
            SESSIONS[sid] = {"id": sid, "device": dev, "state": "idle", "media": None, "position_sec": 0,
                             "volume": 0.5, "muted": False, "queue": [], "created_at": iso()}
            return self._send(201, {"ok": True, "session": SESSIONS[sid]})
        if path == "/groups":
            gid = uid("grp")
            GROUPS[gid] = {"id": gid, "name": body.get("name") or "Multi-room", "device_ids": body.get("device_ids") or [], "at": iso()}
            return self._send(201, {"ok": True, "group": GROUPS[gid], "requires_pro": True})
        if path == "/billing/pro":
            inv = pay.create_invoice("cast", 0, "USD", method=body.get("method") or "stripe", sku=body.get("sku") or "pro", customer=body.get("customer") or "user")
            return self._send(201, {"ok": True, "invoice": inv})
        if path.startswith("/sessions/"):
            parts = path.split("/")
            sid = parts[2]; s = SESSIONS.get(sid)
            if not s: return self._send(404, {"ok": False})
            action = parts[3] if len(parts)>3 else ""
            if action == "load":
                s["media"] = {"url": body.get("url") or "", "title": body.get("title") or "Media",
                              "content_type": body.get("content_type") or "video/mp4", "duration_sec": int(body.get("duration_sec") or 0)}
                s["state"] = "playing"; s["position_sec"] = 0
            elif action == "queue":
                s.setdefault("queue", []).append({"url": body.get("url"), "title": body.get("title") or "Queued"})
            elif action == "play": s["state"] = "playing"
            elif action == "pause": s["state"] = "paused"
            elif action == "stop": s["state"] = "idle"; s["media"] = None
            elif action == "seek": s["position_sec"] = int(body.get("position_sec") or 0)
            elif action == "volume":
                s["volume"] = max(0.0, min(1.0, float(body.get("level") or 0.5)))
                s["muted"] = bool(body.get("muted", s["muted"]))
            elif action == "mirror":
                s["state"] = "mirroring"
                s["media"] = {"type": "screen", "title": "Screen Mirror", "quality": body.get("quality") or "720p"}
            else:
                return self._send(400, {"ok": False, "error": "unknown_action"})
            s["updated_at"] = iso()
            return self._send(200, {"ok": True, "session": s})
        if path == "/discover":
            for d in DEVICES:
                if d["id"] != "tv3": d["online"] = True
            return self._send(200, {"ok": True, "devices": DEVICES})
        if path == "/payments/create":
            inv = pay.create_invoice("cast", float(body.get("amount") or 0), body.get("currency") or "USD",
                method=body.get("method") or "stripe", sku=body.get("sku"))
            return self._send(201, {"ok": True, "invoice": inv})
        self._send(404, {"ok": False})

def main():
    serve(H, port=int(__import__("os").environ.get("PORT", "8765")), name="Cast v3")
if __name__ == "__main__":
    main()
