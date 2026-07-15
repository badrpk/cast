from __future__ import annotations
"""Cast control plane — parity with Chromecast / local casting controllers."""
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parent))

from http_util import JsonAPI, serve, uid, iso

DEVICES = [
    {"id": "tv1", "name": "Living Room TV", "protocol": "chromecast", "ip": "192.168.1.20", "online": True, "model": "Chromecast HD"},
    {"id": "tv2", "name": "Bedroom Fire", "protocol": "dlna", "ip": "192.168.1.21", "online": True, "model": "Fire TV"},
    {"id": "tv3", "name": "Office Projector", "protocol": "miracast", "ip": "192.168.1.22", "online": False, "model": "Epson"},
    {"id": "tv4", "name": "Mac AirPlay", "protocol": "airplay", "ip": "192.168.1.23", "online": True, "model": "Apple TV"},
]
SESSIONS: dict[str, dict] = {}

class H(JsonAPI):
    def do_GET(self):
        path, q = self.parse()
        if path in ("/", "/health"):
            return self._send(200, {"ok": True, "service": "cast", "version": "2.0.0",
                                    "parity_target": "Chromecast / AirPlay / DLNA controllers",
                                    "protocols": ["chromecast", "dlna", "miracast", "airplay", "webrtc"]})
        if path == "/capabilities":
            return self._send(200, {"ok": True, "competitor": "Google Cast / Apple AirPlay",
                                    "features": ["device_discovery", "session", "media_load", "play_pause",
                                                 "seek", "volume", "screen_mirror", "multi_protocol"]})
        if path == "/devices":
            proto = (q.get("protocol") or [None])[0]
            rows = [d for d in DEVICES if not proto or d["protocol"] == proto]
            online = (q.get("online") or [None])[0]
            if online == "1":
                rows = [d for d in rows if d["online"]]
            return self._send(200, {"ok": True, "devices": rows})
        if path == "/sessions":
            return self._send(200, {"ok": True, "sessions": list(SESSIONS.values())})
        if path.startswith("/sessions/"):
            s = SESSIONS.get(path.split("/")[2])
            return self._send(200 if s else 404, {"ok": bool(s), "session": s} if s else {"ok": False})
        self._send(404, {"ok": False})

    def do_POST(self):
        path, _ = self.parse()
        body = self._read_json()
        if path == "/sessions":
            dev = next((d for d in DEVICES if d["id"] == body.get("device_id")), None)
            if not dev:
                return self._send(400, {"ok": False, "error": "unknown_device"})
            if not dev["online"]:
                return self._send(400, {"ok": False, "error": "device_offline"})
            sid = uid("sess")
            SESSIONS[sid] = {
                "id": sid, "device": dev, "state": "idle", "media": None,
                "position_sec": 0, "volume": 0.5, "muted": False, "created_at": iso(),
            }
            return self._send(201, {"ok": True, "session": SESSIONS[sid]})
        if path.startswith("/sessions/"):
            parts = path.split("/")
            sid = parts[2]
            s = SESSIONS.get(sid)
            if not s:
                return self._send(404, {"ok": False})
            action = parts[3] if len(parts) > 3 else ""
            if action == "load":
                s["media"] = {"url": body.get("url") or "", "title": body.get("title") or "Media",
                              "content_type": body.get("content_type") or "video/mp4", "duration_sec": int(body.get("duration_sec") or 0)}
                s["state"] = "playing"
                s["position_sec"] = 0
            elif action == "play":
                s["state"] = "playing"
            elif action == "pause":
                s["state"] = "paused"
            elif action == "stop":
                s["state"] = "idle"; s["media"] = None; s["position_sec"] = 0
            elif action == "seek":
                s["position_sec"] = int(body.get("position_sec") or 0)
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
        if path.startswith("/sessions/") is False and path == "/discover":
            # simulate rediscovery
            for d in DEVICES:
                if d["id"] != "tv3":
                    d["online"] = True
            return self._send(200, {"ok": True, "devices": DEVICES})
        self._send(404, {"ok": False})

def main():
    serve(H, port=int(__import__("os").environ.get("PORT", "8765")), name="Cast v2 (Chromecast parity)")

if __name__ == "__main__":
    main()
