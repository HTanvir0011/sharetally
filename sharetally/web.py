"""ShareTally web application: server-rendered pages plus a small JSON API."""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import sqlite3
from contextlib import asynccontextmanager
from datetime import date
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import ai, audit, db, explain, security, synthetic
from .config import Settings
from .engine.ledger import ENGINE_VERSION, LEVEL_RANK, Ledger, Transfer, status_of
from .engine.units import QuantityError, fmt_dec, fmt_share, normalize, parse_quantity, to_bn_digits
from .evaluation import evaluate
from .repository import crosswalk_candidates, deed_ref, get_as_of, ledger_for, people, plot_label

PKG = Path(__file__).resolve().parent
COOKIE = "st_session"
LOGIN_COOKIE = "st_login_csrf"
OFFICE = synthetic.OFFICE
FICTIONAL_MARKERS = [m for pair in synthetic.MARKERS for m in pair] + ["Demo", "ডেমো"]
DECISIONS = {
    "hold_notice": ("Hold — issue notice to parties", "স্থগিত — পক্ষগণকে নোটিশ"),
    "field_inquiry": ("Request field inquiry / certified copies", "মাঠ তদন্ত / সার্টিফাইড কপি চাওয়া"),
    "explained": ("Finding explained by evidence — continue", "প্রমাণে ব্যাখ্যা পাওয়া গেছে — অগ্রসর"),
    "proceed": ("No conflict — continue normal process", "দ্বন্দ্ব নেই — স্বাভাবিক প্রক্রিয়া"),
}
STATUS_CLASS = {"CONFLICT": "conflict", "INCOMPLETE": "incomplete", "ATTENTION": "attention",
                "NO_CONFLICT": "clear"}
STATUS_ORDER = {"CONFLICT": 0, "INCOMPLETE": 1, "ATTENTION": 2, "NO_CONFLICT": 3}

settings = Settings()
templates = Jinja2Templates(directory=str(PKG / "templates"))


def _asset_version() -> str:
    digest = hashlib.sha256()
    for name in ("css/app.css", "js/app.js"):
        digest.update((PKG / "static" / name).read_bytes())
    return digest.hexdigest()[:10]


ASSET_VERSION = _asset_version()


# ---------------------------------------------------------------- setup


def open_db() -> sqlite3.Connection:
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = db.connect(settings.db_path)
    return conn


def bootstrap() -> None:
    conn = open_db()
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        db.init_schema(conn)
        if not db.is_seeded(conn):
            db.seed(conn, synthetic.build_dataset())
            audit.append(conn, "system", "system", "dataset_seeded", "database",
                         {"generator": "sharetally.synthetic", "seed": synthetic.SEED})
        security.ensure_users(conn, settings.demo_users, settings.pbkdf2_iterations)
    finally:
        conn.close()


@lru_cache(maxsize=1)
def pristine_evaluation() -> dict:
    """Evaluate on a fresh copy of the synthetic data so live demo edits never change the score."""
    conn = db.connect(":memory:")
    db.init_schema(conn)
    db.seed(conn, synthetic.build_dataset())
    result = evaluate(conn)
    conn.close()
    return result


@asynccontextmanager
async def lifespan(_app: FastAPI):
    bootstrap()
    yield


app = FastAPI(title="ShareTally API", version=ENGINE_VERSION, lifespan=lifespan, docs_url=None, redoc_url=None,
              openapi_url="/api/openapi.json")
app.mount("/static", StaticFiles(directory=str(PKG / "static")), name="static")

