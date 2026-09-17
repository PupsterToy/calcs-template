/**
 * ts-parser-test.ts — E2E-проверка TypeScript-порта простого парсера
 * (того самого кода, который работает в браузере на странице).
 *
 * Проверяет на реальных файлах:
 *   1) xlsx (SheetJS)  — глубокое равенство с эталоном src/data/demo-teams.json
 *   2) csv (файл)      — соответствие эталону с допуском на округление CSV
 *   3) Google-ссылка   — скачивание /export?format=csv и gviz (end-to-end)
 *
 * Запуск: bun scripts/ts-parser-test.ts
 */
import { readFileSync } from "fs";
import { parseCsv } from "../src/lib/showcase/csv";
import { fetchSheetCsv, parseGoogleUrl } from "../src/lib/showcase/google";
import { colLetter, parseShowcaseGrid, toNum } from "../src/lib/showcase/parse";
import type { ShowcaseData, TeamBlock } from "../src/lib/showcase/types";
import { pickShowcaseSheet, readWorkbook } from "../src/lib/showcase/xlsx";

const BASE = "/home/z/my-project";
const SHEET_URL =
  "https://docs.google.com/spreadsheets/d/19C-JTqT5uSE5RjSPohIz5XeHp1hVfOcJ7ehEYAQiNC4/edit?gid=121343185#gid=121343185";

let failures = 0;
function ok(cond: boolean, msg: string) {
  if (!cond) {
    failures++;
    console.error("  FAIL:", msg);
  }
}

/** Глубокое сравнение: числа — с допуском, строки/массивы — точно. */
function deepEq(a: unknown, b: unknown, tol: number, path: string): boolean {
  if (a === null || b === null) {
    if (a !== b) {
      console.error(`  ${path}: ${a} != ${b}`);
      return false;
    }
    return true;
  }
  if (typeof a === "number" && typeof b === "number") {
    const good = Math.abs(a - b) <= Math.max(tol, Math.max(Math.abs(a), Math.abs(b)) * 1e-5);
    if (!good) console.error(`  ${path}: ${a} != ${b}`);
    return good;
  }
  if (typeof a !== typeof b || Array.isArray(a) !== Array.isArray(b)) {
    console.error(`  ${path}: типы ${typeof a} / ${typeof b}`);
    return false;
  }
  if (Array.isArray(a)) {
    if (a.length !== (b as unknown[]).length) {
      console.error(`  ${path}: длины ${a.length} != ${(b as unknown[]).length}`);
      return false;
    }
    return a.every((x, i) => deepEq(x, (b as unknown[])[i], tol, `${path}[${i}]`));
  }
  if (typeof a === "object") {
    const ka = Object.keys(a as object).sort();
    const kb = Object.keys(b as object).sort();
    if (ka.join(",") !== kb.join(",")) {
      console.error(`  ${path}: ключи ${ka} != ${kb}`);
      return false;
    }
    return ka.every((k) =>
      deepEq((a as Record<string, unknown>)[k], (b as Record<string, unknown>)[k], tol, `${path}.${k}`),
    );
  }
  if (a !== b) {
    console.error(`  ${path}: ${JSON.stringify(a)} != ${JSON.stringify(b)}`);
    return false;
  }
  return true;
}

// ---------- юнит-проверки утилит ----------
console.log("Утилиты:");
ok(toNum("1,959,082") === 1959082, "toNum: 1,959,082");
ok(toNum("51.09%")! > 0.510899 && toNum("51.09%")! < 0.510901, "toNum: 51.09%");
ok(toNum("14.5s") === 14.5, "toNum: 14.5s");
ok(toNum("—") === null, "toNum: — => null");
ok(colLetter(1) === "A" && colLetter(10) === "J" && colLetter(29) === "AC" && colLetter(86) === "CH", "colLetter");
ok(JSON.stringify(parseGoogleUrl(SHEET_URL)) === '{"sid":"19C-JTqT5uSE5RjSPohIz5XeHp1hVfOcJ7ehEYAQiNC4","gid":"121343185"}', "parseGoogleUrl");

// ---------- эталон ----------
const demo = JSON.parse(readFileSync(`${BASE}/src/data/demo-teams.json`, "utf-8")) as ShowcaseData;
const refTeams = demo.teams.filter((t) => !t.is_empty) as TeamBlock[];
console.log(`Эталон: ${refTeams.length} команд`);

