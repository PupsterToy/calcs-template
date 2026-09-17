#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Генерирует автономную HTML-страницу со всеми командами из JSON-дампа шоукаса.
Данные встраиваются внутрь файла — страница работает офлайн, без сервера."""
import json
from datetime import date
from pathlib import Path

SRC = Path("/home/z/my-project/download/showcase_all_teams.json")
OUT = Path("/home/z/my-project/download/showcase.html")
SRC_URL = "https://docs.google.com/spreadsheets/d/19C-JTqT5uSE5RjSPohIz5XeHp1hVfOcJ7ehEYAQiNC4/edit?gid=121343185#gid=121343185"

TEMPLATE = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Genshin Impact — Showcase команд</title>
<style>
  :root {
    --bg: #141c2b; --panel: #1d2739; --panel2: #24304a; --line: #2f3d59;
    --gold: #d3bc8e; --gold-dim: #a68b5c; --text: #e8e2d5; --muted: #9aa5b8;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; color: var(--text);
    font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: radial-gradient(1200px 600px at 50% -120px, #1e2c47 0%, var(--bg) 55%);
    min-height: 100vh;
  }
  .wrap { max-width: 1440px; margin: 0 auto; padding: 28px 22px 60px; }
  header h1 { font-size: 26px; margin: 0; color: var(--gold); letter-spacing: .5px; font-weight: 600; }
  header .sub { color: var(--muted); margin-top: 6px; font-size: 13.5px; }
  header a { color: var(--gold); text-decoration: none; }
  header a:hover { text-decoration: underline; }
  .stats { display: flex; gap: 14px; margin: 20px 0; flex-wrap: wrap; }
  .stat { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 10px 18px; min-width: 140px; }
  .stat .v { font-size: 21px; color: var(--gold); font-weight: 600; font-variant-numeric: tabular-nums; }
  .stat .k { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .8px; margin-top: 3px; }
  .controls { display: flex; gap: 10px; margin-bottom: 8px; flex-wrap: wrap; }
  details.legend { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; margin: 16px 0 20px; }
  details.legend summary { cursor: pointer; padding: 10px 16px; color: var(--gold); font-size: 13.5px; font-weight: 600; user-select: none; }
  details.legend[open] summary { border-bottom: 1px solid var(--line); }
  details.legend .body { padding: 8px 18px 12px; font-size: 13px; line-height: 1.55; }
  details.legend p { margin: 7px 0; }
  details.legend ul { margin: 7px 0; padding-left: 22px; }
  details.legend li { margin: 3px 0; }
  details.legend b { color: var(--gold); }
  details.legend .tag { display: inline-block; border: 1px solid var(--line); border-radius: 6px; padding: 1px 8px; font-size: 11px; color: var(--muted); background: #00000038; }
  #q { flex: 1; min-width: 240px; }
  #q, #sort {
    background: var(--panel); border: 1px solid var(--line); color: var(--text);
    border-radius: 8px; padding: 10px 13px; font-size: 14px; outline: none;
  }
  #q:focus, #sort:focus { border-color: var(--gold-dim); }
  #count { color: var(--muted); font-size: 12.5px; margin: 4px 2px 16px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(440px, 100%), 1fr)); gap: 18px; }
  .card {
    background: linear-gradient(180deg, var(--panel2), var(--panel));
    border: 1px solid var(--line); border-radius: 14px; padding: 16px 18px 13px;
    position: relative; overflow: hidden; transition: border-color .15s;
  }
  .card:hover { border-color: var(--gold-dim); }
  .card::before { content: ''; position: absolute; inset: 0 0 auto 0; height: 3px;
    background: linear-gradient(90deg, transparent, var(--gold-dim), transparent); opacity: .75; }
  .card-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 10px; }
  .card h2 { margin: 0; font-size: 16px; color: var(--gold); font-weight: 600; }
  .slot { font-size: 11px; color: var(--muted); border: 1px solid var(--line); border-radius: 6px; padding: 2px 8px; white-space: nowrap; }
  .topbadge { font-size: 10.5px; color: #1c2333; background: var(--gold); border-radius: 6px; padding: 2.5px 8px; font-weight: 700; letter-spacing: .4px; white-space: nowrap; }
  .team-stats { display: flex; gap: 7px; flex-wrap: wrap; margin-bottom: 10px; }
  .chip { background: #00000042; border: 1px solid var(--line); border-radius: 8px; padding: 4px 10px; font-size: 12.5px; color: var(--muted); cursor: default; }
  .chip b { color: var(--text); font-weight: 600; font-variant-numeric: tabular-nums; }
  .stack { display: flex; height: 8px; border-radius: 4px; overflow: hidden; margin: 2px 0 6px; background: #00000050; }
  .stack i { height: 100%; }
  table.chars { width: 100%; border-collapse: collapse; font-size: 13px; }
  table.chars td { padding: 6px 6px 5px; border-top: 1px solid #00000038; vertical-align: top; }
  td.cnum { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; width: 1%; }
  .cname { font-weight: 600; white-space: nowrap; }
  .cons { color: var(--gold); font-size: 11.5px; }
  .cdot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 6px; }
  .cbar { height: 6px; border-radius: 3px; background: #00000050; overflow: hidden; margin-top: 4px; }
  .cbar i { display: block; height: 100%; }
  .cpct { color: var(--muted); font-size: 11px; margin-top: 3px; }
  .gear { color: var(--muted); font-size: 11.5px; margin-top: 3px; }
  .rot { margin-top: 10px; background: #00000042; border: 1px solid var(--line); border-left: 3px solid var(--gold-dim);
    border-radius: 8px; padding: 8px 11px; font-size: 12.5px; line-height: 1.5; }
  .rot .lbl { color: var(--gold); font-size: 10.5px; text-transform: uppercase; letter-spacing: .8px; display: block; margin-bottom: 3px; }
  .extra { color: var(--muted); font-size: 11.5px; margin-top: 8px; white-space: pre-line; line-height: 1.45; }
  .foot { display: flex; justify-content: space-between; color: var(--muted); font-size: 11px; margin-top: 10px; }
  .empty { color: var(--muted); text-align: center; padding: 40px; grid-column: 1 / -1; font-size: 15px; }
  footer.page { margin-top: 28px; color: var(--muted); font-size: 11.5px; text-align: center; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Genshin Impact — Showcase команд</h1>
    <div class="sub">Источник: <a href="__SRC__" target="_blank" rel="noopener">Google Sheets · Timmie's Bird</a> · лист «__SHEET__» · данные на __GENERATED__</div>
  </header>

  <details class="legend" open>
    <summary>Что означает «слот R2·C1» и другие метки на карточках?</summary>
    <div class="body">
      <p>Лист Showcase в таблице — это сетка карточек-команд <b>6&nbsp;рядов × 6&nbsp;колонок</b> (36 слотов, из них заполнено __FILLED__).
      Метка <span class="tag">слот R·C</span> в углу карточки показывает её место в этой сетке:</p>
      <ul>
        <li><b>R</b> (row) — ряд сетки, от 1 (верхний) до 6 (нижний); на листе один ряд занимает полосу в 10 строк;</li>
        <li><b>C</b> (column) — колонка сетки, от 1 (левая) до 6 (правая); одна колонка занимает полосу в 19 столбцов.</li>
      </ul>
      <p>Пример: «слот R2·C1» — команда расположена во 2-м ряду, 1-й колонке листа.
      Якорь каждого блока — ячейка с заголовком «Team» (для R2·C1 это <b>J14</b>, карточка занимает диапазон <b>B14:S22</b>).
      Наведите курсор на метку слота на любой карточке — увидите её якорь и диапазон. Пустые слоты (без персонажей) на страницу не выводятся.</p>
    </div>
  </details>

  <div class="stats" id="stats"></div>

  <div class="controls">
    <input id="q" type="search" placeholder="Поиск: команда, персонаж, оружие, сет…">
    <select id="sort">
      <option value="dpr">Сортировка: DPR ↓</option>
      <option value="dps">Сортировка: DPS ↓</option>
      <option value="time">Сортировка: время ротации ↑</option>
      <option value="name">Сортировка: имя ↑</option>
    </select>
  </div>
  <div id="count"></div>

  <div class="grid" id="grid"></div>

  <footer class="page">Данные извлечены автоматически из таблицы-шоукаса (этап 1 пайплайна) · всего слотов: __TOTAL__, заполнено: __FILLED__</footer>
</div>
<noscript>Для отображения команд включите JavaScript.</noscript>
<script>
const DATA = __DATA__;
const TEAMS = DATA.teams.filter(t => !t.is_empty && t.characters.length);
const COLORS = ['#d4b483', '#b08cff', '#6fc3df', '#a6c96a', '#f2a3a3', '#f2d16b'];
const COLANCHORS = ['J', 'AC', 'AV', 'BO', 'CH'];

const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g,
  m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const fmtInt = n => (n == null || isNaN(n)) ? '—' : Math.round(n).toLocaleString('ru-RU');
const fmt1 = n => (n == null || isNaN(n)) ? '—' : (+n).toLocaleString('ru-RU', {minimumFractionDigits: 1, maximumFractionDigits: 1});

const bestDps = Math.max(...TEAMS.map(t => t.dps || 0));
const bestDpr = Math.max(...TEAMS.map(t => t.total_dpr || 0));
const uniqChars = new Set(TEAMS.flatMap(t => t.characters.map(c => c.name.replace(/^C\d+\s*/, '')))).size;

function slotInfo(a) {
  const m = /^([A-Z]+)(\d+)$/.exec(a || '');
  if (!m) return null;
  const col = COLANCHORS.indexOf(m[1]) + 1;
  const row = Math.round((+m[2] - 4) / 10) + 1;
  return col > 0 ? {row: row, col: col, cell: a} : null;
}

function slotLabel(a) {
  const s = slotInfo(a);
  return s ? 'слот R' + s.row + '·C' + s.col : (a || '');
}

function nameHtml(n) {
  const m = /^(C\d+)\s+(.*)$/.exec(n);
  return m ? '<span class="cons">' + m[1] + '</span> ' + esc(m[2]) : esc(n);
}

function card(t) {
  const chars = t.characters.map((c, i) => {
    const col = COLORS[i % COLORS.length];
    const share = c.damage_share != null ? c.damage_share * 100
                : (t.total_dpr ? c.damage / t.total_dpr * 100 : 0);
    const gear = [c.weapon, c.artifact_set, c.er_requirement].filter(Boolean).map(esc).join(' · ') || '—';
    return '<tr><td>' +
      '<div class="cname"><span class="cdot" style="background:' + col + '"></span>' + nameHtml(c.name) + '</div>' +
      '<div class="cbar"><i style="width:' + Math.min(100, share).toFixed(1) + '%; background:' + col + '"></i></div>' +
      '<div class="gear">' + gear + '</div></td>' +
      '<td class="cnum">' + fmtInt(c.damage) +
      '<div class="cpct">' + share.toFixed(1) + '% · ' + fmt1(c.field_time_s) + 'с</div></td></tr>';
  }).join('');
  const stack = t.characters.map((c, i) =>
    '<i style="width:' + ((c.damage_share || 0) * 100).toFixed(2) + '%; background:' + COLORS[i % COLORS.length] + '"></i>').join('');
  const rot = t.rotation
    ? '<div class="rot"><span class="lbl">Ротация · ' + fmt1(t.rotation_time_s) + 'с</span>' + esc(t.rotation) + '</div>' : '';
  const extra = t.extra_info ? '<div class="extra">' + esc(t.extra_info) + '</div>' : '';
  const badge = (t.dps && t.dps === bestDps) ? '<span class="topbadge">Топ DPS</span>' : '';
  const si = slotInfo(t._anchor);
  const slotTitle = si
    ? 'Позиция карточки в сетке листа: ряд ' + si.row + ', колонка ' + si.col +
      '. Якорь — ячейка ' + si.cell + ' (заголовок «Team»)' +
      (t._range ? '; карточка занимает диапазон ' + t._range : '') + '.'
    : '';
  return '<article class="card">' +
    '<div class="card-head"><h2>' + esc(t.calc_sheet || '—') + '</h2><div style="display:flex;gap:6px;align-items:center">' +
    badge + '<span class="slot" title="' + esc(slotTitle) + '">' + slotLabel(t._anchor) + '</span></div></div>' +
    '<div class="team-stats">' +
    '<span class="chip" title="' + (t.total_dpr != null ? t.total_dpr : '') + '">DPR <b>' + fmtInt(t.total_dpr) + '</b></span>' +
    '<span class="chip" title="' + (t.dps != null ? t.dps : '') + '">DPS <b>' + fmtInt(t.dps) + '</b></span>' +
    '<span class="chip">ротация <b>' + fmt1(t.rotation_time_s) + 'с</b></span>' +
    '<span class="chip">героев <b>' + t.characters.length + '</b></span></div>' +
    '<div class="stack">' + stack + '</div>' +
    '<table class="chars"><tbody>' + chars + '</tbody></table>' + rot + extra +
    '<div class="foot"><span>' + (t.author ? 'by ' + esc(t.author) : '') + '</span><span>' + esc(t.date || '') + '</span></div>' +
    '</article>';
}

const grid = document.getElementById('grid');
const countEl = document.getElementById('count');

function currentList() {
  const q = document.getElementById('q').value.trim().toLowerCase();
  const mode = document.getElementById('sort').value;
  const list = TEAMS.filter(t => {
    if (!q) return true;
    const hay = [t.calc_sheet, t.rotation, t.author]
      .concat(t.characters.flatMap(c => [c.name, c.weapon, c.artifact_set]))
      .filter(Boolean).join(' ').toLowerCase();
    return hay.includes(q);
  });
  const cmp = {
    dpr:  (a, b) => (b.total_dpr || 0) - (a.total_dpr || 0),
    dps:  (a, b) => (b.dps || 0) - (a.dps || 0),
    time: (a, b) => ((a.rotation_time_s || 1e9) - (b.rotation_time_s || 1e9)) || ((b.dps || 0) - (a.dps || 0)),
    name: (a, b) => String(a.calc_sheet || '').localeCompare(String(b.calc_sheet || ''), 'ru'),
  }[mode];
  list.sort(cmp);
  return list;
}

function render() {
  const list = currentList();
  grid.innerHTML = list.length ? list.map(card).join('') : '<div class="empty">Ничего не найдено</div>';
  countEl.textContent = 'Показано команд: ' + list.length + ' из ' + TEAMS.length;
}

document.getElementById('stats').innerHTML =
  '<div class="stat"><div class="v">' + TEAMS.length + '</div><div class="k">команд</div></div>' +
  '<div class="stat"><div class="v">' + uniqChars + '</div><div class="k">персонажей</div></div>' +
  '<div class="stat"><div class="v">' + fmtInt(bestDpr) + '</div><div class="k">лучший DPR</div></div>' +
  '<div class="stat"><div class="v">' + fmtInt(bestDps) + '</div><div class="k">лучший DPS</div></div>';

document.getElementById('q').addEventListener('input', render);
document.getElementById('sort').addEventListener('change', render);
render();
</script>
</body>
</html>
"""


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    payload = dict(data)
    payload["generated"] = date.today().isoformat()
    payload["source_url"] = SRC_URL

    html = (TEMPLATE
            .replace("__SRC__", SRC_URL)
            .replace("__SHEET__", str(data.get("sheet", "Showcase")))
            .replace("__GENERATED__", payload["generated"])
            .replace("__TOTAL__", str(data.get("total_slots", "?")))
            .replace("__FILLED__", str(data.get("filled_slots", "?")))
            .replace("__DATA__", json.dumps(payload, ensure_ascii=False)))
    OUT.write_text(html, encoding="utf-8")
    print(f"OK: {OUT} ({OUT.stat().st_size} байт, {data['filled_slots']} команд, "
          f"{sum(len(t['characters']) for t in data['teams'])} персонажей)")


if __name__ == "__main__":
    main()