CSP = ("default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
       "font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; "
       "frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = CSP
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if not request.url.path.startswith("/static"):
        response.headers["Cache-Control"] = "no-store"
    if settings.secure_cookies:
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response


# ---------------------------------------------------------------- auth helpers


class LoginRequired(Exception):
    pass


class Forbidden(Exception):
    pass


class BadRequest(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def is_api(request: Request) -> bool:
    return request.url.path.startswith("/api/")


@app.exception_handler(LoginRequired)
async def _login_required(request: Request, _exc: LoginRequired):
    if is_api(request):
        return JSONResponse({"error": "authentication required"}, status_code=401)
    return RedirectResponse(f"/login?next={quote(request.url.path)}", status_code=303)


@app.exception_handler(Forbidden)
async def _forbidden(request: Request, _exc: Forbidden):
    if is_api(request):
        return JSONResponse({"error": "forbidden for this role"}, status_code=403)
    return render(request, "error.html", {"code": 403, "message": "Your role cannot open this page."}, status=403)


@app.exception_handler(BadRequest)
async def _bad_request(request: Request, exc: BadRequest):
    if is_api(request):
        return JSONResponse({"error": exc.message}, status_code=400)
    return render(request, "error.html", {"code": 400, "message": exc.message}, status=400)


@app.exception_handler(404)
async def _not_found(request: Request, _exc):
    if is_api(request):
        return JSONResponse({"error": "not found"}, status_code=404)
    return render(request, "error.html", {"code": 404, "message": "Not found."}, status=404)


def current_user(request: Request, conn: sqlite3.Connection) -> sqlite3.Row | None:
    return security.load_session(conn, request.cookies.get(COOKIE))


def require(request: Request, conn: sqlite3.Connection, *roles: str) -> sqlite3.Row:
    user = current_user(request, conn)
    if user is None:
        raise LoginRequired()
    if roles and user["role"] not in roles:
        raise Forbidden()
    request.state.user = user
    return user


def check_csrf(user: sqlite3.Row, supplied: str | None) -> None:
    if not security.csrf_ok(user["csrf"], supplied):
        raise Forbidden()


def render(request: Request, name: str, ctx: dict | None = None, status: int = 200) -> HTMLResponse:
    user = getattr(request.state, "user", None)
    base = {"user": user, "as_of": getattr(request.state, "as_of", None), "status_class": STATUS_CLASS,
            "explain": explain, "bn": to_bn_digits, "engine_version": ENGINE_VERSION, "asset_v": ASSET_VERSION}
    return templates.TemplateResponse(request, name, {**base, **(ctx or {})}, status_code=status)


def as_of_for(conn: sqlite3.Connection) -> date:
    return date.fromisoformat(settings.as_of) if settings.as_of else get_as_of(conn)


class Page:
    """Per-request database handle plus the demo clock."""

    def __init__(self, request: Request):
        self.conn = open_db()
        self.request = request
        self.as_of = as_of_for(self.conn)
        request.state.as_of = self.as_of

    def __enter__(self) -> "Page":
        return self

    def __exit__(self, *exc) -> None:
        self.conn.close()


# ---------------------------------------------------------------- view models


def finding_view(f, names: dict) -> dict:
    return {
        "code": f.code, "level": f.level, "proposed": f.proposed,
        "title_en": explain.title(f.code, "en"), "title_bn": explain.title(f.code, "bn"),
        "text_en": explain.describe(f, names, "en"), "text_bn": explain.describe(f, names, "bn"),
        "action_en": explain.action(f.code, "en"), "action_bn": explain.action(f.code, "bn"),
        "evidence": f.evidence,
    }


def sorted_findings(findings) -> list:
    return sorted(findings, key=lambda f: (-LEVEL_RANK[f.level], f.code))


def strip_view(balances: dict[str, Fraction], overflow: Fraction, names: dict, order: list[str]) -> dict:
    """Segments for the SVG share strip (viewBox width 1000). Colours follow ``order`` so a
    person keeps the same colour in every strip."""
    positive = [(p, balances[p]) for p in order if balances.get(p, 0) > 0]
    total = sum((s for _, s in positive), Fraction(0))
    span = max(Fraction(1), total + overflow)
    scale = Fraction(1000) / span
    segs, x = [], Fraction(0)
    for pid, share in positive:
        w = share * scale
        segs.append({"x": float(x), "w": float(w), "cls": f"seg-{order.index(pid) % 8}",
                     "label": names.get(pid, {}).get("en", pid), "pct": fmt_dec(share * 100, 1)})
        x += w
    whole = float(scale)  # x position where 100% of the plot ends
    over = {"x": float(x), "w": float(overflow * scale)} if overflow > 0 else None
    return {"segments": segs, "whole": whole, "overflow": over, "unallocated": float(max(Fraction(0), 1 - total) * scale)}


def row_view(r, names: dict, ledger: Ledger) -> dict:
    n = lambda pid: names.get(pid, {}).get("en", pid)  # noqa: E731
    s = r.summary
    if r.kind == "baseline":
        text = f"Recorded holder {n(s['person'])}: {s['raw']} = {fmt_share(s['share'])}"
    elif r.kind == "pre_record":
        text = f"Before the record date (already reflected): {n(s['seller'])} → {n(s['buyer'])}, {s['raw']}"
    elif r.kind == "inheritance":
        if r.applied == "applied":
            heirs = ", ".join(f"{n(p)} {fr.numerator}/{fr.denominator}" for p, fr in s["heirs"])
            text = f"Inheritance from {n(s['deceased'])}: {heirs}"
        else:
            text = f"Inheritance from {n(s['deceased'])} — not applied"
    elif r.kind == "transfer":
        ref = f" (deed describes it as {s['plot_ref']})" if s.get("plot_ref") else ""
        text = f"{s['deed_type'].title()}: {n(s['seller'])} → {n(s['buyer'])}, {s['raw']}{ref}"
        if s.get("rounding_note"):
            text += f" — within rounding of the stated figure ({s['rounding_note']} decimal)"
    else:
        text = f"Mutation application ({s['status']}): {n(s['from'])} → {n(s['applicant'])}, {s['raw']}; cites {s['cited']}"
    balances = []
    if ledger.area_dec is not None:
        balances = [f"{n(p)}: {fmt_dec(v * ledger.area_dec)}" for p, v in r.balances_after.items()]
    return {"date": r.date.isoformat(), "kind": r.kind, "ref": r.ref, "source_id": r.source_id, "text": text,
            "applied": r.applied, "balances": balances, "codes": r.codes, "proposed": r.proposed}


def ledger_view(conn: sqlite3.Connection, ledger: Ledger, names: dict) -> dict:
    area = ledger.area_dec
    holders = sorted(set(ledger.baseline) | {p for p, v in ledger.balances.items() if v != 0})
    overflow = sum((Fraction(f.facts["shortfall_dec"]) / area for f in ledger.findings
                    if f.code == "OVER_TRANSFER" and area), Fraction(0))
    order: list[str] = []  # people in order of first appearance: recorded holders, then later acquirers
    for r in ledger.rows:
        for pid in (r.summary.get("person"), *r.balances_after):
            if pid and pid not in order and (pid in ledger.baseline or pid in ledger.balances):
                order.append(pid)
    legend = [{"label": names.get(p, {}).get("en", p), "cls": f"seg-{i % 8}",
               "before": fmt_dec(ledger.baseline.get(p, Fraction(0)) * 100, 1),
               "now": fmt_dec(ledger.balances.get(p, Fraction(0)) * 100, 1)} for i, p in enumerate(order)]
    return {
        "legend": legend,
        "overflow_pct": fmt_dec(overflow * 100, 1) if overflow else None,
        "status": ledger.status,
        "area": fmt_dec(area) if area is not None else "?",
        "findings": [finding_view(f, names) for f in sorted_findings(ledger.findings)],
        "holders": [{"id": p, "name_en": names.get(p, {}).get("en", p), "name_bn": names.get(p, {}).get("bn", p),
                     "baseline": fmt_share(ledger.baseline.get(p, Fraction(0))),
                     "baseline_dec": fmt_dec(ledger.baseline.get(p, Fraction(0)) * area) if area else "?",
                     "current": fmt_share(ledger.balances.get(p, Fraction(0))),
                     "current_dec": fmt_dec(ledger.balances.get(p, Fraction(0)) * area) if area else "?"}
                    for p in holders],
        "strip_before": strip_view(ledger.baseline, Fraction(0), names, order),
        "strip_now": strip_view(ledger.balances, overflow, names, order),
        "rows": [row_view(r, names, ledger) for r in ledger.rows],
    }


def plot_context(conn: sqlite3.Connection, plot_id: str) -> dict:
    plot = conn.execute("""SELECT p.*, m.name_en, m.name_bn, m.jl_no, m.upazila, m.district FROM plot p
                           JOIN mouza m ON m.id = p.mouza_id WHERE p.id = ?""", (plot_id,)).fetchone()
    coverage = conn.execute("SELECT * FROM coverage WHERE mouza_id = ?", (plot["mouza_id"],)).fetchall()
    units = conn.execute("SELECT * FROM local_unit WHERE mouza_id = ?", (plot["mouza_id"],)).fetchall()
    return {"plot": plot, "coverage": coverage, "local_units": units, "label": plot_label(conn, plot_id)}


def case_rows(conn: sqlite3.Connection, as_of: date, statuses: tuple[str, ...] = ("pending",)) -> list[dict]:
    names = people(conn)
    cases = conn.execute(f"""SELECT * FROM mutation_case WHERE status IN ({','.join('?' * len(statuses))})
                             ORDER BY filed_date""", statuses).fetchall()
    ledgers: dict[str, Ledger] = {}
    out = []
    for c in cases:
        if c["plot_id"] not in ledgers:
            ledgers[c["plot_id"]] = ledger_for(conn, c["plot_id"], as_of)
        lg = ledgers[c["plot_id"]]
        review = conn.execute("SELECT * FROM review WHERE case_id = ? ORDER BY id DESC LIMIT 1", (c["id"],)).fetchone()
        out.append({"case": c, "status": lg.case_status.get(c["id"], "NO_CONFLICT"),
                    "codes": sorted({f.code for f in lg.case_findings.get(c["id"], [])}),
                    "plot_label": plot_label(conn, c["plot_id"]), "from": names[c["from_id"]]["en"],
                    "to": names[c["to_id"]]["en"], "review": review})
    out.sort(key=lambda r: (STATUS_ORDER[r["status"]], r["case"]["filed_date"]))
    return out


def plot_rows(conn: sqlite3.Connection, as_of: date, q: str = "") -> list[dict]:
    sql = """SELECT p.id, p.scenario, p.title, p.dag_no, p.area_raw, p.record_ref, m.name_en, m.jl_no FROM plot p
             JOIN mouza m ON m.id = p.mouza_id"""
    args: tuple = ()
    if q:
        like = f"%{q[:60]}%"
        sql += """ WHERE p.dag_no LIKE ? OR p.record_ref LIKE ? OR m.name_en LIKE ? OR m.jl_no LIKE ? OR p.id LIKE ?
                   OR p.id IN (SELECT plot_id FROM holding h JOIN person pe ON pe.id = h.person_id
                               WHERE pe.name_en LIKE ? OR pe.name_bn LIKE ?)
                   OR p.id IN (SELECT di.plot_id FROM deed_item di JOIN deed d ON d.id = di.deed_id
                               WHERE d.deed_no LIKE ?)"""
        args = (like,) * 8
    sql += " ORDER BY m.jl_no, CAST(p.dag_no AS INTEGER)"
    out = []
    for r in conn.execute(sql, args).fetchall():
        lg = ledger_for(conn, r["id"], as_of)
        out.append({"row": r, "status": lg.status, "codes": sorted({f.code for f in lg.findings})})
    return out


# ---------------------------------------------------------------- public pages


@app.get("/healthz")
def healthz():
    return {"ok": True, "engine": ENGINE_VERSION}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    with Page(request) as pg:
        user = current_user(request, pg.conn)
        if user is None:
            return RedirectResponse("/login", status_code=303)
        request.state.user = user
        return RedirectResponse("/dashboard", status_code=303)


@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    with Page(request) as pg:
        request.state.user = current_user(request, pg.conn)
        return render(request, "about.html")


def _safe_next(target: str | None) -> str:
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:
        return target
    return "/dashboard"


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request, next: str | None = None):  # noqa: A002 - query parameter name
    with Page(request):
        token = secrets.token_urlsafe(24)
        resp = render(request, "login.html", {"login_csrf": token, "next": _safe_next(next), "error": None,
                                              "demo_users": settings.demo_users if settings.show_demo_logins else ()})
        resp.set_cookie(LOGIN_COOKIE, token, httponly=True, samesite="strict", secure=settings.secure_cookies,
                        max_age=900)
        return resp


@app.post("/login", response_class=HTMLResponse)
async def login(request: Request):
    form = await request.form()
    username = str(form.get("username", ""))[:60].strip()
    password = str(form.get("password", ""))[:200]
    next_url = _safe_next(str(form.get("next", "")))
    with Page(request) as pg:
        if not security.csrf_ok(request.cookies.get(LOGIN_COOKIE), str(form.get("login_csrf", ""))):
            raise Forbidden()
        ip = request.client.host if request.client else "unknown"
        keys = [f"user:{username.lower()}", f"ip:{ip}"]
        ctx = {"login_csrf": request.cookies.get(LOGIN_COOKIE), "next": next_url,
               "demo_users": settings.demo_users if settings.show_demo_logins else ()}
        if security.throttled(pg.conn, keys):
            audit.append(pg.conn, username or "?", "anonymous", "login_throttled", "session", {"ip": ip})
            return render(request, "login.html", {**ctx, "error": "Too many failed attempts. Try again in 15 minutes."},
                          status=429)
        user = security.authenticate(pg.conn, username, password)
        if user is None:
            security.record_failure(pg.conn, keys)
            audit.append(pg.conn, username or "?", "anonymous", "login_failed", "session", {"ip": ip})
            return render(request, "login.html", {**ctx, "error": "Wrong username or password."}, status=401)
        token, _csrf = security.create_session(pg.conn, user["username"], settings.session_hours)
        audit.append(pg.conn, user["username"], user["role"], "login", "session", {"ip": ip})
        resp = RedirectResponse(next_url, status_code=303)
        resp.set_cookie(COOKIE, token, httponly=True, samesite="lax", secure=settings.secure_cookies,
                        max_age=settings.session_hours * 3600, path="/")
        resp.delete_cookie(LOGIN_COOKIE)
        return resp


@app.post("/logout")
async def logout(request: Request):
    form = await request.form()
    with Page(request) as pg:
        user = require(request, pg.conn)
        check_csrf(user, str(form.get("csrf_token", "")))
        security.destroy_session(pg.conn, request.cookies.get(COOKIE))
        audit.append(pg.conn, user["username"], user["role"], "logout", "session")
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie(COOKIE, path="/")
    return resp


# ---------------------------------------------------------------- reviewer / auditor pages


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    with Page(request) as pg:
        user = require(request, pg.conn)
        cases = case_rows(pg.conn, pg.as_of)
        counts = {s: sum(1 for c in cases if c["status"] == s) for s in STATUS_ORDER}
        notices = pg.conn.execute("SELECT COUNT(*) FROM deed WHERE received_via = 'lt_notice'").fetchone()[0]
        return render(request, "dashboard.html", {
            "counts": counts, "pending": len(cases), "reviewed": sum(1 for c in cases if c["review"]),
            "top": cases[:5], "notices": notices, "evaluation": pristine_evaluation(),
            "chain": audit.verify(pg.conn) if user["role"] == "auditor" else None})


@app.get("/cases", response_class=HTMLResponse)
def case_queue(request: Request, status: str = ""):
    with Page(request) as pg:
        require(request, pg.conn, "reviewer", "auditor")
        rows = case_rows(pg.conn, pg.as_of)
        if status in STATUS_ORDER:
            rows = [r for r in rows if r["status"] == status]
        return render(request, "cases.html", {"rows": rows, "filter": status})


@app.get("/cases/{case_id}", response_class=HTMLResponse)
def case_detail(request: Request, case_id: str):
    with Page(request) as pg:
        user = require(request, pg.conn, "reviewer", "auditor")
        case = pg.conn.execute("SELECT * FROM mutation_case WHERE id = ?", (case_id,)).fetchone()
        if case is None:
            return render(request, "error.html", {"code": 404, "message": "Case not found."}, status=404)
        names = people(pg.conn)
        lg = ledger_for(pg.conn, case["plot_id"], pg.as_of)
        status = lg.case_status.get(case_id, "NO_CONFLICT")
        reviews = pg.conn.execute("SELECT * FROM review WHERE case_id = ? ORDER BY id DESC", (case_id,)).fetchall()
        return render(request, "case.html", {
            "case": case, "status": status, "names": names,
            "case_findings": [finding_view(f, names) for f in sorted_findings(lg.case_findings.get(case_id, []))],
            "ledger": ledger_view(pg.conn, lg, names), **plot_context(pg.conn, case["plot_id"]),
            "reviews": reviews, "decisions": DECISIONS, "can_decide": user["role"] == "reviewer",
            "saved": request.query_params.get("saved")})


@app.post("/cases/{case_id}/decision")
async def case_decision(request: Request, case_id: str):
    form = await request.form()
    with Page(request) as pg:
        user = require(request, pg.conn, "reviewer")
        check_csrf(user, str(form.get("csrf_token", "")))
        case = pg.conn.execute("SELECT * FROM mutation_case WHERE id = ?", (case_id,)).fetchone()
        if case is None:
            raise BadRequest("Unknown case.")
        decision = str(form.get("decision", ""))
        note = str(form.get("note", "")).strip()
        if decision not in DECISIONS:
            raise BadRequest("Choose one of the listed decisions.")
        if not 5 <= len(note) <= 1000:
            raise BadRequest("Write a reason of 5 to 1000 characters.")
        lg = ledger_for(pg.conn, case["plot_id"], pg.as_of)
        status = lg.case_status.get(case_id, "NO_CONFLICT")
        if decision == "proceed" and status in ("CONFLICT", "INCOMPLETE"):
            raise BadRequest("A case with a conflict or incomplete records cannot be marked 'no conflict'. "
                             "Use 'explained' and give the evidence instead.")
        pg.conn.execute("INSERT INTO review (case_id, decision, note, reviewer, engine_status, engine_version, created_at)"
                        " VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
                        (case_id, decision, note, user["username"], status, ENGINE_VERSION))
        pg.conn.commit()
        audit.append(pg.conn, user["username"], user["role"], "case_reviewed", case["case_no"],
                     {"decision": decision, "engine_status": status, "engine_version": ENGINE_VERSION,
                      "note_sha256": hashlib.sha256(note.encode()).hexdigest()})
    return RedirectResponse(f"/cases/{case_id}?saved=1", status_code=303)


@app.get("/plots", response_class=HTMLResponse)
def plot_list(request: Request, q: str = "", status: str = ""):
    with Page(request) as pg:
        require(request, pg.conn)
        rows = plot_rows(pg.conn, pg.as_of, q.strip())
        if status in STATUS_ORDER:
            rows = [r for r in rows if r["status"] == status]
        return render(request, "plots.html", {"rows": rows, "q": q, "filter": status})


@app.get("/plots/{plot_id}", response_class=HTMLResponse)
def plot_detail(request: Request, plot_id: str):
    with Page(request) as pg:
        require(request, pg.conn)
        lg = ledger_for(pg.conn, plot_id, pg.as_of)
        if lg is None:
            return render(request, "error.html", {"code": 404, "message": "Plot not found."}, status=404)
        names = people(pg.conn)
        cases = pg.conn.execute("SELECT * FROM mutation_case WHERE plot_id = ? ORDER BY filed_date", (plot_id,)).fetchall()
        return render(request, "plot.html", {
            "ledger": ledger_view(pg.conn, lg, names), "names": names, "cases": cases,
            "case_status": lg.case_status, "saved": request.query_params.get("saved"),
            **plot_context(pg.conn, plot_id)})


@app.get("/evaluation", response_class=HTMLResponse)
def evaluation_page(request: Request):
    with Page(request) as pg:
        require(request, pg.conn)
        return render(request, "evaluation.html", {"ev": pristine_evaluation()})


@app.get("/audit", response_class=HTMLResponse)
def audit_page(request: Request):
    with Page(request) as pg:
        require(request, pg.conn, "auditor")
        entries = pg.conn.execute("SELECT * FROM audit_log ORDER BY seq DESC LIMIT 200").fetchall()
        return render(request, "audit.html", {"entries": entries, "chain": audit.verify(pg.conn)})


# ---------------------------------------------------------------- clerk: L.T. notice intake


def _intake_lists(conn: sqlite3.Connection) -> dict:
    plots = conn.execute("""SELECT p.id, p.dag_no, p.survey, m.name_en, m.jl_no FROM plot p JOIN mouza m
                            ON m.id = p.mouza_id ORDER BY m.jl_no, CAST(p.dag_no AS INTEGER)""").fetchall()
    persons = conn.execute("SELECT * FROM person ORDER BY id").fetchall()
    return {"plots": plots, "persons": persons}


INTAKE_FIELDS = ["deed_no", "deed_type", "execution_date", "registration_date", "plot_id", "plot_ref", "seller_id",
                 "buyer_id", "new_buyer_en", "new_buyer_bn", "quantity"]


def _validate_intake(conn: sqlite3.Connection, f: dict, as_of: date) -> list[str]:
    errors = []
    if not re.fullmatch(r"\d{4}/\d{1,6}", f["deed_no"]):
        errors.append("Deed number must look like 2026/0812.")
    elif conn.execute("SELECT 1 FROM deed WHERE office = ? AND deed_no = ?", (OFFICE, f["deed_no"])).fetchone():
        errors.append("This deed number is already in the registry index.")
    if f["deed_type"] not in ("sale", "gift"):
        errors.append("Deed type must be sale or gift.")
    dates = {}
    for key in ("execution_date", "registration_date"):
        try:
            dates[key] = date.fromisoformat(f[key])
        except ValueError:
            errors.append(f"{key.replace('_', ' ').capitalize()} must be a date.")
    if len(dates) == 2:
        if dates["registration_date"] < dates["execution_date"]:
            errors.append("Registration cannot be before execution.")
        if dates["registration_date"] > as_of:
            errors.append(f"Registration date cannot be after the demo clock ({as_of.isoformat()}).")
    plot = conn.execute("SELECT * FROM plot WHERE id = ?", (f["plot_id"],)).fetchone()
    if plot is None:
        errors.append("Choose the plot (current dag).")
    elif f["plot_ref"] and plot["id"] not in crosswalk_candidates(conn, plot["mouza_id"], f["plot_ref"]):
        errors.append("The old-survey reference does not map to the chosen plot in the crosswalk.")
    if not conn.execute("SELECT 1 FROM person WHERE id = ?", (f["seller_id"],)).fetchone():
        errors.append("Seller must be an existing person ID (e.g. P-0005).")
    if f["buyer_id"]:
        if not conn.execute("SELECT 1 FROM person WHERE id = ?", (f["buyer_id"],)).fetchone():
            errors.append("Buyer ID not found.")
        elif f["buyer_id"] == f["seller_id"]:
            errors.append("Buyer and seller must differ.")
    elif not f["new_buyer_en"]:
        errors.append("Give a buyer ID or a new fictional buyer name.")
    else:
        for value in (f["new_buyer_en"], f["new_buyer_bn"]):
            if value and not re.fullmatch(r"[A-Za-zঀ-৿ .'-]{3,60}", value):
                errors.append("Names may contain letters, spaces, dots, apostrophes and hyphens only (3-60).")
        if not any(m.lower() in f["new_buyer_en"].lower() for m in FICTIONAL_MARKERS):
            errors.append("This prototype only accepts fictional names: include a marker such as 'Namuna' or "
                          "'Kalponik' (e.g. 'Ruma Namuna').")
    try:
        parse_quantity(f["quantity"], {"katha": Fraction(1), "bigha": Fraction(1)})
    except QuantityError:
        errors.append("Quantity must be like '10 decimal', '0.10 acre', '1/4 share' or '৮ আনা'.")
    return errors


def _proposed_transfer(f: dict, buyer_id: str) -> Transfer:
    return Transfer(id="PROPOSED", deed_id="PROPOSED", deed_ref=f"{OFFICE} {f['deed_no'] or '(new)'} (proposed)",
                    office=OFFICE, deed_no=f["deed_no"] or "(new)", deed_type=f["deed_type"] or "sale",
                    execution_date=date.fromisoformat(f["execution_date"]),
                    registration_date=date.fromisoformat(f["registration_date"]),
                    seller_id=f["seller_id"], buyer_id=buyer_id, quantity_raw=f["quantity"], plot_ref=f["plot_ref"],
                    proposed=True)


@app.get("/intake", response_class=HTMLResponse)
def intake_form(request: Request):
    with Page(request) as pg:
        require(request, pg.conn, "clerk")
        empty = {k: "" for k in INTAKE_FIELDS} | {"deed_type": "sale", "execution_date": pg.as_of.isoformat(),
                                                   "registration_date": pg.as_of.isoformat()}
        return render(request, "intake.html", {"f": empty, "errors": [], "check": None, **_intake_lists(pg.conn)})


@app.post("/intake", response_class=HTMLResponse)
async def intake_submit(request: Request):
    form = await request.form()
    with Page(request) as pg:
        user = require(request, pg.conn, "clerk")
        check_csrf(user, str(form.get("csrf_token", "")))
        f = {k: str(form.get(k, "")).strip()[:120] for k in INTAKE_FIELDS}
        f["seller_id"] = f["seller_id"].split(" ")[0].upper()
        f["buyer_id"] = f["buyer_id"].split(" ")[0].upper()
        action = str(form.get("action", "check"))
        errors = _validate_intake(pg.conn, f, pg.as_of)
        check = None
        if not errors:
            names = people(pg.conn)
            buyer_id = f["buyer_id"] or "NEW-BUYER"
            if not f["buyer_id"]:
                names[buyer_id] = {"en": f["new_buyer_en"], "bn": f["new_buyer_bn"] or f["new_buyer_en"]}
            lg = ledger_for(pg.conn, f["plot_id"], pg.as_of, extra_transfers=(_proposed_transfer(f, buyer_id),))
            proposed = [x for x in lg.findings if x.proposed]
            wide = [x for x in lg.findings if "plot" in x.related and x.rank >= LEVEL_RANK["incomplete"]]
            relevant = sorted_findings(proposed + [w for w in wide if w not in proposed])
            check = {"status": status_of(relevant), "findings": [finding_view(x, names) for x in relevant],
                     "ledger": ledger_view(pg.conn, lg, names)}
            audit.append(pg.conn, user["username"], user["role"], "pre_registration_check", f["plot_id"],
                         {"deed_no": f["deed_no"], "status": check["status"]})
            if action == "save":
                if not f["buyer_id"]:
                    n = pg.conn.execute("SELECT COUNT(*) FROM person").fetchone()[0] + 1
                    while pg.conn.execute("SELECT 1 FROM person WHERE id = ?", (f"P-{n:04d}",)).fetchone():
                        n += 1
                    f["buyer_id"] = f"P-{n:04d}"
                    pg.conn.execute("INSERT INTO person VALUES (?, ?, ?)",
                                    (f["buyer_id"], f["new_buyer_en"], f["new_buyer_bn"] or f["new_buyer_en"]))
                deed_id = f"D-{f['deed_no'].replace('/', '-')}"
                pg.conn.execute("INSERT INTO deed (id, office, deed_no, deed_type, execution_date, registration_date, "
                                "received_via, created_by) VALUES (?, ?, ?, ?, ?, ?, 'lt_notice', ?)",
                                (deed_id, OFFICE, f["deed_no"], f["deed_type"], f["execution_date"],
                                 f["registration_date"], user["username"]))
                item_n = pg.conn.execute("SELECT COUNT(*) FROM deed_item").fetchone()[0] + 1
                plot = pg.conn.execute("SELECT * FROM plot WHERE id = ?", (f["plot_id"],)).fetchone()
                pg.conn.execute("INSERT INTO deed_item VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (f"DI-{item_n:04d}-{secrets.token_hex(2)}", deed_id, plot["mouza_id"], f["plot_ref"],
                                 None if f["plot_ref"] else f["plot_id"], f["seller_id"], f["buyer_id"], f["quantity"]))
                pg.conn.commit()
                audit.append(pg.conn, user["username"], user["role"], "lt_notice_recorded", deed_ref(OFFICE, f["deed_no"]),
                             {"plot": f["plot_id"], "engine_status_at_entry": check["status"]})
                return RedirectResponse(f"/plots/{f['plot_id']}?saved={quote(f['deed_no'])}", status_code=303)
        return render(request, "intake.html", {"f": f, "errors": errors, "check": check, **_intake_lists(pg.conn)},
                      status=400 if errors else 200)


