"""Deterministic English and Bangla wording for findings.

This is the always-available explanation path. The optional AI rewrite in
``ai.py`` is checked against these same facts and falls back to this text.
"""

from __future__ import annotations

from .engine.ledger import Finding
from .engine.units import to_bn_digits

STATUS = {
    "CONFLICT": ("Conflict found — reviewer decision needed", "দ্বন্দ্ব পাওয়া গেছে — পর্যালোচকের সিদ্ধান্ত প্রয়োজন"),
    "INCOMPLETE": ("Incomplete — records cannot confirm", "অসম্পূর্ণ — রেকর্ড দিয়ে নিশ্চিত করা যায় না"),
    "ATTENTION": ("No conflict, but needs attention", "দ্বন্দ্ব নেই, তবে লক্ষ্য রাখা প্রয়োজন"),
    "NO_CONFLICT": ("No conflict found in supplied records", "সরবরাহকৃত রেকর্ডে কোনো দ্বন্দ্ব পাওয়া যায়নি"),
}

TITLES = {
    "OVER_TRANSFER": ("Transfer exceeds the seller's remaining share", "বিক্রেতার অবশিষ্ট অংশের চেয়ে বেশি হস্তান্তর"),
    "DEED_NOT_IN_INDEX": ("Cited deed not found in the registry index", "উল্লিখিত দলিল রেজিস্ট্রি সূচিতে নেই"),
    "MUTATION_MISMATCH": ("Mutation application differs from the deed", "নামজারি আবেদন ও দলিলের তথ্যে অমিল"),
    "SHARE_TOTAL_MISMATCH": ("Recorded shares add up to more than the whole plot",
                             "খতিয়ানে অংশের যোগফল পুরো দাগের চেয়ে বেশি"),
    "NO_RECORDED_SOURCE": ("Seller's source of title is not in the supplied records",
                           "সরবরাহকৃত রেকর্ডে বিক্রেতার মালিকানার উৎস নেই"),
    "CITED_DEED_UNVERIFIABLE": ("Cited deed is older than the digital index",
                                "উল্লিখিত দলিল ডিজিটাল সূচির সময়সীমার বাইরে"),
    "COVERAGE_GAP": ("Registry index does not cover the whole period", "রেজিস্ট্রি সূচিতে সময়ের ফাঁক আছে"),
    "AMBIGUOUS_REFERENCE": ("Deed names an old-survey dag that maps to several plots",
                            "দলিলে পুরোনো জরিপের দাগ, যা একাধিক বর্তমান দাগে বিভক্ত"),
    "UNIT_UNRESOLVED": ("Unit size is not defined for this mouza", "এই মৌজায় এককের মাপ নির্ধারিত নেই"),
    "INHERITANCE_SHARES_INCOMPLETE": ("Heir shares do not add up to the whole estate",
                                      "ওয়ারিশদের অংশের যোগফল পূর্ণ নয়"),
    "UNALLOCATED_SHARE": ("Part of the plot has no recorded holder", "দাগের একাংশের কোনো রেকর্ডভুক্ত মালিক নেই"),
    "INVALID_QUANTITY": ("A quantity could not be read", "একটি পরিমাণ পড়া যায়নি"),
    "RECORD_LAG": ("Registered transfer not yet reflected by mutation", "নিবন্ধিত হস্তান্তরের নামজারি হয়নি"),
    "RAPID_RESALE": ("Resold soon after it was acquired", "অর্জনের অল্প দিনের মধ্যে আবার বিক্রি"),
}

