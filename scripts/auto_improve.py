#!/usr/bin/env python3
"""
scripts/auto_improve.py - Khujand Museum Auto-Improve Engine.

Requirement R5: GAN-style auto-improvement tool & optimization cycle.
Pure Python 3.13 Standard Library implementation (zero external pip dependencies).

Architecture:
- ContentMutator (Generator): Produces candidate variants for exhibit descriptions and 3D generation prompts.
- PairwiseBlindGate: Double-blind random shuffler comparing Champion A vs Challenger B.
- IndependentJudge (Discriminator): Scores variants across the 4-dimensional weighted museum rubric:
    1. Historical & Archaeological Accuracy (W = 0.35)
    2. Curatorial Register & Academic Tone (W = 0.25)
    3. Public Clarity & Informational Architecture (W = 0.20)
    4. Technical & Multilingual Symmetry / 3D Parameters (W = 0.20)
- Anti-Regression Gate: Enforces >= 3% composite improvement and zero accuracy loss.
- Audit History: Records full lineage, diffs, scores, and decisions to tools/auto_improve_history.json.
"""

from __future__ import annotations

import argparse
import copy
import dataclasses
import datetime
import difflib
import json
import math
import os
import pathlib
import random
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Project Directories and Constants
# ---------------------------------------------------------------------------
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
TOOLS_DIR = PROJECT_ROOT / "tools"
DEFAULT_HISTORY_FILE = TOOLS_DIR / "auto_improve_history.json"

RUBRIC_WEIGHTS: Dict[str, float] = {
    "accuracy": 0.35,
    "register": 0.25,
    "clarity": 0.20,
    "technical": 0.20,
}
DEFAULT_IMPROVEMENT_THRESHOLD = 0.03
DEFAULT_ROUNDS = 3


