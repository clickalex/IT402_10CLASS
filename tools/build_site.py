#!/usr/bin/env python3
"""Build the IT-402 Unit 1 website from the repo's source study files.

CONTENT RULE (enforced by verify() below):
  * Every question, option, answer, explanation, table cell and notes line is
    copied VERBATIM from the source files into the new pages. Only shared site
    chrome (header/nav/footer/hero/toolbars) is added around it.
  * The only presentation-level fix: the quiz source repeats two section
    headings back-to-back (duplicate ids sec-u1b/sec-u1x); the site renders
    each heading once. No question/answer text is touched. The duplicate printable
    drill is retired.

Usage:  python3 tools/build_site.py
"""
import html as htmlmod
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = ROOT / "tools" / "templates"

# ---------------------------------------------------------------- sources
SRC = {
    "learn": ROOT / "01-Learn-Readable-Summary.html",
    "write": ROOT / "02-Write-Question-Bank.html",
    "quiz": ROOT / "03-Drill-140-MCQ-Quiz.html",
    "revise": ROOT / "04-Revise-Rapid-Sheet.html",
    "qbank": ROOT / "05-Book-Style-150Plus-QBank.html",
}

PAGES = {}  # name -> html, filled by builders


def read(p):
    return pathlib.Path(p).read_text(encoding="utf-8")


def body_inner(doc):
    m = re.search(r"<body[^>]*>(.*)</body>", doc, re.S)
    if not m:
        raise ValueError("no <body> found")
    return m.group(1)


def strip_frame_divs(body):
    """Remove xhtml2pdf frame artifacts (not content)."""
    body = re.sub(r'<div id="(header|footer)_content">.*?</div>\s*', "", body, flags=re.S)
    return body


# ------------------------------------------------------- block extractor
def scan_blocks(body):
    """Return [('h2', html) | ('q', qid, answer_or_None, inner_html)] in order."""
    tokens = []
    for m in re.finditer(r"<h2\b[^>]*>.*?</h2>", body, re.S):
        tokens.append((m.start(), "h2", m.group(0)))
    for m in re.finditer(r'<div class="q" id="([^"]+)"( data-answer="(\d+)")?>', body):
        tokens.append((m.start(), "q", m))
    tokens.sort(key=lambda t: t[0])
    out = []
    for _, kind, pay in tokens:
        if kind == "h2":
            out.append(("h2", pay))
            continue
        m = pay
        start = m.end()
        depth, idx = 1, start
        while depth > 0:
            nxt_open = body.find("<div", idx)
            nxt_close = body.find("</div>", idx)
            if nxt_close == -1:
                raise ValueError("unbalanced <div> for " + m.group(1))
            if nxt_open != -1 and nxt_open < nxt_close:
                depth += 1
                idx = body.find(">", nxt_open) + 1
            else:
                depth -= 1
                idx = nxt_close + len("</div>")
        inner = body[start: idx - len("</div>")]
        # Drop legacy inline handlers (the new shell binds its own listeners;
        # visible question/answer text is untouched).
        inner = re.sub(r' onclick="[^"]*"', "", inner)
        out.append(("q", m.group(1), m.group(3), inner))
    return out


def h2_title(h2html):
    return re.sub(r"<[^>]+>", "", h2html).strip()


def h2_id(h2html):
    m = re.search(r'id="([^"]+)"', h2html)
    return m.group(1) if m else None


INLINE_TAGS = "strong|em|b|i|span|a|label|code|button"


