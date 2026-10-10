#!/usr/bin/env python3
"""
scripts/generate_3d_icons.py
Generates 3D Gold & Claymorphism icons in SVG and WebP format for Khujand Museum.
Terracotta body (#C86D46 / #E07A5F), 24K gold accents (#FFD700 / #E5A93C), dual shadows, specular highlights.
"""

import os
import pathlib
from PIL import Image
from playwright.sync_api import sync_playwright

ICONS_DIR = pathlib.Path(__file__).resolve().parent.parent / "images" / "icons"
ICONS_DIR.mkdir(parents=True, exist_ok=True)

SHARED_DEFS = """
  <defs>
    <!-- Terracotta Clay Gradients -->
    <linearGradient id="clay-grad" x1="20%" y1="10%" x2="80%" y2="90%">
      <stop offset="0%" stop-color="#F4956D"/>
      <stop offset="40%" stop-color="#DE6E44"/>
      <stop offset="85%" stop-color="#B84E25"/>
      <stop offset="100%" stop-color="#883312"/>
    </linearGradient>
    <radialGradient id="clay-sphere" cx="35%" cy="30%" r="70%">
      <stop offset="0%" stop-color="#FFB391"/>
      <stop offset="35%" stop-color="#DE6E44"/>
      <stop offset="80%" stop-color="#A54019"/>
      <stop offset="100%" stop-color="#6F260C"/>
    </radialGradient>
    <linearGradient id="clay-light" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FAF1E6"/>
      <stop offset="60%" stop-color="#E8CEB5"/>
      <stop offset="100%" stop-color="#C29A78"/>
    </linearGradient>
    <linearGradient id="clay-dark" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#883312"/>
      <stop offset="100%" stop-color="#4E1A08"/>
    </linearGradient>

    <!-- 24K Burnished Gold Gradients -->
    <linearGradient id="gold-grad" x1="15%" y1="10%" x2="85%" y2="90%">
      <stop offset="0%" stop-color="#FFF8D1"/>
      <stop offset="25%" stop-color="#FFDA44"/>
      <stop offset="60%" stop-color="#E2A619"/>
      <stop offset="88%" stop-color="#AD7408"/>
      <stop offset="100%" stop-color="#734700"/>
    </linearGradient>
    <radialGradient id="gold-sphere" cx="32%" cy="28%" r="68%">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="25%" stop-color="#FFE875"/>
      <stop offset="65%" stop-color="#E5A91D"/>
      <stop offset="90%" stop-color="#9A6202"/>
      <stop offset="100%" stop-color="#613B00"/>
    </radialGradient>
    <linearGradient id="gold-rim" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.95"/>
      <stop offset="40%" stop-color="#FFE066" stop-opacity="0.8"/>
      <stop offset="80%" stop-color="#C68910" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#553000" stop-opacity="0.1"/>
    </linearGradient>
    <linearGradient id="gold-shine" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#FFE066" stop-opacity="0"/>
      <stop offset="50%" stop-color="#FFFFFF" stop-opacity="0.85"/>
      <stop offset="100%" stop-color="#FFE066" stop-opacity="0"/>
    </linearGradient>

    <!-- Ambient & Contact Drop Shadows -->
    <filter id="clay-shadow" x="-30%" y="-30%" width="160%" height="170%">
      <feDropShadow dx="0" dy="5" stdDeviation="4.5" flood-color="#4E1A08" flood-opacity="0.28"/>
      <feDropShadow dx="0" dy="12" stdDeviation="9" flood-color="#9A6202" flood-opacity="0.18"/>
    </filter>
    <filter id="soft-glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="2.5" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>
"""