ACTIONS = {
    "OVER_TRANSFER": ("Hold the case. Notify the seller and every earlier buyer named here, and obtain certified "
                      "copies of the listed deeds before deciding.",
                      "মামলা স্থগিত রাখুন। বিক্রেতা ও এখানে উল্লিখিত পূর্ববর্তী সকল ক্রেতাকে নোটিশ দিন এবং সিদ্ধান্তের "
                      "আগে তালিকাভুক্ত দলিলের সার্টিফাইড কপি সংগ্রহ করুন।"),
    "DEED_NOT_IN_INDEX": ("Ask the Sub-Registry office to confirm the deed number and date. Do not proceed on "
                          "the applicant's copy alone.",
                          "সাব-রেজিস্ট্রি অফিস থেকে দলিল নম্বর ও তারিখ যাচাই করুন। শুধু আবেদনকারীর কপির ভিত্তিতে "
                          "অগ্রসর হবেন না।"),
    "MUTATION_MISMATCH": ("Return the application for correction or verify the certified deed copy.",
                          "আবেদন সংশোধনের জন্য ফেরত দিন অথবা দলিলের সার্টিফাইড কপি যাচাই করুন।"),
    "SHARE_TOTAL_MISMATCH": ("Refer the record for correction before any mutation on this plot.",
                             "এই দাগে নামজারির আগে রেকর্ড সংশোধনের জন্য পাঠান।"),
    "NO_RECORDED_SOURCE": ("Request the seller's source documents (earlier deed, succession certificate) and "
                           "check them manually.",
                           "বিক্রেতার মালিকানার উৎস-দলিল (পূর্ববর্তী দলিল, ওয়ারিশ সনদ) চেয়ে নিয়ে হাতে যাচাই করুন।"),
    "CITED_DEED_UNVERIFIABLE": ("Search the paper volumes at the Sub-Registry for the cited year.",
                                "সংশ্লিষ্ট বছরের জন্য সাব-রেজিস্ট্রি অফিসের কাগজের ভলিউমে তল্লাশি করুন।"),
    "COVERAGE_GAP": ("Treat any 'no conflict' result as unconfirmed for the gap period; search paper records.",
                     "ফাঁকের সময়ের জন্য 'দ্বন্দ্ব নেই' ফলাফলকে অনিশ্চিত ধরুন; কাগজের রেকর্ড তল্লাশি করুন।"),
    "AMBIGUOUS_REFERENCE": ("Ask the surveyor to confirm which current dag the deed covers.",
                            "দলিলটি কোন বর্তমান দাগের, তা সার্ভেয়ারের মাধ্যমে নিশ্চিত করুন।"),
    "UNIT_UNRESOLVED": ("Confirm the local size of the unit with the Union Land Office, then re-run the check.",
                        "ইউনিয়ন ভূমি অফিস থেকে এককের স্থানীয় মাপ নিশ্চিত করে আবার যাচাই করুন।"),
    "INHERITANCE_SHARES_INCOMPLETE": ("Obtain the complete heir list and shares before recording any heir.",
                                      "কোনো ওয়ারিশের নামজারির আগে সম্পূর্ণ ওয়ারিশ তালিকা ও অংশ সংগ্রহ করুন।"),
    "UNALLOCATED_SHARE": ("Find the other khatian(s) covering this dag before relying on balances.",
                          "ব্যালান্সের ওপর নির্ভর করার আগে এই দাগের অন্য খতিয়ান খুঁজে বের করুন।"),
    "INVALID_QUANTITY": ("Correct the quantity text and re-run the check.", "পরিমাণ সংশোধন করে আবার যাচাই করুন।"),
    "RECORD_LAG": ("The khatian is stale for this plot. Any buyer relying on it alone is at risk; encourage the "
                   "buyer to complete mutation.",
                   "এই দাগের খতিয়ান হালনাগাদ নয়। শুধু খতিয়ান দেখে কেনা ঝুঁকিপূর্ণ; ক্রেতাকে নামজারি সম্পন্ন করতে উৎসাহিত করুন।"),
    "RAPID_RESALE": ("Context only. Check consideration and identity documents as usual; this is not evidence of "
                     "wrongdoing by itself.",
                     "শুধু প্রেক্ষাপট। স্বাভাবিক নিয়মে মূল্য ও পরিচয়পত্র যাচাই করুন; এটি নিজে কোনো অনিয়মের প্রমাণ নয়।"),
}

FIELD_NAMES = {"seller": ("seller", "বিক্রেতা"), "buyer": ("buyer", "ক্রেতা"), "date": ("deed date", "দলিলের তারিখ"),
               "quantity": ("quantity", "পরিমাণ"), "plot": ("plot", "দাগ")}


def _name(names: dict, pid: str | None, lang: str) -> str:
    if not pid:
        return "?"
    person = names.get(pid)
    return person[lang] if person else pid


_BN_VOWEL_END = set("ািীুূৃেৈোৌঅআইঈউঊএঐওঔ")


def _genitive_bn(name: str) -> str:
    """Bangla possessive: নমুনা -> নমুনার, কাল্পনিক -> কাল্পনিকের."""
    return name + ("র" if name and name[-1] in _BN_VOWEL_END else "ের")


def status_text(status: str, lang: str = "en") -> str:
    en, bn = STATUS[status]
    return en if lang == "en" else bn


def title(code: str, lang: str = "en") -> str:
    en, bn = TITLES.get(code, (code, code))
    return en if lang == "en" else bn


def action(code: str, lang: str = "en") -> str:
    en, bn = ACTIONS.get(code, ("Review manually.", "হাতে যাচাই করুন।"))
    return en if lang == "en" else bn


def describe(f: Finding, names: dict, lang: str = "en") -> str:
    text = _describe_en(f, names) if lang == "en" else _describe_bn(f, names)
    return text if lang == "en" else to_bn_digits(text)