# ---------------------------------------------------------------- JSON API


async def _json_body(request: Request) -> dict:
    try:
        body = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise BadRequest("Body must be a JSON object.") from exc
    if not isinstance(body, dict):
        raise BadRequest("Body must be a JSON object.")
    return body


def _ledger_json(conn: sqlite3.Connection, lg: Ledger) -> dict:
    names = people(conn)
    view = ledger_view(conn, lg, names)
    return {"plot_id": lg.plot_id, "as_of": lg.as_of.isoformat(), "engine_version": lg.engine_version,
            "status": lg.status, "status_text": explain.status_text(lg.status), "area_decimal": view["area"],
            "holders": view["holders"], "findings": view["findings"],
            "timeline": [{k: v for k, v in r.items()} for r in view["rows"]],
            "case_status": lg.case_status}


@app.get("/api/plots/{plot_id}/ledger")
def api_ledger(request: Request, plot_id: str):
    with Page(request) as pg:
        require(request, pg.conn)
        lg = ledger_for(pg.conn, plot_id, pg.as_of)
        if lg is None:
            return JSONResponse({"error": "not found"}, status_code=404)
        return _ledger_json(pg.conn, lg)


@app.get("/api/cases")
def api_cases(request: Request):
    with Page(request) as pg:
        require(request, pg.conn, "reviewer", "auditor")
        return [{"id": r["case"]["id"], "case_no": r["case"]["case_no"], "plot_id": r["case"]["plot_id"],
                 "status": r["status"], "codes": r["codes"], "reviewed": bool(r["review"])}
                for r in case_rows(pg.conn, pg.as_of)]


