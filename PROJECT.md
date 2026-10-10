# Project: Historical Museum of Sughd Region (Khujand Fortress) Website Modernization

## Architecture
- **Platform**: High-performance static web application (HTML5, modern CSS3, vanilla ES6+, WebGL via Three.js r128, GSAP 3.12 ScrollTrigger).
- **Directory Layout**:
  - `index.html`: Main landing page with Hero, About, 3D Scroll-World, Exhibitions, Highlights, Timeline, Gallery preview, Visit info, Map, CTA, Footer.
  - `pages/`: Sub-pages (`expositions.html`, `history.html`, `events.html`, `gallery.html`, `contacts.html`). Note: `pages/virtual-tour.html` removed in M2.
  - `css/style.css`: Primary stylesheet with design tokens, layout grids, cards, responsive breakpoints, and animations.
  - `js/main.js`: Core client controller (i18n translation, audio player, QR ticket generator, gallery filters, modals).
  - `js/scroll-world.js`: Standalone interactive 3D WebGL / GSAP Scroll-World module for the 4 historical epochs.
  - `js/animations.js`: Standalone professional animation module (3D tilt cards, specular glare, magnetic buttons, parallax).
  - `images/`: Local media assets hierarchy (`exhibits/`, `fortress/`, `highlights/`, `icons/`).
  - `scripts/auto_improve.py`: Zero-dependency Python 3.13 GAN-style auto-improvement engine for historical texts and 3D prompts.
  - `tests/`: Opaque-box E2E test suite across Tiers 1-4 with dedicated runner.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Authentic Local Media Migration | Replace 44 external Unsplash placeholders (gamepads, cakes, gavels) with 15+ verified authentic Khujand Museum / Fortress WebP assets in `images/` | M1 | Survey / R1 |
| 2 | Virtual Tour File Removal | Delete `pages/virtual-tour.html` (574 lines) and inline 2D canvas | M2 | Survey / R2 |
| 3 | Tour Promo Banner Elimination | Delete promo banner from `index.html:205-225` (21 lines) to free slot for Scroll-World | M2 | Survey / R2 |
| 4 | Navigation & Footer Tour Link Removal | Remove `virtual-tour.html` links from `<nav>` and `<footer>` across all 6 pages and clean `js/main.js` dictionary | M2 | Survey / R2 |
| 5 | Sitemap Validation | Confirm `sitemap.xml` validity and ensure zero broken links | M2 | Survey / R2 |
| 6 | 3D Gold & Claymorphism Icons | Replace 178 flat UTF-8 emojis with 3D terracotta clay body, burnished 24K gold accents, soft shadows, and micro-levitation | M3 | Survey / R4 |
| 7 | Decoupled i18n Icon Rendering | Update `js/main.js` `applyLanguage()` so dynamic translation does not wipe out 3D icon markup | M3 | Survey / R4 |
| 8 | 4-Epoch WebGL Scroll-World | Interactive 3D scene (Sogdiana -> Alexandria Eschate -> Timur Malik defense -> Modern Museum) with GSAP scrubbed camera | M4 | Survey / R3 |
| 9 | Zero-Video Procedural 3D World | Procedural low-poly meshes (<25,000 triangles), canvas textures, and GLSL shaders with zero heavy external video dependencies | M4 | Survey / R3 |
| 10 | 60 FPS WebGL Performance Optimization | IntersectionObserver auto-sleep when offscreen + DPR clamped to <=1.0 mobile / <=1.75 desktop | M4 | Survey / R3 |
| 11 | GAN-Style Auto-Improve Engine | Python 3.13 CLI tool (`scripts/auto_improve.py`) implementing ContentMutator -> PairwiseBlindGate -> IndependentJudge | M5 | Survey / R5 |
| 12 | Museum Rubric Text Optimization | Optimize historical descriptions and 3D generation prompts under 4-dimensional weighted museum rubric | M5 | Survey / R5 |
| 13 | 3D Tilt Cards with Specular Glare | Mouse perspective tilt on cards with radial cursor-following glare overlay, guarded on touchscreens | M6 | Survey / R6 |
| 14 | Cinematic Staggered Reveals | GSAP ScrollTrigger batch animations replacing layout-thrashing `getBoundingClientRect()` listeners | M6 | Survey / R6 |
| 15 | Micro-Interactions & Parallax | Magnetic button attraction, gold caustic shimmer sweeps, and smooth background parallax | M6 | Survey / R6 |
| 16 | Comprehensive E2E Testing Track | Independent opaque-box test suite (Tiers 1-4) verifying all criteria + Tier 5 adversarial hardening | Final | Survey / Dual Track |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Authentic Local Media Migration | Populate `images/` with authentic Khujand assets; update all 44 image tags/styles across HTML & CSS; eliminate all gamepads, cakes, and stock photos | none | DONE |
| M2 | Virtual Tour Removal & Nav Cleanup | Delete `pages/virtual-tour.html`, strip banner in `index.html:205-225`, remove nav/footer links in 6 pages, clean `js/main.js` keys | none | DONE |
| M3 | 3D Gold & Claymorphism Icon System | Render/create 3D icons in `images/icons/` & CSS; replace flat emojis across all pages; decouple i18n text replacement | M2 | IN_PROGRESS |
| M4 | 3D WebGL & GSAP Scroll-World | Implement `js/scroll-world.js`; mount in `#scroll-world` at `index.html`; 4 historical epochs; procedural geometry & shaders; 60 FPS auto-sleep | M2 | PLANNED |
| M5 | GAN-Style Auto-Improve Tool | Implement `scripts/auto_improve.py`; run text & prompt optimization; output `tools/auto_improve_history.json` | none | DONE |
| M6 | Professional Animation System | Implement `js/animations.js`; 3D tilt cards + glare; GSAP batched reveals; magnetic buttons; 60 FPS compositor rules | M4 | PLANNED |
| Final | 100% E2E Test Suite & Adversarial Hardening | Pass all Tier 1-4 tests from `TEST_READY.md`; Tier 5 adversarial coverage hardening | M1, M2, M3, M4, M5, M6, TEST_READY.md | IN_PROGRESS (Test Writer) |

