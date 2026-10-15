"""End-to-end workflow: clerk records a notice, reviewer sees the effect and decides."""

import re

from conftest import csrf_of, login


def intake(client, csrf, **overrides):
    form = {"csrf_token": csrf, "deed_no": "2026/0900", "deed_type": "sale", "execution_date": "2026-09-25",
            "registration_date": "2026-09-25", "plot_id": "M901-BS-1101", "plot_ref": "", "seller_id": "P-0002",
            "buyer_id": "", "new_buyer_en": "Ruma Namuna", "new_buyer_bn": "রুমা নমুনা", "quantity": "10 decimal",
            "action": "check"}
    form.update(overrides)
    return client.post("/intake", data=form, follow_redirects=False)


def test_pre_registration_check_then_save(app_client):
    csrf = login(app_client, "clerk")
    # Kamrul holds 25 decimal of BS 1101; 10 decimal fits.
    r = intake(app_client, csrf)
    assert r.status_code == 200 and "No conflict found in supplied records" in r.text
    # 30 decimal does not, and the check says so before anything is stored.
    r = intake(app_client, csrf, quantity="30 decimal")
    assert "OVER_TRANSFER" in r.text and "5.00 decimal more than held" in r.text
    r = intake(app_client, csrf, action="save")
    assert r.status_code == 303 and r.headers["location"].startswith("/plots/M901-BS-1101")
    page = app_client.get(r.headers["location"])
    assert "DEMO-SRO 2026/0900" in page.text
    # The same deed number cannot be recorded twice.
    r = intake(app_client, csrf, action="save")
    assert r.status_code == 400 and "already in the registry index" in r.text


def test_second_sale_after_saved_notice_is_flagged(app_client):
    csrf = login(app_client, "clerk")
    assert intake(app_client, csrf, quantity="20 decimal", action="save").status_code == 303
    r = intake(app_client, csrf, deed_no="2026/0901", quantity="10 decimal", new_buyer_en="Lipi Kalponik",
               new_buyer_bn="")
    assert "OVER_TRANSFER" in r.text and "earlier transfers" in r.text.lower()


def test_reviewer_decision_is_audited(app_client):
    csrf = login(app_client, "reviewer")
    r = app_client.post("/cases/MC-0002/decision",
                        data={"csrf_token": csrf, "decision": "hold_notice", "note": "Earlier deed 2023/0457 conflicts."},
                        follow_redirects=False)
    assert r.status_code == 303
    page = app_client.get("/cases/MC-0002")
    assert "hold notice" in page.text and "engine said CONFLICT" in page.text
    app_client.post("/logout", data={"csrf_token": csrf_of(app_client)})
    login(app_client, "auditor")
    audit_page = app_client.get("/audit")
    assert "case_reviewed" in audit_page.text and "Chain intact" in audit_page.text


def test_explain_falls_back_to_template_without_key(app_client):
    csrf = login(app_client, "reviewer")
    r = app_client.post("/api/assist/explain", json={"case_id": "MC-0002"}, headers={"X-CSRF-Token": csrf})
    data = r.json()
    assert data["source"] == "template"
    assert "১০.০০ শতাংশ" in data["bn"] and "10.00 decimal" in data["en"]


def test_extract_matches_people_and_plot_deterministically(app_client):
    csrf = login(app_client, "clerk")
    text = ("দলিল নং: 2026/0850\nসম্পাদনের তারিখ: ২০২৬-০৯-২০\nদাতা (বিক্রেতা): জয়নাল নমুনা\n"
            "গ্রহীতা (ক্রেতা): শাপলা নমুনা\nমৌজা: শাপলা চর (ডেমো), জে.এল. নং ৯০১\nদাগ: বিএস ১২০১\nপরিমাণ: ১০ শতাংশ")
    data = app_client.post("/api/assist/extract", json={"text": text}, headers={"X-CSRF-Token": csrf}).json()
    assert data["source"] == "rules"
    assert data["matches"]["plot_id"] == "M901-BS-1201"
    assert re.fullmatch(r"P-\d{4}", data["matches"]["seller"])
    assert data["fields"]["execution_date"] == "2026-09-20"


def test_api_check(app_client):
    csrf = login(app_client, "clerk")
    r = app_client.post("/api/check", json={"plot_id": "M901-BS-1205", "seller_id": "P-0010", "quantity": "20 decimal",
                                            "execution_date": "2026-09-20", "registration_date": "2026-09-20"},
                        headers={"X-CSRF-Token": csrf})
    assert r.status_code == 200, r.text
    assert r.json()["status"] in ("CONFLICT", "INCOMPLETE")