ICONS_SVG = {
    "icon-museum-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)">
    <!-- Base Plinth -->
    <rect x="18" y="100" width="92" height="12" rx="4" fill="url(#clay-grad)"/>
    <rect x="22" y="93" width="84" height="8" rx="3" fill="url(#clay-sphere)"/>
    <rect x="18" y="100" width="92" height="3" fill="url(#gold-grad)"/>

    <!-- Outer Fortress Domes (Left & Right) -->
    <path d="M26 62 Q26 44 38 44 Q50 44 50 62 Z" fill="url(#clay-grad)"/>
    <path d="M78 62 Q78 44 90 44 Q102 44 102 62 Z" fill="url(#clay-grad)"/>
    <circle cx="38" cy="42" r="3.5" fill="url(#gold-sphere)"/>
    <circle cx="90" cy="42" r="3.5" fill="url(#gold-sphere)"/>

    <!-- Central Grand Dome -->
    <path d="M42 52 Q42 16 64 16 Q86 16 86 52 Z" fill="url(#clay-sphere)"/>
    <!-- Dome Gold Ribs -->
    <path d="M51 48 Q54 22 64 16 Q74 22 77 48" stroke="url(#gold-grad)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
    <line x1="64" y1="16" x2="64" y2="48" stroke="url(#gold-grad)" stroke-width="2.5"/>
    <!-- Spire & Crescent -->
    <rect x="62.5" y="8" width="3" height="9" rx="1.5" fill="url(#gold-sphere)"/>
    <path d="M64 4 C67 4 69 6 69 9 C67 8 65 8 63 9 C63 6 63 4 64 4 Z" fill="url(#gold-sphere)"/>

    <!-- Drum Base & Pediment -->
    <rect x="36" y="50" width="56" height="12" rx="3" fill="url(#gold-grad)"/>
    <polygon points="64,52 24,70 104,70" fill="url(#clay-grad)"/>
    <polygon points="64,56 32,70 96,70" fill="url(#clay-sphere)"/>
    <circle cx="64" cy="64" r="4.5" fill="url(#gold-sphere)"/>

    <!-- Columns (4 Portico Columns) -->
    <g fill="url(#clay-grad)">
      <rect x="29" y="70" width="9" height="23" rx="2"/>
      <rect x="47" y="70" width="9" height="23" rx="2"/>
      <rect x="72" y="70" width="9" height="23" rx="2"/>
      <rect x="90" y="70" width="9" height="23" rx="2"/>
    </g>
    <!-- Column Capitals & Bases -->
    <g fill="url(#gold-grad)">
      <rect x="27.5" y="69" width="12" height="3" rx="1.5"/>
      <rect x="45.5" y="69" width="12" height="3" rx="1.5"/>
      <rect x="70.5" y="69" width="12" height="3" rx="1.5"/>
      <rect x="88.5" y="69" width="12" height="3" rx="1.5"/>
      <rect x="27.5" y="90" width="12" height="3" rx="1.5"/>
      <rect x="45.5" y="90" width="12" height="3" rx="1.5"/>
      <rect x="70.5" y="90" width="12" height="3" rx="1.5"/>
      <rect x="88.5" y="90" width="12" height="3" rx="1.5"/>
    </g>

    <!-- Arched Portal Entrance -->
    <path d="M58 93 V80 Q58 74 64 74 Q70 74 70 80 V93 Z" fill="url(#clay-dark)"/>
    <path d="M57 93 V80 Q57 73 64 73 Q71 73 71 80 V93" stroke="url(#gold-grad)" stroke-width="2" fill="none"/>
  </g>
</svg>""",

    "icon-fortress-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)">
    <!-- Base Adobe Mound -->
    <path d="M16 108 C32 104 96 104 112 108 L116 116 H12 Z" fill="url(#clay-dark)"/>
    <rect x="22" y="100" width="84" height="10" rx="3" fill="url(#clay-grad)"/>
    <rect x="22" y="100" width="84" height="2.5" fill="url(#gold-grad)"/>

    <!-- Fortress Main Wall -->
    <rect x="26" y="44" width="76" height="58" rx="5" fill="url(#clay-sphere)"/>

    <!-- Left & Right Flanking Bastions -->
    <rect x="20" y="32" width="22" height="70" rx="4" fill="url(#clay-grad)"/>
    <rect x="86" y="32" width="22" height="70" rx="4" fill="url(#clay-grad)"/>

    <!-- Battlements / Crenellations -->
    <!-- Center wall crenels -->
    <g fill="url(#clay-grad)">
      <rect x="44" y="38" width="8" height="9" rx="1.5"/>
      <rect x="56" y="38" width="8" height="9" rx="1.5"/>
      <rect x="68" y="38" width="8" height="9" rx="1.5"/>
      <rect x="76" y="38" width="8" height="9" rx="1.5"/>
    </g>
    <!-- Tower crenels with Gold Caps -->
    <g fill="url(#gold-grad)">
      <rect x="20" y="26" width="6" height="8" rx="1.5"/>
      <rect x="28" y="26" width="6" height="8" rx="1.5"/>
      <rect x="36" y="26" width="6" height="8" rx="1.5"/>
      <rect x="86" y="26" width="6" height="8" rx="1.5"/>
      <rect x="94" y="26" width="6" height="8" rx="1.5"/>
      <rect x="102" y="26" width="6" height="8" rx="1.5"/>
      <line x1="20" y1="34" x2="42" y2="34" stroke="url(#gold-grad)" stroke-width="2"/>
      <line x1="86" y1="34" x2="108" y2="34" stroke="url(#gold-grad)" stroke-width="2"/>
    </g>

    <!-- Fortress Gate -->
    <path d="M52 100 V72 Q52 64 64 64 Q76 64 76 72 V100 Z" fill="url(#clay-dark)"/>
    <path d="M50 100 V72 Q50 62 64 62 Q78 62 78 72 V100" stroke="url(#gold-grad)" stroke-width="2.5" fill="none"/>
    <!-- Studded Gate Beams -->
    <line x1="53" y1="78" x2="75" y2="78" stroke="url(#gold-grad)" stroke-width="1.8"/>
    <line x1="53" y1="88" x2="75" y2="88" stroke="url(#gold-grad)" stroke-width="1.8"/>
    <circle cx="64" cy="83" r="2.5" fill="url(#gold-sphere)"/>

    <!-- Central Sogdian Warrior Shield (Burnished 24K Gold) -->
    <circle cx="64" cy="50" r="11" fill="url(#gold-sphere)"/>
    <circle cx="64" cy="50" r="8" fill="url(#clay-grad)"/>
    <polygon points="64,44 66,48 70,48 67,51 68,55 64,53 60,55 61,51 58,48 62,48" fill="url(#gold-sphere)"/>

    <!-- Tower Arrow Slits -->
    <rect x="29" y="52" width="4" height="12" rx="2" fill="url(#clay-dark)"/>
    <rect x="95" y="52" width="4" height="12" rx="2" fill="url(#clay-dark)"/>
  </g>
</svg>""",

    "icon-amphora-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)">
    <!-- Base Pedestal -->
    <ellipse cx="64" cy="110" rx="22" ry="7" fill="url(#clay-dark)"/>
    <ellipse cx="64" cy="107" rx="20" ry="5.5" fill="url(#clay-grad)"/>
    <ellipse cx="64" cy="107" rx="18" ry="3.5" stroke="url(#gold-grad)" stroke-width="1.5" fill="none"/>

    <!-- Handles Left & Right -->
    <path d="M42 42 C20 42 18 78 44 86" stroke="url(#clay-grad)" stroke-width="8" stroke-linecap="round" fill="none"/>
    <path d="M42 42 C22 42 20 78 44 86" stroke="url(#gold-rim)" stroke-width="2" stroke-linecap="round" fill="none"/>
    <path d="M86 42 C108 42 110 78 84 86" stroke="url(#clay-grad)" stroke-width="8" stroke-linecap="round" fill="none"/>
    <path d="M86 42 C106 42 108 78 84 86" stroke="url(#gold-rim)" stroke-width="2" stroke-linecap="round" fill="none"/>

    <!-- Khum Body -->
    <path d="M44 32 C44 26 48 22 64 22 C80 22 84 26 84 32 C84 46 98 62 98 80 C98 98 80 106 64 106 C48 106 30 98 30 80 C30 62 44 46 44 32 Z" fill="url(#clay-sphere)"/>

    <!-- Flared Neck & Rim -->
    <ellipse cx="64" cy="22" rx="19" ry="6" fill="url(#clay-grad)"/>
    <ellipse cx="64" cy="19" rx="21" ry="6.5" fill="url(#gold-grad)"/>
    <ellipse cx="64" cy="19" rx="16" ry="4.5" fill="url(#clay-dark)"/>

    <!-- 24K Gold Ornament Bands on Amphora Belly -->
    <!-- Upper Band -->
    <path d="M34 68 C44 74 84 74 94 68" stroke="url(#gold-grad)" stroke-width="4.5" stroke-linecap="round" fill="none"/>
    <!-- Sogdian Wave Meander Accent -->
    <path d="M37 78 Q43 73 50 78 Q57 83 64 78 Q71 73 78 78 Q85 83 91 78" stroke="url(#gold-grad)" stroke-width="3" stroke-linecap="round" fill="none"/>
    <!-- Lower Band -->
    <path d="M40 88 C50 93 78 93 88 88" stroke="url(#gold-grad)" stroke-width="3" stroke-linecap="round" fill="none"/>

    <!-- Golden Museum Medallion on Vessel Chest -->
    <circle cx="64" cy="50" r="7.5" fill="url(#gold-sphere)"/>
    <circle cx="64" cy="50" r="4.5" fill="url(#clay-grad)"/>
  </g>
</svg>""",

    "icon-ticket-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)" transform="rotate(-6 64 64)">
    <!-- Ticket Card Body (Terracotta + Gold Edge) -->
    <rect x="18" y="34" width="92" height="60" rx="12" fill="url(#clay-grad)"/>
    <!-- Inset Cream Pass Body -->
    <rect x="22" y="38" width="84" height="52" rx="9" fill="url(#clay-light)"/>

    <!-- Perforation Cutout Circles -->
    <circle cx="18" cy="64" r="7" fill="#FEFCF9"/>
    <circle cx="110" cy="64" r="7" fill="#FEFCF9"/>
    <!-- Perforated Dash Line -->
    <line x1="84" y1="38" x2="84" y2="90" stroke="url(#clay-dark)" stroke-width="2" stroke-dasharray="4 3"/>

    <!-- Left Brand Bar -->
    <rect x="25" y="42" width="6" height="44" rx="3" fill="url(#gold-grad)"/>

    <!-- 24K Gold Museum Crest Medallion -->
    <circle cx="54" cy="56" r="11" fill="url(#gold-sphere)"/>
    <polygon points="54,49 56,53 60,53 57,56 58,60 54,58 50,60 51,56 48,53 52,53" fill="url(#clay-dark)"/>

    <!-- Text Lines Simulation -->
    <rect x="40" y="72" width="28" height="4" rx="2" fill="url(#clay-dark)"/>
    <rect x="42" y="79" width="24" height="3" rx="1.5" fill="url(#gold-grad)"/>

    <!-- Stub Barcode Simulation -->
    <g fill="url(#clay-dark)">
      <rect x="89" y="46" width="2" height="36"/>
      <rect x="93" y="46" width="3.5" height="36"/>
      <rect x="98" y="46" width="1.5" height="36"/>
      <rect x="101" y="46" width="3" height="36"/>
    </g>

    <!-- 24K Gold Corner VIP Ribbon -->
    <polygon points="22,50 36,38 46,38 22,60" fill="url(#gold-sphere)"/>
  </g>
</svg>""",

    "icon-audioguide-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)">
    <!-- Arch Headband -->
    <path d="M28 70 C28 32 100 32 100 70" stroke="url(#clay-grad)" stroke-width="12" stroke-linecap="round" fill="none"/>
    <!-- Headband Top Gold Trim -->
    <path d="M36 58 C42 36 86 36 92 58" stroke="url(#gold-grad)" stroke-width="3" stroke-linecap="round" fill="none"/>
    <!-- Headband Cushion Pads -->
    <path d="M44 40 C52 35 76 35 84 40" stroke="url(#clay-light)" stroke-width="5" stroke-linecap="round" fill="none"/>

    <!-- Headphone Extender Sliders -->
    <rect x="22" y="66" width="8" height="14" rx="3" fill="url(#gold-sphere)"/>
    <rect x="98" y="66" width="8" height="14" rx="3" fill="url(#gold-sphere)"/>

    <!-- Left Ear Cup -->
    <rect x="14" y="74" width="24" height="34" rx="12" fill="url(#clay-sphere)"/>
    <rect x="16" y="76" width="20" height="30" rx="10" stroke="url(#gold-grad)" stroke-width="3" fill="none"/>
    <circle cx="26" cy="91" r="5" fill="url(#gold-sphere)"/>

    <!-- Right Ear Cup -->
    <rect x="90" y="74" width="24" height="34" rx="12" fill="url(#clay-sphere)"/>
    <rect x="92" y="76" width="20" height="30" rx="10" stroke="url(#gold-grad)" stroke-width="3" fill="none"/>
    <circle cx="102" cy="91" r="5" fill="url(#gold-sphere)"/>

    <!-- Sound Wave Radiations from Headset Center -->
    <circle cx="64" cy="85" r="9" fill="url(#gold-sphere)"/>
    <polygon points="61,80 69,85 61,90" fill="url(#clay-dark)"/>
    <path d="M50 85 C50 78 54 73 54 73" stroke="url(#gold-grad)" stroke-width="2.5" stroke-linecap="round"/>
    <path d="M78 85 C78 78 74 73 74 73" stroke="url(#gold-grad)" stroke-width="2.5" stroke-linecap="round"/>
  </g>
</svg>""",

    "icon-pin-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)">
    <!-- Contact Ground Ellipse -->
    <ellipse cx="64" cy="116" rx="18" ry="6" fill="url(#clay-dark)" opacity="0.6"/>
    <ellipse cx="64" cy="116" rx="12" ry="3.5" fill="url(#gold-grad)" opacity="0.8"/>

    <!-- 3D Teardrop Pin Body -->
    <path d="M64 114 C64 114 26 76 26 48 C26 24 43 14 64 14 C85 14 102 24 102 48 C102 76 64 114 64 114 Z" fill="url(#clay-sphere)"/>
    <!-- Specular Bevel Arc -->
    <path d="M34 44 C34 28 47 20 64 20" stroke="url(#gold-rim)" stroke-width="4" stroke-linecap="round" fill="none"/>

    <!-- Top 24K Gold Sphere Cap -->
    <circle cx="64" cy="16" r="6" fill="url(#gold-sphere)"/>

    <!-- Center Hollow Outer Gold Ring -->
    <circle cx="64" cy="48" r="18" fill="url(#gold-sphere)"/>
    <!-- Inset Cream Core -->
    <circle cx="64" cy="48" r="13" fill="url(#clay-light)"/>
    <!-- Center Sogdian Terracotta Star Gem -->
    <circle cx="64" cy="48" r="7" fill="url(#clay-sphere)"/>
    <polygon points="64,43 65.5,46.5 69,48 65.5,49.5 64,53 62.5,49.5 59,48 62.5,46.5" fill="url(#gold-sphere)"/>
  </g>
</svg>""",

    "icon-phone-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)" transform="rotate(-25 64 64)">
    <!-- Curved Handset Handle -->
    <path d="M38 42 C38 68 60 90 86 90" stroke="url(#clay-grad)" stroke-width="22" stroke-linecap="round" fill="none"/>
    <path d="M38 42 C38 68 60 90 86 90" stroke="url(#gold-rim)" stroke-width="4" stroke-linecap="round" fill="none"/>

    <!-- Top Earpiece -->
    <rect x="22" y="24" width="28" height="28" rx="14" fill="url(#clay-sphere)"/>
    <circle cx="36" cy="38" r="10" stroke="url(#gold-grad)" stroke-width="3" fill="url(#clay-light)"/>
    <circle cx="36" cy="38" r="4" fill="url(#gold-sphere)"/>

    <!-- Bottom Mouthpiece -->
    <rect x="78" y="80" width="28" height="28" rx="14" fill="url(#clay-sphere)"/>
    <circle cx="92" cy="94" r="10" stroke="url(#gold-grad)" stroke-width="3" fill="url(#clay-light)"/>
    <circle cx="92" cy="94" r="4" fill="url(#gold-sphere)"/>

    <!-- Sound Sparks -->
    <path d="M42 16 Q48 10 54 16" stroke="url(#gold-grad)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
    <path d="M98 72 Q104 66 110 72" stroke="url(#gold-grad)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
  </g>
</svg>""",

    "icon-email-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)">
    <!-- Envelope Body -->
    <rect x="18" y="32" width="92" height="64" rx="14" fill="url(#clay-sphere)"/>
    <!-- Envelope Gold Border -->
    <rect x="18" y="32" width="92" height="64" rx="14" stroke="url(#gold-grad)" stroke-width="2.5" fill="none"/>

    <!-- Fold Creases -->
    <!-- Bottom flaps -->
    <polygon points="19,95 64,62 109,95" fill="url(#clay-grad)"/>
    <path d="M19 95 L64 62 L109 95" stroke="url(#gold-rim)" stroke-width="1.8" fill="none"/>

    <!-- Top Flap Folded Down -->
    <polygon points="19,33 64,70 109,33" fill="url(#clay-light)"/>
    <path d="M19 33 L64 70 L109 33" stroke="url(#gold-grad)" stroke-width="2.5" fill="none"/>

    <!-- Embossed 24K Gold Wax Seal in Center -->
    <circle cx="64" cy="68" r="14" fill="url(#gold-sphere)"/>
    <!-- Wax drips / rosette -->
    <circle cx="64" cy="68" r="9" fill="url(#clay-grad)"/>
    <!-- Seal Star Motif -->
    <polygon points="64,62 65.5,66 69,66 66,68.5 67,72.5 64,70 61,72.5 62,68.5 59,66 62.5,66" fill="url(#gold-sphere)"/>
  </g>
</svg>""",

    "icon-star-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)">
    <!-- 8-Pointed Sogdian Star Faceted Mesh -->
    <!-- Facet Group 1 (Main Gold Ray Points) -->
    <polygon points="64,12 76,46 116,64 76,82 64,116 52,82 12,64 52,46" fill="url(#gold-sphere)"/>
    <!-- Diagonal Interstitial Points -->
    <polygon points="64,28 92,28 100,56 100,72 92,100 64,100 36,100 28,72 28,56 36,28" fill="url(#clay-grad)"/>
    <polygon points="64,14 74,48 114,64 74,80 64,114 54,80 14,64 54,48" stroke="url(#gold-rim)" stroke-width="2.5" fill="none"/>

    <!-- Central Terracotta Gem Core -->
    <circle cx="64" cy="64" r="20" fill="url(#clay-sphere)"/>
    <circle cx="64" cy="64" r="16" stroke="url(#gold-grad)" stroke-width="3" fill="url(#gold-sphere)"/>
    <circle cx="64" cy="64" r="10" fill="url(#clay-sphere)"/>

    <!-- Specular Highlight Glints -->
    <circle cx="59" cy="59" r="3.5" fill="#FFFFFF" opacity="0.9"/>
  </g>
</svg>""",

    "icon-audio-on-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)">
    <!-- Speaker Body (Rear Box) -->
    <rect x="20" y="44" width="24" height="40" rx="8" fill="url(#clay-sphere)"/>
    <rect x="22" y="46" width="20" height="36" rx="6" stroke="url(#gold-grad)" stroke-width="2" fill="none"/>

    <!-- Speaker Cone (Expanding Front) -->
    <polygon points="42,44 74,22 74,106 42,84" fill="url(#clay-grad)"/>
    <path d="M42 44 L74 22 V106 L42 84 Z" stroke="url(#gold-grad)" stroke-width="3" stroke-linejoin="round" fill="none"/>
    <!-- Speaker Rim Trim -->
    <line x1="74" y1="22" x2="74" y2="106" stroke="url(#gold-sphere)" stroke-width="4.5" stroke-linecap="round"/>

    <!-- Central Gold Driver Dome -->
    <ellipse cx="42" cy="64" rx="5" ry="12" fill="url(#gold-sphere)"/>

    <!-- Radiating Sound Waves (3 Golden Arcs) -->
    <path d="M85 50 C92 58 92 70 85 78" stroke="url(#gold-sphere)" stroke-width="4" stroke-linecap="round" fill="none"/>
    <path d="M96 40 C107 52 107 76 96 88" stroke="url(#gold-grad)" stroke-width="4" stroke-linecap="round" fill="none"/>
    <path d="M107 30 C122 46 122 82 107 98" stroke="url(#gold-grad)" stroke-width="3.5" stroke-linecap="round" fill="none"/>
  </g>
</svg>""",

    "icon-audio-off-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)">
    <!-- Speaker Body (Rear Box) -->
    <rect x="20" y="44" width="24" height="40" rx="8" fill="url(#clay-sphere)"/>
    <rect x="22" y="46" width="20" height="36" rx="6" stroke="url(#gold-grad)" stroke-width="2" fill="none"/>

    <!-- Speaker Cone -->
    <polygon points="42,44 74,22 74,106 42,84" fill="url(#clay-grad)"/>
    <path d="M42 44 L74 22 V106 L42 84 Z" stroke="url(#gold-grad)" stroke-width="3" stroke-linejoin="round" fill="none"/>
    <line x1="74" y1="22" x2="74" y2="106" stroke="url(#gold-sphere)" stroke-width="4.5" stroke-linecap="round"/>

    <!-- Mute Diagonal Slash -->
    <line x1="86" y1="44" x2="114" y2="84" stroke="url(#gold-sphere)" stroke-width="6" stroke-linecap="round"/>
    <line x1="114" y1="44" x2="86" y2="84" stroke="url(#gold-sphere)" stroke-width="6" stroke-linecap="round"/>
    <circle cx="100" cy="64" r="3" fill="#FFFFFF"/>
  </g>
</svg>""",

    "icon-trophy-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)">
    <!-- Stepped Pedestal Base -->
    <rect x="36" y="104" width="56" height="12" rx="4" fill="url(#clay-dark)"/>
    <rect x="42" y="96" width="44" height="8" rx="3" fill="url(#gold-grad)"/>
    <!-- Stem Column -->
    <rect x="58" y="78" width="12" height="20" rx="3" fill="url(#gold-sphere)"/>

    <!-- Trophy Side Handles -->
    <path d="M42 36 C18 36 18 72 46 72" stroke="url(#gold-sphere)" stroke-width="6" stroke-linecap="round" fill="none"/>
    <path d="M86 36 C110 36 110 72 82 72" stroke="url(#gold-sphere)" stroke-width="6" stroke-linecap="round" fill="none"/>

    <!-- Main Cup Body -->
    <path d="M38 24 C38 24 36 74 64 78 C92 74 90 24 90 24 Z" fill="url(#clay-sphere)"/>
    <!-- Top Gold Rim Bevel -->
    <ellipse cx="64" cy="24" rx="27" ry="8" fill="url(#gold-sphere)"/>
    <ellipse cx="64" cy="24" rx="23" ry="5.5" fill="url(#clay-dark)"/>

    <!-- Laurel Wreath Ornament in Gold -->
    <circle cx="64" cy="48" r="14" stroke="url(#gold-grad)" stroke-width="3" stroke-dasharray="6 3" fill="none"/>
    <circle cx="64" cy="48" r="8" fill="url(#gold-sphere)"/>
    <polygon points="64,43 65.5,46.5 69,48 65.5,49.5 64,53 62.5,49.5 59,48 62.5,46.5" fill="url(#clay-dark)"/>
  </g>
</svg>""",

    "icon-search-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)">
    <!-- Angled Handle (Terracotta + Gold Ferrule) -->
    <g transform="rotate(45 74 74)">
      <!-- Handle Body -->
      <rect x="68" y="76" width="14" height="38" rx="7" fill="url(#clay-sphere)"/>
      <rect x="68" y="76" width="14" height="38" rx="7" stroke="url(#clay-dark)" stroke-width="1.5" fill="none"/>
      <!-- Gold Ferrule Ring -->
      <rect x="66" y="68" width="18" height="10" rx="3" fill="url(#gold-sphere)"/>
      <!-- Gold Pommel End Cap -->
      <circle cx="75" cy="114" r="5" fill="url(#gold-sphere)"/>
    </g>

    <!-- Magnifying Glass Bezel (Burnished 24K Gold) -->
    <circle cx="52" cy="52" r="32" stroke="url(#gold-sphere)" stroke-width="9" fill="none"/>
    <!-- Inset Glass Lens with Specular Glare -->
    <circle cx="52" cy="52" r="27.5" fill="url(#clay-light)" opacity="0.35"/>
    <path d="M34 40 C38 32 46 28 56 28" stroke="#FFFFFF" stroke-width="4.5" stroke-linecap="round" fill="none" opacity="0.9"/>
    <circle cx="36" cy="56" r="3" fill="#FFFFFF" opacity="0.8"/>
  </g>
</svg>""",

    "icon-clock-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)">
    <!-- Top Crown Winder Loop -->
    <path d="M54 22 C54 14 74 14 74 22" stroke="url(#gold-grad)" stroke-width="4.5" fill="none"/>
    <rect x="60" y="18" width="8" height="7" rx="2" fill="url(#gold-sphere)"/>

    <!-- Clock Body Disc (Terracotta Claymorphism) -->
    <circle cx="64" cy="68" r="44" fill="url(#clay-sphere)"/>
    <!-- Outer 24K Gold Bezel Rim -->
    <circle cx="64" cy="68" r="44" stroke="url(#gold-sphere)" stroke-width="6" fill="none"/>
    <!-- Inner Dial Face (Cream Alabaster Clay) -->
    <circle cx="64" cy="68" r="36" fill="url(#clay-light)"/>

    <!-- Hour Markers (Golden Studs) -->
    <circle cx="64" cy="38" r="3.5" fill="url(#gold-sphere)"/> <!-- 12 -->
    <circle cx="94" cy="68" r="3.5" fill="url(#gold-sphere)"/> <!-- 3 -->
    <circle cx="64" cy="98" r="3.5" fill="url(#gold-sphere)"/> <!-- 6 -->
    <circle cx="34" cy="68" r="3.5" fill="url(#gold-sphere)"/> <!-- 9 -->
    <g fill="url(#clay-dark)">
      <circle cx="79" cy="42" r="2"/> <!-- 1 -->
      <circle cx="90" cy="53" r="2"/> <!-- 2 -->
      <circle cx="90" cy="83" r="2"/> <!-- 4 -->
      <circle cx="79" cy="94" r="2"/> <!-- 5 -->
      <circle cx="49" cy="94" r="2"/> <!-- 7 -->
      <circle cx="38" cy="83" r="2"/> <!-- 8 -->
      <circle cx="38" cy="53" r="2"/> <!-- 10 -->
      <circle cx="49" cy="42" r="2"/> <!-- 11 -->
    </g>

    <!-- Clock Hands (10:10 Majestic Pose) -->
    <!-- Hour Hand -->
    <line x1="64" y1="68" x2="48" y2="52" stroke="url(#gold-sphere)" stroke-width="5" stroke-linecap="round"/>
    <!-- Minute Hand -->
    <line x1="64" y1="68" x2="84" y2="46" stroke="url(#clay-dark)" stroke-width="4" stroke-linecap="round"/>
    <!-- Center Pivot Cap -->
    <circle cx="64" cy="68" r="5" fill="url(#gold-sphere)"/>
  </g>
</svg>""",

    "icon-lock-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)">
    <!-- Hardened 24K Gold Shackle Arch -->
    <path d="M40 58 V38 C40 22 88 22 88 38 V58" stroke="url(#gold-sphere)" stroke-width="12" stroke-linecap="round" fill="none"/>
    <path d="M42 56 V38 C42 24 86 24 86 38 V56" stroke="url(#gold-rim)" stroke-width="3" stroke-linecap="round" fill="none"/>

    <!-- Rounded Padlock Body (Terracotta Claymorphism) -->
    <rect x="24" y="52" width="80" height="62" rx="18" fill="url(#clay-sphere)"/>
    <rect x="24" y="52" width="80" height="62" rx="18" stroke="url(#gold-grad)" stroke-width="3" fill="none"/>

    <!-- Center Keyhole Bezel (Burnished Gold Medallion) -->
    <circle cx="64" cy="80" r="14" fill="url(#gold-sphere)"/>
    <circle cx="64" cy="80" r="10" fill="url(#clay-dark)"/>
    <!-- Keyhole Shape -->
    <circle cx="64" cy="78" r="4.5" fill="url(#clay-sphere)"/>
    <polygon points="61,80 67,80 68,91 60,91" fill="url(#clay-sphere)"/>
  </g>
</svg>""",

    "icon-mountain-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)">
    <!-- Medallion Frame Background -->
    <circle cx="64" cy="64" r="48" fill="url(#clay-light)"/>
    <circle cx="64" cy="64" r="48" stroke="url(#gold-sphere)" stroke-width="5" fill="none"/>

    <!-- 24K Gold Rising Sun & Beams -->
    <circle cx="64" cy="54" r="18" fill="url(#gold-sphere)"/>
    <!-- Radial Sun Rays -->
    <g stroke="url(#gold-grad)" stroke-width="3" stroke-linecap="round">
      <line x1="64" y1="30" x2="64" y2="24"/>
      <line x1="44" y1="38" x2="38" y2="34"/>
      <line x1="84" y1="38" x2="90" y2="34"/>
      <line x1="32" y1="54" x2="26" y2="54"/>
      <line x1="96" y1="54" x2="102" y2="54"/>
    </g>

    <!-- Mogol-Tau Twin Peaks (Terracotta Clay Mountains) -->
    <!-- Rear Peak -->
    <polygon points="76,40 106,94 48,94" fill="url(#clay-dark)"/>
    <polygon points="76,40 86,58 76,64 66,56" fill="url(#gold-rim)"/>
    <!-- Front Main Peak -->
    <polygon points="46,46 84,102 18,102" fill="url(#clay-sphere)"/>
    <polygon points="46,46 56,66 44,72 36,64" fill="url(#gold-rim)"/>

    <!-- Syr Darya River Wave Relief -->
    <path d="M22 98 Q42 88 64 98 Q86 108 106 98 L106 112 Q86 112 64 112 Q42 112 22 112 Z" fill="url(#clay-grad)"/>
    <path d="M22 98 Q42 88 64 98 Q86 108 106 98" stroke="url(#gold-grad)" stroke-width="3" fill="none"/>
  </g>
</svg>""",

    "icon-bus-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)">
    <!-- Wheels Base -->
    <rect x="28" y="98" width="14" height="14" rx="4" fill="url(#clay-dark)"/>
    <rect x="86" y="98" width="14" height="14" rx="4" fill="url(#clay-dark)"/>

    <!-- Bus Cabin Body -->
    <rect x="24" y="32" width="80" height="70" rx="16" fill="url(#clay-sphere)"/>
    <!-- Gold Trim Band -->
    <rect x="24" y="32" width="80" height="70" rx="16" stroke="url(#gold-grad)" stroke-width="2.5" fill="none"/>

    <!-- Destination Sign Box -->
    <rect x="40" y="36" width="48" height="10" rx="3" fill="url(#gold-sphere)"/>
    <rect x="44" y="39" width="40" height="4" rx="2" fill="url(#clay-dark)"/>

    <!-- Large Panoramic Windshield -->
    <rect x="30" y="50" width="68" height="26" rx="6" fill="url(#clay-light)"/>
    <line x1="64" y1="50" x2="64" y2="76" stroke="url(#clay-dark)" stroke-width="2"/>

    <!-- 24K Gold Round Headlights -->
    <circle cx="38" cy="88" r="7" fill="url(#gold-sphere)"/>
    <circle cx="38" cy="88" r="4" fill="#FFFFFF"/>
    <circle cx="90" cy="88" r="7" fill="url(#gold-sphere)"/>
    <circle cx="90" cy="88" r="4" fill="#FFFFFF"/>

    <!-- Radiator Grille -->
    <rect x="52" y="84" width="24" height="12" rx="3" fill="url(#gold-grad)"/>
    <line x1="56" y1="87" x2="72" y2="87" stroke="url(#clay-dark)" stroke-width="1.5"/>
    <line x1="56" y1="90" x2="72" y2="90" stroke="url(#clay-dark)" stroke-width="1.5"/>
    <line x1="56" y1="93" x2="72" y2="93" stroke="url(#clay-dark)" stroke-width="1.5"/>
  </g>
</svg>""",

    "icon-book-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)">
    <!-- Book Pages Block (Golden Edge) -->
    <rect x="32" y="24" width="72" height="84" rx="8" fill="url(#gold-grad)"/>
    <line x1="102" y1="26" x2="102" y2="106" stroke="url(#clay-light)" stroke-width="4"/>

    <!-- Terracotta Front Leather Cover -->
    <rect x="24" y="22" width="74" height="86" rx="8" fill="url(#clay-sphere)"/>
    <rect x="24" y="22" width="74" height="86" rx="8" stroke="url(#gold-grad)" stroke-width="2.5" fill="none"/>

    <!-- Spine Binding -->
    <rect x="22" y="20" width="12" height="90" rx="6" fill="url(#clay-dark)"/>
    <line x1="26" y1="36" x2="30" y2="36" stroke="url(#gold-grad)" stroke-width="2"/>
    <line x1="26" y1="64" x2="30" y2="64" stroke="url(#gold-grad)" stroke-width="2"/>
    <line x1="26" y1="92" x2="30" y2="92" stroke="url(#gold-grad)" stroke-width="2"/>

    <!-- Embossed 24K Gold Rosette on Cover -->
    <circle cx="62" cy="64" r="16" fill="url(#gold-sphere)"/>
    <circle cx="62" cy="64" r="11" fill="url(#clay-sphere)"/>
    <polygon points="62,56 64,61 69,61 65,64 67,69 62,66 57,69 59,64 55,61 60,61" fill="url(#gold-sphere)"/>
  </g>
</svg>""",

    "icon-camera-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)">
    <!-- Shutter Button & Flash on Top -->
    <rect x="34" y="28" width="14" height="8" rx="3" fill="url(#gold-sphere)"/>
    <rect x="80" y="24" width="18" height="12" rx="4" fill="url(#clay-dark)"/>
    <circle cx="89" cy="30" r="3.5" fill="url(#gold-sphere)"/>

    <!-- Camera Body (Terracotta Squircle) -->
    <rect x="18" y="34" width="92" height="66" rx="18" fill="url(#clay-sphere)"/>
    <rect x="18" y="34" width="92" height="66" rx="18" stroke="url(#gold-grad)" stroke-width="2.5" fill="none"/>

    <!-- Leather Grip Inset -->
    <rect x="24" y="44" width="22" height="46" rx="6" fill="url(#clay-dark)"/>

    <!-- 24K Gold Large Lens Barrel -->
    <circle cx="68" cy="68" r="26" fill="url(#gold-sphere)"/>
    <circle cx="68" cy="68" r="21" fill="url(#clay-dark)"/>
    <circle cx="68" cy="68" r="14" fill="url(#clay-sphere)"/>
    <!-- Glass Specular Reflection -->
    <circle cx="68" cy="68" r="9" fill="url(#gold-sphere)"/>
    <circle cx="64" cy="64" r="3" fill="#FFFFFF"/>
  </g>
</svg>""",

    "icon-plane-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)" transform="rotate(-30 64 64)">
    <!-- Fuselage Body -->
    <path d="M64 16 C60 28 58 84 58 100 C58 106 70 106 70 100 C70 84 68 28 64 16 Z" fill="url(#clay-sphere)"/>
    <!-- Cockpit Window -->
    <ellipse cx="64" cy="28" rx="4" ry="7" fill="url(#gold-sphere)"/>

    <!-- Swept 24K Gold Wings -->
    <polygon points="64,52 18,74 22,82 64,68" fill="url(#gold-sphere)"/>
    <polygon points="64,52 110,74 106,82 64,68" fill="url(#gold-sphere)"/>

    <!-- Tail Wings -->
    <polygon points="64,92 40,104 42,108 64,100" fill="url(#clay-grad)"/>
    <polygon points="64,92 88,104 86,108 64,100" fill="url(#clay-grad)"/>
    <!-- Tail Fin -->
    <rect x="62.5" y="86" width="3" height="16" rx="1.5" fill="url(#gold-sphere)"/>
  </g>
</svg>""",

    "icon-print-3d": f"""<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
{SHARED_DEFS}
  <g filter="url(#clay-shadow)">
    <!-- Rear Paper Feed Sheet -->
    <rect x="36" y="16" width="56" height="34" rx="4" fill="url(#clay-light)"/>
    <line x1="42" y1="24" x2="86" y2="24" stroke="url(#gold-grad)" stroke-width="2"/>
    <line x1="42" y1="32" x2="76" y2="32" stroke="url(#gold-grad)" stroke-width="2"/>

    <!-- Printer Housing Body -->
    <rect x="20" y="44" width="88" height="48" rx="14" fill="url(#clay-sphere)"/>
    <rect x="20" y="44" width="88" height="48" rx="14" stroke="url(#gold-grad)" stroke-width="2.5" fill="none"/>

    <!-- Control Buttons -->
    <circle cx="94" cy="56" r="4" fill="url(#gold-sphere)"/>
    <circle cx="94" cy="66" r="3" fill="url(#clay-dark)"/>

    <!-- Output Slot -->
    <rect x="32" y="70" width="64" height="8" rx="3" fill="url(#clay-dark)"/>

    <!-- Emerging Golden Ticket Pass -->
    <rect x="36" y="74" width="56" height="36" rx="6" fill="url(#gold-sphere)"/>
    <rect x="42" y="82" width="44" height="4" rx="2" fill="url(#clay-dark)"/>
    <rect x="42" y="90" width="32" height="4" rx="2" fill="url(#clay-dark)"/>
    <rect x="42" y="98" width="20" height="3" rx="1.5" fill="url(#clay-dark)"/>
  </g>
</svg>"""
}

