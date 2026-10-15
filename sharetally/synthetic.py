"""Reproducible synthetic dataset for ShareTally.

Every person, plot, deed and case here is fictional. Names carry an obvious
marker (Namuna = "sample", Kalponik = "fictional", Udahoron = "example", Porikkha = "test",
Kritrim = "synthetic"), mouzas
are suffixed "(DEMO)" and use JL numbers 901-903, and deed/case numbers carry a
DEMO prefix. No real record or real person's data is used.

Scenario plots (S01-S18) are hand-written test cases. Their expected results are
declared here, next to the data, before the engine is run; the evaluation script
compares the engine against these declarations. Background plots are generated
from a fixed random seed and are designed to contain no conflict.
"""

from __future__ import annotations

import random
from datetime import date, timedelta

AS_OF = date(2026, 10, 1)
OFFICE = "DEMO-SRO"
SEED = 2026

GIVEN = [
    ("Joynal", "জয়নাল"), ("Rahela", "রাহেলা"), ("Mizan", "মিজান"), ("Shapla", "শাপলা"),
    ("Kamrul", "কামরুল"), ("Nasima", "নাসিমা"), ("Habib", "হাবিব"), ("Rokeya", "রোকেয়া"),
    ("Tofazzal", "তোফাজ্জল"), ("Jahanara", "জাহানারা"), ("Sabbir", "সাব্বির"), ("Moushumi", "মৌসুমী"),
    ("Anwar", "আনোয়ার"), ("Lipi", "লিপি"), ("Faruk", "ফারুক"), ("Ruma", "রুমা"),
    ("Delwar", "দেলোয়ার"), ("Shirin", "শিরিন"), ("Monir", "মনির"), ("Taslima", "তাসলিমা"),
    ("Belal", "বেলাল"), ("Kohinur", "কোহিনূর"), ("Selim", "সেলিম"), ("Parul", "পারুল"),
    ("Alamgir", "আলমগীর"), ("Bokul", "বকুল"), ("Rafiq", "রফিক"), ("Morjina", "মর্জিনা"),
    ("Shahid", "শহিদ"), ("Ayesha", "আয়েশা"), ("Nurul", "নুরুল"), ("Sufia", "সুফিয়া"),
    ("Kader", "কাদের"), ("Champa", "চম্পা"), ("Jamal", "জামাল"), ("Rina", "রিনা"),
    ("Babul", "বাবুল"), ("Hosne Ara", "হোসনে আরা"), ("Motaleb", "মোতালেব"), ("Dilruba", "দিলরুবা"),
]
MARKERS = [("Namuna", "নমুনা"), ("Kalponik", "কাল্পনিক"), ("Udahoron", "উদাহরণ"), ("Porikkha", "পরীক্ষা"),
           ("Kritrim", "কৃত্রিম")]

MOUZAS = [
    {"id": "M901", "name_en": "Shapla Char (DEMO)", "name_bn": "শাপলা চর (ডেমো)", "jl_no": "901",
     "upazila": "Demo Upazila", "district": "Demo District"},
    {"id": "M902", "name_en": "Kashful Para (DEMO)", "name_bn": "কাশফুল পাড়া (ডেমো)", "jl_no": "902",
     "upazila": "Demo Upazila", "district": "Demo District"},
    {"id": "M903", "name_en": "Hijol Tola (DEMO)", "name_bn": "হিজল তলা (ডেমো)", "jl_no": "903",
     "upazila": "Demo Upazila", "district": "Demo District"},
]

# Katha differs by locality; this demo mouza assumes 720 sq ft so the converter can be shown.
LOCAL_UNITS = [
    {"mouza_id": "M902", "unit": "katha", "decimals": "7200/4356",
     "note": "Demo assumption: 1 katha = 720 sq ft (local definitions vary)"},
]

COVERAGE = [
    {"id": "C901", "mouza_id": "M901", "source": "registry_index", "start_date": "2000-01-01", "end_date": None,
     "note": "Simulated digital index of registered deeds (L.T. notices) for JL 901"},
    {"id": "C902", "mouza_id": "M902", "source": "registry_index", "start_date": "2000-01-01", "end_date": None,
     "note": "Simulated digital index of registered deeds (L.T. notices) for JL 902"},
    {"id": "C903", "mouza_id": "M903", "source": "registry_index", "start_date": "2016-01-01", "end_date": None,
     "note": "Simulated index for JL 903 starts in 2016; older deeds are on paper only"},
]


