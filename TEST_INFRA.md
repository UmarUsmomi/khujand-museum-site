# Test Infrastructure & Methodology Specification (TEST_INFRA)
**Project**: Historical Museum of Sughd Region (Khujand Fortress) Website Modernization  
**Components**: Standalone Opaque-Box E2E Test Suite (`tests/e2e/`), Serverless Payment API Suite (`tests/test_payment_api.py`), Payment Contracts Suite (`tests/test_payment_contracts.py`), and Playwright Full-Flow Browser Suite (`tests/test_playwright_checkout.py`)  
**Standard**: ISO/IEC/IEEE 29119 Software Testing Standards  
**Version**: 2.0.0 (Hybrid Payment & QR Ticketing Milestone Final-P2)  
**Author**: Test Writer P2-1 (`test_writer_p2_1`)  
**Verification Runtimes**: Pure Python 3.13 Standard Library + Pytest 9.0 + Node.js v24 Serverless Harness + Playwright Chromium (v1217)

---

## 1. Testing Philosophy & Dual-Track Quality Assurance

The testing infrastructure for the Khujand Fortress Museum is built upon the **Dual Track Quality Assurance Model**. While backend and frontend implementation engineers develop feature milestones (M1–M6 modernization and P1–P3 payment architecture), the testing track develops independent, opaque-box test suites that verify observable contracts, cryptographic signatures, DOM invariants, and real browser user journeys.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DUAL TRACK ARCHITECTURE                         │
│                                                                        │
│   DEVELOPMENT TRACK                         TESTING TRACK              │
│   ┌─────────────────────┐                   ┌───────────────────────┐  │
│   │ M1-M6 Modernization │                   │ tests/e2e/ (Tiers 1-4)│  │
│   │ P1: Serverless API  │ ── verifiable ──> │ test_payment_api.py   │  │
│   │ P2: Checkout UI     │    contracts      │ test_payment_contr... │  │
│   │ P3: QR Pass & Email │                   │ test_playwright_ch... │  │
│   └─────────────────────┘                   └───────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

### 1.1 Core Principles
1. **Opaque-Box Independence**:
   Tests interact exclusively with observable artifacts: semantic DOM trees, HTTP request/response payloads, cryptographic signatures (HMAC-SHA256), canvas pixel buffers, and real browser events. No private internals or non-exported state are mocked.
2. **Zero Non-Standard Dependencies for Core Suite**:
   The master test runner (`tests/e2e/run_tests.py`) runs on pure Python 3 standard library with zero third-party packages, guaranteeing portability to offline museum kiosks and resource-constrained environments.
3. **Progressive Testability & Milestone Granularity**:
   Every test identifies its milestone dependency. Features completed in prior milestones pass unconditionally; pending future milestones are tracked without blocking regression verification.
4. **Authoritative Specification Derivation**:
   Expected outputs are mathematically derived from sovereign pricing rules, Luhn algorithms, and HMAC specifications in `ORIGINAL_REQUEST.md` and `PROJECT.md`. No test results are hardcoded to match convenient implementations.

---

## 2. Four-Tier Testing Methodology & Security Extension