def norm_text(s):
    # Inline tags render without surrounding spaces ("<b>x</b>." -> "x.");
    # block-level tags act as separators.
    s = re.sub(r"</?(?:" + INLINE_TAGS + r")(?:\s[^>]*)?>", "", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = htmlmod.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


# ------------------------------------------------------------- shell
def shell(title, desc, page, body_html, pager_html=""):
    tpl = read(T / "_shell.html")
    return (
        tpl.replace("{{TITLE}}", title)
        .replace("{{DESC}}", desc)
        .replace("{{PAGE}}", page)
        .replace("{{BODY}}", body_html)
        .replace("{{PAGER}}", pager_html)
    )


def pager(prev=None, nxt=None):
    if not prev and not nxt:
        return ""
    parts = ['<div class="container reading"><nav class="pager" aria-label="Study cycle navigation">']
    if prev:
        parts.append(f'<a href="{prev[0]}"><span>← Previous step</span><b>{prev[1]}</b></a>')
    if nxt:
        parts.append(f'<a class="next" href="{nxt[0]}"><span>Next step →</span><b>{nxt[1]}</b></a>')
    parts.append("</nav></div>")
    return "\n".join(parts)


def crumbs(page_label):
    return (
        '<div class="container reading">'
        f'<nav aria-label="Breadcrumb" class="small" style="margin:14px 0 4px">'
        f'<a href="index.html">Home</a> › {page_label}</nav></div>'
    )


# ---------------------------------------------------------------- index
def build_index():
    body = read(T / "index_body.html")
    PAGES["index.html"] = shell(
        "Unit 1: Communication Skills–II — Complete Study Cycle",
        "IT-402 Class X Unit 1 complete study cycle: Learn summary, Write question bank, 140-MCQ drill, 1-page rapid revision sheet and 151 book-style Q&As. CBSE-verified.",
        "home",
        body,
    )


# ---------------------------------------------------------------- learn / write / revise (verbatim bodies)
def build_simple(src_key, out_name, page, crumb_label):
    raw = strip_frame_divs(body_inner(read(SRC[src_key]))).strip()
    scope = {"learn": "content-learn", "write": "content-write", "revise": "content-revise"}[page]
    extra = ""
    if page == "revise":
        # Turn each ☐ into a real (persisted) checkbox; text stays identical.
        n = [0]

        def repl(_m):
            n[0] += 1
            return (
                f'<label class="tick"><input type="checkbox" data-k="r{n[0]}" '
                f'aria-label="self-test item {n[0]}"></label>'
            )

        raw, count = re.subn("☐", repl, raw)
        print(f"  revise: {count} self-test boxes made checkable")
        extra = '<p class="small center" id="reviseMsg" aria-live="polite"></p>'
    body = crumbs(crumb_label) + f'\n<div class="container reading"><div class="{scope}">\n{raw}\n{extra}</div></div>'
    titles = {
        "learn": ("📖 LEARN — Unit 1 Summary (points & tables only)",
                  "Readable Unit 1 summary: 3 methods, 7-step cycle, feedback types, 7 barriers, 7 Cs, writing skills — points and tables only."),
        "write": ("✍️ WRITE — Unit 1 Question Bank (10 starter Q&As)",
                  "10 starter Q&As with model answers: 4 short + 2 long + 2 application + 2 case-study questions."),
        "revise": ("⚡ REVISE — Unit 1 in 1 Page (rapid sheet)",
                   "Whole Unit 1 on one page plus 60-second self-test. Read 3 times on exam morning."),
    }
    pagers = {
        "learn": pager(None, ("write.html", "✍️ Write — question bank")),
        "write": pager(("learn.html", "📖 Learn — summary"), ("drill.html", "🎯 Drill — 140 MCQs")),
        "revise": pager(("drill.html", "🎯 Drill — 140 MCQs"), ("qbank.html", "📝 Bank-151")),
    }
    PAGES[out_name] = shell(titles[page][0], titles[page][1], page, body, pagers[page])


# ---------------------------------------------------------------- drill (verbatim 140 MCQs)
SHORT_LABELS = [
    ("sec-u1a", "Book"), ("sec-u1b", "Extra"), ("sec-u1x", "Tricky"),
    ("sec-m2", "Methods-2"), ("sec-f2", "Feedback-2"), ("sec-b2", "Barriers-2"),
    ("sec-c2", "7Cs-2"), ("sec-w2", "Writing-2"),
]

HERO_DRILL = """<div class="page-hero">
  <div class="container">
    <div class="crumbs"><a href="index.html">Home</a> › 🎯 Drill</div>
    <h1>DRILL — 140 MCQs</h1>
    <p>Book (5) + Extra (15) + Tricky (20) + Methods-2 + Feedback-2 + Barriers-2 + 7Cs-2 + Writing-2 (20 each). Attempt first, then reveal. Your answers and progress are saved on this device.</p>
  </div>
</div>"""


def build_drill():
    blocks = scan_blocks(body_inner(read(SRC["quiz"])))
    # dedupe consecutive identical h2 (source repeats sec-u1b / sec-u1x headings)
    dedup = []
    for b in blocks:
        if b[0] == "h2" and dedup and dedup[-1][0] == "h2" and dedup[-1][1] == b[1]:
            print("  drill: dropped repeated heading:", h2_title(b[1])[:60])
            continue
        dedup.append(b)
    blocks = dedup

    sections, cur = [], None
    for b in blocks:
        if b[0] == "h2":
            cur = {"id": h2_id(b[1]), "title": h2_title(b[1]), "qs": []}
            sections.append(cur)
        else:
            _, qid, ans, inner = b
            cur["qs"].append((qid, ans, inner))
    print(f"  drill: {len(sections)} sections, {sum(len(s['qs']) for s in sections)} questions")

    jump = ['<div class="jump"><b>Jump to:</b> ']
    jump.append(" • ".join(
        f'<a href="#{sid}">{label}</a>' for sid, label in SHORT_LABELS))
    jump.append("</div>")

    opts = ['<option value="">All sections (140)</option>'] + [
        f'<option value="{s["id"]}">{htmlmod.escape(s["title"])} ({len(s["qs"])})</option>'
        for s in sections
    ]
    toolbar = f"""<div class="toolbar" role="search">
    <span class="score" id="score">Score: 0 / 0 revealed</span>
    <input type="search" id="qSearch" placeholder="Search questions…" aria-label="Search questions">
    <select id="secFilter" aria-label="Filter by section">{''.join(opts)}</select>
    <button class="btn-main" id="showAll" type="button">Show all answers</button>
    <button class="btn-line" id="hideAll" type="button">Hide all</button>
    <button id="resetAll" type="button" title="Clear saved answers on this device">Reset</button>
  </div>
  <div class="progress" aria-hidden="true"><div id="progressBar"></div></div>"""

    parts = [HERO_DRILL, '<div class="container reading">', toolbar, "".join(jump)]
    for s in sections:
        total = f'{len(s["qs"])} questions'
        parts.append(
            f'<h2 class="sec-head" id="{s["id"]}" data-sec="{s["id"]}">'
            f'{htmlmod.escape(s["title"])} <span class="count" data-total="{total}">{total}</span></h2>'
        )
        for qid, ans, inner in s["qs"]:
            parts.append(
                f'<div class="q" id="{qid}" data-answer="{ans}" data-sec="{s["id"]}">\n{inner}\n</div>'
            )
    parts.append('<div class="no-results" id="noResults">No questions match your search. Try simpler keywords (e.g. “feedback”, “barrier”, “article”).</div>')
    parts.append('<p class="small center">IT-402 • Unit 1 Drill (140 MCQs) • Attempt first, then reveal! ★</p>')
    parts.append("</div>")
    PAGES["drill.html"] = shell(
        "🎯 DRILL — 140 MCQs (interactive quiz)",
        "Interactive Unit 1 drill: 140 MCQs with hidden answers, score tracking, search and section filters.",
        "drill",
        "\n".join(parts),
        pager(("write.html", "✍️ Write — question bank"), ("revise.html", "⚡ Revise — rapid sheet")),
    )


# ---------------------------------------------------------------- qbank (verbatim 151 Q&As)
HERO_QBANK = """<div class="page-hero hero-bank">
  <div class="container">
    <div class="crumbs"><a href="index.html">Home</a> › 📝 Bank-151</div>
    <h1>BANK-151 — Book-Style Q&amp;As</h1>
    <p>45 Short + 32 Long + 37 Application + 37 Competency (incl. your book's exact questions ⭐) with hidden, click-to-reveal answers. Write each answer in a notebook WITHOUT seeing, then reveal &amp; self-mark (15–20/day).</p>
  </div>
</div>"""

TYPE_RE = re.compile(r'class="tag (tS|tL|tA|tC)"')
TYPE_NAMES = {"tS": "Short", "tL": "Long", "tA": "Application", "tC": "Competency"}


def build_qbank():
    blocks = scan_blocks(body_inner(read(SRC["qbank"])))
    sections, cur, n = [], None, 0
    for b in blocks:
        if b[0] == "h2":
            n += 1
            cur = {"id": f"qb{n}", "title": h2_title(b[1]), "qs": []}
            sections.append(cur)
        else:
            _, qid, _ans, inner = b
            m = TYPE_RE.search(inner)
            if not m:
                raise ValueError(f"no type tag in {qid}")
            cur["qs"].append((qid, m.group(1), "1" if "tBook" in inner else "0", inner))
    total = sum(len(s["qs"]) for s in sections)
    tcount = {}
    for s in sections:
        for _, t, _, _ in s["qs"]:
            tcount[t] = tcount.get(t, 0) + 1
    print(f"  qbank: {len(sections)} sections, {total} questions, types={tcount}")

    type_opts = ['<option value="">All types (151)</option>'] + [
        f'<option value="{k}">{TYPE_NAMES[k]} ({tcount.get(k, 0)})</option>'
        for k in ("tS", "tL", "tA", "tC")
    ]
    toolbar = f"""<div class="toolbar" role="search">
    <span class="score" id="count">0 / {total} revealed</span>
    <input type="search" id="qSearch" placeholder="Search questions…" aria-label="Search questions">
    <select id="typeFilter" aria-label="Filter by question type">{''.join(type_opts)}</select>
    <label class="small" style="display:inline-flex;align-items:center;gap:5px"><input type="checkbox" id="bookOnly"> ⭐ Book only</label>
    <button class="btn-main" id="showAll" type="button">Show all</button>
    <button class="btn-line" id="hideAll" type="button">Hide all</button>
  </div>
  <div class="progress" aria-hidden="true"><div id="progressBar"></div></div>"""
    jump = ['<div class="jump"><b>Jump to:</b> ']
    jump.append(" • ".join(
        f'<a href="#{s["id"]}">{htmlmod.escape(s["title"])}</a>' for s in sections))
    jump.append("</div>")

    parts = [HERO_QBANK, '<div class="container reading">', toolbar, "".join(jump)]
    for s in sections:
        total_s = f'{len(s["qs"])} questions'
        parts.append(
            f'<h2 class="sec-head" id="{s["id"]}" data-sec="{s["id"]}">'
            f'{htmlmod.escape(s["title"])} <span class="count" data-total="{total_s}">{total_s}</span></h2>'
        )
        for qid, t, book, inner in s["qs"]:
            parts.append(
                f'<div class="q" id="{qid}" data-type="{t}" data-book="{book}" data-sec="{s["id"]}">\n{inner}\n</div>'
            )
    parts.append('<div class="no-results" id="noResults">No questions match. Try simpler keywords or clear the filters.</div>')
    parts.append('<p class="small center">IT-402 • Unit 1 — 151 Book-Style Q&amp;As • Attempt first, then reveal ★</p>')
    parts.append("</div>")
    PAGES["qbank.html"] = shell(
        "📝 BANK-151 — 151 book-style Q&As",
        "151 book-style Q&As: 45 short + 32 long + 37 application + 37 competency with click-to-reveal answers, search and filters.",
        "qbank",
        "\n".join(parts),
        pager(("revise.html", "⚡ Revise — rapid sheet"), ("syllabus.html", "CBSE syllabus alignment")),
    )


# ---------------------------------------------------------------- syllabus
def build_syllabus():
    body = read(T / "syllabus_body.html")
    PAGES["syllabus.html"] = shell(
        "CBSE Syllabus Alignment — Unit 1",
        "How the Unit 1 content maps to the official CBSE Employability Skills-X Learning Outcomes.",
        "syllabus",
        body,
        pager(("qbank.html", "📝 Bank-151"), ("index.html", "🏠 Back to home")),
    )


# ---------------------------------------------------------------- verify
def verify():
    errors = []

    def check(cond, msg):
        print(("  ✓ " if cond else "  ✗ FAIL: ") + msg)
        if not cond:
            errors.append(msg)

    # --- drill: 140 blocks, verbatim text, answers intact
    src_quiz = read(SRC["quiz"])
    src_blocks = [b for b in scan_blocks(body_inner(src_quiz)) if b[0] == "q"]
    page = PAGES["drill.html"]
    check(len(src_blocks) == 140, f"quiz source has 140 questions (got {len(src_blocks)})")
    check(page.count('class="q"') == 140, "drill.html renders 140 questions")
    check(page.count('class="opt"') == 560, "drill.html renders 560 options")
    missing = [qid for _, qid, _a, inner in src_blocks if norm_text(inner) not in norm_text(page)]
    check(not missing, f"all 140 question texts verbatim in drill.html (missing: {missing[:3]})")
    for _, qid, ans, _ in src_blocks:
        if f'id="{qid}" data-answer="{ans}"' not in page:
            missing.append(qid)
    check(len(missing) == 0, "all 140 answer keys intact")

    # --- qbank: 151 blocks, verbatim text
    src_qb = read(SRC["qbank"])
    qb_blocks = [b for b in scan_blocks(body_inner(src_qb)) if b[0] == "q"]
    qpage = PAGES["qbank.html"]
    check(len(qb_blocks) == 151, f"qbank source has 151 Q&As (got {len(qb_blocks)})")
    check(qpage.count('class="q"') == 151, "qbank.html renders 151 Q&As")
    qmissing = [qid for _, qid, _a, inner in qb_blocks if norm_text(inner) not in norm_text(qpage)]
    check(not qmissing, f"all 151 Q&A texts verbatim in qbank.html (missing: {qmissing[:3]})")
    for tag, want in (("tS", 45), ("tL", 32), ("tA", 37), ("tC", 37)):
        got = qpage.count(f'data-type="{tag}"')
        check(got == want, f"qbank type {tag}: {got}/{want}")
    src_book = sum(b[3].count("tBook") for b in qb_blocks)  # old <style> def excluded
    check(src_book == qpage.count("tBook"),
          f"book-exact ⭐ flags preserved ({src_book} in questions)")

    # --- learn / write / revise: body text containment
    for key, out in (("learn", "learn.html"), ("write", "write.html"),
                     ("revise", "revise.html")):
        src_txt = norm_text(strip_frame_divs(body_inner(read(SRC[key]))))
        # revise ☐ became checkboxes: drop them from comparison (re-collapse)
        src_txt = re.sub(r"\s+", " ", src_txt.replace("☐", " ")).strip()
        out_txt = re.sub(r"\s+", " ", norm_text(PAGES[out]).replace("☐", " ")).strip()
        # compare in chunks to localise any drift
        words, win, bad = src_txt.split(" "), 60, 0
        for k in range(0, len(words), win):
            if " ".join(words[k:k + win]) not in out_txt:
                bad += 1
        check(bad == 0, f"{out}: source text fully contained ({len(words)} words, {bad} drifted chunks)")

    # --- forbidden strings (audit guarantees)
    for name, html in PAGES.items():
        check("8 parts of speech" not in html, f"{name}: no '8 parts of speech'")
        check("pdf-frame" not in html and "DejaVu" not in html, f"{name}: no print-frame leftovers")

    # --- write page: 10 Q&As
    check(PAGES["write.html"].count('class="ansbox"') == 10, "write.html renders 10 starter Q&As")

    if errors:
        print(f"\nVERIFY FAILED: {len(errors)} error(s)")
        sys.exit(1)
    print("\nAll content checks passed ✔")


# ---------------------------------------------------------------- main
def main():
    print("Building site from:", ROOT)
    build_index()
    build_simple("learn", "learn.html", "learn", "📖 Learn")
    build_simple("write", "write.html", "write", "✍️ Write")
    build_drill()
    build_simple("revise", "revise.html", "revise", "⚡ Revise")
    build_qbank()
    build_syllabus()
    PAGES["404.html"] = shell("Page not found", "Return to the study cycle.", "404", '<div class="container reading section"><h1>404 — Page not found</h1><p>This page does not exist. Continue your study cycle below.</p><a class="btn btn-brand" href="index.html">Back to home</a></div>')
    print("Verifying…")
    verify()
    for name, html in PAGES.items():
        (ROOT / name).write_text(html, encoding="utf-8")
        print(f"  wrote {name} ({len(html)//1024} KB)")
    print("Done.")


if __name__ == "__main__":
    main()