class Builder:
    def __init__(self) -> None:
        self.data: dict[str, list] = {k: [] for k in (
            "persons", "plots", "holdings", "deeds", "deed_items", "crosswalk", "inheritances", "heirs",
            "mutation_cases", "expected")}
        self._names: list[tuple[str, str]] = [
            (f"{g} {m}", f"{gb} {mb}") for m, mb in MARKERS for g, gb in GIVEN]
        self._n ={"person": 0, "holding": 0, "item": 0, "case": 0, "inh": 0}

    def person(self, given: str | None = None) -> str:
        """Next unused fictional name, or the next unused one with this given name."""
        self._n["person"] += 1
        pid = f"P-{self._n['person']:04d}"
        index = next(i for i, (en, _) in enumerate(self._names) if given is None or en.split(" ")[0] == given)
        en, bn = self._names.pop(index)
        self.data["persons"].append({"id": pid, "name_en": en, "name_bn": bn})
        return pid

    def people(self, n: int) -> list[str]:
        return [self.person() for _ in range(n)]

    def plot(self, mouza: str, dag: str, area: str, record_date: str, khatian: str, scenario: str,
             title: str, holdings: list[tuple[str, str]]) -> str:
        plot_id = f"{mouza}-BS-{dag}"
        self.data["plots"].append({
            "id": plot_id, "mouza_id": mouza, "survey": "BS", "dag_no": dag, "area_raw": area,
            "record_date": record_date, "record_ref": f"BS Khatian {khatian}", "scenario": scenario,
            "title": title})
        for person_id, share in holdings:
            self._n["holding"] += 1
            self.data["holdings"].append({"id": f"H-{self._n['holding']:04d}", "plot_id": plot_id,
                                          "person_id": person_id, "khatian_no": khatian, "share_raw": share})
        return plot_id

    def deed(self, deed_no: str, executed: str, seller: str, buyer: str, quantity: str, *,
             plot_id: str | None, mouza: str, plot_ref: str = "", registered: str | None = None,
             deed_type: str = "sale") -> str:
        deed_id = f"D-{deed_no.replace('/', '-')}"
        self.data["deeds"].append({"id": deed_id, "office": OFFICE, "deed_no": deed_no, "deed_type": deed_type,
                                   "execution_date": executed, "registration_date": registered or executed,
                                   "received_via": "registry_index", "created_by": "seed"})
        self._n["item"] += 1
        self.data["deed_items"].append({"id": f"DI-{self._n['item']:04d}", "deed_id": deed_id, "mouza_id": mouza,
                                        "plot_ref": plot_ref, "plot_id": plot_id, "seller_id": seller,
                                        "buyer_id": buyer, "quantity_raw": quantity})
        return deed_id

    def case(self, plot_id: str, case_no: str, filed: str, status: str, deed_no: str, deed_date: str,
             from_id: str, to_id: str, quantity: str, decided: str | None = None) -> str:
        self._n["case"] += 1
        case_id = f"MC-{self._n['case']:04d}"
        self.data["mutation_cases"].append({
            "id": case_id, "case_no": f"DEMO-MC/{case_no}", "plot_id": plot_id, "filed_date": filed,
            "status": status, "basis_office": OFFICE, "basis_deed_no": deed_no, "basis_deed_date": deed_date,
            "from_id": from_id, "to_id": to_id, "quantity_raw": quantity, "decided_date": decided})
        return case_id

    def inheritance(self, plot_id: str, deceased: str, when: str, certificate: str,
                    heirs: list[tuple[str, str]]) -> str:
        self._n["inh"] += 1
        inh_id = f"INH-{self._n['inh']:03d}"
        self.data["inheritances"].append({"id": inh_id, "plot_id": plot_id, "deceased_id": deceased,
                                          "event_date": when, "certificate_ref": certificate})
        for person_id, fraction in heirs:
            self.data["heirs"].append({"inheritance_id": inh_id, "person_id": person_id, "fraction_raw": fraction})
        return inh_id

    def expect(self, object_type: str, object_id: str, status: str, codes: set[str], scenario: str,
               description: str) -> None:
        self.data["expected"].append({"object_type": object_type, "object_id": object_id, "status": status,
                                      "codes": sorted(codes), "scenario": scenario, "description": description})