// ---------- 1) xlsx ----------
console.log("1) xlsx (SheetJS):");
const wb = readWorkbook(readFileSync(`${BASE}/download/showcase_template.xlsx`));
const sheet = pickShowcaseSheet(wb.names);
ok(sheet === "Showcase", `автовыбор листа: ${sheet}`);
if (sheet) {
  const res = parseShowcaseGrid(wb.getGrid(sheet), "test.xlsx", "xlsx");
  ok(res.slots_total === demo.slots_total && res.slots_filled === demo.slots_filled,
    `слоты: ${res.slots_total}/${res.slots_filled} vs ${demo.slots_total}/${demo.slots_filled}`);
  ok(res.grid.rows === demo.grid.rows && res.grid.cols === demo.grid.cols,
    `сетка: ${JSON.stringify(res.grid)} vs ${JSON.stringify(demo.grid)}`);
  ok(deepEq(res.teams, demo.teams, 0, "xlsx.teams"), "глубокое равенство с эталоном");
  console.log(`  слот первой: ${res.teams[0].slot} (${res.teams[0].anchor}), последней: ${res.teams.at(-1)!.slot} (${res.teams.at(-1)!.anchor})`);
}

// ---------- 2) csv-файл ----------
console.log("2) csv-файл:");
const csvText = readFileSync(`${BASE}/download/showcase_sheet.csv`, "utf-8");
const resc = parseShowcaseGrid(parseCsv(csvText), "test.csv", "csv");
ok(resc.slots_filled === refTeams.length, `команд: ${resc.slots_filled}`);
ok(JSON.stringify(resc.teams.map((t) => t.slot)) === JSON.stringify(demo.teams.map((t) => t.slot)),
  "последовательность слотов совпадает");
ok(deepEq(resc.teams, demo.teams, 1.0, "csv.teams"), "равенство с эталоном (допуск 1.0)");
ok(resc.teams[0].date === demo.teams[0].date, `дата: ${resc.teams[0].date}`);

// ---------- 3) Google-ссылка (end-to-end) ----------
console.log("3) Google-ссылка:");
const { text, via } = await fetchSheetCsv(SHEET_URL);
const resu = parseShowcaseGrid(parseCsv(text), "google", "csv");
ok(via === "export", `эндпоинт: ${via}`);
ok(resu.slots_filled === refTeams.length, `команд: ${resu.slots_filled}`);
ok(deepEq(resu.teams, demo.teams, 1.0, "url.teams"), "равенство с эталоном (допуск 1.0)");

// gviz (запасной эндпоинт: пропускает пустые строки — проверяем устойчивость якорей)
const gviz = await fetch(
  "https://docs.google.com/spreadsheets/d/19C-JTqT5uSE5RjSPohIz5XeHp1hVfOcJ7ehEYAQiNC4/gviz/tq?tqx=out:csv&gid=121343185",
);
const resg = parseShowcaseGrid(parseCsv(await gviz.text()), "gviz", "csv", { alignedRows: false });
ok(resg.slots_filled === refTeams.length, `gviz команд: ${resg.slots_filled}`);
ok(JSON.stringify(resg.teams.map((t) => t.slot)) === JSON.stringify(demo.teams.map((t) => t.slot)),
  "gviz: слоты совпадают (позиционные метки устойчивы к пропуску пустых строк)");
ok(resg.teams.every((t) => t.anchor === null && t.range === null), "gviz: адреса якорей скрыты");
// известное ограничение gviz: ячейки с межлистовыми формулами (автор) приходят пустыми
const stripGviz = (t: TeamBlock) => ({ ...t, anchor: null, range: null, author: null });
ok(
  deepEq(resg.teams.map(stripGviz), demo.teams.map(stripAddr2), 1.0, "gviz.teams"),
  "gviz: данные равны эталону",
);
function stripAddr2(t: TeamBlock) {
  return { ...t, anchor: null, range: null, author: null };
}

console.log(failures === 0 ? "\nИТОГ: все проверки пройдены" : `\nИТОГ: провалено проверок: ${failures}`);
process.exit(failures === 0 ? 0 : 1);
