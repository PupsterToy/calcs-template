#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simple_csv.py — ПРОСТОЙ парсер Showcase-листа из CSV (только csv).

Принцип тот же, что у simple_xlsx.py: ТОЛЬКО видимые (отображаемые на листе)
значения. CSV — это всегда "сухие" значения: формулы, имена расчётных листов
и гиперссылки в него не попадают в принципе.

Вход:  путь к .csv ИЛИ Google-ссылка на таблицу/лист (лист скачается в CSV:
       /export?format=csv&gid=...). Готовые ссылки экспорта тоже принимаются.
Опции: --out файл.json — сохранить результат; иначе печать в консоль.

Особенности CSV-значений (нормализуются автоматически):
  - числа отформатированы: '1,959,082' / '51.09%' / '14.5s';
  - точность ниже, чем в xlsx (округление до целых урона, до 2 знаков — проценты);
  - даты в виде строк '9/17/2026';
  - многострочные ячейки заключены в кавычки (модуль csv это понимает).

Формат командного блока (якорь — ячейка 'Team' в (r, c); bc = c - 8):
  r+1..r+4   col c      — имена персонажей ("C0 Sandrone")
              col c+2    — DPR, col c+3 — доля урона, col c+4 — время на поле, с
  r+4/r+5/r+6 cols bc+0/2/4/6 — оружие / сет артефактов / требования ER
  r+5: col c+2 — Total DPR, col c+3 — дата; r+6: col c — длит. ротации,
       col c+2 — DPS, col c+3 — автор; r+7: col bc+1 — текст ротации
  r+1..r+8, cols c+6..c+9 — примечания (Extra Information)

Сетка листа: слоты 6x6, шаг 19 колонок / 10 строк. Слот пуст ⇢ нет имён персонажей.
"""
import argparse
import csv
import io
import json
import re
import sys
import urllib.request
from datetime import datetime

SHEET_HINT = "Showcase"  # имя листа известно из контекста; в CSV его нет


# ---------------------------- вспомогательные ----------------------------

def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read().decode("utf-8-sig", errors="replace")


def google_csv_url(src):
    """Строит ссылку экспорта листа Google-таблицы в CSV (или берёт готовую)."""
    if "format=csv" in src or "out:csv" in src:
        return src
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", src)
    sid = m.group(1) if m else src
    url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv"
    gid = re.search(r"[#&?]gid=(\d+)", src)
    return url + (f"&gid={gid.group(1)}" if gid else "")


def text(v):
    """Строка без краёв или None."""
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def to_num(v):
    """Число или None. Понимает отформатированные строки CSV:
    '1,959,082' -> 1959082.0; '51.09%' -> 0.5109; '14.5s' -> 14.5."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = text(v)
    if not s:
        return None
    pct = "%" in s
    s = s.replace(",", "").replace("%", "").rstrip("s").strip()
    try:
        x = float(s)
    except ValueError:
        return None
    return x / 100.0 if pct else x


def to_date(v):
    """ISO-дата из строки ('9/17/2026', '17.09.2026', ...)."""
    s = text(v)
    if not s:
        return None
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    return s


# ---------------------------- сетка CSV ----------------------------

class Grid:
    """CSV-строки как сетка с 1-based координатами (аналог листа openpyxl)."""

    def __init__(self, csv_text):
        self._rows = list(csv.reader(io.StringIO(csv_text)))

    def val(self, row, column):
        """Значение ячейки (row, column), 1-based; вне сетки — None."""
        r = self._rows[row - 1] if 0 < row <= len(self._rows) else None
        if r is None:
            return None
        return r[column - 1] if 0 < column <= len(r) else None


# ---------------------------- разбор листа ----------------------------

def find_team_anchors(grid):
    """Все ячейки 'Team' — левые верхние углы сводок блоков."""
    anchors = []
    for ri, row in enumerate(grid._rows, 1):
        for ci, v in enumerate(row, 1):
            if v is not None and v.strip() == "Team":
                anchors.append((ri, ci))
    return sorted(anchors)


