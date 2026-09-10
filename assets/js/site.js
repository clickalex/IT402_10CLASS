/* IT-402 Unit 1 site JS — vanilla, offline. Nav + theme + quiz/bank engines + checklist. */
(function () {
  "use strict";

  /* ---------- storage helper (fails safe in private mode) ---------- */
  var store = {
    get: function (k, d) {
      try { var v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); }
      catch (e) { return d; }
    },
    set: function (k, v) {
      try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* ignore */ }
    },
    del: function (k) { try { localStorage.removeItem(k); } catch (e) { /* ignore */ } }
  };

  /* ---------- theme ---------- */
  var themeBtn = document.getElementById("themeBtn");
  function applyTheme(t) {
    document.documentElement.setAttribute("data-theme", t);
    if (themeBtn) themeBtn.textContent = t === "dark" ? "☀️" : "🌙";
  }
  var savedTheme = store.get("it402-theme", null);
  if (savedTheme === "dark" || savedTheme === "light") { applyTheme(savedTheme); }
  else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) { applyTheme("dark"); }
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      applyTheme(next); store.set("it402-theme", next);
    });
  }

  /* ---------- mobile nav ---------- */
  var navToggle = document.getElementById("navToggle");
  var mainNav = document.getElementById("mainNav");
  if (navToggle && mainNav) {
    navToggle.addEventListener("click", function () {
      var open = mainNav.classList.toggle("open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    mainNav.addEventListener("click", function (e) {
      if (e.target.tagName === "A") mainNav.classList.remove("open");
    });
  }

  var page = document.body.getAttribute("data-page") || "";

  /* ================= DRILL (140 MCQ quiz) ================= */
  if (page === "drill") {
    var KEY_SEL = "it402-drill-sel-v1";
    var KEY_REV = "it402-drill-rev-v1";
    var sels = store.get(KEY_SEL, {});
    var revs = store.get(KEY_REV, {});
    var qs = Array.prototype.slice.call(document.querySelectorAll(".q"));
    var scoreEl = document.getElementById("score");
    var progEl = document.getElementById("progressBar");
    var searchEl = document.getElementById("qSearch");
    var secEl = document.getElementById("secFilter");
    var noRes = document.getElementById("noResults");
    var countEls = document.querySelectorAll(".sec-head .count");

    function isRevealed(q) { return q.querySelector(".ans").style.display === "block"; }

    function paintOne(q, show) {
      var ans = q.querySelector(".ans");
      var btn = q.querySelector(".reveal");
      var correct = q.getAttribute("data-answer");
      if (show) {
        ans.style.display = "block";
        if (btn) btn.textContent = "Hide Answer";
        q.querySelectorAll(".opt").forEach(function (b) {
          b.classList.remove("correct", "wrong");
          if (b.getAttribute("data-i") === correct) b.classList.add("correct");
          else if (b.classList.contains("sel")) b.classList.add("wrong");
        });
      } else {
        ans.style.display = "none";
        if (btn) btn.textContent = "Show Answer";
        q.querySelectorAll(".opt").forEach(function (b) { b.classList.remove("correct", "wrong"); });
      }
    }

    function updateScore() {
      var got = 0, revealed = 0, answered = 0;
      qs.forEach(function (q) {
        var sel = q.querySelector(".opt.sel");
        if (sel) answered++;
        if (isRevealed(q)) {
          revealed++;
          if (sel && sel.getAttribute("data-i") === q.getAttribute("data-answer")) got++;
        }
      });
      if (scoreEl) scoreEl.textContent = "Score: " + got + " / " + revealed + " revealed • " + answered + " / " + qs.length + " answered";
      if (progEl) progEl.style.width = Math.round((revealed / qs.length) * 100) + "%";
    }

    qs.forEach(function (q) {
      var id = q.id;
      // restore selection
      if (sels[id] !== undefined) {
        var btn = q.querySelector('.opt[data-i="' + sels[id] + '"]');
        if (btn) btn.classList.add("sel");
      }
      q.querySelectorAll(".opt").forEach(function (b) {
        b.addEventListener("click", function () {
          q.querySelectorAll(".opt").forEach(function (x) { x.classList.remove("sel"); });
          b.classList.add("sel");
          sels[id] = b.getAttribute("data-i");
          store.set(KEY_SEL, sels);
          if (isRevealed(q)) paintOne(q, true); // refresh right/wrong paint
          updateScore();
        });
      });
      var r = q.querySelector(".reveal");
      if (r) {
        r.addEventListener("click", function () {
          var show = !isRevealed(q);
          paintOne(q, show);
          if (show) revs[id] = 1; else delete revs[id];
          store.set(KEY_REV, revs);
          updateScore();
        });
      }
      if (revs[id]) paintOne(q, true);
    });

    document.getElementById("showAll").addEventListener("click", function () {
      qs.forEach(function (q) { paintOne(q, true); revs[q.id] = 1; });
      store.set(KEY_REV, revs); updateScore();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
    document.getElementById("hideAll").addEventListener("click", function () {
      qs.forEach(function (q) { paintOne(q, false); });
      revs = {}; store.set(KEY_REV, revs); updateScore();
    });
    document.getElementById("resetAll").addEventListener("click", function () {
      if (!window.confirm("Reset all answers and revealed states on this device?")) return;
      sels = {}; revs = {};
      store.del(KEY_SEL); store.del(KEY_REV);
      qs.forEach(function (q) {
        q.querySelectorAll(".opt").forEach(function (b) { b.classList.remove("sel"); });
        paintOne(q, false);
      });
      updateScore();
    });

    function applyFilter() {
      var term = (searchEl.value || "").trim().toLowerCase();
      var sec = secEl.value;
      var visible = 0;
      var perSec = {};
      qs.forEach(function (q) {
        var okSec = !sec || q.getAttribute("data-sec") === sec;
        var okTerm = !term || q.textContent.toLowerCase().indexOf(term) !== -1;
        var show = okSec && okTerm;
        q.classList.toggle("hidden", !show);
        if (show) { visible++; var s = q.getAttribute("data-sec"); perSec[s] = (perSec[s] || 0) + 1; }
      });
      document.querySelectorAll(".sec-head").forEach(function (h) {
        var id = h.getAttribute("data-sec");
        var show = !sec || sec === id;
        // hide section head if its questions are all filtered out by search
        if (term && !perSec[id]) show = false;
        h.style.display = show ? "" : "none";
        var c = h.querySelector(".count");
        if (c && (term || sec)) c.textContent = "showing " + (perSec[id] || 0);
        else if (c) c.textContent = c.getAttribute("data-total") || "";
      });
      if (noRes) noRes.style.display = visible ? "none" : "block";
    }
    if (searchEl) searchEl.addEventListener("input", applyFilter);
    if (secEl) secEl.addEventListener("change", applyFilter);
    updateScore();
  }

  /* ================= QBANK (151 Q&As) ================= */
  if (page === "qbank") {
    var KEY_QR = "it402-qbank-rev-v1";
    var qrevs = store.get(KEY_QR, {});
    var bqs = Array.prototype.slice.call(document.querySelectorAll(".q"));
    var countEl = document.getElementById("count");
    var bSearch = document.getElementById("qSearch");
    var typeEl = document.getElementById("typeFilter");
    var bookEl = document.getElementById("bookOnly");
    var bNoRes = document.getElementById("noResults");

    function bRevealed(q) { return q.querySelector(".ans").style.display === "block"; }
    function bPaint(q, show) {
      q.querySelector(".ans").style.display = show ? "block" : "none";
      var r = q.querySelector(".reveal");
      if (r) r.textContent = show ? "Hide Answer" : "Show Answer";
    }
    function bCount() {
      var n = 0;
      bqs.forEach(function (q) { if (bRevealed(q)) n++; });
      if (countEl) countEl.textContent = n + " / " + bqs.length + " revealed";
      var pb = document.getElementById("progressBar");
      if (pb) pb.style.width = Math.round((n / bqs.length) * 100) + "%";
    }

    bqs.forEach(function (q) {
      var r = q.querySelector(".reveal");
      if (r) {
        r.addEventListener("click", function () {
          var show = !bRevealed(q);
          bPaint(q, show);
          if (show) qrevs[q.id] = 1; else delete qrevs[q.id];
          store.set(KEY_QR, qrevs); bCount();
        });
      }
      if (qrevs[q.id]) bPaint(q, true);
    });
    document.getElementById("showAll").addEventListener("click", function () {
      bqs.forEach(function (q) { bPaint(q, true); qrevs[q.id] = 1; });
      store.set(KEY_QR, qrevs); bCount();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
    document.getElementById("hideAll").addEventListener("click", function () {
      bqs.forEach(function (q) { bPaint(q, false); });
      qrevs = {}; store.set(KEY_QR, qrevs); bCount();
    });

    function bFilter() {
      var term = (bSearch.value || "").trim().toLowerCase();
      var type = typeEl.value; // "", S, L, A, C
      var book = bookEl.checked;
      var visible = 0;
      var perSec = {};
      bqs.forEach(function (q) {
        var okT = !type || q.getAttribute("data-type") === type;
        var okB = !book || q.getAttribute("data-book") === "1";
        var okS = !term || q.textContent.toLowerCase().indexOf(term) !== -1;
        var show = okT && okB && okS;
        q.classList.toggle("hidden", !show);
        if (show) { visible++; var s = q.getAttribute("data-sec"); perSec[s] = (perSec[s] || 0) + 1; }
      });
      document.querySelectorAll(".sec-head").forEach(function (h) {
        var id = h.getAttribute("data-sec");
        var showH = (perSec[id] || 0) > 0;
        h.style.display = showH ? "" : "none";
        var c = h.querySelector(".count");
        if (c && (term || type || book)) c.textContent = "showing " + (perSec[id] || 0);
        else if (c) c.textContent = c.getAttribute("data-total") || "";
      });
      if (bNoRes) bNoRes.style.display = visible ? "none" : "block";
    }
    if (bSearch) bSearch.addEventListener("input", bFilter);
    if (typeEl) typeEl.addEventListener("change", bFilter);
    if (bookEl) bookEl.addEventListener("change", bFilter);
    bCount();
  }

  /* ================= REVISE checklist (persisted) ================= */
  if (page === "revise") {
    var KEY_R = "it402-revise-v1";
    var ticks = store.get(KEY_R, {});
    var boxes = document.querySelectorAll(".content-revise input[type='checkbox'][data-k]");
    boxes.forEach(function (b) {
      if (ticks[b.getAttribute("data-k")]) b.checked = true;
      b.addEventListener("change", function () {
        ticks[b.getAttribute("data-k")] = b.checked ? 1 : 0;
        store.set(KEY_R, ticks);
        var done = 0;
        boxes.forEach(function (x) { if (x.checked) done++; });
        var msg = document.getElementById("reviseMsg");
        if (msg) {
          msg.textContent = done === boxes.length && boxes.length
            ? "All " + done + " ✓ — Unit 1 mastered, 2/2 in exam. ★"
            : done + " / " + boxes.length + " recalled — keep going!";
        }
      });
    });
  }
})();