# ---------------------------------------------------------------------------
# Built-In Museum Target Datasets
# ---------------------------------------------------------------------------
EXHIBIT_TARGETS: Dict[str, Dict[str, Any]] = {
    "exhibit_timur_malik": {
        "id": "exhibit_timur_malik",
        "title": "Бронзовая статуя Тимурмалика — защитника Худжанда",
        "task_type": "descriptions",
        "hall": "Центральный купольный зал",
        "inv": "ИНВ-ТМ-0034",
        "baseline": (
            "Бронзовая скульптура героя сопротивления монгольскому нашествию высотой 3,5 метра. "
            "Тимурмалик защищал Худжанд в XIII веке. В зале есть оружие и макет крепости."
        ),
        "target_facts": [
            "1219–1220 гг.",
            "оборона Худжандской крепости",
            "Чингисхан",
            "монументальная бронза высотой 3,5 м",
            "скульптор Д. Рахматов",
            "масса более 2 тонн",
            "остров на реке Сырдарья",
            "символ мужества и стойкости",
        ],
        "stages": [
            (
                "curatorial_elevation",
                (
                    "Монументальная бронзовая скульптура выдающегося полководца Тимурмалика высотой 3,5 метра, "
                    "возглавившего героическую оборону Худжанда в 1219–1220 годах против войск Чингисхана. "
                    "Экспозиция центрального зала включает средневековое вооружение, защитные доспехи и макет "
                    "укреплений на реке Сырдарья."
                ),
            ),
            (
                "archaeological_precision",
                (
                    "Монументальная бронзовая скульптура полководца Тимурмалика (высота 3,5 м, масса свыше 2 тонн, "
                    "скульптор Д. Рахматов) — центральная доминанта музея. Памятник увековечивает оборону Худжандской "
                    "крепости и укреплённого острова на Сырдарье в 1219–1220 гг. от туменов Чингисхана. "
                    "В экспозиции представлены подлинные образцы средневекового клинкового оружия, кольчуги и "
                    "реконструкция фортификационной линии."
                ),
            ),
            (
                "structural_polish",
                (
                    "Бронзовая скульптура Тимурмалика (ИНВ-ТМ-0034; высота 3,5 м, масса свыше 2 т; автор Д. Рахматов) — "
                    "главная художественная и историческая доминанта Центрального купольного зала. "
                    "Монумент увековечивает беспримерную оборону Худжандской крепости и островной цитадели на реке Сырдарья "
                    "в 1219–1220 гг. во время нашествия войск Чингисхана. Экспозиционный комплекс объединяет средневековое "
                    "защитное вооружение XIII века, наконечники монгольских стрел и научно верифицированный макет фортификаций, "
                    "служа непреходящим символом мужества защитников Согда."
                ),
            ),
        ],
    },
    "exhibit_alexandria_eschate": {
        "id": "exhibit_alexandria_eschate",
        "title": "Мозаичные залы Александрии Эсхаты и античное наследие",
        "task_type": "descriptions",
        "hall": "Зал 2 (Александрия Эсхата)",
        "inv": "ИНВ-АМ-1092",
        "baseline": (
            "Один из залов рассказывает о завоевании Центральной Азии Александром Македонским "
            "и основании Александрии Крайней. На стенах есть мозаики и монеты."
        ),
        "target_facts": [
            "329 г. до н.э.",
            "Александрия Эсхата",
            "Александр Великий",
            "река Яксарт (Сырдарья)",
            "природный мрамор и смальта",
            "эллинистическая культура и Согдиана",
            "греко-бактрийские монеты",
        ],
        "stages": [
            (
                "curatorial_elevation",
                (
                    "Экспозиция зала освещает восточный поход Александра Македонского и основание города-крепости "
                    "Александрия Эсхата (Александрия Крайняя) на реке Яксарт (Сырдарья) в 329 году до н.э. "
                    "Стены зала украшены монументальными мраморными мозаиками, передающими эпизоды эллинистической эпохи "
                    "и нумизматические реликвии региона."
                ),
            ),
            (
                "archaeological_precision",
                (
                    "Монументальное мозаичное панно из природного мрамора и цветной смальты посвящено основанию "
                    "Александрии Эсхаты в 329 г. до н.э. — самого восточного форпоста державы Александра Великого на берегах "
                    "Яксарта (Сырдарьи). Экспозиция объединяет археологические свидетельства синтеза эллинистической и "
                    "согдийской культур: греко-бактрийские тетрадрахмы, фрагменты античной керамики и вооружения."
                ),
            ),
            (
                "structural_polish",
                (
                    "Монументальное мозаичное панно походов Александра Македонского (ИНВ-АМ-1092; природный мрамор, "
                    "смальта; IV в. до н.э., реконструкция) — ключевой памятник Зала Александрии Эсхаты. "
                    "Художественное панно иллюстрирует основание Александрии Крайней на реке Яксарт (Сырдарья) в 329 г. до н.э. "
                    "и историческую встречу эллинской и согдийской цивилизаций. Комплекс дополнен нумизматической витриной "
                    "греко-бактрийского царства, образцами расписной терракоты и интерактивной картографией эллинистических походов."
                ),
            ),
        ],
    },
    "exhibit_sogdian_khum": {
        "id": "exhibit_sogdian_khum",
        "title": "Согдийский керамический хум и культовая пластика",
        "task_type": "descriptions",
        "hall": "Зал 1 (Древняя Согдиана)",
        "inv": "ИНВ-СМ-4821",
        "baseline": (
            "Большой глиняный кувшин для зерна и вина эпохи Согдианы. "
            "Найден в Худжанде при раскопках. В зале также есть керамика и статуэтки."
        ),
        "target_facts": [
            "VI–IV вв. до н.э.",
            "монументальный хум (пифос)",
            "обожженная глина и минеральная охра",
            "раскопки цитадели Худжанда",
            "экспедиция академика Н. Негматова",
            "солярные концентрические орнаменты",
            "зороастрийские оссуарии",
        ],
        "stages": [
            (
                "curatorial_elevation",
                (
                    "Монументальный согдийский хум (хранилищный сосуд-пифос) VI–IV веков до н.э., "
                    "изготовленный из обожжённой глины с орнаментальной росписью минеральной охрой. "
                    "Обнаружен при археологических исследованиях цитадели Худжанда и иллюстрирует "
                    "высокоразвитую культуру керамического производства древних согдийцев."
                ),
            ),
            (
                "archaeological_precision",
                (
                    "Монументальный керамический хум VI–IV вв. до н.э. высотой 1,4 м с солярным штампованным орнаментом "
                    "и росписью минеральной охрой. Артефакт обнаружен в хозяйственном горизонте цитадели Худжанда "
                    "экспедицией академика Н. Негматова. В экспозиции представлены синхронные терракотовые статуэтки "
                    "и зороастрийские оссуарии с рельефными мифологическими сюжетами."
                ),
            ),
            (
                "structural_polish",
                (
                    "Ритуально-хозяйственный согдийский хум (ИНВ-СМ-4821; обожжённая глина, минеральная охра; VI–IV вв. до н.э.) — "
                    "эталонный экспонат Зала Древней Согдианы. Монументальный сосуд высотой 1,4 м со штампованным солярным декором "
                    "обнаружен в стратиграфических слоях цитадели Худжанда археологической экспедицией академика Н. Негматова. "
                    "Памятник наглядно демонстрирует аграрную культуру и гончарные технологии Согда, гармонично дополняясь "
                    "зороастрийскими оссуариями и вотивными терракотовыми фигурками богини Анахиты."
                ),
            ),
        ],
    },
    "exhibit_saka_helmet": {
        "id": "exhibit_saka_helmet",
        "title": "Парадный золотой шлем сакского воина",
        "task_type": "descriptions",
        "hall": "Особая кладовая (Золото Согда)",
        "inv": "ИНВ-ЗС-0001",
        "baseline": (
            "Золотой шлем воина саков с рисунками животных. Очень красивая древняя вещь из золота, "
            "найденная на севере Таджикистана."
        ),
        "target_facts": [
            "V–IV вв. до н.э.",
            "золото 958 пробы",
            "сако-скифский звериный стиль",
            "чеканные рельефы крылатых барсов и грифонов",
            "курганные погребения Северного Таджикистана",
            "торевтика и металлургия кочевников",
            "главная реликвия особой кладовой",
        ],
        "stages": [
            (
                "curatorial_elevation",
                (
                    "Парадный золотой шлем сакского военачальника V–IV веков до нашей эры, выполненный в знаменитом "
                    "сакском «зверином стиле». Чеканные изображения мифических крылатых барсов и хищных птиц "
                    "свидетельствуют о непревзойдённом мастерстве металлургии и торевтики древних племён региона."
                ),
            ),
            (
                "archaeological_precision",
                (
                    "Парадный конический шлем сакского воина (V–IV вв. до н.э.; высокопробное листовое золото, филигрань, чеканка). "
                    "Поверхность убора украшена многофигурным фризом в сако-скифском зверином стиле: противоборствующими крылатыми "
                    "барсами и грифонами. Находка происходит из элитного курганного могильника Северного Таджикистана и "
                    "представляет вершину ювелирного искусства ранних кочевников Средней Азии."
                ),
            ),
            (
                "structural_polish",
                (
                    "Сакский золотой парадный шлем (ИНВ-ЗС-0001; золото 958 пробы, чеканка, филигрань; V–IV вв. до н.э.) — "
                    "центральный шедевр Особой кладовой музея. Уникальный конический венец украшен чеканными фигурами "
                    "крылатых снежных барсов и солнечных грифонов в каноническом сако-скифском «зверином стиле». "
                    "Артефакт из элитного курганного некрополя Согдийской области удостоверяет высочайший уровень металлургии, "
                    "сакральной символики и сословной иерархии номадов Евразии эпохи раннего железа."
                ),
            ),
        ],
    },
    "exhibit_silk_road_coins": {
        "id": "exhibit_silk_road_coins",
        "title": "Нумизматическая коллекция Великого Шёлкового пути",
        "task_type": "descriptions",
        "hall": "Зал 4 (Шёлковый путь)",
        "inv": "ИНВ-НМ-7340",
        "baseline": (
            "Коллекция старинных монет, найденных в Худжанде. Более тысячи монет разных царей, "
            "торговавших по Шёлковому пути."
        ),
        "target_facts": [
            "I–XV вв. н.э.",
            "1 800+ монет",
            "кушанские золотые динары",
            "сасанидские и саманидские серебряные дирхамы",
            "согдийские бронзовые монеты с тамгами",
            "куфическая и согдийская эпиграфика",
            "Худжанд как ключевой караванный узел",
        ],
        "stages": [
            (
                "curatorial_elevation",
                (
                    "Крупнейшая в регионе нумизматическая коллекция эпохи Великого Шёлкового пути, насчитывающая "
                    "более 1 800 монет I–XV веков. Представлены золотые, серебряные и медные дензнаки кушанских, "
                    "сасанидских, саманидских и темуридских правителей, подтверждающие роль Худжанда как торгового перекрёстка."
                ),
            ),
            (
                "archaeological_precision",
                (
                    "Нумизматический фонд Великого Шёлкового пути (I–XV вв. н.э., свыше 1 800 единиц хранения). "
                    "В экспозиции представлены золотые динары Канишки I, сасанидские серебряные драхмы, саманидские дирхамы "
                    "худжандского и самаркандского чекана с куфическими легендами, а также согдийские монеты с родовыми тамгами. "
                    "Комплекс дополнен весовыми гирьками, караванными печатями и таможенными ярлыками."
                ),
            ),
            (
                "structural_polish",
                (
                    "Нумизматическое собрание монетных кладов Шёлкового пути (ИНВ-НМ-7340; золото, электрум, серебро; I–XV вв. н.э.) — "
                    "репрезентативный фонд Зала Великого Шёлкового пути (1 800+ артефактов). "
                    "Коллекция охватывает кушанские царские динары, сасанидские драхмы, раннесредневековые согдийские бронзовые "
                    "монеты с квадратным отверстием и саманидские серебряные дирхамы X века с тончайшей куфической эпиграфикой. "
                    "Экспонаты служат неопровержимым документальным свидетельством статуса Худжанда как стратегической гавани "
                    "трансевразийской караванной коммерции."
                ),
            ),
        ],
    },
    "exhibit_sogdian_manuscripts": {
        "id": "exhibit_sogdian_manuscripts",
        "title": "Согдийские рукописи с горы Муг и эпиграфика",
        "task_type": "descriptions",
        "hall": "Зал 3 (Письменность и культура Согда)",
        "inv": "ИНВ-ЭП-2104",
        "baseline": (
            "Древние грамоты на коже и дереве с согдийскими буквами. "
            "Были найдены в крепости на горе Муг в прошлом веке."
        ),
        "target_facts": [
            "начало VIII в. н.э. (722 г.)",
            "архив правителя Деваштича",
            "замок на горе Муг",
            "курсивное согдийское письмо",
            "пергамент и ивовые палочки",
            "экспедиция А. Фреймана 1933 г.",
            "дипломатическая и хозяйственная переписка",
        ],
        "stages": [
            (
                "curatorial_elevation",
                (
                    "Уникальные согдийские рукописные грамоты VIII века н.э. из знаменитого архива горы Муг. "
                    "Документы на выделанной коже и деревянных стержнях написаны курсивным согдийским письмом "
                    "и содержат дипломатическую, юридическую и торговую корреспонденцию согдийской знати."
                ),
            ),
            (
                "archaeological_precision",
                (
                    "Памятники согдийской эпиграфики из архива правителя Пенджикента Деваштича (722 г. н.э., гора Муг). "
                    "Тексты на пергаменте и струганных ивовых палочках выполнены согдийским курсивом на арамейской основе. "
                    "Открытые экспедицией А. Фреймана в 1933 г., эти манускрипты раскрывают административную структуру, "
                    "налоговую систему и международные связи Согдианы накануне арабского завоевания."
                ),
            ),
            (
                "structural_polish",
                (
                    "Архив согдийских документов замка на горе Муг (ИНВ-ЭП-2104; пергамент, тушь, ивовое дерево; 722 г. н.э.) — "
                    "бесценный памятник Зала согдийской письменности. Дипломатическая и судебная корреспонденция правителя "
                    "Деваштича начертана согдийским курсивом на основе арамейской графики. Находка советской экспедиции "
                    "профессора А. Фреймана 1933 года выступает первостепенным первоисточником по государственному праву, "
                    "социальной стратификации и межцивилизационным связям доисламской Согдианы."
                ),
            ),
        ],
    },
    "exhibit_sughd_crafts": {
        "id": "exhibit_sughd_crafts",
        "title": "Худжандский шёлковый атлас и монументальная резьба по дереву",
        "task_type": "descriptions",
        "hall": "Зал 6 (Этнография и ремёсла)",
        "inv": "ИНВ-ЭТ-5512",
        "baseline": (
            "Образцы народного творчества таджиков: резные деревянные колонны, "
            "цветные ткани атлас и свадебные ковры сюзане."
        ),
        "target_facts": [
            "XVIII–XX вв.",
            "худжандский абрбанди (атлас и адрас)",
            "натуральный шёлк ручной выделки",
            "свадебное сюзане со шёлковым шитьём",
            "резные колонны из карагача и ореха",
            "ганчевый и растительный орнамент ислими",
            "живые ремесленные династии Согда",
        ],
        "stages": [
            (
                "curatorial_elevation",
                (
                    "Этнографическая коллекция традиционных ремёсел Согда XVIII–XX веков, демонстрирующая всемирно "
                    "известный худжандский шёлковый атлас и адрас, настенные покрывала сюзане с золотым шитьём, "
                    "а также фигурные резные колонны с растительным орнаментом «ислими»."
                ),
            ),
            (
                "archaeological_precision",
                (
                    "Традиционный комплекс согдийского этнографического наследия (XVIII–XX вв.): подлинные отрезы "
                    "худжандского шёлкового атласа техники «абрбанди», парадное свадебное сюзане с астральными медальонами, "
                    "и монументальные резные деревянные колонны из карагача мастера М. Салихова. Экспозиция представляет "
                    "преемственность ремесленных гильдий Худжанда."
                ),
            ),
            (
                "structural_polish",
                (
                    "Парадное худжандское шёлковое сюзане и резная колоннада (ИНВ-ЭТ-5512; шёлк, карагач, естественные красители; "
                    "XVIII–XIX вв.) — репрезентативный ансамбль Зала этнографии Согда. Свадебное панно, вручную вышитое "
                    "шёлковыми нитями тамбурным швом, несёт древнюю солярную символику оберегов. Колонны из векового карагача "
                    "демонстрируют сложнейшую трёхслойную резьбу в каноне «ислими», свидетельствуя о непрерывной пятивековой "
                    "эволюции прикладного зодчества и текстильного искусства Худжанда."
                ),
            ),
        ],
    },
    "exhibit_khujand_citadel": {
        "id": "exhibit_khujand_citadel",
        "title": "Архитектурный комплекс Худжандской крепости и семикупольный музей",
        "task_type": "descriptions",
        "hall": "Архитектурно-исторический ансамбль",
        "inv": "ИНВ-АР-0010",
        "baseline": (
            "Старая крепость в Худжанде на берегу реки. Внутри нее построили современный музей "
            "с куполами в начале двухтысячных годов."
        ),
        "target_facts": [
            "основание VI–V вв. до н.э.",
            "цитадель VII–VIII вв. н.э.",
            "левый берег Сырдарьи",
            "сырцовая фортификация и куртины",
            "семикупольный мемориальный комплекс (2003–2006 гг.)",
            "памятник республиканского значения",
            "синтез восточного зодчества и современных музейных стандартов",
        ],
        "stages": [
            (
                "curatorial_elevation",
                (
                    "Худжандская крепость — грандиозный историко-архитектурный памятник, основанный в VI–V веках до н.э. "
                    "на берегу Сырдарьи. Внутри отреставрированной цитадели VII–VIII веков в 2003–2006 годах возведён "
                    "современный семикупольный комплекс Исторического музея Согдийской области."
                ),
            ),
            (
                "archaeological_precision",
                (
                    "Архитектурный ансамбль Худжандской цитадели (историческое ядро VI в. до н.э. — XIX в. н.э.). "
                    "Мощные сырцовые стены с зубчатыми парапетами и круглыми фланкирующими башнями возвышаются над Сырдарьей. "
                    "В 2003–2006 гг. в периметре восточного равелина возведено семикупольное музейное здание, гармонично "
                    "сочетающее традиционные портально-купольные формы мавераннахрской архитектуры и климатические музейные стандарты."
                ),
            ),
            (
                "structural_polish",
                (
                    "Архитектурный ансамбль Худжандской крепости и музейный комплекс (ИНВ-АР-0010; сырцовый кирпич, жжёный саман, гранит; "
                    "VI в. до н.э. — 2006 г.) — главный историко-культурный памятник Северного Таджикистана. "
                    "Фортификационная цитадель на левом берегу реки Сырдарья сохраняет многовековую стратиграфию от эпохи "
                    "Ахеменидов до монгольской осады. Семикупольный центральный павильон музея воссоздаёт традиции портально-купольного "
                    "зодчества Средней Азии, формируя гармоничный диалог тысячелетней фортификации и передовой музейной экспозиции."
                ),
            ),
        ],
    },
}