@app.post("/api/check")
async def api_check(request: Request):
    """Pre-registration check of a proposed transfer. Nothing is stored."""
    with Page(request) as pg:
        user = require(request, pg.conn, "clerk", "reviewer")
        check_csrf(user, request.headers.get("X-CSRF-Token"))
        body = await _json_body(request)
        f = {k: str(body.get(k, "")).strip()[:120] for k in INTAKE_FIELDS}
        f["deed_type"] = f["deed_type"] or "sale"
        f["deed_no"] = f["deed_no"] or "9999/0001"
        if not f["buyer_id"] and not f["new_buyer_en"]:
            f["new_buyer_en"] = "Proposed Buyer Namuna"
        errors = [e for e in _validate_intake(pg.conn, f, pg.as_of) if not e.startswith("This deed number")]
        if errors:
            return JSONResponse({"errors": errors}, status_code=400)
        lg = ledger_for(pg.conn, f["plot_id"], pg.as_of,
                        extra_transfers=(_proposed_transfer(f, f["buyer_id"] or "NEW-BUYER"),))
        names = people(pg.conn)
        names.setdefault("NEW-BUYER", {"en": f["new_buyer_en"], "bn": f["new_buyer_en"]})
        relevant = [x for x in lg.findings if x.proposed or ("plot" in x.related and x.rank >= 2)]
        return {"status": status_of(relevant), "findings": [finding_view(x, names) for x in sorted_findings(relevant)]}


