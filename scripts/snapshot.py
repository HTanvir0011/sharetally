"""Render key screens to PNG for the README, concept note and deck.

Usage:  python scripts/snapshot.py [path-to-msedge-or-chrome]
Renders pages through the app's test client (fresh synthetic database), saves them as
static HTML in .snapshots/, then captures PNGs into docs/img/ with a headless browser.
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
WORK = ROOT / ".snapshots"
IMG = ROOT / "docs" / "img"
BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"]


def main() -> None:
    WORK.mkdir(exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    os.environ["SHARETALLY_DB"] = str(Path(tempfile.mkdtemp()) / "snap.db")
    os.environ["SHARETALLY_PBKDF2_ITERATIONS"] = "1000"
    from fastapi.testclient import TestClient

    from sharetally.web import app

    static_url = (ROOT / "sharetally" / "static").as_uri() + "/"
    pages: list[tuple[str, str, int, int]] = []

    def save(name: str, html: str, width: int, height: int) -> None:
        html = re.sub(r'(href|src)="/static/', rf'\1="{static_url}', html)
        html = html.replace('<html lang="en">', '<html lang="en" data-theme="light">', 1)
        (WORK / f"{name}.html").write_text(html, encoding="utf-8")
        pages.append((name, (WORK / f"{name}.html").as_uri(), width, height))

    def login(client: TestClient, user: str, password: str) -> str:
        token = re.search(r'name="login_csrf" value="([^"]+)"', client.get("/login").text).group(1)
        client.post("/login", data={"username": user, "password": password, "login_csrf": token})
        return re.search(r'name="csrf-token" content="([^"]+)"', client.get("/dashboard").text).group(1)

    with TestClient(app) as client:
        save("login", client.get("/login").text, 1280, 760)
        login(client, "reviewer.demo", "review-demo-2026")
        save("queue", client.get("/cases").text, 1280, 900)
        save("case-conflict", client.get("/cases/MC-0002").text, 1280, 1180)
        save("case-incomplete", client.get("/cases/MC-0009").text, 1280, 900)
        save("plot-double-sale", client.get("/plots/M901-BS-1201").text, 1280, 1400)
        save("evaluation", client.get("/evaluation").text, 1280, 1100)
        save("case-mobile", client.get("/cases/MC-0002").text, 390, 1500)
    with TestClient(app) as client:
        csrf = login(client, "clerk.demo", "clerk-demo-2026")
        form = {"csrf_token": csrf, "deed_no": "2026/0850", "deed_type": "sale", "execution_date": "2026-09-20",
                "registration_date": "2026-09-20", "plot_id": "M901-BS-1201", "plot_ref": "", "seller_id": "P-0004",
                "buyer_id": "", "new_buyer_en": "Ruma Kalponik", "new_buyer_bn": "রুমা কাল্পনিক",
                "quantity": "৫ শতাংশ", "action": "check"}
        save("intake-check", client.post("/intake", data=form).text, 1280, 1300)

    browser = sys.argv[1] if len(sys.argv) > 1 else next((b for b in BROWSERS if Path(b).exists()), None)
    if not browser:
        print("No Edge/Chrome found; HTML snapshots are in", WORK)
        return
    profile = Path(tempfile.mkdtemp())
    for name, url, width, height in pages:
        out = IMG / f"{name}.png"
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={profile}",
                        f"--window-size={width},{height}", "--force-device-scale-factor=1.5",
                        "--virtual-time-budget=4000", f"--screenshot={out}", url],
                       check=False, capture_output=True, timeout=90)
        print(("ok " if out.exists() else "FAILED ") + str(out.relative_to(ROOT)))


if __name__ == "__main__":
    main()