def _describe_en(f: Finding, names: dict) -> str:
    x = f.facts
    n = lambda pid: _name(names, pid, "en")  # noqa: E731
    match f.code:
        case "OVER_TRANSFER":
            if x["prior"]:
                earlier = "; ".join(f"{p['dec']} decimal to {n(p['buyer'])} by deed {p['deed_ref']} ({p['date']})"
                                    for p in x["prior"])
                return (f"{n(x['seller'])} held {x['held_dec']} decimal in this plot. Earlier transfers: {earlier}. "
                        f"That leaves {x['available_dec']} decimal, but deed {x['deed_ref']} transfers "
                        f"{x['requested_dec']} decimal to {n(x['buyer'])} — {x['shortfall_dec']} decimal more than "
                        f"remains.")
            return (f"{n(x['seller'])} held {x['held_dec']} decimal in this plot, but deed {x['deed_ref']} transfers "
                    f"{x['requested_dec']} decimal to {n(x['buyer'])} — {x['shortfall_dec']} decimal more than held.")
        case "DEED_NOT_IN_INDEX":
            return (f"Case {x['case_no']} cites {x['cited']}. The registry index covers that date for this mouza "
                    f"but has no such deed.")
        case "MUTATION_MISMATCH":
            fields = ", ".join(FIELD_NAMES[k][0] for k in x["fields"])
            extra = (f" Application: {x['case_quantity']}; deed: {x['deed_quantity']}."
                     if "quantity" in x["fields"] and x.get("deed_quantity") else "")
            return f"Case {x['case_no']} does not match {x['cited']} on: {fields}.{extra}"
        case "SHARE_TOTAL_MISMATCH":
            return (f"Shares recorded in {x['record_ref']} total {x['total']} of the plot — {x['excess_dec']} decimal "
                    f"more than exists.")
        case "UNALLOCATED_SHARE":
            return (f"Shares recorded in {x['record_ref']} total {x['total']}; {x['missing_dec']} decimal of the plot "
                    f"has no holder in the supplied records.")
        case "NO_RECORDED_SOURCE":
            via = x.get("deed_ref") or x.get("via")
            return (f"{n(x['person'])} transfers or inherits under {via}, but holds nothing in the supplied khatian, "
                    f"deeds or succession records for this plot.")
        case "CITED_DEED_UNVERIFIABLE":
            return (f"Case {x['case_no']} cites {x['cited']}, which is outside the period covered by the digital "
                    f"registry index. It can be neither confirmed nor ruled out here.")
        case "COVERAGE_GAP":
            return (f"The digital registry index has no coverage from {x['gap_start']} to {x['gap_end']}. Transfers "
                    f"in that period would not be visible, so balances cannot be confirmed.")
        case "AMBIGUOUS_REFERENCE":
            return (f"Deed {x['deed_ref']} describes the land as {x['plot_ref']}, which corresponds to "
                    f"{len(x['candidates'])} current plots ({', '.join(x['candidates'])}). The transfer was not applied "
                    f"to any of them.")
        case "UNIT_UNRESOLVED":
            return (f"The {x['what']} '{x['raw']}' uses {x['unit']}, whose size varies by area and is not configured "
                    f"for this mouza. It was not converted.")
        case "INHERITANCE_SHARES_INCOMPLETE":
            return (f"Succession record {x['certificate']} gives heir shares totalling {x['heir_total']}, not the whole "
                    f"estate of {n(x['deceased'])}. The inheritance was not applied.")
        case "INVALID_QUANTITY":
            return f"The {x['what']} '{x['raw']}' could not be read as a quantity."
        case "RECORD_LAG":
            pending = f" Mutation case {x['pending_case']} is still pending." if x.get("pending_case") else ""
            return (f"Deed {x['deed_ref']} was registered {x['days']} days ago and no approved mutation reflects it."
                    f"{pending}")
        case "RAPID_RESALE":
            return (f"{n(x['seller'])} resold by deed {x['deed_ref']} only {x['days']} days after acquiring via "
                    f"{x['acquired_via']}.")
    return f.code


