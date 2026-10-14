const CLOSED_DAYS = new Set();
async function orderHash(payload) {
  const bytes = new TextEncoder().encode(JSON.stringify(payload));
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, '0')).join('').slice(0, 16).toUpperCase();
}
export function initTicketValidation() {
  const date = document.querySelector('#ticketDateInput');
  if (!date) return;
  const today = new Date();
  const iso = new Date(today.getTime() - today.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
  date.min = iso;
  date.addEventListener('input', () => {
    const invalid = !date.value || date.value < iso || CLOSED_DAYS.has(date.value);
    date.setCustomValidity(invalid ? 'Выберите доступную будущую дату.' : '');
  });
  document.querySelector('#ticketBookingForm')?.addEventListener('submit', event => {
    date.dispatchEvent(new Event('input'));
    if (!event.target.checkValidity()) { event.preventDefault(); date.reportValidity(); }
  });

  const modal = document.querySelector('#ticketModal');
  const save = document.querySelector('#saveTicketBtn');
  if (modal && save && !document.querySelector('#downloadTicketImageBtn')) {
    const imageButton = document.createElement('button');
    imageButton.type = 'button'; imageButton.id = 'downloadTicketImageBtn'; imageButton.className = 'btn btn-outline'; imageButton.textContent = 'Сохранить QR как изображение';
    save.parentElement?.insertBefore(imageButton, save);
    imageButton.addEventListener('click', () => {
      const canvas = document.querySelector('#ticketQrCanvas');
      if (!canvas) return;
      const link = document.createElement('a'); link.download = 'khujand-museum-ticket.png'; link.href = canvas.toDataURL('image/png'); link.click();
    });
    document.querySelector('#printTicketBtn')?.addEventListener('click', () => {
      document.body.classList.add('print-ticket-only');
      window.addEventListener('afterprint', () => document.body.classList.remove('print-ticket-only'), { once: true });
    }, { capture: true });
  }

  window.MuseumTicket = {
    async createOrder(order) { return { ...order, hash: await orderHash(order), provider: 'pending-backend' }; },
    paymentProviders: ['alif-pay', 'korti-milli']
  };
}
