const SUPPORTED = ['ru', 'tj', 'en'];
const memory = {};

export async function loadLocale(lang = localStorage.getItem('museumLang') || document.documentElement.lang || 'ru') {
  const selected = SUPPORTED.includes(lang) ? lang : 'ru';
  if (!memory[selected]) {
    const response = await fetch(`/data/i18n/${selected}.json`);
    memory[selected] = response.ok ? await response.json() : {};
  }
  document.documentElement.lang = selected === 'tj' ? 'tg' : selected;
  localStorage.setItem('museumLang', selected);
  Object.entries(memory[selected]).forEach(([key, value]) => {
    document.querySelectorAll(`[data-i18n="${CSS.escape(key)}"]`).forEach(node => {
      if (node.matches('input, textarea, select, form, .form-group') || node.querySelector('input, textarea, select')) return;
      node.textContent = value;
    });
    document.querySelectorAll(`[data-i18n-placeholder="${CSS.escape(key)}"]`).forEach(node => node.setAttribute('placeholder', value));
    document.querySelectorAll(`[data-i18n-title="${CSS.escape(key)}"]`).forEach(node => node.setAttribute('title', value));
    document.querySelectorAll(`[data-i18n-aria="${CSS.escape(key)}"]`).forEach(node => node.setAttribute('aria-label', value));
  });
  document.dispatchEvent(new CustomEvent('museum:locale', { detail: { lang: selected } }));
  return selected;
}

export function initI18n() {
  [...document.querySelectorAll('[data-lang]')].filter(control => !control.closest('.lang-switch')).forEach(control => control.addEventListener('click', event => {
    event.preventDefault();
    loadLocale(control.dataset.lang);
  }));
  return loadLocale();
}
