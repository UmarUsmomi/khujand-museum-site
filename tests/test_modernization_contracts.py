from pathlib import Path
import json

ROOT = Path(__file__).parents[1]


def test_pwa_assets_and_audio_cache_entries_exist():
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['display'] == 'standalone'
    service_worker = (ROOT / 'sw.js').read_text(encoding='utf-8')
    for path in ('/index.html', '/pages/contacts.html', '/voices/rus.mp3', '/voices/taj.mp3', '/voices/eng.mp3'):
        assert path in service_worker


def test_modular_entrypoint_and_locales_are_present():
    entry = (ROOT / 'js' / 'app-enhancements.js').read_text(encoding='utf-8')
    assert "./modules/i18n.js" in entry
    assert all((ROOT / 'data' / 'i18n' / f'{lang}.json').exists() for lang in ('ru', 'tj', 'en'))


def test_home_has_semantic_main_map_and_audio_schema():
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    assert '<main id="main-content">' in html
    assert 'data-museum-map' in html
    assert '"@type": "AudioObject"' in html


def test_contacts_has_mobile_safe_form_labels_and_nonofficial_copy():
    html = (ROOT / 'pages' / 'contacts.html').read_text(encoding='utf-8')
    assert 'id="contactEmail"' in html
    assert 'for="contactEmail"' in html
    assert 'Уменьшить число взрослых билетов' in html
    assert 'Официальный портал учреждения' not in html
