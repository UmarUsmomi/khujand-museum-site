const halls = Array.from({ length: 12 }, (_, index) => ({ id: index + 1, title: `Зал ${index + 1}`, x: 40 + (index % 4) * 145, y: 32 + Math.floor(index / 4) * 82 }));
export function initMuseumMap() {
  const host = document.querySelector('[data-museum-map]');
  if (!host) return;
  host.innerHTML = `<svg class="museum-map" viewBox="0 0 640 300" role="img" aria-labelledby="museum-map-label"><title id="museum-map-label">План двенадцати залов музея</title><rect class="museum-map-ground" x="10" y="10" width="620" height="280" rx="24" fill="#f5ead8"></rect>${halls.map(hall => `<rect class="museum-map-room" x="${hall.x}" y="${hall.y}" width="116" height="56" rx="10" tabindex="0" role="button" aria-label="${hall.title}" data-hall="${hall.id}" fill="#1a2744"></rect><text class="museum-map-label" x="${hall.x + 58}" y="${hall.y + 33}" text-anchor="middle">${hall.id}</text>`).join('')}</svg><p class="map-status" aria-live="polite"></p>`;
  host.addEventListener('click', event => {
    const button = event.target.closest('[data-hall]');
    if (!button) return;
    const hall = halls.find(item => item.id === Number(button.dataset.hall));
    host.querySelector('.map-status').textContent = `${hall.title}: коллекция открыта. Аудиогид доступен в плеере.`;
    window.openAudioGuide?.();
  });
  host.addEventListener('keydown', event => { if ((event.key === 'Enter' || event.key === ' ') && event.target.matches('[data-hall]')) { event.preventDefault(); event.target.dispatchEvent(new MouseEvent('click', { bubbles: true })); } });
}