def parse_block(grid, r, c, row_index, col_index):
    """Один командный блок: только видимые значения."""
    bc = c - 8  # колонка B блока

    chars = []
    for i in range(4):
        name = text(grid.val(r + 1 + i, c))
        if not name or name == "Total DPR":
            break
        chars.append({
            "name": name,
            "damage": to_num(grid.val(r + 1 + i, c + 2)),
            "damage_share": to_num(grid.val(r + 1 + i, c + 3)),
            "field_time_s": to_num(grid.val(r + 1 + i, c + 4)),
            "weapon": text(grid.val(r + 4, bc + 2 * i)),
            "artifact_set": text(grid.val(r + 5, bc + 2 * i)),
            "er_requirement": text(grid.val(r + 6, bc + 2 * i)),
        })

    extra = None
    for cc in range(c + 6, c + 10):
        for rr in range(r + 1, r + 9):
            v = text(grid.val(rr, cc))
            if v:
                extra = v
                break
        if extra:
            break

    return {
        "slot": f"R{row_index[r]}·C{col_index[c]}",
        "anchor": None,  # буквенную ссылку в CSV не восстановить (нет имён колонок) —
        "range": None,    # при необходимости адрес даёт сетка: (r, c) якоря 'Team'
        "team_name": " · ".join(re.sub(r"^C\d+\s+", "", ch["name"]) for ch in chars) or None,
        "characters": chars,
        "total_dpr": to_num(grid.val(r + 5, c + 2)),
        "dps": to_num(grid.val(r + 6, c + 2)),
        "rotation_time_s": to_num(grid.val(r + 6, c)),
        "rotation": text(grid.val(r + 7, bc + 1)),
        "extra_info": extra,
        "author": text(grid.val(r + 6, c + 3)),
        "date": to_date(grid.val(r + 5, c + 3)),
        "is_empty": not chars,
    }


def parse_showcase(csv_text, source):
    """CSV-текст -> простой JSON-словарь."""
    grid = Grid(csv_text)
    anchors = find_team_anchors(grid)
    if not anchors:
        raise SystemExit("Якоря 'Team' не найдены: это не Showcase-лист (или он пуст)")
    # Метки слотов — ПО ПОЗИЦИИ ЯКОРЯ в сетке, а не по абсолютным координатам
    # (gviz-экспорт, например, пропускает пустые строки — позиционный расчёт устойчив).
    rows = sorted({r for r, _ in anchors})
    cols = sorted({c for _, c in anchors})
    row_index = {r: i + 1 for i, r in enumerate(rows)}
    col_index = {c: i + 1 for i, c in enumerate(cols)}

    teams = [parse_block(grid, r, c, row_index, col_index) for r, c in anchors]
    filled = [t for t in teams if not t["is_empty"]]
    return {
        "format": "showcase-simple/1",
        "source": source,
        "source_type": "csv",
        "sheet": SHEET_HINT,
        "extracted_at": datetime.now().isoformat(timespec="seconds"),
        "grid": {"rows": len(rows), "cols": len(cols)},
        "slots_total": len(teams),
        "slots_filled": len(filled),
        "teams": teams,
    }


def load_csv_text(source):
    """Локальный .csv или Google-ссылка -> CSV-текст."""
    if re.match(r"^https?://", source):
        url = google_csv_url(source)
        text_ = download(url)
        if not text_ or text_.lstrip()[:1] == "<":
            raise SystemExit(f"Google вернул не CSV (нет доступа?): {text_[:120]!r}")
        return text_
    with open(source, encoding="utf-8-sig") as fh:
        return fh.read()


def main():
    ap = argparse.ArgumentParser(
        description="Простой парсер Showcase-листа (CSV): только видимые значения")
    ap.add_argument("source", help="путь к .csv или Google-ссылка на таблицу/лист")
    ap.add_argument("--out", default=None, help="сохранить JSON в файл")
    a = ap.parse_args()

    res = parse_showcase(load_csv_text(a.source), a.source)

    filled = [t for t in res["teams"] if not t["is_empty"]]
    nchars = sum(len(t["characters"]) for t in filled)
    print(f"Слотов: {res['slots_total']} | заполнено: {res['slots_filled']} | персонажей: {nchars}")
    warns = 0
    for t in filled:
        d_sum = sum(c["damage"] or 0 for c in t["characters"])
        if t["total_dpr"] and abs(d_sum - t["total_dpr"]) / t["total_dpr"] > 0.005:
            print(f"  ! {t['slot']}: сумма урона {d_sum:.0f} != Total DPR {t['total_dpr']:.0f}", file=sys.stderr)
            warns += 1
    print(f"Проверка сумм: {'OK' if not warns else f'{warns} расхождений'}")

    out = json.dumps(res, ensure_ascii=False, indent=2)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"Сохранено: {a.out}")
    else:
        print(out)


if __name__ == "__main__":
    main()
