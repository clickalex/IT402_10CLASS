# Unit 1: Communication Skills–II — Complete Study Cycle
### IT-402 Class X | Part A (2 marks) | HTML + Markdown only (no PDFs)

## The 4-step cycle (follow in order)

| Step | File | What to do |
|---|---|---|
| 📖 **LEARN** | `01-Learn-Readable-Summary.html` | Points/tables only. Read once → cover → recall aloud |
| ✍️ **WRITE** | `02-Write-Question-Bank.html` | 10 starter Q&As: 4 short + 2 long + 2 application + 2 case-study. Cover answers → write → compare |
| 🎯 **DRILL** | `03-Drill-140-MCQ-Quiz.html` + `03-Drill-140-MCQ-Printable.html` | **140 MCQs**: Book 5 + Extra 15 + Tricky 20 + Methods-2 20 + Feedback-2 20 + Barriers-2 20 + 7Cs-2 20 + Writing-2 20. Interactive + printable with key. Target **125+/140** |
| ⚡ **REVISE** | `04-Revise-Rapid-Sheet.html` | Whole unit on 1 page + 60-sec self-test. Read 3× on exam morning |
| 📝 **BANK-151** | `05-Book-Style-150Plus-QBank.html` + `05-Book-Style-150Plus-QBank.md` | **151 book-style Q&As**: 45 Short + 32 Long + 37 Application + 37 Competency (incl. your book's exact questions ⭐) with hidden/click-to-reveal answers |
| 📚 Reference | `00-Reference-Detailed-Notes.md` | Full deep notes, only if a topic feels weak |

## Book topics covered (all 5)
1. Methods of Communication • 2. Feedback in Communication Cycle • 3. Overcoming Barriers • 4. Principles (7 Cs) • 5. Basic Writing Skills

## Targets
- Drill: 125–140 = Excellent • 110–124 = Good • Below 110 = re-learn, then retry
- Bank-151: write answers in a notebook WITHOUT seeing, then reveal & self-mark (do 15–20/day)
- Rapid sheet: all 8 checkboxes from memory = 2/2 in exam

> All `.html` files work offline — open in any browser. `.md` files are plain-text notes.

---

## 🌐 Website (added 10 Sept 2026)

Open **`index.html`** in any browser — or serve the folder (`python3 -m http.server 8000`) and visit `http://localhost:8000`. Fully offline (the only external links are the two official CBSE references on the Syllabus page).

| Page | Source file (copied **verbatim**) |
|---|---|
| `index.html` — home + study cycle | `README.md` (navigation text) |
| `learn.html` | `01-Learn-Readable-Summary.html` |
| `write.html` | `02-Write-Question-Bank.html` |
| `drill.html` — interactive 140-MCQ quiz (score, search, section filter, saved progress) | `03-Drill-140-MCQ-Quiz.html` |
| `drill-print.html` — printable 140 MCQs + key | `03-Drill-140-MCQ-Printable.html` |
| `revise.html` — rapid sheet (checkable self-test) | `04-Revise-Rapid-Sheet.html` |
| `qbank.html` — 151 Q&As (search, type filter, ⭐ book-only) | `05-Book-Style-150Plus-QBank.html` |
| `reference.html` — detailed notes | `00-Reference-Detailed-Notes.md` |
| `syllabus.html` — CBSE alignment | `AUDIT-REPORT.md` + official CBSE curriculum |

**Content integrity:** `tools/build_site.py` copies every question, option, answer, explanation and notes line verbatim and then verifies it (140/140 drill texts + keys, 151/151 Q&A texts, type counts 45/32/37/37, 14 ⭐ flags, full text containment for Learn/Write/Revise/Print/Reference, zero "8 parts of speech"). CBSE re-checked on build date against the [official curriculum PDF](https://cbseacademic.nic.in/web_material/Curriculum26/sec/EmployabilitySkills_X.pdf) — the 5 topics match the 5 Learning Outcomes exactly. Only presentation-level touches: shared nav, search/filter tools, dark mode, printable view. One dedupe: the quiz source repeats two section headings back-to-back (duplicate ids); the site renders each once. **Original `00–05` files are unmodified.**

**Rebuild:** `python3 tools/build_site.py` (regenerates all 9 pages from sources; fails loudly if any content drifts).