def _describe_bn(f: Finding, names: dict) -> str:
    x = f.facts
    n = lambda pid: _name(names, pid, "bn")  # noqa: E731
    g = lambda pid: _genitive_bn(n(pid))  # noqa: E731
    match f.code:
        case "OVER_TRANSFER":
            if x["prior"]:
                earlier = "; ".join(f"দলিল {p['deed_ref']} ({p['date']}) মূলে {g(p['buyer'])} কাছে {p['dec']} শতাংশ"
                                    for p in x["prior"])
                return (f"এই দাগে {g(x['seller'])} মোট {x['held_dec']} শতাংশ ছিল। আগের হস্তান্তর: {earlier}। "
                        f"অবশিষ্ট থাকে {x['available_dec']} শতাংশ, কিন্তু দলিল {x['deed_ref']}-এ {g(x['buyer'])} কাছে "
                        f"{x['requested_dec']} শতাংশ হস্তান্তর দেখানো হয়েছে — অবশিষ্টের চেয়ে {x['shortfall_dec']} শতাংশ বেশি।")
            return (f"এই দাগে {g(x['seller'])} {x['held_dec']} শতাংশ ছিল, কিন্তু দলিল {x['deed_ref']}-এ "
                    f"{g(x['buyer'])} কাছে {x['requested_dec']} শতাংশ হস্তান্তর দেখানো হয়েছে — "
                    f"{x['shortfall_dec']} শতাংশ বেশি।")
        case "DEED_NOT_IN_INDEX":
            return (f"মামলা {x['case_no']}-এ {x['cited']} উল্লেখ আছে। ওই তারিখ এই মৌজার রেজিস্ট্রি সূচির আওতায় থাকলেও "
                    f"এমন কোনো দলিল সূচিতে নেই।")
        case "MUTATION_MISMATCH":
            fields = ", ".join(FIELD_NAMES[k][1] for k in x["fields"])
            extra = (f" আবেদন: {x['case_quantity']}; দলিল: {x['deed_quantity']}।"
                     if "quantity" in x["fields"] and x.get("deed_quantity") else "")
            return f"মামলা {x['case_no']} ও {x['cited']}-এর মধ্যে অমিল: {fields}।{extra}"
        case "SHARE_TOTAL_MISMATCH":
            return (f"{x['record_ref']}-এ রেকর্ডকৃত অংশের যোগফল দাগের {x['total']} — যা প্রকৃত জমির চেয়ে "
                    f"{x['excess_dec']} শতাংশ বেশি।")
        case "UNALLOCATED_SHARE":
            return (f"{x['record_ref']}-এ অংশের যোগফল {x['total']}; দাগের {x['missing_dec']} শতাংশের কোনো মালিক "
                    f"সরবরাহকৃত রেকর্ডে নেই।")
        case "NO_RECORDED_SOURCE":
            via = x.get("deed_ref") or x.get("via")
            return (f"{n(x['person'])} {via} মূলে হস্তান্তর বা উত্তরাধিকার দেখাচ্ছেন, কিন্তু এই দাগের সরবরাহকৃত খতিয়ান, "
                    f"দলিল বা ওয়ারিশ রেকর্ডে তাঁর কোনো অংশ নেই।")
        case "CITED_DEED_UNVERIFIABLE":
            return (f"মামলা {x['case_no']}-এ {x['cited']} উল্লেখ আছে, যা ডিজিটাল রেজিস্ট্রি সূচির সময়সীমার বাইরে। "
                    f"এখান থেকে এটি নিশ্চিত বা বাতিল করা যায় না।")
        case "COVERAGE_GAP":
            return (f"{x['gap_start']} থেকে {x['gap_end']} পর্যন্ত ডিজিটাল রেজিস্ট্রি সূচি নেই। ওই সময়ের হস্তান্তর দেখা "
                    f"যাবে না, তাই অংশের হিসাব নিশ্চিত নয়।")
        case "AMBIGUOUS_REFERENCE":
            return (f"দলিল {x['deed_ref']}-এ জমিকে {x['plot_ref']} হিসেবে বর্ণনা করা হয়েছে, যা বর্তমানে "
                    f"{len(x['candidates'])}টি দাগে বিভক্ত ({', '.join(x['candidates'])})। হস্তান্তরটি কোনো দাগে প্রয়োগ "
                    f"করা হয়নি।")
        case "UNIT_UNRESOLVED":
            return (f"'{x['raw']}' পরিমাণে {x['unit']} একক ব্যবহৃত হয়েছে, যার মাপ এলাকাভেদে ভিন্ন এবং এই মৌজার জন্য "
                    f"নির্ধারিত নেই। তাই রূপান্তর করা হয়নি।")
        case "INHERITANCE_SHARES_INCOMPLETE":
            return (f"ওয়ারিশ রেকর্ড {x['certificate']}-এ {g(x['deceased'])} ওয়ারিশদের অংশের যোগফল {x['heir_total']}, "
                    f"পূর্ণ নয়। উত্তরাধিকার প্রয়োগ করা হয়নি।")
        case "INVALID_QUANTITY":
            return f"'{x['raw']}' পরিমাণটি পড়া যায়নি।"
        case "RECORD_LAG":
            pending = f" নামজারি মামলা {x['pending_case']} এখনো অনিষ্পন্ন।" if x.get("pending_case") else ""
            return f"দলিল {x['deed_ref']} {x['days']} দিন আগে নিবন্ধিত, কিন্তু কোনো অনুমোদিত নামজারি নেই।{pending}"
        case "RAPID_RESALE":
            return (f"{n(x['seller'])} {x['acquired_via']} মূলে অর্জনের মাত্র {x['days']} দিন পর দলিল {x['deed_ref']} "
                    f"মূলে আবার বিক্রি করেছেন।")
    return f.code
