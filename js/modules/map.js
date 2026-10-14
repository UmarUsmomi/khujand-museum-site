export const HALLS_DATA = [
  {
    id: 1,
    num: "01",
    title: "Истоки Согда и Саразм",
    era: "IV–II тыс. до н.э.",
    desc: "Эпоха энеолита и бронзы Зарафшанской долины, древнейшее земледелие, металлургия и керамика Саразма."
  },
  {
    id: 2,
    num: "02",
    title: "Александрия Эсхата",
    era: "329 г. до н.э.",
    desc: "Основание города-крепости Александром Македонским на Сырдарье, эллинистическая культура и греко-бактрийское искусство."
  },
  {
    id: 3,
    num: "03",
    title: "Цитадель древнего Худжанда",
    era: "IV–I вв. до н.э.",
    desc: "Мощная фортификационная система: сырцовые стены, башни и глубокий ров античной цитадели Худжанда."
  },
  {
    id: 4,
    num: "04",
    title: "Великий Шёлковый путь",
    era: "I–XV вв.",
    desc: "Ключевой торговый узел Средней Азии: монеты Кушанского царства, согдийские караваны и редкие артефакты."
  },
  {
    id: 5,
    num: "05",
    title: "Золотой шлем саков",
    era: "V–IV вв. до н.э.",
    desc: "Уникальный золотой парадный шлем с чеканными фигурами крылатых барсов в скифо-сакском зверином стиле."
  },
  {
    id: 6,
    num: "06",
    title: "Подвиг Темурмалика",
    era: "1219–1220 гг.",
    desc: "Легендарная оборона Худжандской крепости народным героем от орд Чингисхана, оружие и доспехи воинов."
  },
  {
    id: 7,
    num: "07",
    title: "Средневековый Худжанд",
    era: "IX–XIII вв.",
    desc: "Эпоха Саманидов: расцвет городской культуры, глазурованная посуда, художественная ковка и чеканная медь."
  },
  {
    id: 8,
    num: "08",
    title: "Шёлкоткачество и атлас",
    era: "XVIII–XX вв.",
    desc: "Традиционные ручные станки, знаменитый худжандский хан-атлас, адрас и вековые секреты восточного шёлка."
  },
  {
    id: 9,
    num: "09",
    title: "Каллиграфия и манускрипты",
    era: "XIV–XIX вв.",
    desc: "Рукописные книги, восточная книжная миниатюра, поэтические сборники Камола Худжанди и научные трактаты."
  },
  {
    id: 10,
    num: "10",
    title: "Этнография Согда",
    era: "XIX — начало XX в.",
    desc: "Традиционный быт, золотошвейные сюзане, резное дерево, национальные костюмы и серебряные ювелирные украшения."
  },
  {
    id: 11,
    num: "11",
    title: "Цитадель в новое время",
    era: "XIX — середина XX в.",
    desc: "История Худжандской крепости в период Кокандского ханства и Нового времени, старинные фотографии и документы."
  },
  {
    id: 12,
    num: "12",
    title: "Возрождение крепости",
    era: "XXI век",
    desc: "Грандиозная реставрация и возрождение архитектурного комплекса «Крепость Худжанда» как символа национальной гордости."
  }
];

export function initMuseumMap() {
  const host = document.querySelector('[data-museum-map]');
  if (!host) return;
  if (host.dataset.mapInitialized) return;
  host.dataset.mapInitialized = 'true';

  // Render authentic interactive 12-hall guide if not present
  if (host.querySelectorAll('.museum-hall-card').length < 12) {
    host.innerHTML = `
    <div class="museum-halls-grid" role="list" aria-label="12 залов Исторического музея Худжандской крепости">
      ${HALLS_DATA.map((hall, idx) => `
        <button type="button" 
                class="museum-hall-card ${idx === 0 ? 'active' : ''}" 
                role="listitem" 
                data-hall="${hall.id}"
                aria-label="${hall.title}: ${hall.era}">
          <div class="museum-hall-header">
            <span class="hall-num-pill">${hall.num}</span>
            <span class="hall-era-badge">${hall.era}</span>
          </div>
          <h4 class="museum-hall-title">${hall.title}</h4>
          <p class="museum-hall-desc">${hall.desc}</p>
        </button>
      `).join('')}
    </div>

    <!-- Active Hall Detail Card -->
    <div class="hall-detail-card" id="hallDetailCard">
      <div class="hall-detail-badge" id="hallDetailBadge">Зал ${HALLS_DATA[0].num} • ${HALLS_DATA[0].era}</div>
      <h3 class="hall-detail-title" id="hallDetailTitle">${HALLS_DATA[0].title}</h3>
      <p class="hall-detail-desc" id="hallDetailDesc">${HALLS_DATA[0].desc}</p>
      <div class="hall-detail-actions">
        <button type="button" class="btn btn-primary" id="btnPlayHallAudio">
          <img src="images/icons/icon-audioguide-3d.webp" class="clay-icon-3d" alt="Аудиогид" width="20" height="20" loading="lazy">
          <span>Слушать аудиогид зала ▶</span>
        </button>
        <a href="pages/expositions.html" class="btn btn-outline">
          <img src="images/icons/icon-museum-3d.webp" class="clay-icon-3d" alt="Экспозиция" width="18" height="18" loading="lazy">
          <span>Смотреть экспозицию зала →</span>
        </a>
      </div>
    </div>
    <p class="map-status sr-only" aria-live="polite">Зал ${HALLS_DATA[0].id}: ${HALLS_DATA[0].title}</p>
  `;
  }

  function selectHall(id) {
    const hall = HALLS_DATA.find(h => h.id === id);
    if (!hall) return;

    // Update active card state
    host.querySelectorAll('.museum-hall-card').forEach(card => {
      card.classList.toggle('active', Number(card.dataset.hall) === id);
    });

    // Update detail card
    const badge = host.querySelector('#hallDetailBadge');
    const title = host.querySelector('#hallDetailTitle');
    const desc = host.querySelector('#hallDetailDesc');
    const status = host.querySelector('.map-status');

    if (badge) badge.textContent = `Зал ${hall.num} • ${hall.era}`;
    if (title) title.textContent = hall.title;
    if (desc) desc.textContent = hall.desc;
    if (status) status.textContent = `Выбран Зал ${hall.num}: ${hall.title}. ${hall.desc}`;
  }

  // Click & Keyboard interactions
  host.addEventListener('click', event => {
    const card = event.target.closest('[data-hall]');
    if (card) {
      const hallId = Number(card.dataset.hall);
      selectHall(hallId);
    }

    if (event.target.closest('#btnPlayHallAudio')) {
      if (typeof window.openAudioGuide === 'function') {
        window.openAudioGuide();
      } else {
        const dockPlay = document.querySelector('.audioguide-dock-btn, #audioToggle');
        dockPlay?.click();
      }
    }
  });

  host.addEventListener('keydown', event => {
    if ((event.key === 'Enter' || event.key === ' ') && event.target.matches('[data-hall]')) {
      event.preventDefault();
      const hallId = Number(event.target.dataset.hall);
      selectHall(hallId);
    }
  });
}