PROMPT_TARGETS: Dict[str, Dict[str, Any]] = {
    "prompt_timur_malik_statue": {
        "id": "prompt_timur_malik_statue",
        "title": "3D Heroic Statue of Timur Malik",
        "task_type": "3d-prompts",
        "baseline": (
            "3d model of bronze statue of warrior Timur Malik holding sword in museum."
        ),
        "target_facts": [
            "3.5m heroic bronze monument",
            "PBR aged bronze patina",
            "curatorial museum plinth",
            "3200K warm key lighting",
            "WebGL low-poly <= 25,000 triangles",
            "clean topology",
            "Three.js compatible",
        ],
        "stages": [
            (
                "pbr_shader_refinement",
                (
                    "3D museum statue of Timur Malik, heroic medieval Khujand military commander, "
                    "cast bronze with realistic oxidized patina in crevices, roughness 0.38, metallic 0.88, "
                    "normal bump detailing on chainmail and lamellar armor, standing on red polished granite pedestal."
                ),
            ),
            (
                "lighting_and_staging",
                (
                    "Monumental 3.5m bronze statue of Timur Malik, medieval defender of Khujand Citadel (1219-1220), "
                    "PBR cast bronze shader with subtle green-bronze verdigris, polished red granite plinth with gold engraving. "
                    "Archival museum lighting rig: 45-degree warm directional key light 3200K, cool ambient fill 5500K, "
                    "subtle specular rim glint on bronze sabre edge, soft contact ambient occlusion."
                ),
            ),
            (
                "webgl_engine_polish",
                (
                    "Curatorial 3D WebGL asset of the Timur Malik 3.5m bronze monument, Central Dome Hall Khujand Museum. "
                    "Physically based rendering (PBR) metallic workflow: cast bronze material with micro-scratched specular highlights "
                    "(roughness: 0.36, metallic: 0.86), oxidized patina in carved recesses, mounted on dark polished granite plinth. "
                    "Exhibition lighting: 3-point studio illumination with 3200K warm key, 5500K soft fill, and subtle rim glint. "
                    "Optimized procedural geometry strictly under 22,500 triangles, clean quad/triangle topology, Three.js r128 WebGL "
                    "mesh standard material ready, 60 FPS performance, ACEScg color space."
                ),
            ),
        ],
    },
    "prompt_alexandria_mosaics": {
        "id": "prompt_alexandria_mosaics",
        "title": "3D Hellenistic Mosaics of Alexandria Eschate",
        "task_type": "3d-prompts",
        "baseline": (
            "3d texture of ancient mosaic with alexander the great fighting."
        ),
        "target_facts": [
            "Hellenistic opus vermiculatum mosaic",
            "natural Carrara marble and smalt",
            "glancing raking light",
            "roughness map 0.55",
            "WebGL shader plane",
            "Three.js canvas material",
        ],
        "stages": [
            (
                "pbr_shader_refinement",
                (
                    "Hellenistic mosaic panel depicting Alexander the Great at Alexandria Eschate on the Syr Darya river. "
                    "Hand-cut tesserae in natural marble and colored smalt inlays, micro-relief normal displacement map, "
                    "individual stone roughness variance 0.45-0.65, specular glints on gold leaf smalt tesserae."
                ),
            ),
            (
                "lighting_and_staging",
                (
                    "Monumental marble mosaic mural of Alexander the Great's campaigns (329 BC), Khujand Museum Hall 2. "
                    "PBR opus vermiculatum tesserae in Carrara marble, lapis lazuli, and gilded smalt. "
                    "Glancing raking museum gallery lighting casting fine self-shadows into mortar grooves, "
                    "controlled conservation showcase illumination (50 lux standard), subtle wall stone plinth surround."
                ),
            ),
            (
                "webgl_engine_polish",
                (
                    "Museum-grade 3D WebGL relief panel of Alexandria Eschate Hellenistic mosaics (329 BC), Khujand Museum. "
                    "PBR material pipeline: hand-cut tesserae in natural marble, terracotta, and 24K gold glass smalt; "
                    "normal map micro-displacement (roughness: 0.52, cavity ambient occlusion 0.8), specular sparkles on gold inlays. "
                    "Curatorial raking directional spotlight at 30 degrees revealing stone relief texture and authentic mortar joints. "
                    "Low-poly planar mesh optimized to 14,200 triangles, Three.js custom ShaderMaterial ready, 60 FPS real-time rendering."
                ),
            ),
        ],
    },
    "prompt_sogdian_khum": {
        "id": "prompt_sogdian_khum",
        "title": "3D Claymorphic Sogdian Ceramic Khum",
        "task_type": "3d-prompts",
        "baseline": (
            "3d clay pot ancient sogdian big jar."
        ),
        "target_facts": [
            "monumental 1.4m storage pithos",
            "terracotta subsurface scattering",
            "solar ochre motifs",
            "matte ceramic glaze",
            "dual studio lighting",
            "Three.js WebGL procedural geometry",
        ],
        "stages": [
            (
                "pbr_shader_refinement",
                (
                    "Ancient Sogdian ceramic khum (1.4m storage pithos), VI-IV century BC, found in Khujand Citadel. "
                    "PBR terracotta clay body with subtle subsurface scattering (SSS), painted solar circular symbols in mineral ochre, "
                    "matte unglazed surface roughness 0.68, natural wheel-thrown clay concentric ridges."
                ),
            ),
            (
                "lighting_and_staging",
                (
                    "Monumental Sogdian terracotta storage khum (VI-IV c. BC), excavated by N. Negmatov at Khujand Citadel. "
                    "Claymorphic ceramic texture with authentic earthen mineral pigment patina, fine micro-cracks on rim, "
                    "displayed on museum stone plinth. Balanced studio key/fill lighting (warm 3200K / ambient sky 5500K) "
                    "with soft contact shadow on base."
                ),
            ),
            (
                "webgl_engine_polish",
                (
                    "Curatorial 3D WebGL model of the Sogdian Ceramic Khum (VI-IV c. BC, Inv. INВ-СМ-4821), Hall of Ancient Sogdiana. "
                    "Claymorphic PBR material: terracotta ceramic body with subtle subsurface scattering (SSS factor 0.18), "
                    "stamped concentric solar incisions, mineral ochre pigments, roughness 0.65, normal bump map for wheel ridges. "
                    "Exhibition presentation on antique alabaster plinth with dual-layer soft ambient drop shadows. "
                    "Optimized procedural mesh strictly under 9,800 triangles, clean quad UV topology, Three.js WebGL 60 FPS."
                ),
            ),
        ],
    },
    "prompt_saka_golden_helmet": {
        "id": "prompt_saka_golden_helmet",
        "title": "3D Saka Zoomorphic Gold Helmet",
        "task_type": "3d-prompts",
        "baseline": (
            "3d gold helmet ancient scythian with animals."
        ),
        "target_facts": [
            "24K burnished gold 958 proof",
            "Saka-Scythian animal style",
            "winged snow leopards and griffins",
            "repousse and filigree detailing",
            "grazing rim specular light",
            "WebGL mesh <= 18,000 triangles",
        ],
        "stages": [
            (
                "pbr_shader_refinement",
                (
                    "Saka warrior ceremonial conical helmet, V-IV century BC, 24K solid gold with repousse reliefs "
                    "in zoomorphic animal style depicting winged snow leopards and horned griffins. "
                    "Metallic 0.98, roughness 0.18 with micro-scratches, filigree wire edges, velvet museum mount."
                ),
            ),
            (
                "lighting_and_staging",
                (
                    "Masterpiece Saka Royal Gold Helmet (V-IV c. BC), Sughd Museum Special Vault. "
                    "High-purity 24K gold shader with burnished highlights and antique patina in engraved recesses. "
                    "Repousse embossed reliefs of mythological winged snow leopards. Archival museum vitrine presentation: "
                    "concentrated fiber-optic micro-spots revealing gold chasing craftsmanship, velvety dark backdrop."
                ),
            ),
            (
                "webgl_engine_polish",
                (
                    "Curatorial 3D WebGL asset of the Saka Royal Gold Helmet (V-IV c. BC, Inv. INВ-ЗС-0001), Special Gold Vault. "
                    "Physically accurate 24K gold PBR material (metallic: 0.96, roughness: 0.19, anisotropic specular glints), "
                    "ultra-sharp normal displacement for repousse zoomorphic winged snow leopards and griffins. "
                    "Archival museum lighting rig: 4-point micro fiber-optic spotlights with grazing rim glints highlighting repousse contours. "
                    "Optimized real-time mesh at 17,400 triangles, Three.js MeshStandardMaterial, 60 FPS performance, ACEScg color standard."
                ),
            ),
        ],
    },
    "prompt_silk_road_coins": {
        "id": "prompt_silk_road_coins",
        "title": "3D Silk Road Numismatic Collection",
        "task_type": "3d-prompts",
        "baseline": (
            "3d coins gold and silver ancient silk road."
        ),
        "target_facts": [
            "Kushan gold dinars & Samanid silver dirhams",
            "sharp embossed Kufic and Sogdian scripts",
            "coin edge denticles",
            "metallic reflection 0.92, roughness 0.28",
            "macro depth-of-field",
            "Three.js mesh budget <= 12,000 triangles",
        ],
        "stages": [
            (
                "pbr_shader_refinement",
                (
                    "Macro 3D render of Kushan gold dinar and Samanid silver dirham coins from Khujand Museum numismatic hall. "
                    "PBR metallic surfaces: silver coin roughness 0.28, gold coin roughness 0.22, sharp die-struck calligraphy relief, "
                    "edge denticles, irregular hammered rims, dark velvet display tray."
                ),
            ),
            (
                "lighting_and_staging",
                (
                    "Numismatic collection of the Great Silk Road (I-XV c. AD), Khujand Museum. "
                    "High-fidelity coins: Kushan gold staters with royal portraiture and Samanid silver dirhams with Kufic calligraphy. "
                    "Raking macro lighting highlighting die-struck epigraphic relief and metallic patina in lettering grooves. "
                    "Museum showcase with low-reflection glass and subtle depth-of-field focus."
                ),
            ),
            (
                "webgl_engine_polish",
                (
                    "High-precision 3D WebGL numismatic asset of Great Silk Road coins (Inv. INВ-НМ-7340), Khujand Museum Hall 4. "
                    "Multi-material PBR setup: Samanid silver dirham (metallic: 0.92, roughness: 0.27) and Kushan gold stater (metallic: 0.96, roughness: 0.21), "
                    "high-resolution normal maps capturing hand-hammered relief, Kufic inscriptions, and rim flan fissures. "
                    "Curatorial macro lighting with dual directional spotlights revealing calligraphic sharpness on black velvet plinth. "
                    "Instanced Three.js mesh budget under 11,500 triangles, 60 FPS real-time rendering, ACEScg color profile."
                ),
            ),
        ],
    },
    "prompt_khujand_citadel_scroll": {
        "id": "prompt_khujand_citadel_scroll",
        "title": "3D Procedural Khujand Citadel 4-Epoch World",
        "task_type": "3d-prompts",
        "baseline": (
            "3d low poly fortress on river for webgl website background."
        ),
        "target_facts": [
            "4 historical epochs progression",
            "adobe mudbrick ramparts and round bastions",
            "Syr Darya river procedural water",
            "golden hour sunset skybox",
            "budget strictly <= 24,500 triangles",
            "60 FPS mobile optimization",
        ],
        "stages": [
            (
                "pbr_shader_refinement",
                (
                    "Procedural 3D WebGL scene of Khujand Fortress on the Syr Darya river bank. "
                    "Adobe mudbrick wall textures with crenellated battlements, round bastion towers, "
                    "animated procedural river water plane with reflection, golden hour desert atmosphere."
                ),
            ),
            (
                "lighting_and_staging",
                (
                    "4-Epoch interactive 3D WebGL world of Khujand Citadel (Sogdiana -> Alexandria Eschate -> Timur Malik defense -> Modern Museum). "
                    "Authentic earthen architecture with clay-straw mortar textures, crenellations, and river island redoubt. "
                    "Cinematic lighting: warm late-afternoon Syr Darya sun (3000K), soft violet horizon fill, subtle atmospheric dust haze, "
                    "smooth scrubbed camera transition along the embankment."
                ),
            ),
            (
                "webgl_engine_polish",
                (
                    "Procedural 4-epoch 3D WebGL Scroll-World of Khujand Fortress and Syr Darya embankment, index.html #scroll-world. "
                    "Low-poly architectural models: adobe mudbrick ramparts, crenellated towers, and 7-domed museum pavilion; "
                    "procedural GLSL water shader with dynamic ripples and Fresnel reflection; golden hour atmospheric scattering. "
                    "Strict polygon budget under 23,800 triangles, zero external video dependencies, GSAP ScrollTrigger timeline sync, "
                    "auto-sleep when off-screen via IntersectionObserver, DPR clamped <= 1.75 desktop / 1.0 mobile, rock-solid 60 FPS."
                ),
            ),
        ],
    },
    "prompt_clay_gold_icons": {
        "id": "prompt_clay_gold_icons",
        "title": "3D Gold & Claymorphism Icon System",
        "task_type": "3d-prompts",
        "baseline": (
            "3d icon set museum fortress clay and gold."
        ),
        "target_facts": [
            "terracotta clay body (#C86D46 to #E07A5F)",
            "burnished 24K gold accents and seals",
            "dual-layer soft ambient drop shadows",
            "inner clay bevel highlights",
            "micro-levitation animation",
            "transparent alpha background",
        ],
        "stages": [
            (
                "pbr_shader_refinement",
                (
                    "3D Gold & Claymorphism icon system for Khujand Museum website: terracotta ceramic body, "
                    "burnished gold trim and embossed seals, rounded squircle profile, soft subsurface clay scatter, "
                    "dual ambient drop shadows, transparent alpha background."
                ),
            ),
            (
                "lighting_and_staging",
                (
                    "Suite of 3D Claymorphic icons (Museum Citadel, Timur Sabres, Amphora, Ticket Seal, Compass Pin, Audio Horn). "
                    "Sogdian terracotta clay substrate with matte glaze, overlaid with 24K antique burnished gold leaf trims. "
                    "Curatorial studio lighting: 45-degree key light 3200K, fill light 5500K, rim glint on gold edges, "
                    "dual contact shadow and ambient blur, idle micro-levitation floating pose."
                ),
            ),
            (
                "webgl_engine_polish",
                (
                    "Complete 3D Gold & Claymorphism icon collection (.clay-icon-3d) for the Khujand Museum digital platform. "
                    "Sculpted squircle clay bodies in warm Sogdian terracotta (#C86D46) with matte ceramic finish (roughness: 0.62) "
                    "and electroplated 24K antique gold filigree trims (metallic: 0.95, roughness: 0.20, specular rim glints). "
                    "Dual-layer shadow system (contact 4px, ambient 24px) with CSS keyframe micro-levitation (+-5px, 3.8s ease-in-out). "
                    "WebGL procedural glyph mesh strictly under 5,800 triangles per asset, lossless alpha transparency, 60 FPS."
                ),
            ),
        ],
    },
    "prompt_mount_mugh_scroll": {
        "id": "prompt_mount_mugh_scroll",
        "title": "3D Mount Mugh Sogdian Leather Manuscript",
        "task_type": "3d-prompts",
        "baseline": (
            "3d old paper manuscript with writing."
        ),
        "target_facts": [
            "8th century Sogdian cursive manuscript",
            "ancient leather parchment with deckle edges",
            "authentic carbon ink calligraphy",
            "subtle parchment bump roughness 0.72",
            "climate-controlled museum vitrine",
            "Three.js mesh <= 6,000 triangles",
        ],
        "stages": [
            (
                "pbr_shader_refinement",
                (
                    "3D historical manuscript from Mount Mugh archive (722 AD), Sogdian cursive ink script on aged leather parchment. "
                    "Curled deckle edges, leather grain micro-texture, roughness 0.72, matte carbon ink absorption, "
                    "museum vitrine presentation."
                ),
            ),
            (
                "lighting_and_staging",
                (
                    "Ancient diplomatic letter of Sogdian ruler Devashtich from Mount Mugh (early VIII c.), Sughd Museum Hall 3. "
                    "Hand-dressed goat parchment with authentic cursive calligraphy in lampblack ink, natural aging translucency. "
                    "Controlled archival showcase illumination (50 lux standard, zero UV), soft ambient shadow, dark walnut vitrine floor."
                ),
            ),
            (
                "webgl_engine_polish",
                (
                    "Museum-standard 3D WebGL representation of the Mount Mugh Sogdian Manuscript (722 AD, Inv. INВ-ЭП-2104). "
                    "Curatorial PBR parchment material: aged animal skin grain with subsurface translucency (transmission: 0.12, roughness: 0.70), "
                    "authentic Sogdian cursive ink calligraphy with slight carbon sheen, curling deckle edges via subtle vertex displacement. "
                    "Archival museum glass vitrine lighting with soft diffuse conservation LEDs (50 lux) and anti-glare reflection. "
                    "Optimized low-poly mesh under 5,400 triangles, Three.js canvas texture map ready, 60 FPS real-time rendering."
                ),
            ),
        ],
    },
}


