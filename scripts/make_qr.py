"""
Make the slide QR code for the live demo link.

  .venv/bin/pip install segno==1.6.1        # one time; not needed by the server
  .venv/bin/python scripts/make_qr.py https://carebridge.onrender.com

Writes docs/qr-live-demo.png (for slides) and docs/qr-live-demo.svg (sharp at any size).
Scan it with a phone camera before the presentation to be sure it opens the right page.
"""

import sys
from pathlib import Path

import segno

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    if len(sys.argv) < 2 or not sys.argv[1].startswith("https://"):
        sys.exit("Usage: make_qr.py https://your-app.onrender.com  [output folder]")
    url = sys.argv[1].rstrip("/")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "docs"
    out.mkdir(parents=True, exist_ok=True)
    qr = segno.make(url, error="h")                 # high error correction: still scans from the back of a room
    qr.save(out / "qr-live-demo.png", scale=20, border=2, dark="#0f172a")
    qr.save(out / "qr-live-demo.svg", scale=20, border=2, dark="#0f172a")
    print(f"QR for {url} -> {out / 'qr-live-demo.png'} and .svg")


if __name__ == "__main__":
    main()