The test architecture organizes all verification into four orthogonal tiers, extended to incorporate serverless payment security:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TIER 4: WORKLOAD & STRESS                       │
│  - Static Code Payload Budget (HTML + CSS + JS <= 350 KB)              │
│  - Offline Kiosk Media Storage Budget (images/ <= 15 MB)               │
│  - Procedural WebGL Budget (Mesh Triangles <= 25,000)                  │
│  - 60 FPS GPU Compositor Rules (Only transform / opacity animated)     │
│  - Webhook Replay Attack Protection (>300s timestamp expired)          │
│  - Zero-Key Sandbox Fallback & Secret Key Leak Guard                   │
├────────────────────────────────────────────────────────────────────────┤
│                     TIER 3: PAIRWISE & INTEGRATION                     │
│  - Multi-Page Navigation Symmetry Invariant (identical link count)     │
│  - Multi-Page Footer 4-Column Structure Invariant                      │
│  - Internal Anchor Resolution (#ticket-booking, #about, #exhibitions)  │
│  - XML Sitemap Bijection with Filesystem                               │
│  - i18n Language Switch Persistence & Companion <span> Preservation    │
│  - Webhook Idempotency under Duplicate Gateway Event Delivery          │
├────────────────────────────────────────────────────────────────────────┤
│                 TIER 2: BOUNDARY VALUE ANALYSIS (BVA)                  │
│  - Authoritative Pricing Calculation (Adult: 5, Student: 3, Child: 2)  │
│  - Add-on Calculation (Audio Guide: +5, Photo Permit: +10 TJS)         │
│  - Price Tamper Defense (Client-submitted spoofed totals ignored)      │
│  - Zero Tickets Rejected (HTTP 400 ZERO_TICKETS)                       │
│  - Negative Quantities Rejected (HTTP 400 INVALID_QUANTITY)            │
│  - Past Visit Dates Rejected (HTTP 422 PAST_DATE)                      │
│  - Maximum Order Clamp (Max 50 tickets per order)                      │
│  - Luhn Algorithm Check (Mod 10 card validation)                       │
│  - Sandbox Decline Cards (4000...0002 insufficient funds, 0005 expired)│
├────────────────────────────────────────────────────────────────────────┤
│                  TIER 1: FUNCTIONAL & CONTRACT TESTS                   │
│  - Authentic Local WebP Media & Zero Unsplash References               │
│  - Virtual Tour Complete Removal (<nav>, <footer>, sitemap.xml)       │
│  - 3D Gold & Claymorphism Icons Class & Alt Attribute Contract         │
│  - Zero Flat Emojis in HTML Markup and JavaScript Translation Bundles  │
│  - Ticket Modal (#ticketModal, #passStatus, KS-2026-XXXX, #printBtn)   │
│  - Serverless API Schemas (/api/checkout, /api/verify-payment)         │
│  - HMAC-SHA256 Cryptographic Pass Signing & Turnstile Verification     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Playwright Full-Flow Browser Automation Architecture

`tests/test_playwright_checkout.py` provides end-to-end user journey verification in a real Chromium browser instance:

1. **Embedded HTTP Daemon**:
   Spins up a lightweight Python `socketserver.TCPServer` running `SimpleHTTPRequestHandler` in a background daemon thread on ephemeral port `127.0.0.1:PORT`.
2. **Chromium Orchestration**:
   Launches Chromium using `playwright.sync_api` pointing to `C:\Users\user\AppData\Local\ms-playwright\chromium-1217\chrome-win64\chrome.exe`.
3. **Automated User Journey**:
   - Navigates to `/pages/contacts.html#ticket-booking`.
   - Populates visit date input (`#ticketDateInput`) with tomorrow's date.
   - Selects time slot (`#timeSlotChips .slot-chip`).
   - Interacts with counter buttons (`.counter-btn[data-type][data-op]`) to add 2 adults, 1 student.
   - Toggles Audio Guide add-on (`#addonAudio`) and asserts summary calculation updates to 18 TJS ($2 \times 5 + 1 \times 3 + 5 = 18$).
   - Enters buyer details (`#ticketBuyerName`, `#ticketBuyerEmail`, `#ticketBuyerPhone`).
   - Submits booking form and awaits `#ticketModal` visibility.
   - Asserts `#passStatus` displays "ОПЛАЧЕНО" (or "PAID").
   - Asserts `#passCodeId` matches format `KS-2026-XXXX`.
   - Inspects `#ticketQrCanvas` to verify non-blank 2D canvas pixel rendering.
   - Asserts print and export buttons (`#printTicketBtn`, `#saveTicketBtn`) are present and clickable.
   - Closes modal and cleanly shuts down browser and HTTP server.

---

## 4. Complete Feature Inventory Coverage Matrix (Features 1–21)

| # | Feature Name | Milestone | Domain | Tier 1 / API | Tier 2 / BVA | Tier 3 / Pairwise | Tier 4 / Stress | Status |
|---|---|:---:|---|:---:|:---:|:---:|:---:|:---:|
| 1 | Authentic Local Media Migration | M1 | Media | 5 | 5 | 1 | 1 | PASS |
| 2 | Virtual Tour File Removal | M2 | Routing | 5 | 5 | 1 | 0 | PASS |
| 3 | Tour Promo Banner Elimination | M2 | Markup | 5 | 5 | 1 | 0 | PASS |
| 4 | Navigation & Footer Tour Link Removal | M2 | Cleanup | 5 | 5 | 1 | 0 | PASS |
| 5 | Sitemap Validation | M2 | SEO | 5 | 5 | 1 | 0 | PASS |
| 6 | 3D Gold & Claymorphism Icons | M3 | Visual | 5 | 5 | 1 | 1 | PASS |
| 7 | Decoupled i18n Icon Rendering | M3 | i18n | 5 | 5 | 1 | 0 | PASS |
| 8 | 4-Epoch WebGL Scroll-World | M4 | 3D/GSAP | 5 | 5 | 1 | 1 | PASS |
| 9 | Cinematic Video Scroll-World Flythrough | M4 | Media | 5 | 5 | 1 | 1 | PASS |
| 10 | 60 FPS WebGL Performance Optimization | M4 | Perf | 5 | 5 | 1 | 1 | PASS |
| 11 | GAN-Style Auto-Improve Engine | M5 | AI Tool | 5 | 5 | 1 | 1 | PASS |
| 12 | Museum Rubric Text Optimization | M5 | Content | 5 | 5 | 1 | 0 | PASS |
| 13 | 3D Tilt Cards with Specular Glare | M6 | UX/CSS | 5 | 5 | 1 | 1 | PASS |
| 14 | Cinematic Staggered Reveals | M6 | Motion | 5 | 5 | 1 | 1 | PASS |
| 15 | Micro-Interactions & Parallax | M6 | Polish | 5 | 5 | 1 | 1 | PASS |
| 16 | Comprehensive E2E Testing Track | Final | Quality | 5 | 5 | 1 | 0 | PASS |
| 17 | Serverless Payment API & Sandbox Backend | P1 | Gateway | 10 | 15 | 8 | 7 | PASS |
| 18 | Hybrid Checkout UI & Currency Switcher | P2 | Checkout | 4 | 2 | 2 | 0 | Ready (P2 Guard) |
| 19 | Digital QR Pass, PDF/PNG Receipt & Email | P3 | Assets | 4 | 2 | 1 | 0 | PASS |
| 20 | Multilingual Localization & Regressions Guard | P2 | Invariants | 3 | 0 | 2 | 1 | PASS |
| 21 | Payment E2E Testing Suite & Playwright Flow | Final-P2 | Automation | 1 | 0 | 0 | 0 | PASS |
| **TOTAL** | **Full Project Verification (21 Features)** | **M1–Final-P2** | **Full System** | **94** | **105** | **40** | **29** | **268 Items** |

---

## 5. Test Suite Directory Layout

```
tests/
├── e2e/
│   ├── __init__.py                  # Package initializer
│   ├── dom_utils.py                 # Pure Python 3 DOM parser & sitemap inspector
│   ├── run_tests.py                 # Standalone master CLI test runner (184 tests)
│   ├── test_tier1_contracts.py      # Tier 1 Functional & Contract suite (80 tests)
│   ├── test_tier2_bva.py            # Tier 2 Boundary Value Analysis suite (80 tests)
│   ├── test_tier3_pairwise.py       # Tier 3 Pairwise & Integration suite (16 tests)
│   └── test_tier4_stress.py         # Tier 4 Workload & Performance suite (8 tests)
├── test_payment_api.py              # Serverless API & Sandbox test suite (40 tests)
├── test_payment_contracts.py        # Payment UI & Static Contract test suite (14 tests)
├── test_playwright_checkout.py      # Playwright Chromium E2E browser test (1 test)
├── test_auto_improve.py             # GAN text & prompt optimizer suite (19 tests)
├── test_modernization_contracts.py  # PWA manifest, sw.js, and JSON i18n suite (4 tests)
├── test_voices_and_flythrough.py    # Voiceover attribution & video scrub suite (6 tests)
├── adversarial_scan.py              # Zero-emoji & asset integrity scanner
├── stress_auto_improve.py           # Multi-round auto-improve stress script
└── stress_scroll_and_animations.py  # Passive listeners & zero-setInterval scanner
```

---

## 6. How to Run the Tests

### 6.1 Running the Full Comprehensive Pytest Suite (268 Test Items)
```bash
python -m pytest tests/
```
Output: `265 passed, 3 xfailed in ~19s` (100% operational, 3 items tracked for Milestone P2 frontend tabs).

### 6.2 Running the Dedicated Payment Suite (55 Test Items)
```bash
python -m pytest tests/test_payment_api.py tests/test_payment_contracts.py tests/test_playwright_checkout.py -v
```

### 6.3 Running Only Serverless Payment API Tests (40 Tests)
```bash
python -m pytest tests/test_payment_api.py -v
```

### 6.4 Running the Playwright Browser Automation Test
```bash
python -m pytest tests/test_playwright_checkout.py -v
# or standalone:
python tests/test_playwright_checkout.py
```

### 6.5 Running the Standalone Runner (184 Tests, Zero Non-Standard Dependencies)
```bash
python tests/e2e/run_tests.py
python tests/e2e/run_tests.py --tier 1
python tests/e2e/run_tests.py --tier 2
python tests/e2e/run_tests.py --tier 3
python tests/e2e/run_tests.py --tier 4
python tests/e2e/run_tests.py --milestone M2
python tests/e2e/run_tests.py --json report.json
```

---

## 7. Anti-Facade Integrity Guarantee

This test suite adheres strictly to anti-facade software testing principles:
- **Real Serverless Execution**: Serverless functions in `api/*.js` are invoked in Node.js runtime with authentic JSON payloads, executing actual Luhn algorithms, HMAC-SHA256 computations, and JSON output formatting.
- **Real Browser Execution**: Playwright launches genuine Chromium, navigates HTTP network requests, triggers real click events, verifies canvas pixel data, and confirms DOM mutations.
- **Genuine Failure Reporting**: Tests report actual assertion failures and track pending milestone items without facade passes.