def _scenarios(b: Builder) -> None:
    # S01 - ordinary sale, mutation approved: nothing to report.
    a, c, n = (b.person(g) for g in ("Rahela", "Kamrul", "Nasima"))
    p = b.plot("M901", "1101", "50 decimal", "2018-06-30", "210", "S01", "Ordinary sale, mutation done",
               [(a, "1/2 share"), (c, "1/2 share")])
    b.deed("2024/0110", "2024-03-10", a, n, "10 decimal", plot_id=p, mouza="M901")
    b.case(p, "2024/0201", "2024-03-25", "approved", "2024/0110", "2024-03-10", a, n, "10 decimal", "2024-04-20")
    b.expect("plot", p, "NO_CONFLICT", set(), "S01", "Sale within share; mutation approved")

    # S02 - same 20 decimal sold twice; first buyer never mutated, so the khatian still shows the seller.
    joynal, shirin, mizan, shapla = (b.person(g) for g in ("Joynal", "Shirin", "Mizan", "Shapla"))
    p = b.plot("M901", "1201", "60 decimal", "2019-06-30", "340", "S02", "Second sale while first is unmutated",
               [(joynal, "৮ আনা"), (shirin, "৮ আনা")])
    b.deed("2023/0457", "2023-02-10", joynal, mizan, "20 decimal", plot_id=p, mouza="M901")
    b.deed("2026/0688", "2026-08-21", joynal, shapla, "20 decimal", plot_id=p, mouza="M901")
    cid = b.case(p, "2026/0312", "2026-09-15", "pending", "2026/0688", "2026-08-21", joynal, shapla, "20 decimal")
    b.expect("plot", p, "CONFLICT", {"OVER_TRANSFER", "RECORD_LAG"}, "S02",
             "Second deed exceeds remaining share by 10 decimal; first deed never mutated")
    b.expect("case", cid, "CONFLICT", {"OVER_TRANSFER"}, "S02", "Application relies on the conflicting second deed")

    # S03 - co-heir of undivided (ejmali) land sells more than a one-third share.
    h1, h2, h3, buyer = b.people(4)
    p = b.plot("M901", "1205", "45 decimal", "2016-06-30", "412", "S03", "Co-heir sells beyond share",
               [(h1, "1/3 share"), (h2, "1/3 share"), (h3, "1/3 share")])
    b.deed("2026/0733", "2026-07-12", h1, buyer, "20 decimal", plot_id=p, mouza="M901")
    cid = b.case(p, "2026/0390", "2026-07-20", "pending", "2026/0733", "2026-07-12", h1, buyer, "20 decimal")
    b.expect("plot", p, "CONFLICT", {"OVER_TRANSFER"}, "S03", "20 decimal sold from a 15 decimal share")
    b.expect("case", cid, "CONFLICT", {"OVER_TRANSFER"}, "S03", "Mutation would record 5 decimal more than held")

    # S04 - mutation cites a deed number the (fully covered) registry index has never seen.
    owner, applicant = b.people(2)
    p = b.plot("M901", "1210", "40 decimal", "2017-06-30", "455", "S04", "Mutation cites unknown deed",
               [(owner, "1 share")])
    cid = b.case(p, "2026/0405", "2026-08-05", "pending", "2026/0999", "2026-06-18", owner, applicant, "15 decimal")
    b.expect("plot", p, "CONFLICT", {"DEED_NOT_IN_INDEX"}, "S04", "Cited deed absent from a covered index")
    b.expect("case", cid, "CONFLICT", {"DEED_NOT_IN_INDEX"}, "S04", "Verify deed with Sub-Registry before mutation")

    # S05 - cited deed predates the digital index: cannot verify, must not pass as clean.
    owner, applicant = b.people(2)
    p = b.plot("M903", "2101", "30 decimal", "2005-06-30", "88", "S05", "Cited deed older than digital index",
               [(owner, "1 share")])
    cid = b.case(p, "2026/0418", "2026-08-20", "pending", "2008/0141", "2008-04-02", owner, applicant, "30 decimal")
    b.expect("plot", p, "INCOMPLETE", {"CITED_DEED_UNVERIFIABLE", "COVERAGE_GAP"}, "S05",
             "Index starts 2016; 2008 deed and 2005-2015 transfers unknown")
    b.expect("case", cid, "INCOMPLETE", {"CITED_DEED_UNVERIFIABLE", "COVERAGE_GAP"}, "S05",
             "Needs manual search of paper volumes")

    # S06 - mutation asks for more than the deed transferred.
    lipi, faruk, ruma = b.people(3)
    p = b.plot("M902", "3101", "66 decimal", "2018-06-30", "120", "S06", "Mutation quantity differs from deed",
               [(lipi, "1/2 share"), (faruk, "1/2 share")])
    b.deed("2026/0612", "2026-08-01", faruk, ruma, "10 decimal", plot_id=p, mouza="M902")
    cid = b.case(p, "2026/0377", "2026-08-20", "pending", "2026/0612", "2026-08-01", faruk, ruma, "15 decimal")
    b.expect("plot", p, "CONFLICT", {"MUTATION_MISMATCH"}, "S06", "Deed says 10 decimal; application says 15")
    b.expect("case", cid, "CONFLICT", {"MUTATION_MISMATCH"}, "S06", "Quantity mismatch")

    # S07 - three quick resales of the same 10 decimal. Arithmetic is fine; shown as context only.
    d0, d1, d2, d3 = b.people(4)
    p = b.plot("M902", "3105", "33 decimal", "2018-06-30", "131", "S07", "Rapid resale chain",
               [(d0, "1 share")])
    b.deed("2026/0301", "2026-03-05", d0, d1, "10 decimal", plot_id=p, mouza="M902")
    b.case(p, "2026/0150", "2026-03-12", "approved", "2026/0301", "2026-03-05", d0, d1, "10 decimal", "2026-04-02")
    b.deed("2026/0388", "2026-04-10", d1, d2, "10 decimal", plot_id=p, mouza="M902")
    b.case(p, "2026/0190", "2026-04-15", "approved", "2026/0388", "2026-04-10", d1, d2, "10 decimal", "2026-05-06")
    b.deed("2026/0455", "2026-05-20", d2, d3, "10 decimal", plot_id=p, mouza="M902")
    b.case(p, "2026/0230", "2026-05-25", "approved", "2026/0455", "2026-05-20", d2, d3, "10 decimal", "2026-06-15")
    b.expect("plot", p, "ATTENTION", {"RAPID_RESALE"}, "S07", "Resold after 36 and 40 days; context, not a conflict")

    # S08 - seller does not appear anywhere in the supplied records.
    p1, p2, stranger, buyer = b.people(4)
    p = b.plot("M901", "1215", "52 decimal", "2019-06-30", "470", "S08", "Seller has no recorded source",
               [(p1, "1/2 share"), (p2, "1/2 share")])
    b.deed("2026/0702", "2026-07-15", stranger, buyer, "10 decimal", plot_id=p, mouza="M901")
    cid = b.case(p, "2026/0399", "2026-08-01", "pending", "2026/0702", "2026-07-15", stranger, buyer, "10 decimal")
    b.expect("plot", p, "INCOMPLETE", {"NO_RECORDED_SOURCE"}, "S08", "Seller's title not in supplied records")
    b.expect("case", cid, "INCOMPLETE", {"NO_RECORDED_SOURCE"}, "S08", "Ask for seller's source documents")

    # S09 - nothing wrong in the data we have, but the index misses 2010-2015: must not report clean.
    bokul, rafiq, morjina, shahid = b.people(4)
    p = b.plot("M903", "2105", "40 decimal", "2010-06-30", "95", "S09", "Registry coverage gap",
               [(bokul, "1/2 share"), (rafiq, "1/2 share")])
    b.deed("2024/0222", "2024-05-05", bokul, morjina, "5 decimal", plot_id=p, mouza="M903")
    b.case(p, "2024/0301", "2024-05-20", "approved", "2024/0222", "2024-05-05", bokul, morjina, "5 decimal",
           "2024-06-10")
    b.deed("2026/0801", "2026-08-10", rafiq, shahid, "8 decimal", plot_id=p, mouza="M903")
    cid = b.case(p, "2026/0425", "2026-08-25", "pending", "2026/0801", "2026-08-10", rafiq, shahid, "8 decimal")
    b.expect("plot", p, "INCOMPLETE", {"COVERAGE_GAP"}, "S09", "No conflict seen, but 2010-2015 not indexed")
    b.expect("case", cid, "INCOMPLETE", {"COVERAGE_GAP"}, "S09", "Clean-looking case still incomplete")

    # S10 - deed names old RS dag 245, which became two BS dags.
    ayesha, nurul = b.people(2)
    pa = b.plot("M901", "1301", "35 decimal", "2015-06-30", "501", "S10", "Old-survey dag maps to two plots",
                [(ayesha, "1 share")])
    pb = b.plot("M901", "1302", "25 decimal", "2015-06-30", "501", "S10", "Old-survey dag maps to two plots",
                [(ayesha, "1 share")])
    for target in (pa, pb):
        b.data["crosswalk"].append({"mouza_id": "M901", "old_survey": "RS", "old_dag": "245", "plot_id": target,
                                    "note": "Synthetic crosswalk: RS 245 split into BS 1301 and BS 1302"})
    b.deed("2026/0640", "2026-07-20", ayesha, nurul, "12 decimal", plot_id=None, mouza="M901", plot_ref="RS 245")
    cid = b.case(pa, "2026/0410", "2026-08-10", "pending", "2026/0640", "2026-07-20", ayesha, nurul, "12 decimal")
    b.expect("plot", pa, "INCOMPLETE", {"AMBIGUOUS_REFERENCE"}, "S10", "Cannot tell which BS dag was sold")
    b.expect("plot", pb, "INCOMPLETE", {"AMBIGUOUS_REFERENCE"}, "S10", "Cannot tell which BS dag was sold")
    b.expect("case", cid, "INCOMPLETE", {"AMBIGUOUS_REFERENCE"}, "S10", "Needs surveyor/crosswalk confirmation")

    # S11 - bigha has no configured local size in this mouza.
    sufia, jamal = b.people(2)
    p = b.plot("M901", "1220", "66 decimal", "2016-06-30", "480", "S11", "Unit without local definition",
               [(sufia, "1 share")])
    b.deed("2026/0655", "2026-07-25", sufia, jamal, "1 bigha", plot_id=p, mouza="M901")
    cid = b.case(p, "2026/0412", "2026-08-12", "pending", "2026/0655", "2026-07-25", sufia, jamal, "1 bigha")
    b.expect("plot", p, "INCOMPLETE", {"UNIT_UNRESOLVED"}, "S11", "Bigha size varies; not guessed")
    b.expect("case", cid, "INCOMPLETE", {"UNIT_UNRESOLVED"}, "S11", "Confirm local bigha definition")

    # S12 - inheritance by (synthetic) succession certificate, then an heir sells exactly her share.
    deceased, son, daughter, widow, buyer = b.people(5)
    p = b.plot("M902", "3110", "48 decimal", "2014-06-30", "140", "S12", "Inheritance then sale within share",
               [(deceased, "1 share")])
    b.inheritance(p, deceased, "2020-03-01", "DEMO-UP/SC/2020/017",
                  [(son, "1/2 share"), (daughter, "1/4 share"), (widow, "1/4 share")])
    b.deed("2026/0590", "2026-08-05", daughter, buyer, "12 decimal", plot_id=p, mouza="M902")
    cid = b.case(p, "2026/0415", "2026-08-20", "pending", "2026/0590", "2026-08-05", daughter, buyer, "12 decimal")
    b.expect("plot", p, "NO_CONFLICT", set(), "S12", "Heir sells exactly her 12 decimal")
    b.expect("case", cid, "NO_CONFLICT", set(), "S12", "Inheritance chain closes")

    # S13 - heir fractions on the certificate add up to 5/6 only.
    deceased, e, f, g = b.people(4)
    p = b.plot("M902", "3115", "30 decimal", "2014-06-30", "145", "S13", "Heir shares do not add up",
               [(deceased, "1 share")])
    b.inheritance(p, deceased, "2021-09-09", "DEMO-UP/SC/2021/044", [(e, "1/2 share"), (f, "1/3 share")])
    b.deed("2026/0700", "2026-08-15", e, g, "10 decimal", plot_id=p, mouza="M902")
    cid = b.case(p, "2026/0420", "2026-08-30", "pending", "2026/0700", "2026-08-15", e, g, "10 decimal")
    b.expect("plot", p, "INCOMPLETE", {"INHERITANCE_SHARES_INCOMPLETE", "NO_RECORDED_SOURCE"}, "S13",
             "Certificate covers 5/6; heir's share unknown")
    b.expect("case", cid, "INCOMPLETE", {"INHERITANCE_SHARES_INCOMPLETE", "NO_RECORDED_SOURCE"}, "S13",
             "Obtain complete heir list")

    # S14 - the record itself allocates 125% of the plot.
    h, i, j = b.people(3)
    p = b.plot("M901", "1225", "40 decimal", "2017-06-30", "490", "S14", "Khatian shares exceed whole",
               [(h, "3/4 share"), (i, "1/2 share")])
    b.deed("2026/0710", "2026-08-02", i, j, "5 decimal", plot_id=p, mouza="M901")
    cid = b.case(p, "2026/0402", "2026-08-16", "pending", "2026/0710", "2026-08-02", i, j, "5 decimal")
    b.expect("plot", p, "CONFLICT", {"SHARE_TOTAL_MISMATCH"}, "S14", "Recorded shares sum to 5/4")
    b.expect("case", cid, "CONFLICT", {"SHARE_TOTAL_MISMATCH"}, "S14", "Record must be corrected first")

    # S15 - anna notation, acres, Bangla digits and katha all reconcile.
    k, l_, m, n2 = b.people(4)
    p = b.plot("M902", "3120", "80 decimal", "2016-06-30", "150", "S15", "Mixed notation, consistent",
               [(k, "৫ আনা ১০ গণ্ডা"), (l_, "১০ আনা ১০ গণ্ডা")])
    b.deed("2026/0720", "2026-08-08", k, m, "0.25 acre", plot_id=p, mouza="M902")
    cid = b.case(p, "2026/0421", "2026-08-22", "pending", "2026/0720", "2026-08-08", k, m, "২৫ শতাংশ")
    b.deed("2026/0726", "2026-08-12", l_, n2, "5 katha", plot_id=p, mouza="M902")
    b.expect("plot", p, "NO_CONFLICT", set(), "S15", "27.5 decimal share; 25 decimal sold; units agree")
    b.expect("case", cid, "NO_CONFLICT", set(), "S15", "0.25 acre equals 25 shotangsho")

    # S16 - one-third of 50 decimal written as 16.67: within rounding of the stated precision.
    o, pp, q, r = b.people(4)
    p = b.plot("M901", "1230", "50 decimal", "2018-06-30", "495", "S16", "Rounded one-third share",
               [(o, "1/3 share"), (pp, "1/3 share"), (q, "1/3 share")])
    b.deed("2026/0730", "2026-08-09", o, r, "16.67 decimal", plot_id=p, mouza="M901")
    cid = b.case(p, "2026/0422", "2026-08-24", "pending", "2026/0730", "2026-08-09", o, r, "16.67 decimal")
    b.expect("plot", p, "NO_CONFLICT", set(), "S16", "16.67 vs 16.6667 is rounding, not over-sale")
    b.expect("case", cid, "NO_CONFLICT", set(), "S16", "No false positive from rounding")

    # S17 - seller already sold everything (and it was mutated) but sells again elsewhere.
    s, t, u = b.people(3)
    p = b.plot("M901", "1235", "30 decimal", "2016-06-30", "498", "S17", "Sale after selling everything",
               [(s, "1 share")])
    b.deed("2025/0505", "2025-03-03", s, t, "30 decimal", plot_id=p, mouza="M901")
    b.case(p, "2025/0210", "2025-03-15", "approved", "2025/0505", "2025-03-03", s, t, "30 decimal", "2025-04-10")
    b.deed("2026/0745", "2026-08-18", s, u, "10 decimal", plot_id=p, mouza="M901")
    cid = b.case(p, "2026/0428", "2026-09-01", "pending", "2026/0745", "2026-08-18", s, u, "10 decimal")
    b.expect("plot", p, "CONFLICT", {"OVER_TRANSFER"}, "S17", "Seller holds nothing after 2025 sale")
    b.expect("case", cid, "CONFLICT", {"OVER_TRANSFER"}, "S17", "Zero remaining share")

    # S18 - valid sale registered a year ago and never mutated: the khatian is stale.
    v, w, x = b.people(3)
    p = b.plot("M902", "3125", "40 decimal", "2017-06-30", "160", "S18", "Registered but never mutated",
               [(v, "1/2 share"), (w, "1/2 share")])
    b.deed("2025/0901", "2025-11-05", v, x, "10 decimal", plot_id=p, mouza="M902")
    b.expect("plot", p, "ATTENTION", {"RECORD_LAG"}, "S18", "Khatian still shows seller 330 days later")


