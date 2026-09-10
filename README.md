# IT-402 Class X — Communication Skills–II

A static study guide covering the five Unit 1 topics through learning, writing,
practice questions and revision. Start at **index.html**.

## Study cycle

| Page | Contents |
|---|---|
| `learn.html` | Readable summary with points and tables |
| `write.html` | 10 starter questions and model answers |
| `drill.html` | 140 interactive MCQs; scoring, search, section filter and saved progress |
| `revise.html` | Rapid revision sheet and eight saved self-test checkboxes |
| `qbank.html` | 151 Q&As; search, type filter and book-question filter |
| `reference.html` | Detailed notes, six expanded deep-dive/workshop sections, worked examples and exam guidance |
| `syllabus.html` | Curriculum alignment and official references |

The duplicate printable drill has been removed from the study cycle. Its two old
URLs redirect to `drill.html` so bookmarks do not break. The interactive question
set, 560 options and answer keys are unchanged.

## English, Hindi and Hinglish

Use the **language selector in the header**, including on mobile and the 404 page.
The choice persists across pages when browser storage is available. Switching does
not reset answers, revealed states, search/filter values, checkboxes or theme.

- English is the original content and works offline.
- Hindi uses automatic translation. Hinglish uses the provider's Roman Hindi
  output, which can retain English technical terms; it is not a human-authored
  conversational adaptation.
- First-time translations need an internet connection to Google's public
  translation endpoint (`translate.googleapis.com`). Only public page text is
  sent; typed searches and the student's selected answers are not sent.
- Page text, questions, options, hidden explanations, navigation, tooltips and
  accessibility labels are included. Filenames/code and the language selector's
  native labels remain unchanged.
- Completed translations are cached on the device for both languages. Storage
  limits/private mode may prevent persistent caching. Uncached pages still need
  internet. No remote translation script or API credentials are used.
- Progress and a retryable error notice are visible. If the service is blocked,
  rate-limited or unavailable, untranslated material stays in English; selecting
  English immediately restores the original. The third-party public endpoint has
  no availability guarantee.
- Automatic translations are study aids, **not official CBSE translations**.
  Check grammar examples, technical terms and answers against the English
  original; automatic translation can alter language-specific examples.

## Serve and rebuild

```sh
python3 -m http.server 8000 --bind 0.0.0.0
python3 tools/build_site.py
```

The builder regenerates nine site pages and the two redirect stubs. Edit shared
markup in `tools/templates/`, presentation in `assets/css/site.css`, behaviour in
`assets/js/`, and detailed notes in `00-Reference-Detailed-Notes.md`.
The numbered HTML files (other than the retired printable file) are archived
English source materials, not the shared-shell website.

The build verifies all 140 MCQs and answer keys, 151 Q&As (45 short, 32 long,
37 application, 37 competency), 14 book flags, all 10 starter answers, and full
English source-text containment for Learn, Write, Revise and Reference. Existing
source question/answer text remains intact; the reference source was expanded.

## Browser regression checks

```sh
pip install playwright
playwright install chromium
# With the static server running:
python3 tools/test_site.py
# Alternatively set CHROMIUM_PATH to an existing Chromium executable.
```

Checks cover all nine pages at 320, 375, 768, 1024 and 1440 pixels in all three
language modes (135 layout combinations), original English restoration,
mobile-menu keyboard handling, retained quiz/bank state, saved checkboxes,
language preference, cached switching, service failure and old-URL redirects.
Translation network responses are mocked with expanded text for deterministic
layout/behaviour tests; they do not certify live provider availability or
translation accuracy. No runtime build system or package installation is needed
to use the website.
