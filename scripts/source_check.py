#!/usr/bin/env python3
"""Проверка: карточки-источника (кэш), шапка расчётного листа, содержимое AI257/AK257."""
from openpyxl import load_workbook
from openpyxl.worksheet.formula import ArrayFormula

FULL = "/home/z/my-project/download/full_workbook.xlsx"

def atext(v):
    if isinstance(v, ArrayFormula):
        return f"ARRAY({v.text})"
    return v

print("=== 1. Кэш формул источника 'Sand Yae Ode Alyo' AA256:AM262 ===")
wv = load_workbook(FULL, read_only=True, data_only=True)
sv = wv["Sand Yae Ode Alyo"]
for r in range(256, 263):
    for c in range(27, 41):  # AB..AN
        cell = sv.cell(row=r, column=c)
        if cell.value is not None and str(cell.value).strip() != "":
            print(f"  {cell.coordinate}: {str(cell.value)[:70]!r}")
print()

print("=== 2. RAW: что тянут AA256, AC256, AE256, AG256, AI257, AK257, AA260 ===")
wf = load_workbook(FULL, read_only=True, data_only=False)
sf = wf["Sand Yae Ode Alyo"]
for coord in ("AA256", "AC256", "AE256", "AG256", "AI257", "AK257", "AA260", "AC260"):
    print(f"  {coord}: {atext(sf[coord].value)!r}")
print()

print("=== 3. Шапка расчётного листа (A1:L8) — откуда имена ===")
for r in range(1, 9):
    for c in range(1, 13):
        cell = sv.cell(row=r, column=c)
        if cell.value is not None and str(cell.value).strip() != "":
            print(f"  {cell.coordinate}: {str(cell.value)[:60]!r}")
wv.close()
wf.close()