# ---------------------------------------------------------------------------
# Lexicon & Heuristics for IndependentJudge
# ---------------------------------------------------------------------------
HISTORICAL_ANCHORS_RU = [
    r"1219[–\-]1220",
    r"329\s*(?:г\.|году)?\s*до\s*н\.?\s*э\.?",
    r"vi[–\-]iv\s*вв?\.?\s*до\s*н\.?\s*э\.?",
    r"v[–\-]iv\s*вв?\.?\s*до\s*н\.?\s*э\.?",
    r"i[–\-]xv\s*вв?\.?",
    r"viii\s*в\.?",
    r"xviii[–\-]xx\s*вв?\.?",
    r"тимурмалик",
    r"александр\s*(?:македонск|велик)",
    r"александри[яи]\s*эсхат",
    r"чингисхан",
    r"согдиан",
    r"худжанд",
    r"сырдарь",
    r"яксарт",
    r"гора\s*муг",
    r"деваштич",
    r"негматов",
    r"цитадел",
    r"крепост",
    r"оссуари",
    r"хум",
    r"сакск",
    r"кушанск",
    r"саманидск",
    r"атлас",
    r"адрас",
    r"сюзане",
    r"карагач",
    r"семикупольн",
]

CURATORIAL_TERMS_RU = [
    "экспозици",
    "монументальн",
    "артефакт",
    "археологическ",
    "реконструкци",
    "торевтик",
    "зооморфн",
    "чеканк",
    "филигран",
    "эпиграфик",
    "нумизматик",
    "стратиграфи",
    "пифос",
    "рельефн",
    "инвентарн",
    "патин",
    "эллинистическ",
    "вооружени",
    "памятник",
    "солярн",
    "доминанта",
    "коллекци",
    "курганн",
]