@app.post("/api/assist/explain")
async def api_explain(request: Request):
    with Page(request) as pg:
        user = require(request, pg.conn, "reviewer")
        check_csrf(user, request.headers.get("X-CSRF-Token"))
        body = await _json_body(request)
        case = pg.conn.execute("SELECT * FROM mutation_case WHERE id = ?", (str(body.get("case_id", ""))[:20],)).fetchone()
        if case is None:
            return JSONResponse({"error": "not found"}, status_code=404)
        names = people(pg.conn)
        lg = ledger_for(pg.conn, case["plot_id"], pg.as_of)
        fs = sorted_findings(lg.case_findings.get(case["id"], []))
        status = lg.case_status.get(case["id"], "NO_CONFLICT")
        involved = {case["from_id"], case["to_id"]}
        for f in fs:
            for key in ("seller", "buyer", "person", "deceased"):
                if f.facts.get(key):
                    involved.add(f.facts[key])
            for p in f.facts.get("prior", []):
                involved.add(p["buyer"])
        involved_people = {pid: names[pid] for pid in involved if pid in names}
        head_en = f"Mutation case {case['case_no']}: {explain.status_text(status, 'en')}."
        head_bn = to_bn_digits(f"নামজারি মামলা {case['case_no']}: {explain.status_text(status, 'bn')}।")
        template_en = " ".join([head_en] + [explain.describe(f, names, "en") + " " + explain.action(f.code, "en") for f in fs])
        template_bn = " ".join([head_bn] + [explain.describe(f, names, "bn") + " " + explain.action(f.code, "bn") for f in fs])
        result = ai.draft_notice([{"code": f.code, "title": explain.title(f.code), "text_en": explain.describe(f, names, "en")}
                                  for f in fs], involved_people, template_bn, template_en, settings.ai_model)
        audit.append(pg.conn, user["username"], user["role"], "notice_drafted", case["case_no"],
                     {"source": result["source"], "reason": result.get("reason", "")})
        return result


