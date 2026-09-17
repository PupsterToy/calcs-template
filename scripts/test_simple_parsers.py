#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_simple_parsers.py — проверка простых парсеров (simple_xlsx.py / simple_csv.py)
против эталона scripts/../download/showcase_all_teams.json (сложный парсер, этап 1).

Сравнивает по якорю 'Team':
  - количество команд, имена персонажей, оружие/сеты/ER (с точностью до trim);
  - числа: xlsx должен совпасть точно, CSV — с допуском на округление экспорта;
  - ротации, авторы, даты; метки слотов R·C.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import simple_xlsx as sx
import simple_csv as sc

BASE = Path("/home/z/my-project")
REF = json.loads((BASE / "download/showcase_all_teams.json").read_text(encoding="utf-8"))
REF_TEAMS = {t["_anchor"]: t for t in REF["teams"] if not t["is_empty"]}
# соответствие слот -> якорь берём из xlsx-режима (там якоря известны точно);
# порядок блоков у всех источников одинаков (сортировка по позиции якоря)
SLOT_TO_ANCHOR = {}


def norm(v):
    return str(v).strip() if v is not None else None


def check(result, label, tol):
    ok, fails = 0, []

    def cmp_num(name, a, b, tol):
        if a is None and b is None:
            return
        if a is None or b is None:
            fails.append(f"{name}: {a!r} != {b!r}")
        elif abs(a - b) > tol(max(abs(a), abs(b), 1.0)):
            fails.append(f"{name}: {a} != {b}")

    for t in result["teams"]:
        if t["is_empty"]:
            continue
        if t["anchor"]:  # xlsx: якорь известен точно
            ref = REF_TEAMS.get(t["anchor"])
            SLOT_TO_ANCHOR[t["slot"]] = t["anchor"]
        else:  # csv: якоря нет — матчим по метке слота через xlsx-маппинг
            ref = REF_TEAMS.get(SLOT_TO_ANCHOR.get(t["slot"]))
        if ref is None:
            fails.append(f"{t['slot']}: команда не найдена в эталоне")
            continue
        ok += 1
        if len(t["characters"]) != len(ref["characters"]):
            fails.append(f"{t['slot']}: число персонажей {len(t['characters'])} != {len(ref['characters'])}")
            continue
        for a, b in zip(t["characters"], ref["characters"]):
            if a["name"] != norm(b["name"]):
                fails.append(f"{t['slot']}: имя {a['name']!r} != {b['name']!r}")
            for f in ("weapon", "artifact_set", "er_requirement"):
                if a[f] != norm(b[f]):
                    fails.append(f"{t['slot']}/{a['name']}: {f} {a[f]!r} != {norm(b[f])!r}")
            for f in ("damage", "damage_share", "field_time_s"):
                cmp_num(f"{t['slot']}/{a['name']}.{f}", a[f], b[f], tol)
        for f in ("total_dpr", "dps", "rotation_time_s"):
            cmp_num(f"{t['slot']}.{f}", t[f], ref[f], tol)
        if t["rotation"] != norm(ref["rotation"]):
            fails.append(f"{t['slot']}: ротация отличается")
        if t["author"] != norm(ref["author"]):
            fails.append(f"{t['slot']}: автор {t['author']!r} != {norm(ref['author'])!r}")
        if t["date"] != ref["date"]:
            fails.append(f"{t['slot']}: дата {t['date']} != {ref['date']}")

    print(f"[{label}] команд совпало: {ok}/{len(REF_TEAMS)}")
    if fails:
        print(f"[{label}] РАСХОЖДЕНИЯ ({len(fails)}):")
        for f in fails[:15]:
            print("   -", f)
        if len(fails) > 15:
            print(f"   ... и ещё {len(fails) - 15}")
    else:
        print(f"[{label}] OK — все значения соответствуют эталону")
    return len(fails)


total_fails = 0

# 1) xlsx-файл (точное совпадение)
ws = sx.open_sheet(str(BASE / "download/showcase_template.xlsx"))
res_x = sx.parse_showcase(ws, str(BASE / "download/showcase_template.xlsx"))
total_fails += check(res_x, "xlsx-файл", tol=lambda s: s * 1e-9)

# 2) csv-файл (допуск на округление экспорта)
res_c = sc.parse_showcase((BASE / "download/showcase_sheet.csv").read_text(encoding="utf-8-sig"),
                           str(BASE / "download/showcase_sheet.csv"))
total_fails += check(res_c, "csv-файл", tol=lambda s: max(1.0, s * 0.005))

# 3) csv по Google-ссылке (end-to-end)
try:
    text = sc.load_csv_text("https://docs.google.com/spreadsheets/d/19C-JTqT5uSE5RjSPohIz5XeHp1hVfOcJ7ehEYAQiNC4/edit?gid=121343185#gid=121343185")
    res_u = sc.parse_showcase(text, "google-url-csv")
    total_fails += check(res_u, "csv-URL", tol=lambda s: max(1.0, s * 0.005))
except SystemExit as e:
    print(f"[csv-URL] ПРОПУЩЕН: {e}")
    total_fails += 1

# сводка по меткам слотов
print("\nМетки слотов (xlsx):", ", ".join(t["slot"] for t in res_x["teams"][:10]), "...")
print("Метки слотов (csv): ", ", ".join(t["slot"] for t in res_c["teams"][:10]), "...")
assert [t["slot"] for t in res_x["teams"]] == [t["slot"] for t in res_c["teams"]], "метки слотов разошлись!"

# сохранить простые JSON-результаты
(BASE / "download/showcase_simple.json").write_text(
    json.dumps(res_x, ensure_ascii=False, indent=2), encoding="utf-8")
(BASE / "download/showcase_simple_csv.json").write_text(
    json.dumps(res_c, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nСохранено: download/showcase_simple.json (xlsx, {res_x['slots_filled']} команд), "
      f"download/showcase_simple_csv.json (csv, {res_c['slots_filled']} команд)")

sys.exit(1 if total_fails else 0)