# Duplicate icon-audio-3d as alias to icon-audio-on-3d
ICONS_SVG["icon-audio-3d"] = ICONS_SVG["icon-audio-on-3d"]


def main():
    print(f"Generating {len(ICONS_SVG)} 3D Gold & Claymorphism icons...")

    # Step 1: Write all SVGs
    for name, svg_content in ICONS_SVG.items():
        svg_path = ICONS_DIR / f"{name}.svg"
        svg_path.write_text(svg_content.strip(), encoding="utf-8")
        print(f"  [SVG] Saved: {svg_path.name}")

    # Step 2: Use Playwright Chromium to render pixel-perfect 128x128 transparent WebP files
    print("\nRendering 128x128 WebP assets via Playwright Chromium...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 128, "height": 128})

        for name, svg_content in ICONS_SVG.items():
            webp_path = ICONS_DIR / f"{name}.webp"

            # Render SVG via HTML wrapper with transparent background
            html = f"""<!DOCTYPE html>
<html>
<head>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{ width: 128px; height: 128px; background: transparent; overflow: hidden; }}
    svg {{ width: 128px; height: 128px; display: block; }}
  </style>
</head>
<body>
{svg_content}
</body>
</html>"""
            page.set_content(html)
            page.wait_for_timeout(50)

            # Capture PNG bytes with transparent background
            png_bytes = page.screenshot(omit_background=True)

            # Convert to WebP using Pillow
            import io
            img = Image.open(io.BytesIO(png_bytes))
            img.save(webp_path, format="WEBP", lossless=True, quality=95)
            print(f"  [WEBP] Saved: {webp_path.name} ({webp_path.stat().st_size} bytes)")

        browser.close()

    print("\nAll 3D Gold & Claymorphism icons generated successfully!")


if __name__ == "__main__":
    main()
