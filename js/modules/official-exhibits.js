export async function initOfficialExhibits() {
  const mount = document.querySelector('[data-official-exhibits]');
  if (!mount) return;
  try {
    const response = await fetch('../data/official-exhibits.json');
    if (!response.ok) throw new Error('official exhibit manifest unavailable');
    const catalog = await response.json();
    mount.innerHTML = `<div class="official-source-note">Фотоархив: <a href="${catalog.source.url}" target="_blank" rel="noopener noreferrer">сайт учреждения «Қалъаи Хуҷанд»</a>. Подписи к отдельным предметам появятся после музейной атрибуции снимков.</div><div class="official-exhibits-grid">${catalog.items.map(item => `<figure class="official-exhibit-card"><a href="${item.sourceImage}" target="_blank" rel="noopener noreferrer"><img loading="lazy" decoding="async" src="${item.image}" alt="${item.title}"></a><figcaption>${item.title}<small>Источник: фотоархив учреждения</small></figcaption></figure>`).join('')}</div>`;
  } catch (error) {
    mount.innerHTML = '<p class="official-source-note">Фотоархив учреждения временно недоступен. Локальные материалы сайта продолжают работать.</p>';
  }
}
