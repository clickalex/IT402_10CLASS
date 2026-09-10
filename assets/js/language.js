/* Automatic page translation. Public study text only; no typed search text or answers
 * are sent. The English DOM is the source of truth; nodes and event handlers survive.
 * Cache is local to this device. No keys, remote scripts or framework required. */
(function () {
  'use strict';
  var selected = 'en', generation = 0, controller;
  var originals = new WeakMap(), records = [], observer, select, notice, status, retry;
  var CACHE_KEY = 'it402-translations-v1';
  var cache = Object.create(null);
  try {
    var savedCache = JSON.parse(localStorage.getItem(CACHE_KEY) || '{}');
    if (savedCache && typeof savedCache === 'object' && !Array.isArray(savedCache)) {
      Object.keys(savedCache).forEach(function (key) {
        var entry = savedCache[key];
        if (entry && typeof entry.hi === 'string' && typeof entry.hinglish === 'string') cache[key] = entry;
      });
    }
  } catch (_) {}
  var ui = {
    'Home': ['होम', 'Home'],
    '📖 Learn': ['📖 सीखें', '📖 Seekhein'],
    '✍️ Write': ['✍️ लिखें', '✍️ Likhein'],
    '🎯 Drill': ['🎯 अभ्यास', '🎯 Practice'],
    '⚡ Revise': ['⚡ दोहराएँ', '⚡ Revision'],
    '📝 Bank-151': ['📝 प्रश्न बैंक-151', '📝 Question Bank-151'],
    '📚 Notes': ['📚 विस्तृत नोट्स', '📚 Detailed Notes'],
    'Syllabus': ['पाठ्यक्रम', 'Syllabus'],
    'Show Answer': ['उत्तर दिखाएँ', 'Answer dikhayein'],
    'Hide Answer': ['उत्तर छिपाएँ', 'Answer chhupayein'],
    'Show all answers': ['सभी उत्तर दिखाएँ', 'Saare answers dikhayein'],
    'Show all': ['सभी उत्तर दिखाएँ', 'Saare answers dikhayein'],
    'Hide all': ['सभी उत्तर छिपाएँ', 'Saare answers chhupayein'],
    'Reset': ['रीसेट करें', 'Reset karein'],
    'Search questions…': ['प्रश्न खोजें…', 'Questions khojein…'],
    'Search questions': ['प्रश्न खोजें', 'Questions khojein'],
    'Filter by section': ['खंड के अनुसार छाँटें', 'Section ke hisaab se filter karein'],
    'Filter by type': ['प्रकार के अनुसार छाँटें', 'Type ke hisaab se filter karein'],
    'Open menu': ['मेन्यू खोलें', 'Menu kholein'],
    'Close menu': ['मेन्यू बंद करें', 'Menu band karein'],
    'Toggle dark mode': ['डार्क मोड बदलें', 'Dark mode badlein'],
    'Dark / light mode': ['डार्क / लाइट मोड', 'Dark / light mode'],
    'Skip to content': ['मुख्य सामग्री पर जाएँ', 'Main content par jayein'],
    'Reset all answers and revealed states on this device?': ['क्या इस डिवाइस पर सभी चुने हुए और दिखाए गए उत्तर रीसेट करें?', 'Is device par saare selected aur revealed answers reset karein?']
  };
  function known(text, lang) {
    if (lang === 'en') return text;
    var i = lang === 'hi' ? 0 : 1;
    if (Object.prototype.hasOwnProperty.call(ui, text)) return ui[text][i];
    var m;
    if ((m = text.match(/^Score: (\d+) \/ (\d+) revealed • (\d+) \/ (\d+) answered$/)))
      return lang === 'hi' ? 'स्कोर: ' + m[1] + ' / ' + m[2] + ' उत्तर दिखाए • ' + m[3] + ' / ' + m[4] + ' हल किए' : 'Score: ' + m[1] + ' / ' + m[2] + ' answers dikhaye • ' + m[3] + ' / ' + m[4] + ' attempt kiye';
    if ((m = text.match(/^(\d+) \/ (\d+) revealed$/))) return m[1] + ' / ' + m[2] + (lang === 'hi' ? ' उत्तर दिखाए' : ' answers dikhaye');
    if ((m = text.match(/^showing (\d+)$/))) return (lang === 'hi' ? 'दिखाए गए: ' : 'Dikh rahe hain: ') + m[1];
    if ((m = text.match(/^(\d+) questions$/))) return m[1] + (lang === 'hi' ? ' प्रश्न' : ' questions');
    if ((m = text.match(/^(\d+) \/ (\d+) recalled — keep going!$/))) return m[1] + ' / ' + m[2] + (lang === 'hi' ? ' याद हैं — अभ्यास जारी रखें!' : ' yaad hain — practice jaari rakhein!');
    if ((m = text.match(/^All (\d+) ✓ — Unit 1 mastered, 2\/2 in exam\. ★$/))) return lang === 'hi' ? 'सभी ' + m[1] + ' ✓ — पुनरावृत्ति पूरी! अभ्यास जारी रखें। ★' : 'Saare ' + m[1] + ' ✓ — revision complete! Practice jaari rakhein. ★';
    return null;
  }
  function t(text) { return known(text, selected) || text; }
  window.it402Language = { t: t, current: function () { return selected; } };
  function excluded(el) { return !el || el.closest('script, style, code, [translate="no"], #languageNotice'); }
  function capture(root) {
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    var node;
    while ((node = walker.nextNode())) {
      if (excluded(node.parentElement) || originals.has(node)) continue;
      var text = node.nodeValue;
      if (!/[a-zA-Z]/.test(text)) continue;
      var rec = { node: node, source: text, last: text };
      originals.set(node, rec); records.push(rec);
    }
    root.querySelectorAll('[placeholder], [aria-label], [title]').forEach(function (el) {
      if (excluded(el) || el.dataset.languageCaptured) return;
      el.dataset.languageCaptured = '1';
      ['placeholder', 'aria-label', 'title'].forEach(function (attr) {
        var text = el.getAttribute(attr);
        if (text && /[a-zA-Z]/.test(text)) records.push({ node: el, attr: attr, source: text, last: text });
      });
    });
  }
  function translation(source) {
    var text = source.trim();
    if (selected === 'en') return source;
    var result = known(text, selected);
    if (result === null && cache[text]) result = cache[text][selected];
    return result ? source.replace(text, function () { return result; }) : source;
  }
  function render() {
    if (observer) observer.disconnect();
    records = records.filter(function (rec) {
      if (!rec.node.isConnected) return false;
      var result = translation(rec.source);
      if (rec.attr) {
        if (rec.node.getAttribute(rec.attr) !== result) rec.node.setAttribute(rec.attr, result);
      } else if (rec.node.nodeValue !== result) rec.node.nodeValue = result;
      rec.last = result;
      return true;
    });
    if (observer) observer.observe(document.body, { childList: true, subtree: true, characterData: true });
  }
  function save() {
    try { localStorage.setItem(CACHE_KEY, JSON.stringify(cache)); } catch (_) { /* Memory cache still works if quota/storage is unavailable. */ }
  }
  function message(kind, done, total) {
    var hi = selected === 'hi';
    notice.hidden = selected === 'en';
    if (kind === 'loading') status.textContent = hi
      ? 'स्वचालित अनुवाद: ' + done + '/' + total + ' अंश तैयार। पहली बार इंटरनेट चाहिए। अंग्रेज़ी व्याकरण के उदाहरण जाँचें।'
      : 'Automatic translation: ' + done + '/' + total + ' parts ready. Pehli baar internet chahiye. English grammar examples ko original se check karein.';
    if (kind === 'complete') status.textContent = hi
      ? 'स्वचालित हिंदी अनुवाद • यह आधिकारिक अनुवाद नहीं है। व्याकरण के उदाहरण और उत्तर मूल अंग्रेज़ी से जाँचें। इस डिवाइस पर अनुवाद सहेजे जाते हैं, यदि ब्राउज़र अनुमति दे।'
      : 'Automatic Hinglish (Roman Hindi) • Official translation nahi hai. Grammar examples aur answers original English se check karein. Browser allow kare toh translations is device par save hote hain.';
    if (kind === 'error') status.textContent = hi
      ? 'कुछ सामग्री का अनुवाद नहीं हो सका; वह अंग्रेज़ी में दिखाई गई है। इंटरनेट जाँचें और फिर कोशिश करें, या English चुनें।'
      : 'Kuch content translate nahi hua; woh English mein dikh raha hai. Internet check karke retry karein, ya English chunein.';
    retry.hidden = kind !== 'error';
  }
  async function requestBatch(texts, signal) {
    // Newline-aligned batches are validated before any result can replace content.
    var url = new URL('https://translate.googleapis.com/translate_a/single');
    url.search = new URLSearchParams({ client: 'gtx', sl: 'en', tl: 'hi', q: texts.join('\n') }).toString();
    url.searchParams.append('dt', 't'); url.searchParams.append('dt', 'rm');
    var timer, timeout = new AbortController();
    var abort = function () { timeout.abort(); };
    signal.addEventListener('abort', abort, { once: true });
    try {
      timer = setTimeout(abort, 18000);
      var response = await fetch(url.toString(), { signal: timeout.signal, credentials: 'omit', referrerPolicy: 'no-referrer' });
      if (!response.ok) throw new Error('Translation service unavailable');
      var data = await response.json();
      if (!Array.isArray(data[0])) throw new Error('Invalid translation');
      var hi = data[0].filter(function (s) { return typeof s[0] === 'string'; }).map(function (s) { return s[0]; }).join('').trim().split(/\n/);
      var roman = data[0].filter(function (s) { return s[0] === null && typeof s[2] === 'string'; }).map(function (s) { return s[2]; }).join('').trim().split(/\n/);
      if (roman.length === 1 && !roman[0] && hi.every(function (s) { return !/[\u0900-\u097f]/.test(s); })) roman = hi.slice();
      if (hi.length !== texts.length || roman.length !== texts.length || hi.some(function (s) { return !s.trim(); }) || roman.some(function (s) { return !s.trim(); })) throw new Error('Unaligned translation');
      texts.forEach(function (s, i) { cache[s] = { hi: hi[i].trim(), hinglish: roman[i].trim() }; });
    } finally { clearTimeout(timer); signal.removeEventListener('abort', abort); }
  }
  async function apply(lang) {
    selected = ['en', 'hi', 'hinglish'].indexOf(lang) >= 0 ? lang : 'en';
    select.value = selected;
    try { localStorage.setItem('it402-language', selected); } catch (_) {}
    document.documentElement.lang = selected === 'hinglish' ? 'hi-Latn' : selected;
    var mine = ++generation;
    if (controller) controller.abort();
    controller = new AbortController();
    var signal = controller.signal;
    render();
    document.dispatchEvent(new Event('languagechange'));
    if (selected === 'en') { notice.hidden = true; return; }
    var unique = Array.from(new Set(records.map(function (r) { return r.source.trim(); }))).filter(function (s) {
      return /[a-zA-Z]/.test(s) && known(s, selected) === null;
    });
    var pending = unique.filter(function (s) { return !cache[s] || !cache[s][selected]; });
    var done = unique.length - pending.length, failed = false, cursor = 0;
    message(pending.length ? 'loading' : 'complete', done, unique.length);
    var batches = [], batch = [], length = 0;
    pending.forEach(function (s) {
      // Normalise embedded newlines for the request; keep original cache key intact.
      if (length + s.length > 1800 && batch.length) { batches.push(batch); batch = []; length = 0; }
      batch.push(s); length += s.length + 1;
    });
    if (batch.length) batches.push(batch);
    async function worker() {
      while (cursor < batches.length && mine === generation && !failed) {
        var items = batches[cursor++];
        try {
          var normal = items.map(function (s) { return s.replace(/\s*\n\s*/g, ' '); });
          try {
            await requestBatch(normal, signal);
          } catch (error) {
            // Some fragments make the provider merge lines. Retry those individually
            // rather than ever assigning a translation to the wrong question.
            if (error.message !== 'Unaligned translation' || normal.length === 1) throw error;
            for (var j = 0; j < normal.length; j++) {
              if (signal.aborted) throw new Error('Aborted');
              await requestBatch([normal[j]], signal);
            }
          }
          if (mine !== generation) return;
          items.forEach(function (s, i) { cache[s] = cache[normal[i]]; });
          done += items.length;
          render(); save(); message('loading', done, unique.length);
        } catch (_) { if (mine === generation) failed = true; }
      }
    }
    await Promise.all([worker(), worker()]);
    if (mine !== generation) return;
    render(); message(failed ? 'error' : 'complete', done, unique.length);
    document.dispatchEvent(new Event('languagechange'));
  }
  document.addEventListener('DOMContentLoaded', function () {
    select = document.getElementById('languageSelect');
    if (!select) return;
    notice = document.getElementById('languageNotice'); status = document.getElementById('languageStatus'); retry = document.getElementById('translationRetry');
    document.querySelectorAll('.q').forEach(function (q) { q.dataset.searchOriginal = q.textContent.toLowerCase(); });
    capture(document.documentElement);
    observer = new MutationObserver(function (changes) {
      changes.forEach(function (change) {
        if (change.type === 'characterData') {
          var rec = originals.get(change.target);
          if (rec && change.target.nodeValue !== rec.last) rec.source = change.target.nodeValue;
        }
      });
      capture(document.body); render();
    });
    var saved = 'en';
    try { saved = localStorage.getItem('it402-language') || 'en'; } catch (_) {}
    select.addEventListener('change', function () { apply(select.value); });
    retry.addEventListener('click', function () { apply(selected); });
    apply(saved);
  });
})();
