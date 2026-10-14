import { initI18n } from './modules/i18n.js';
import { initAccessibleDialogs } from './modules/modal.js';
import { initAudioGuide } from './modules/audio-guide.js';
import { initTicketValidation } from './modules/tickets.js';
import { initMuseumMap } from './modules/map.js';
import { track } from './modules/analytics.js';
import { initOfficialExhibits } from './modules/official-exhibits.js';

window.MuseumApp = { track };
document.addEventListener('DOMContentLoaded', () => {
  initI18n();
  initAccessibleDialogs();
  initAudioGuide();
  initTicketValidation();
  initMuseumMap();
  initOfficialExhibits();
  const nav = document.querySelector('.nav-links');
  if (nav && !nav.querySelector('.mobile-lang-switch')) {
    const switcher = document.createElement('div');
    switcher.className = 'mobile-lang-switch';
    switcher.setAttribute('aria-label', 'Язык сайта');
    switcher.innerHTML = ['ru', 'tj', 'en'].map(lang => `<button type="button" data-mobile-lang="${lang}">${lang.toUpperCase()}</button>`).join('');
    switcher.addEventListener('click', event => { const lang = event.target.closest('[data-mobile-lang]')?.dataset.mobileLang; if (lang) document.querySelector(`.lang-switch a[data-lang="${lang}"]`)?.click(); });
    nav.appendChild(switcher);
  }
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
});
