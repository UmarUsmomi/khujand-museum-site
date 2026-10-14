export function initAccessibleDialogs() {
  document.querySelectorAll('[role="dialog"], .ticket-modal-backdrop, .audioguide-modal').forEach(dialog => {
    dialog.setAttribute('aria-modal', 'true');
    let lastFocused = null;
    const focusables = () => [...dialog.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')].filter(node => !node.disabled && node.offsetParent !== null);
    const observer = new MutationObserver(() => {
      if (dialog.classList.contains('active') || dialog.classList.contains('open')) {
        dialog.removeAttribute('hidden');
        lastFocused = document.activeElement;
        focusables()[0]?.focus();
      }
    });
    observer.observe(dialog, { attributes: true, attributeFilter: ['class'] });
    dialog.addEventListener('keydown', event => {
      if (event.key === 'Escape') {
        dialog.classList.remove('active', 'open');
        lastFocused?.focus();
        return;
      }
      if (event.key !== 'Tab') return;
      const items = focusables();
      if (!items.length) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    });
  });
}
