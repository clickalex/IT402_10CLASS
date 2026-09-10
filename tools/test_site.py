#!/usr/bin/env python3
"""Browser regression checks. Run a static server on :8000, then:
  pip install playwright
  playwright install chromium
  python tools/test_site.py
Set CHROMIUM_PATH to use an existing Chromium binary.
Translation responses are mocked: these tests check UI/data integrity, not linguistic quality.
"""
import json
import os
from urllib.parse import parse_qs, urlparse
from playwright.sync_api import sync_playwright

BASE = os.environ.get('SITE_URL', 'http://127.0.0.1:8000')
PAGES = ['index', 'learn', 'write', 'drill', 'revise', 'qbank', 'reference', 'syllabus', '404']


def mock_translation(route):
    lines = parse_qs(urlparse(route.request.url).query)['q'][0].split('\n')
    # Deliberately longer text exercises layouts as well as the translation mapping.
    hindi = ['हिंदी अनुवाद ' + s for s in lines]
    roman = ['Hinglish mein ' + s for s in lines]
    route.fulfill(json=[[['\n'.join(hindi), '\n'.join(lines)], [None, None, '\n'.join(roman)]]],
                  headers={'Access-Control-Allow-Origin': '*'})


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None,
                                headless=True, args=['--no-sandbox'])
    context = browser.new_context()
    context.route('https://translate.googleapis.com/**', mock_translation)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    checks = 0
    for name in PAGES:
        page.goto(f'{BASE}/{name}.html')
        original = page.locator('main').inner_text()
        for lang in ['en', 'hi', 'hinglish']:
            page.select_option('#languageSelect', lang)
            if lang != 'en':
                page.wait_for_function("document.getElementById('languageStatus').textContent.includes('Official translation nahi') || document.getElementById('languageStatus').textContent.includes('यह आधिकारिक अनुवाद नहीं')")
            for width in [320, 375, 768, 1024, 1440]:
                page.set_viewport_size({'width': width, 'height': 900})
                overflow = page.evaluate('document.documentElement.scrollWidth > innerWidth')
                assert not overflow, f'Horizontal overflow: {name}/{lang}/{width}'
                assert page.locator('#languageSelect').is_visible()
                checks += 1
        page.select_option('#languageSelect', 'en')
        # Dynamic score text is allowed to initialise, all content otherwise restored.
        assert page.locator('main').inner_text() == original, f'English restoration failed: {name}'
    page.set_viewport_size({'width': 375, 'height': 812})
    page.goto(f'{BASE}/drill.html')
    page.click('#navToggle')
    assert page.locator('#navToggle').get_attribute('aria-expanded') == 'true'
    page.keyboard.press('Escape')
    assert page.locator('#navToggle').get_attribute('aria-expanded') == 'false'
    first = page.locator('.q').first
    key = first.get_attribute('data-answer')
    first.locator(f'.opt[data-i="{key}"]').click()
    first.locator('.reveal').click()
    assert '1 / 1 revealed' in page.locator('#score').inner_text()
    page.select_option('#languageSelect', 'hi')
    page.wait_for_function("document.documentElement.lang === 'hi'")
    assert first.locator('.opt.sel').get_attribute('data-i') == key
    assert first.locator('.ans').is_visible()
    first.locator('.reveal').click()
    assert not first.locator('.ans').is_visible()
    page.select_option('#languageSelect', 'en')
    assert first.locator('.reveal').inner_text() == 'Show Answer'
    page.reload()
    assert page.locator('.q').first.locator('.opt.sel').get_attribute('data-i') == key
    page.fill('#qSearch', 'no-such-question-zzzz')
    assert page.locator('#noResults').is_visible()
    page.fill('#qSearch', '')
    assert not page.locator('#noResults').is_visible()
    page.goto(f'{BASE}/qbank.html')
    page.locator('.q').first.locator('.reveal').click()
    page.select_option('#languageSelect', 'hinglish')
    assert page.locator('.q').first.locator('.ans').is_visible()
    page.select_option('#languageSelect', 'en')
    page.goto(f'{BASE}/revise.html')
    page.locator('input[type=checkbox]').first.check()
    page.reload()
    assert page.locator('input[type=checkbox]').first.is_checked()
    # Preference persists across pages; cached pages translate without network.
    page.select_option('#languageSelect', 'hi')
    page.goto(f'{BASE}/learn.html')
    assert page.locator('#languageSelect').input_value() == 'hi'
    context.set_offline(True)
    page.select_option('#languageSelect', 'hinglish')
    assert page.locator('html').get_attribute('lang') == 'hi-Latn'
    assert page.locator('#translationRetry').is_hidden()
    context.set_offline(False)
    # Invalid saved caches must not break translation or silently stop the worker.
    for corrupt in ['"broken"', '[]', '{"Home":42}']:
        page.evaluate("value => localStorage.setItem('it402-translations-v1', value)", corrupt)
        page.goto(f'{BASE}/learn.html')
        page.select_option('#languageSelect', 'hi')
        page.wait_for_function("document.getElementById('languageStatus').textContent.includes('यह आधिकारिक अनुवाद नहीं')")
        assert page.locator('#translationRetry').is_hidden()
    # Switching back while requests are pending must leave the English DOM intact.
    rapid_context = browser.new_context()
    rapid_context.route('https://translate.googleapis.com/**', lambda route: route.abort())
    rapid = rapid_context.new_page()
    rapid.goto(f'{BASE}/learn.html')
    english = rapid.locator('main').inner_text()
    rapid.evaluate("""() => {
      const select = document.getElementById('languageSelect');
      for (const value of ['hi', 'hinglish', 'en']) {
        select.value = value; select.dispatchEvent(new Event('change'));
      }
    }""")
    assert rapid.locator('main').inner_text() == english
    assert rapid.locator('#languageNotice').is_hidden()
    rapid_context.close()
    # Fresh context with unavailable service must expose a recoverable fallback.
    fail_context = browser.new_context()
    fail_context.route('https://translate.googleapis.com/**', lambda route: route.abort())
    fail_page = fail_context.new_page()
    fail_page.goto(f'{BASE}/learn.html')
    fail_page.select_option('#languageSelect', 'hi')
    fail_page.wait_for_selector('#translationRetry', state='visible')
    fail_page.select_option('#languageSelect', 'en')
    assert fail_page.locator('#languageNotice').is_hidden()
    assert fail_page.locator('html').get_attribute('lang') == 'en'
    for old in ['drill-print', '03-Drill-140-MCQ-Printable']:
        fail_page.goto(f'{BASE}/{old}.html')
        fail_page.wait_for_url('**/drill.html')
    assert not errors, errors
    browser.close()
    print(f'PASS: {checks} page/language/viewport layouts; navigation, drill, bank, checklist, cache, fallback and redirects.')