INFORMAL_PENALTIES_RU = [
    r"\bкрут(?:ой|ая|ое|ые)\b",
    r"\bклассн(?:ый|ая|ое|ые)\b",
    r"\bсупер\b",
    r"\bшок\b",
    r"\bофигенн\w*\b",
    r"\bвещиц\w*\b",
    r"\bштуковин\w*\b",
    r"\bкороче\b",
    r"\bв общем\b",
    r"!{2,}",
]

ANACHRONISM_PENALTIES = [
    r"\bтанк\w*\b",
    r"\bгеймпад\w*\b",
    r"\bторт\w*\b",
    r"\bпластиков\w*\b",
    r"\bджойстик\w*\b",
    r"\bсамолёт\w*\b",
    r"\bкомпьютер\w*\b",
    r"\bримский легион\b",
]

PROMPT_3D_KEYWORDS = [
    "pbr",
    "roughness",
    "metallic",
    "specular",
    "subsurface",
    "normal map",
    "bump",
    "triangles",
    "low-poly",
    "three.js",
    "webgl",
    "lighting",
    "key light",
    "rim",
    "plinth",
    "pedestal",
    "vitrine",
    "acescg",
    "topology",
    "60 fps",
    "shader",
    "ambient occlusion",
]


# ---------------------------------------------------------------------------
# IndependentJudge (Discriminator)
# ---------------------------------------------------------------------------
class IndependentJudge:
    """
    Discriminator scoring texts and 3D prompts across the 4-dimensional museum rubric.
    Operates without internal bias and provides full numerical breakdowns.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or RUBRIC_WEIGHTS
        norm = sum(self.weights.values())
        self.weights = {k: v / norm for k, v in self.weights.items()}

    def evaluate_text_description(
        self, text: str, target_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Evaluates a museum exhibit text description across the 4 dimensions."""
        text_clean = text.strip()
        text_lower = text_clean.lower()
        words = re.findall(r"\b\w+\b", text_lower)
        word_count = len(words)

        # ---------------------------------------------------------
        # Dimension 1: Historical & Archaeological Accuracy (W = 0.35)
        # ---------------------------------------------------------
        acc_score = 0.45  # baseline sensible credit
        matched_anchors: List[str] = []
        for pattern in HISTORICAL_ANCHORS_RU:
            if re.search(pattern, text_lower):
                matched_anchors.append(pattern)
        anchor_bonus = min(0.40, len(matched_anchors) * 0.05)
        acc_score += anchor_bonus

        # Check target-specific facts if provided
        target_facts_matched = 0
        if target_metadata and "target_facts" in target_metadata:
            total_facts = len(target_metadata["target_facts"])
            for fact in target_metadata["target_facts"]:
                # match key words of the fact
                fact_tokens = [
                    w for w in re.findall(r"\b\w{4,}\b", fact.lower())
                ]
                if fact_tokens and any(tok in text_lower for tok in fact_tokens):
                    target_facts_matched += 1
            if total_facts > 0:
                acc_score += 0.20 * (target_facts_matched / total_facts)

        # Anachronism penalty
        anachronisms_found = []
        for anach in ANACHRONISM_PENALTIES:
            if re.search(anach, text_lower):
                anachronisms_found.append(anach)
                acc_score -= 0.35

        acc_score = max(0.05, min(1.0, acc_score))

        # ---------------------------------------------------------
        # Dimension 2: Curatorial Register & Academic Tone (W = 0.25)
        # ---------------------------------------------------------
        reg_score = 0.40
        matched_terms = []
        for term in CURATORIAL_TERMS_RU:
            if term in text_lower:
                matched_terms.append(term)
        term_bonus = min(0.45, len(matched_terms) * 0.05)
        reg_score += term_bonus

        # Check for passive or dignified scholarly markers
        scholarly_markers = ["посвящен", "представлен", "обнаружен", "является", "иллюстрирует", "увековечивает"]
        if any(marker in text_lower for marker in scholarly_markers):
            reg_score += 0.15

        # Penalties for informal/marketing slang
        informal_found = []
        for inf in INFORMAL_PENALTIES_RU:
            if re.search(inf, text_lower):
                informal_found.append(inf)
                reg_score -= 0.20
        reg_score = max(0.05, min(1.0, reg_score))

        # ---------------------------------------------------------
        # Dimension 3: Public Clarity & Informational Architecture (W = 0.20)
        # ---------------------------------------------------------
        clarity_score = 0.35
        # Ideal museum card text has 30 to 110 words
        if 25 <= word_count <= 120:
            clarity_score += 0.30
        elif 15 <= word_count < 25 or 120 < word_count <= 180:
            clarity_score += 0.15
        else:
            clarity_score += 0.05

        # Sentence structure balance
        sentences = [s.strip() for s in re.split(r"[.!?]+", text_clean) if s.strip()]
        if len(sentences) >= 2:
            clarity_score += 0.20
            avg_sentence_len = word_count / len(sentences)
            if 10 <= avg_sentence_len <= 30:
                clarity_score += 0.15

        clarity_score = max(0.05, min(1.0, clarity_score))

        # ---------------------------------------------------------
        # Dimension 4: Technical & Multilingual Symmetry (W = 0.20)
        # ---------------------------------------------------------
        tech_score = 0.30
        # Typography: em-dashes (—)
        if "—" in text_clean:
            tech_score += 0.25
        # Russian angle quotes: « and »
        if "«" in text_clean and "»" in text_clean:
            tech_score += 0.20
        # Standard century notations: вв. or гг.
        if re.search(r"\b(?:вв?|гг?)\.", text_clean):
            tech_score += 0.15
        # Presence of inventory / catalog metadata: ИНВ-
        if re.search(r"ИНВ-[А-Я]{2}-\d+", text_clean):
            tech_score += 0.15

        tech_score = max(0.05, min(1.0, tech_score))

        # Composite score
        composite = (
            self.weights["accuracy"] * acc_score
            + self.weights["register"] * reg_score
            + self.weights["clarity"] * clarity_score
            + self.weights["technical"] * tech_score
        )
        composite = round(max(0.0, min(1.0, composite)), 4)

        return {
            "accuracy": round(acc_score, 4),
            "register": round(reg_score, 4),
            "clarity": round(clarity_score, 4),
            "technical": round(tech_score, 4),
            "composite": composite,
            "breakdown": {
                "word_count": word_count,
                "matched_anchors_count": len(matched_anchors),
                "matched_terms_count": len(matched_terms),
                "anachronisms_count": len(anachronisms_found),
                "informal_slang_count": len(informal_found),
                "target_facts_matched": target_facts_matched,
            },
        }

    def evaluate_3d_prompt(
        self, prompt: str, target_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Evaluates a 3D procedural/rendering prompt across the 4 dimensions."""
        prompt_clean = prompt.strip()
        prompt_lower = prompt_clean.lower()
        words = re.findall(r"\b\w+\b", prompt_lower)
        word_count = len(words)

        # ---------------------------------------------------------
        # Dimension 1: Historical & Archaeological Accuracy (W = 0.35)
        # ---------------------------------------------------------
        acc_score = 0.40
        matched_anchors = []
        for anchor in [
            "khujand", "citadel", "sogdian", "timur malik", "alexandria eschate",
            "saka", "syr darya", "mount mugh", "pithos", "bronze", "terracotta",
            "gold", "silver", "kushan", "samanid", "silk road", "homeric", "hellenistic"
        ]:
            if anchor in prompt_lower:
                matched_anchors.append(anchor)
        acc_score += min(0.35, len(matched_anchors) * 0.08)

        if target_metadata and "target_facts" in target_metadata:
            total_facts = len(target_metadata["target_facts"])
            matched_facts = 0
            for fact in target_metadata["target_facts"]:
                tokens = [w for w in re.findall(r"\b\w{4,}\b", fact.lower())]
                if tokens and any(tok in prompt_lower for tok in tokens):
                    matched_facts += 1
            if total_facts > 0:
                acc_score += 0.25 * (matched_facts / total_facts)

        acc_score = max(0.05, min(1.0, acc_score))

        # ---------------------------------------------------------
        # Dimension 2: Curatorial Register & Museum Staging (W = 0.25)
        # ---------------------------------------------------------
        reg_score = 0.35
        staging_terms = [
            "museum", "curatorial", "plinth", "pedestal", "vitrine", "exhibition",
            "archival", "conservation", "showcase", "patina", "verdigris", "gallery"
        ]
        matched_staging = [t for t in staging_terms if t in prompt_lower]
        reg_score += min(0.40, len(matched_staging) * 0.08)

        # Lighting register
        lighting_terms = ["3200k", "5500k", "key light", "fill", "rim", "ambient", "studio illumination"]
        matched_lighting = [t for t in lighting_terms if t in prompt_lower]
        reg_score += min(0.25, len(matched_lighting) * 0.07)

        reg_score = max(0.05, min(1.0, reg_score))

        # ---------------------------------------------------------
        # Dimension 3: Public Clarity & Prompt Architecture (W = 0.20)
        # ---------------------------------------------------------
        clarity_score = 0.30
        if 25 <= word_count <= 110:
            clarity_score += 0.35
        elif 15 <= word_count < 25 or 110 < word_count <= 160:
            clarity_score += 0.20
        else:
            clarity_score += 0.05

        # Check for structured token blocks separated by commas or sentences
        clauses = [c.strip() for c in prompt_clean.split(",") if c.strip()]
        if len(clauses) >= 4:
            clarity_score += 0.25
        elif len(clauses) >= 2:
            clarity_score += 0.15

        clarity_score = max(0.05, min(1.0, clarity_score))

        # ---------------------------------------------------------
        # Dimension 4: Technical 3D Parameters & WebGL Readiness (W = 0.20)
        # ---------------------------------------------------------
        tech_score = 0.25
        matched_keywords = []
        for kw in PROMPT_3D_KEYWORDS:
            if kw in prompt_lower:
                matched_keywords.append(kw)
        tech_score += min(0.50, len(matched_keywords) * 0.06)

        # Specific WebGL performance constraint checks
        if re.search(r"(?:triangles|tris|\bpoly\b)", prompt_lower):
            tech_score += 0.15
        if re.search(r"(?:three\.js|webgl|shader|60\s*fps)", prompt_lower):
            tech_score += 0.15

        tech_score = max(0.05, min(1.0, tech_score))

        composite = (
            self.weights["accuracy"] * acc_score
            + self.weights["register"] * reg_score
            + self.weights["clarity"] * clarity_score
            + self.weights["technical"] * tech_score
        )
        composite = round(max(0.0, min(1.0, composite)), 4)

        return {
            "accuracy": round(acc_score, 4),
            "register": round(reg_score, 4),
            "clarity": round(clarity_score, 4),
            "technical": round(tech_score, 4),
            "composite": composite,
            "breakdown": {
                "word_count": word_count,
                "matched_anchors_count": len(matched_anchors),
                "matched_staging_count": len(matched_staging),
                "matched_3d_keywords_count": len(matched_keywords),
                "clauses_count": len(clauses),
            },
        }

    def evaluate(
        self, content: str, task_type: str, target_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Routes evaluation according to task type."""
        if task_type == "3d-prompts":
            return self.evaluate_3d_prompt(content, target_metadata)
        return self.evaluate_text_description(content, target_metadata)

    def evaluate_blind(
        self,
        option_1: str,
        option_2: str,
        task_type: str,
        target_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Evaluates Option 1 and Option 2 blindly without knowing Champion or Challenger identities."""
        return {
            "option_1": self.evaluate(option_1, task_type, target_metadata),
            "option_2": self.evaluate(option_2, task_type, target_metadata),
        }


# ---------------------------------------------------------------------------
# ContentMutator (Generator)
# ---------------------------------------------------------------------------
class ContentMutator:
    """
    Generator component creating targeted candidate variants.
    Supports staged progressive mutations and dynamic variations.
    """

    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()

    def generate_candidate(
        self,
        champion_text: str,
        task_type: str,
        round_num: int,
        target_data: Dict[str, Any],
        force_regression: bool = False,
    ) -> Tuple[str, str]:
        """
        Produces a candidate text and the strategy name applied.
        If force_regression is True, produces an intentionally degraded candidate to test rejection gates.
        """
        if force_regression:
            if task_type == "3d-prompts":
                degraded = f"{champion_text} with cheap plastic textures and colorful futuristic laser guns."
            else:
                degraded = f"{champion_text} Короче, супер крутая штуковина, настоящий шок для туристов!"
            return degraded, "adversarial_regression_probe"

        # Check if the target data defines predefined curriculum stages
        stages = target_data.get("stages", [])
        if stages:
            # round_num is 1-indexed; pick corresponding stage or last
            stage_idx = min(round_num - 1, len(stages) - 1)
            strategy_name, staged_content = stages[stage_idx]
            return staged_content, strategy_name

        # Fallback procedural mutation if no predefined stages exist
        if task_type == "3d-prompts":
            return self._mutate_prompt_procedural(champion_text, round_num)
        return self._mutate_text_procedural(champion_text, round_num)

    def _mutate_text_procedural(self, text: str, round_num: int) -> Tuple[str, str]:
        """Procedural mutation adding curatorial terms, typography, and metadata."""
        mutated = text.strip()
        strategy = f"procedural_enhancement_r{round_num}"

        if round_num == 1:
            if "экспозиция" not in mutated.lower():
                mutated = f"Постоянная музейная экспозиция: {mutated}"
            strategy = "procedural_curatorial_elevation"
        elif round_num == 2:
            if "—" not in mutated:
                mutated = mutated.replace(" - ", " — ")
            if "«" not in mutated and '"' in mutated:
                mutated = re.sub(r'"([^"]+)"', r"«\1»", mutated)
            strategy = "procedural_typographical_polish"
        else:
            if not re.search(r"ИНВ-", mutated):
                mutated = f"{mutated} (ИНВ-СМ-4800, памятник республиканского значения)."
            strategy = "procedural_metadata_enrichment"

        return mutated, strategy

    def _mutate_prompt_procedural(self, prompt: str, round_num: int) -> Tuple[str, str]:
        """Procedural mutation adding PBR, lighting, and WebGL budget parameters."""
        mutated = prompt.strip()
        strategy = f"procedural_3d_enhancement_r{round_num}"

        if round_num == 1:
            mutated += ", PBR roughness 0.42, metallic 0.85, normal bump map detailing."
            strategy = "procedural_pbr_refinement"
        elif round_num == 2:
            mutated += ", 3-point museum studio lighting (3200K warm key, 5500K fill), dark exhibition plinth."
            strategy = "procedural_lighting_rig"
        else:
            mutated += ", optimized for WebGL Three.js under 22,000 triangles, clean quads/tris topology, 60 FPS."
            strategy = "procedural_webgl_budget"

        return mutated, strategy


# ---------------------------------------------------------------------------
# PairwiseBlindGate (Shuffler, Evaluator & Anti-Regression Gate)
# ---------------------------------------------------------------------------
class PairwiseBlindGate:
    """
    Double-blind evaluator and gate keeper:
    1. Blindly shuffles Champion A and Challenger B into Option 1 and Option 2.
    2. Submits options to IndependentJudge without revealing identity.
    3. Un-blinds score assignments.
    4. Enforces the Anti-Regression Gate:
       - Delta(Composite) >= threshold (default +0.03 / +3%)
       - Delta(Accuracy) >= 0.0 (Zero accuracy loss)
    """

    def __init__(
        self,
        judge: IndependentJudge,
        threshold: float = DEFAULT_IMPROVEMENT_THRESHOLD,
        rng: Optional[random.Random] = None,
    ):
        self.judge = judge
        self.threshold = threshold
        self.rng = rng or random.Random()

    def evaluate_pair(
        self,
        champion_text: str,
        challenger_text: str,
        task_type: str,
        target_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes a double-blind pairwise evaluation between champion and challenger.
        """
        # Coin flip for double-blind assignment
        is_champion_option_1 = self.rng.random() < 0.5
        if is_champion_option_1:
            opt1_text, opt2_text = champion_text, challenger_text
            assignment = {"option_1": "champion", "option_2": "challenger"}
        else:
            opt1_text, opt2_text = challenger_text, champion_text
            assignment = {"option_1": "challenger", "option_2": "champion"}

        # Independent judge scores both options blindly
        blind_scores = self.judge.evaluate_blind(
            opt1_text, opt2_text, task_type, target_metadata
        )

        # Un-blind scores
        if is_champion_option_1:
            champ_scores = blind_scores["option_1"]
            chall_scores = blind_scores["option_2"]
        else:
            champ_scores = blind_scores["option_2"]
            chall_scores = blind_scores["option_1"]

        score_delta = round(chall_scores["composite"] - champ_scores["composite"], 4)
        accuracy_delta = round(chall_scores["accuracy"] - champ_scores["accuracy"], 4)

        # Anti-Regression Gate verification
        reasons: List[str] = []
        if score_delta < self.threshold:
            reasons.append(
                f"Composite improvement ({score_delta:+.4f}) is below threshold (+{self.threshold:.4f})"
            )
        if accuracy_delta < 0.0:
            reasons.append(
                f"Historical accuracy degraded by {accuracy_delta:+.4f} (must be >= 0.0)"
            )

        promoted = len(reasons) == 0
        if promoted:
            decision = "PROMOTED"
            pct_gain = round((score_delta / max(0.01, champ_scores["composite"])) * 100, 2)
            decision_reason = (
                f"Promoted: Composite score improved by {score_delta:+.4f} (+{pct_gain}%, >= +{self.threshold:.4f}) "
                f"with zero accuracy degradation ({accuracy_delta:+.4f} >= 0.0)."
            )
        else:
            decision = "REJECTED"
            decision_reason = f"Rejected: {'; '.join(reasons)}."

        # Compute unified diff
        diff_lines = list(
            difflib.unified_diff(
                champion_text.splitlines(keepends=True),
                challenger_text.splitlines(keepends=True),
                fromfile="champion_current",
                tofile="challenger_candidate",
                n=1,
            )
        )
        diff_text = "".join(diff_lines).strip()

        return {
            "promoted": promoted,
            "decision": decision,
            "decision_reason": decision_reason,
            "score_delta": score_delta,
            "accuracy_delta": accuracy_delta,
            "blind_assignment": assignment,
            "blind_scores": blind_scores,
            "champion_scores": champ_scores,
            "challenger_scores": chall_scores,
            "diff": diff_text,
        }


# ---------------------------------------------------------------------------
# Optimization Engine & Cycle Coordinator
# ---------------------------------------------------------------------------
class AutoImproveEngine:
    """
    Coordinates the GAN-style optimization cycle over museum exhibits and 3D prompts.
    Produces comprehensive lineage, audit history, and reports.
    """

    def __init__(
        self,
        threshold: float = DEFAULT_IMPROVEMENT_THRESHOLD,
        rounds: int = DEFAULT_ROUNDS,
        dry_run: bool = False,
        seed: Optional[int] = None,
    ):
        self.threshold = threshold
        self.rounds = rounds
        self.dry_run = dry_run
        self.seed = seed
        self.rng = random.Random(seed) if seed is not None else random.Random()
        self.judge = IndependentJudge()
        self.mutator = ContentMutator(rng=self.rng)
        self.gate = PairwiseBlindGate(
            judge=self.judge, threshold=self.threshold, rng=self.rng
        )

    def run_optimization(
        self, task: str = "all"
    ) -> Dict[str, Any]:
        """
        Executes the optimization cycle for selected tasks.
        task can be 'descriptions', '3d-prompts', or 'all'.
        """
        targets_to_run: List[Dict[str, Any]] = []

        if task in ("descriptions", "all"):
            targets_to_run.extend(EXHIBIT_TARGETS.values())
        if task in ("3d-prompts", "all"):
            targets_to_run.extend(PROMPT_TARGETS.values())

        start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        lineage: Dict[str, Any] = {}
        total_promotions = 0
        total_rejections = 0
        total_mutations = 0

        for target in targets_to_run:
            target_id = target["id"]
            task_type = target["task_type"]
            title = target["title"]
            baseline_text = target["baseline"]

            # Evaluate initial baseline (Round 0)
            baseline_scores = self.judge.evaluate(
                baseline_text, task_type, target_metadata=target
            )

            current_champion_text = baseline_text
            current_champion_scores = baseline_scores

            round_records: List[Dict[str, Any]] = []

            for r in range(1, self.rounds + 1):
                total_mutations += 1

                # Generate candidate variant
                challenger_text, strategy_name = self.mutator.generate_candidate(
                    champion_text=current_champion_text,
                    task_type=task_type,
                    round_num=r,
                    target_data=target,
                    force_regression=False,
                )

                # Pairwise blind evaluation
                gate_result = self.gate.evaluate_pair(
                    champion_text=current_champion_text,
                    challenger_text=challenger_text,
                    task_type=task_type,
                    target_metadata=target,
                )

                champion_pre = {
                    "text": current_champion_text,
                    "scores": current_champion_scores,
                }

                if gate_result["promoted"]:
                    total_promotions += 1
                    current_champion_text = challenger_text
                    current_champion_scores = gate_result["challenger_scores"]
                else:
                    total_rejections += 1

                champion_post = {
                    "text": current_champion_text,
                    "scores": current_champion_scores,
                }

                round_record = {
                    "round": r,
                    "strategy": strategy_name,
                    "champion_pre": champion_pre,
                    "challenger": {
                        "text": challenger_text,
                        "scores": gate_result["challenger_scores"],
                    },
                    "blind_gate": {
                        "assignment": gate_result["blind_assignment"],
                        "blind_scores": gate_result["blind_scores"],
                    },
                    "decision": gate_result["decision"],
                    "decision_reason": gate_result["decision_reason"],
                    "score_delta": gate_result["score_delta"],
                    "accuracy_delta": gate_result["accuracy_delta"],
                    "diff": gate_result["diff"],
                    "champion_post": champion_post,
                }
                round_records.append(round_record)

            # Compute overall target gains
            init_comp = baseline_scores["composite"]
            final_comp = current_champion_scores["composite"]
            overall_gain = round(final_comp - init_comp, 4)
            overall_gain_pct = round(
                ((final_comp - init_comp) / max(0.01, init_comp)) * 100, 2
            )

            lineage[target_id] = {
                "target_id": target_id,
                "task_type": task_type,
                "title": title,
                "initial_baseline": {
                    "text": baseline_text,
                    "scores": baseline_scores,
                },
                "final_champion": {
                    "text": current_champion_text,
                    "scores": current_champion_scores,
                },
                "score_gain": overall_gain,
                "score_gain_pct": overall_gain_pct,
                "rounds": round_records,
            }

        end_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Aggregate metrics
        avg_gain_pct = 0.0
        if lineage:
            avg_gain_pct = round(
                sum(item["score_gain_pct"] for item in lineage.values()) / len(lineage),
                2,
            )

        report = {
            "version": "1.0.0",
            "generated_at": end_time,
            "started_at": start_time,
            "configuration": {
                "task": task,
                "rounds": self.rounds,
                "threshold": self.threshold,
                "dry_run": self.dry_run,
                "seed": self.seed,
            },
            "rubric_weights": RUBRIC_WEIGHTS,
            "execution_summary": {
                "total_targets_processed": len(targets_to_run),
                "total_mutations_evaluated": total_mutations,
                "total_promotions": total_promotions,
                "total_rejections": total_rejections,
                "average_improvement_pct": avg_gain_pct,
            },
            "lineage": lineage,
        }

        return report

    def save_history(
        self, report: Dict[str, Any], output_path: pathlib.Path = DEFAULT_HISTORY_FILE
    ) -> None:
        """Saves execution history and lineage to specified JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CLI Command Line Interface
# ---------------------------------------------------------------------------
def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Khujand Museum GAN-style Auto-Improve Engine (Requirement R5)."
    )
    parser.add_argument(
        "--task",
        choices=["descriptions", "3d-prompts", "all"],
        default="all",
        help="Target workload to optimize (default: all)",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=DEFAULT_ROUNDS,
        help=f"Number of optimization rounds per target (default: {DEFAULT_ROUNDS})",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_IMPROVEMENT_THRESHOLD,
        help=f"Minimum composite score delta required for promotion (default: {DEFAULT_IMPROVEMENT_THRESHOLD})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run evaluation cycle without updating active tools/auto_improve_history.json",
    )
    parser.add_argument(
        "--report",
        type=str,
        default=None,
        help="Optional file path to output execution report JSON",
    )
    parser.add_argument(
        "--history-path",
        type=str,
        default=str(DEFAULT_HISTORY_FILE),
        help="Target path for audit history JSON",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional integer seed for deterministic random operations",
    )
    args = parser.parse_args()
    if args.rounds <= 0:
        parser.error("--rounds must be a positive integer (> 0)")
    return args


def main() -> int:
    args = parse_arguments()

    print("=" * 72)
    print("Khujand Museum Modernization - Auto-Improve Optimization Engine (R5)")
    print("=" * 72)
    print(f"Task:              {args.task}")
    print(f"Rounds:            {args.rounds}")
    print(f"Promotion Gate:    Delta >= {args.threshold:.4f} and Accuracy Delta >= 0.0")
    print(f"Dry Run:           {args.dry_run}")
    if args.seed is not None:
        print(f"Random Seed:       {args.seed}")
    print("-" * 72)

    engine = AutoImproveEngine(
        threshold=args.threshold,
        rounds=args.rounds,
        dry_run=args.dry_run,
        seed=args.seed,
    )

    report = engine.run_optimization(task=args.task)
    summary = report["execution_summary"]

    print("\nExecution Summary:")
    print(f"  Targets evaluated:         {summary['total_targets_processed']}")
    print(f"  Candidate mutations:       {summary['total_mutations_evaluated']}")
    print(f"  Promotions:                {summary['total_promotions']}")
    print(f"  Rejections:                {summary['total_rejections']}")
    print(f"  Average Improvement:       +{summary['average_improvement_pct']}%")

    print("\nPer-Target Score Progressions:")
    for target_id, target_data in report["lineage"].items():
        init_c = target_data["initial_baseline"]["scores"]["composite"]
        final_c = target_data["final_champion"]["scores"]["composite"]
        gain_pct = target_data["score_gain_pct"]
        print(
            f"  [{target_data['task_type'][:4].upper()}] {target_id:<30} "
            f"{init_c:.4f} -> {final_c:.4f} (+{gain_pct:.1f}%)"
        )

    # Save to default history file if not dry run
    if not args.dry_run:
        history_path = pathlib.Path(args.history_path)
        engine.save_history(report, history_path)
        print(f"\n[OK] Audit history recorded to: {history_path}")
    else:
        print("\n[DRY-RUN] Execution completed without writing to history file.")

    # Save custom report if requested
    if args.report:
        report_path = pathlib.Path(args.report)
        engine.save_history(report, report_path)
        print(f"[OK] Dedicated execution report saved to: {report_path}")

    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
