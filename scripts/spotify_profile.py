#!/usr/bin/env python3
"""
GitHub Profile Spotify panels.

Reads these environment variables:
  SPOTIFY_CLIENT_ID
  SPOTIFY_CLIENT_SECRET
  SPOTIFY_REFRESH_TOKEN

Writes:
  assets/spotify-now-playing.svg
  assets/spotify-queue.svg
  assets/spotify-history.svg
  assets/spotify-top.svg
"""

from __future__ import annotations

import base64
import html
import json
import os
import sys
import urllib.parse
import urllib.request


API = "https://api.spotify.com/v1"
TOKEN_URL = "https://accounts.spotify.com/api/token"


def request_json(url: str, method: str = "GET", data: bytes | None = None, headers: dict[str, str] | None = None):
    req = urllib.request.Request(url, method=method, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except Exception as exc:
        return {"_error": str(exc)}


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> str | None:
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }).encode()
    result = request_json(
        TOKEN_URL,
        method="POST",
        data=body,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    return result.get("access_token")


def spotify_get(url: str, token: str):
    return request_json(url, headers={"Authorization": f"Bearer {token}"})


def esc(value) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def track_name(item):
    if not item:
        return "Unknown track"
    return item.get("name", "Unknown track")


def artists(item):
    return ", ".join(a.get("name", "") for a in (item or {}).get("artists", [])) or "Unknown artist"


def album(item):
    return (item or {}).get("album", {}).get("name", "") or ""


def spotify_url(item):
    return (item or {}).get("external_urls", {}).get("spotify", "")


def write_svg(path: str, title: str, rows: list[str], footer: str, accent: str = "#00E5FF", height: int = 230):
    safe_rows = rows[:10]
    line_h = 28
    body_h = max(110, 70 + len(safe_rows) * line_h)
    height = max(height, body_h + 55)
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 %d">' % height,
        '<defs><linearGradient id="a" x1="0" x2="1"><stop stop-color="%s"/><stop offset="1" stop-color="#8B5CF6"/></linearGradient></defs>' % accent,
        '<rect width="1000" height="%d" rx="18" fill="#070A12" stroke="#1F2A44"/>' % height,
        '<rect x="24" y="24" width="6" height="%d" rx="3" fill="url(#a)"/>' % (height - 48),
        '<g font-family="Consolas,monospace">',
        '<text x="55" y="58" fill="%s" font-size="18" font-weight="700">%s</text>' % (accent, esc(title)),
    ]
    y = 92
    for row in safe_rows:
        out.append('<text x="55" y="%d" fill="#F8FAFC" font-size="18">%s</text>' % (y, row))
        y += line_h
    out += [
        '<text x="55" y="%d" fill="#64748B" font-size="14">%s</text>' % (height - 24, esc(footer)),
        "</g></svg>",
    ]
    Path = os.path
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))


def main():
    cid = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
    secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
    refresh = os.environ.get("SPOTIFY_REFRESH_TOKEN", "").strip()

    paths = {
        "now": "assets/spotify-now-playing.svg",
        "queue": "assets/spotify-queue.svg",
        "history": "assets/spotify-history.svg",
        "top": "assets/spotify-top.svg",
    }

    if not all([cid, secret, refresh]):
        write_svg(paths["now"], "SPOTIFY // NOW PLAYING", ["Spotify credentials are not configured yet."], "Set SPOTIFY_CLIENT_ID / SECRET / REFRESH_TOKEN")
        write_svg(paths["queue"], "SPOTIFY // QUEUE", ["Queue panel is waiting for the Spotify integration."], "No secret values are written to the repo")
        write_svg(paths["history"], "SPOTIFY // RECENT HISTORY", ["Recent history will appear here after the first successful refresh."], "user-read-recently-played")
        write_svg(paths["top"], "SPOTIFY // TOP SIGNAL", ["Top artists/tracks will appear here after the first successful refresh."], "user-top-read")
        return

    token = refresh_access_token(cid, secret, refresh)
    if not token:
        write_svg(paths["now"], "SPOTIFY // NOW PLAYING", ["Token refresh failed."], "Check Spotify credentials and developer settings", "#FF5CF4")
        return

    current = spotify_get(f"{API}/me/player/currently-playing", token)
    item = current.get("item") if isinstance(current, dict) else None
    playing = bool(current.get("is_playing")) if isinstance(current, dict) else False

    if item:
        status = "▶" if playing else "Ⅱ"
        write_svg(
            paths["now"],
            "SPOTIFY // NOW PLAYING",
            [
                f'{status}  {esc(track_name(item))}',
                f'by {esc(artists(item))}',
                f'album: {esc(album(item))}',
            ],
            "Live playback panel • Spotify Web API",
            "#00E5FF",
            230,
        )
    else:
        write_svg(paths["now"], "SPOTIFY // NOW PLAYING", ["Nothing is playing right now."], "Spotify did not return an active track", "#60A5FA")

    queue = spotify_get(f"{API}/me/player/queue", token)
    qrows = []
    for qitem in (queue.get("queue") or [])[:6]:
        qrows.append(f'→ {esc(track_name(qitem))} — {esc(artists(qitem))}')
    if not qrows:
        qrows = ["Queue is empty or unavailable."]
    write_svg(paths["queue"], "SPOTIFY // QUEUE", qrows, "Next tracks returned by the current playback queue", "#8B5CF6", 300)

    history = spotify_get(f"{API}/me/player/recently-played?limit=6", token)
    hrows = []
    for item in (history.get("items") or [])[:6]:
        tr = item.get("track") or {}
        stamp = (item.get("played_at") or "").replace("T", " ").replace("Z", "")
        hrows.append(f'{esc(track_name(tr))} — {esc(artists(tr))}  [{esc(stamp[:16])}]')
    if not hrows:
        hrows = ["No recently played tracks returned."]
    write_svg(paths["history"], "SPOTIFY // RECENT HISTORY", hrows, "Last 6 recently played tracks", "#60A5FA", 315)

    top = spotify_get(f"{API}/me/top/artists?limit=5&time_range=short_term", token)
    trows = []
    for idx, artist in enumerate((top.get("items") or [])[:5], 1):
        trows.append(f'{idx}. {esc(artist.get("name", "Unknown artist"))}')
    if not trows:
        # Fallback to top tracks if the artist endpoint is unavailable.
        top_tracks = spotify_get(f"{API}/me/top/tracks?limit=5&time_range=short_term", token)
        for idx, tr in enumerate((top_tracks.get("items") or [])[:5], 1):
            trows.append(f'{idx}. {esc(track_name(tr))} — {esc(artists(tr))}')
    if not trows:
        trows = ["Top data is not available for this Spotify app/account."]
    write_svg(paths["top"], "SPOTIFY // TOP SIGNAL", trows, "Short-term listening signal", "#00E5FF", 280)


if __name__ == "__main__":
    main()
