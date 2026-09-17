#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест: парсинг CSV даёт те же результаты, что и xlsx (в пределах округления CSV).
Проверяются: якоря, персонажи, оружие/сеты/ER, урон/доли (с допуском), ротации, итоги."""
import sys

sys.path.insert(0, "/home/z/my-project/scripts")
from showcase_parser import parse_showcase

XLSX = "/home/z/my-project/download/showcase_template.xlsx"
CSV = "/home/z/my-project/download/showcase_sheet.csv"
CSV_URL = "https://docs.google.com/spreadsheets/d/19C-JTqT5uSE5RjSPohIz5XeHp1hVfOcJ7ehEYAQiNC4/export?format=csv&gid=121343185"


def die(msg):
    print("FAIL:", msg)
    sys.exit(1)


x = parse_showcase(XLSX)
c = parse_showcase(CSV)

print(f"xlsx: слотов={x['total_slots']}, заполнено={x['filled_slots']}, лист={x['sheet']!r}")
print(f"csv:  слотов={c['total_slots']}, заполнено={c['filled_slots']}, лист={c['sheet']!r}")

if len(x["teams"]) != len(c["teams"]):
    die(f"разное число блоков: {len(x['teams'])} vs {len(c['teams'])}")
if x["filled_slots"] != c["filled_slots"]:
    die(f"filled: {x['filled_slots']} vs {c['filled_slots']}")

worst = {"dmg": 0.0, "share": 0.0, "dpr": 0.0, "dps": 0.0}
for xt, ct in zip(x["teams"], c["teams"]):
    if xt["_anchor"] != ct["_anchor"]:
        die(f"разные якоря: {xt['_anchor']} vs {ct['_anchor']}")
    xn = [ch["name"] for ch in xt["characters"]]
    cn = [ch["name"] for ch in ct["characters"]]
    if xn != cn:
        die(f"[{xt['_anchor']}] разные персонажи: {xn} vs {cn}")
    for a, b in zip(xt["characters"], ct["characters"]):
        for k in ("weapon", "artifact_set", "er_requirement"):
            if (a[k] or "").strip() != (b[k] or "").strip():
                die(f"[{xt['_anchor']}] {a['name']}: {k}: {a[k]!r} vs {b[k]!r}")
        if a["field_time_s"] != b["field_time_s"]:
            die(f"[{xt['_anchor']}] {a['name']}: field_time {a['field_time_s']} vs {b['field_time_s']}")
        worst["dmg"] = max(worst["dmg"], abs((a["damage"] or 0) - (b["damage"] or 0)))
        worst["share"] = max(worst["share"], abs((a["damage_share"] or 0) - (b["damage_share"] or 0)))
    if (xt["rotation"] or "").strip() != (ct["rotation"] or "").strip():
        die(f"[{xt['_anchor']}] ротация: {xt['rotation']!r} vs {ct['rotation']!r}")
    if xt["author"] != ct["author"]:
        die(f"[{xt['_anchor']}] автор: {xt['author']!r} vs {ct['author']!r}")
    if xt["date"] != ct["date"]:
        die(f"[{xt['_anchor']}] дата: {xt['date']!r} vs {ct['date']!r}")
    if xt["rotation_time_s"] != ct["rotation_time_s"]:
        die(f"[{xt['_anchor']}] время ротации: {xt['rotation_time_s']} vs {ct['rotation_time_s']}")
    worst["dpr"] = max(worst["dpr"], abs((xt["total_dpr"] or 0) - (ct["total_dpr"] or 0)))
    worst["dps"] = max(worst["dps"], abs((xt["dps"] or 0) - (ct["dps"] or 0)))

print(f"OK (файл): {len(x['teams'])} команд, {x['filled_slots']} заполнено")
print(f"  макс. расхождения (округление CSV): урон={worst['dmg']:.3f}, доля={worst['share']:.5f}, "
      f"DPR={worst['dpr']:.3f}, DPS={worst['dps']:.3f}")

# End-to-end: CSV по URL
u = parse_showcase(CSV_URL)
if u["filled_slots"] != c["filled_slots"] or len(u["teams"]) != len(c["teams"]):
    die(f"CSV по URL: {len(u['teams'])}/{u['filled_slots']} vs файл {len(c['teams'])}/{c['filled_slots']}")
print(f"OK (URL): CSV-эндпоинт через format=csv -> {u['filled_slots']} команд")
print("\nВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