@app.post("/api/assist/extract")
async def api_extract(request: Request):
    with Page(request) as pg:
        user = require(request, pg.conn, "clerk")
        check_csrf(user, request.headers.get("X-CSRF-Token"))
        body = await _json_body(request)
        text = str(body.get("text", ""))
        if not text.strip():
            raise BadRequest("Paste the deed summary text first.")
        result = ai.extract_deed(text, settings.ai_model)
        fields = result["fields"]
        # Deterministic matching of names and plot; the model never chooses database IDs.
        matches = {}
        for role, key in (("seller", "seller_name"), ("buyer", "buyer_name")):
            value = normalize(fields.get(key, ""))
            if value:
                hit = pg.conn.execute("SELECT id, name_en FROM person WHERE lower(name_en) = ? OR name_bn = ?",
                                      (value, fields.get(key, "").strip())).fetchone()
                matches[role] = hit["id"] if hit else ""
        plot_hit = ""
        if fields.get("jl_no") and fields.get("dag_no"):
            row = pg.conn.execute("""SELECT p.id FROM plot p JOIN mouza m ON m.id = p.mouza_id
                                     WHERE m.jl_no = ? AND p.dag_no = ? AND p.survey = ?""",
                                  (fields["jl_no"], fields["dag_no"], fields.get("survey") or "BS")).fetchone()
            plot_hit = row["id"] if row else ""
        audit.append(pg.conn, user["username"], user["role"], "deed_text_extracted", "intake",
                     {"source": result["source"], "chars": len(text)})
        return {**result, "matches": {**matches, "plot_id": plot_hit}}


@app.get("/api/evaluation")
def api_evaluation(request: Request):
    with Page(request) as pg:
        require(request, pg.conn)
        return pristine_evaluation()


@app.get("/api/audit/verify")
def api_audit_verify(request: Request):
    with Page(request) as pg:
        require(request, pg.conn, "auditor")
        return audit.verify(pg.conn)