SHARE_PATTERNS = [
    ["1 share"], ["1/2 share", "1/2 share"], ["1/3 share", "1/3 share", "1/3 share"],
    ["1/4 share", "3/4 share"], ["৮ আনা", "৮ আনা"], ["0.60 share", "0.40 share"],
]


def _background(b: Builder, rng: random.Random, count: int = 30) -> None:
    """Clean plots: every sale fits the seller's share and old sales are mutated."""
    for idx in range(count):
        mouza = "M901" if idx % 2 == 0 else "M902"
        dag = str((1400 if mouza == "M901" else 3200) + idx)
        area = rng.randrange(20, 121)
        record = date(rng.randrange(2015, 2020), 6, 30)
        pattern = rng.choice(SHARE_PATTERNS)
        owners = b.people(len(pattern))
        khatian = str(600 + idx)
        p = b.plot(mouza, dag, f"{area} decimal", record.isoformat(), khatian, "BG", "Background (clean)",
                   list(zip(owners, pattern)))
        from .engine.units import parse_quantity  # local import keeps module import light
        for owner, share_raw in zip(owners, pattern):
            if rng.random() < 0.45:
                continue
            held = parse_quantity(share_raw).value * area
            amount = (int(held * 2) // 2) / 2  # at most half the holding, in 0.5 decimal steps
            if amount < 1:
                continue
            buyer = b.person()
            recent = rng.random() < 0.25
            if recent:
                executed = AS_OF - timedelta(days=rng.randrange(10, 60))
            else:
                executed = record + timedelta(days=rng.randrange(200, 2400))
                executed = min(executed, AS_OF - timedelta(days=150))
            deed_no = f"{executed.year}/{rng.randrange(1000, 9999)}"
            while any(d["deed_no"] == deed_no for d in b.data["deeds"]):
                deed_no = f"{executed.year}/{rng.randrange(1000, 9999)}"
            qty = f"{amount:.1f} decimal"
            b.deed(deed_no, executed.isoformat(), owner, buyer, qty, plot_id=p, mouza=mouza)
            filed = executed + timedelta(days=rng.randrange(3, 10))
            case_no = f"{filed.year}/{rng.randrange(5000, 9999)}"
            if recent:
                cid = b.case(p, case_no, filed.isoformat(), "pending", deed_no, executed.isoformat(), owner, buyer,
                             qty)
                b.expect("case", cid, "NO_CONFLICT", set(), "BG", "Recent clean sale")
            else:
                decided = filed + timedelta(days=rng.randrange(20, 50))
                b.case(p, case_no, filed.isoformat(), "approved", deed_no, executed.isoformat(), owner, buyer, qty,
                       decided.isoformat())
        b.expect("plot", p, "NO_CONFLICT", set(), "BG", "Generated clean plot")


def build_dataset() -> dict:
    b = Builder()
    _scenarios(b)
    _background(b, random.Random(SEED))
    return {"as_of": AS_OF.isoformat(), "mouzas": MOUZAS, "local_units": LOCAL_UNITS, "coverage": COVERAGE,
            **b.data}