## Interface Contracts
### Media & Assets (`images/` ↔ HTML / CSS)
- File paths: `images/{exhibits,fortress,highlights,icons}/[name].webp`
- Fallbacks: WebP with clean alt text in Russian, responsive widths `w=800` or `w=1600`
- Zero external `images.unsplash.com` references permitted in production code.

### Navigation & Page Links (HTML ↔ `sitemap.xml` ↔ `js/main.js`)
- Valid internal routes: `/`, `pages/expositions.html`, `pages/history.html`, `pages/events.html`, `pages/gallery.html`, `pages/contacts.html`.
- `pages/virtual-tour.html` must return 404 / be absent from all links, footers, headers, and scripts.

### 3D Scroll-World Container (`index.html` ↔ `js/scroll-world.js`)
- Container ID: `#scroll-world` inserted between `</section><!-- /about -->` and `<section class="exhibitions" id="exhibitions">`.
- Canvas API: Three.js WebGLRenderer mounted inside `#scroll-world-canvas`.
- GSAP ScrollTrigger timeline pins `#scroll-world` over a scroll distance of `400vh` transitioning through eras 1, 2, 3, and 4.
- Performance: When `#scroll-world` is outside viewport, `IntersectionObserver` halts `requestAnimationFrame`.

### 3D Icons (`images/icons/` & CSS ↔ HTML / `js/main.js`)
- Class: `.clay-icon-3d` with inline `<img src="..." class="clay-icon-3d" alt="...">` or CSS custom component.
- i18n convention: Text elements carry `data-i18n` on companion `<span>` tags, NOT on containers enclosing `.clay-icon-3d`.

### Audio Guide & ElevenLabs AI Voice Engine (`voices/` ↔ `js/main.js`)
- Voice files: `voices/rus.mp3` (RU, ~230s), `voices/taj.mp3` (TJ, ~286s), `voices/eng.mp3` (EN, ~257s).
- Seamless Transition: Switching language maintains fractional playback progress (`currentTime / duration`) with volume crossfade.
- Attribution & Compliance: Voiced by ElevenLabs Studio AI; documented in `VOICES_ATTRIBUTION.md`.

### Auto-Improve Tool (`scripts/auto_improve.py`)
- CLI signature: `python scripts/auto_improve.py [--task descriptions|3d-prompts|all] [--rounds N] [--threshold FLOAT] [--report PATH]`
- Input data: JSON dictionaries of exhibit texts and 3D prompts.
- Output: Validated promoted improvements with audit trail in `tools/auto_improve_history.json`.

## Code Layout
- HTML root: `d:/Mysite1/index.html`
- Subpages: `d:/Mysite1/pages/`
- Styles: `d:/Mysite1/css/style.css`
- Scripts: `d:/Mysite1/js/main.js`, `d:/Mysite1/js/scroll-world.js`, `d:/Mysite1/js/animations.js`, `d:/Mysite1/js/vendor/`
- Images: `d:/Mysite1/images/{exhibits,fortress,highlights,icons}/`
- Tools & Scripts: `d:/Mysite1/scripts/auto_improve.py`, `d:/Mysite1/tools/`
- E2E Tests: `d:/Mysite1/tests/e2e/`
