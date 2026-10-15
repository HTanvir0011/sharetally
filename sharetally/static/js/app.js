// ShareTally client script: language toggle, mobile menu, AI assist calls.
// All server text is inserted with textContent, never innerHTML.
(function () {
  "use strict";
  var root = document.documentElement;

  function store(key, value) {
    try { if (value === undefined) { return window.localStorage.getItem(key); } window.localStorage.setItem(key, value); }
    catch (e) { return null; }
    return null;
  }

  if (store("st-lang") === "bn") { root.classList.add("lang-bn"); }
  document.addEventListener("click", function (ev) {
    var t = ev.target.closest("[data-lang-toggle]");
    if (t) {
      root.classList.toggle("lang-bn");
      store("st-lang", root.classList.contains("lang-bn") ? "bn" : "en");
    }
    var m = ev.target.closest("[data-menu]");
    if (m) {
      var nav = document.getElementById("nav");
      var open = nav.classList.toggle("open");
      m.setAttribute("aria-expanded", open ? "true" : "false");
    }
  });

  var csrfMeta = document.querySelector('meta[name="csrf-token"]');
  var csrf = csrfMeta ? csrfMeta.getAttribute("content") : "";

  function postJSON(url, body) {
    return fetch(url, {
      method: "POST", credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
      body: JSON.stringify(body)
    }).then(function (r) {
      return r.json().then(function (data) { if (!r.ok) { throw new Error(data.error || ("HTTP " + r.status)); } return data; });
    });
  }

  // Reviewer: draft a plain-language notice for a case.
  var explainBtn = document.getElementById("explain-btn");
  if (explainBtn) {
    explainBtn.addEventListener("click", function () {
      var out = document.getElementById("explain-out");
      var meta = document.getElementById("explain-meta");
      explainBtn.disabled = true;
      meta.textContent = "Drafting…";
      postJSON("/api/assist/explain", { case_id: explainBtn.getAttribute("data-case") }).then(function (d) {
        out.querySelector("[data-bn]").textContent = d.bn;
        out.querySelector("[data-en]").textContent = d.en;
        out.hidden = false;
        meta.textContent = d.source === "ai"
          ? "AI draft (" + d.model + ") — passed checks: " + d.checks.join(", ") + ". Review before sending."
          : "Template text (deterministic). " + (d.reason || "");
      }).catch(function (e) { meta.textContent = "Could not draft: " + e.message; })
        .finally(function () { explainBtn.disabled = false; });
    });
  }

  // Clerk: extract deed fields from pasted text into the form (human confirms).
  var extractBtn = document.getElementById("extract-btn");
  if (extractBtn) {
    extractBtn.addEventListener("click", function () {
      var text = document.getElementById("deed-text").value;
      var meta = document.getElementById("extract-meta");
      extractBtn.disabled = true;
      meta.textContent = "Reading…";
      postJSON("/api/assist/extract", { text: text }).then(function (d) {
        var f = d.fields, form = document.getElementById("intake-form");
        function set(name, value) { if (value && form.elements[name]) { form.elements[name].value = value; } }
        set("deed_no", f.deed_no); set("deed_type", f.deed_type);
        set("execution_date", f.execution_date);
        set("registration_date", f.registration_date || f.execution_date);
        set("quantity", f.quantity);
        if (d.matches.plot_id) { set("plot_id", d.matches.plot_id); }
        if (d.matches.seller) { set("seller_id", d.matches.seller); }
        if (d.matches.buyer) { set("buyer_id", d.matches.buyer); }
        else if (f.buyer_name) { set("new_buyer_bn", f.buyer_name); }
        var bad = Object.keys(d.status).filter(function (k) { return d.status[k] !== "ok"; });
        meta.textContent = (d.source === "ai" ? "Read by AI (" + d.model + ")" : "Read by rule-based parser") +
          (d.reason ? " — " + d.reason : "") +
          ". Fields needing attention: " + (bad.length ? bad.join(", ") : "none") +
          ". Check every field before running the check.";
      }).catch(function (e) { meta.textContent = "Could not read: " + e.message; })
        .finally(function () { extractBtn.disabled = false; });
    });
  }
})();
