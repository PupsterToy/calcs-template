#!/usr/bin/env python3
"""Финальная разведка: все формулы, картинки (drawings), источник карточки с формулами."""
import os
import re
import zipfile
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.formula import ArrayFormula

SINGLE = "/home/z/my-project/download/showcase_template.xlsx"
FULL = "/home/z/my-project/download/full_workbook.xlsx"

print("=== 1. Drawings (картинки) в одностраничном экспорте ===")
with zipfile.ZipFile(SINGLE) as z:
    names = z.namelist()
    dr = [n for n in names if "drawing" in n or "media" in n]
    for n in sorted(dr):
        print(f"  {n} ({z.getinfo(n).file_size} bytes)")
    # Анализ anchor'ов картинок
    for n in sorted(dr):
        if n.endswith(".xml") and "drawings/drawing" in n:
            xml = z.read(n).decode("utf-8", errors="ignore")
            anchors = re.findall(r"<xdr:from><xdr:col>(\d+)</xdr:col>.*?<xdr:row>(\d+)</xdr:row>", xml)
            print(f"  Anchors {n}: from(col,row) = {anchors[:40]}")
print()

print("=== 2. Все 84 формулы Showcase (координаты, компактно) ===")
wb = load_workbook(FULL, read_only=True, data_only=False)
ws = wb["Showcase"]
kinds = {}
for row in ws.iter_rows(min_row=1, max_row=65, max_col=115):
    for c in row:
        v = c.value
        if isinstance(v, ArrayFormula):
            kinds.setdefault("ARRAY-карточка", []).append(c.coordinate)
        elif isinstance(v, str) and v.startswith("="):
            if "IMAGE" in v:
                kinds.setdefault("IMAGE-ссылка", []).append(c.coordinate)
            else:
                kinds.setdefault("прочее", []).append((c.coordinate, v[:60]))
for k, v in kinds.items():
    print(f"  {k}: {len(v)} шт")
    print(f"    {v}")
wb.close()
print()

print("=== 3. Источник 'Sand Yae Ode Alyo': RAW AA250:AN270 (формулы+значения) ===")
wb2 = load_workbook(FULL, read_only=True, data_only=False)
ws2 = wb2["Sand Yae Ode Alyo"]
for row in ws2.iter_rows(min_row=250, max_row=270, min_col=26, max_col=40):
    for c in row:
        v = c.value
        if v is None or str(v).strip() == "":
            continue
        s = str(v).replace("\n", "\\n")
        print(f"  {c.coordinate}: {s[:100]!r}")
wb2.close()
