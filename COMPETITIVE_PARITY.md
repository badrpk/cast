# Cast — competitive parity

**Target:** Google Cast / Apple AirPlay control planes

| Feature | API |
|---------|-----|
| Device discovery | `GET /devices`, `POST /discover` |
| Multi-protocol | chromecast, dlna, miracast, airplay, webrtc |
| Session | `POST /sessions` |
| Load media | `POST /sessions/{id}/load` |
| Play/pause/stop/seek/volume | matching actions |
| Screen mirror | `POST /sessions/{id}/mirror` |
