"use client";

import { useMemo, useState } from "react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SourcePanel } from "@/components/showcase/source-panel";
import { SlotLegend } from "@/components/showcase/slot-legend";
import { TeamCard } from "@/components/showcase/team-card";
import { parseCsv } from "@/lib/showcase/csv";
import { fmtInt } from "@/lib/showcase/format";
import { fetchSheetCsv } from "@/lib/showcase/google";
import { parseShowcaseGrid } from "@/lib/showcase/parse";
import type { ShowcaseData } from "@/lib/showcase/types";
import { readWorkbook, pickShowcaseSheet, type WorkbookSheets } from "@/lib/showcase/xlsx";
import demoRaw from "@/data/demo-teams.json";

const DEMO_LABEL = "Демо: Showcase · Timmie's Bird";

const demoData: ShowcaseData = {
  ...(demoRaw as unknown as ShowcaseData),
  source_type: "demo",
  source: DEMO_LABEL,
};

type SortMode = "dpr" | "dps" | "time" | "name";

export default function Home() {
  const [data, setData] = useState<ShowcaseData>(demoData);
  const [sourceLabel, setSourceLabel] = useState<string>(DEMO_LABEL);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [pendingSheets, setPendingSheets] = useState<WorkbookSheets | null>(null);
  const [query, setQuery] = useState("");
  const [sortMode, setSortMode] = useState<SortMode>("dpr");

  const teams = useMemo(
    () => data.teams.filter((t) => !t.is_empty && t.characters.length > 0),
    [data],
  );

  const stats = useMemo(
    () => ({
      teams: teams.length,
      chars: new Set(teams.flatMap((t) => t.characters.map((c) => c.name.replace(/^C\d+\s*/, ""))))
        .size,
      bestDpr: Math.max(0, ...teams.map((t) => t.total_dpr ?? 0)),
      bestDps: Math.max(0, ...teams.map((t) => t.dps ?? 0)),
    }),
    [teams],
  );

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = teams.filter((t) => {
      if (!q) return true;
      const hay = [t.team_name, t.rotation, t.author, t.slot]
        .concat(t.characters.flatMap((c) => [c.name, c.weapon, c.artifact_set]))
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });
    const cmp: Record<SortMode, (a: ShowcaseData["teams"][number], b: ShowcaseData["teams"][number]) => number> = {
      dpr: (a, b) => (b.total_dpr ?? 0) - (a.total_dpr ?? 0),
      dps: (a, b) => (b.dps ?? 0) - (a.dps ?? 0),
      time: (a, b) => (a.rotation_time_s ?? 1e9) - (b.rotation_time_s ?? 1e9) || (b.dps ?? 0) - (a.dps ?? 0),
      name: (a, b) => String(a.team_name ?? "").localeCompare(String(b.team_name ?? ""), "ru"),
    };
    return [...list].sort(cmp[sortMode]);
  }, [teams, query, sortMode]);

  function applyGrid(
    grid: ReturnType<typeof parseCsv>,
    label: string,
    type: "xlsx" | "csv",
    alignedRows = true,
  ) {
    const parsed = parseShowcaseGrid(grid, label, type, { alignedRows });
    setData(parsed);
    setSourceLabel(label);
    setNotice(`${parsed.slots_filled} команд · слотов в сетке: ${parsed.slots_total}`);
    setPendingSheets(null);
    setError(null);
  }

  async function onFile(file: File) {
    setError(null);
    setNotice(null);
    setPendingSheets(null);
    const name = file.name.toLowerCase();
    try {
      if (name.endsWith(".csv") || file.type === "text/csv") {
        setBusy(`Читаю ${file.name}…`);
        const text = await file.text();
        applyGrid(parseCsv(text), file.name, "csv");
      } else if (name.endsWith(".xlsx") || name.endsWith(".xls")) {
        setBusy(`Читаю ${file.name}…`);
        const buf = await file.arrayBuffer();
        const sheets = readWorkbook(buf);
        const auto = pickShowcaseSheet(sheets.names);
        if (auto) {
          applyGrid(sheets.getGrid(auto), `${file.name} · лист «${auto}»`, "xlsx");
        } else if (sheets.names.length === 1) {
          applyGrid(sheets.getGrid(sheets.names[0]), `${file.name} · «${sheets.names[0]}»`, "xlsx");
        } else {
          setPendingSheets(sheets);
          setNotice(null);
          setError(
            `В книге ${sheets.names.length} листов, но листа «Showcase» среди них нет. ` +
              "Выберите нужный лист вручную.",
          );
        }
      } else {
        setError("Поддерживаются только файлы .xlsx и .csv.");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  async function onLink(url: string) {
    setError(null);
    setNotice(null);
    setPendingSheets(null);
    try {
      setBusy("Скачиваю лист по ссылке…");
      const { text, via } = await fetchSheetCsv(url);
      // gviz пропускает пустые строки листа — абсолютные адреса якорей не вычисляем
      applyGrid(parseCsv(text), `Google Sheets · ${via === "export" ? "CSV" : "gviz CSV"}`, "csv", via === "export");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  function onPickSheet(name: string) {
    if (!pendingSheets) return;
    try {
      applyGrid(pendingSheets.getGrid(name), `xlsx · лист «${name}»`, "xlsx");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  function onDemo() {
    setData({ ...demoData });
    setSourceLabel(DEMO_LABEL);
    setNotice(null);
    setError(null);
    setPendingSheets(null);
    setQuery("");
  }

  const statCells = [
    { v: String(stats.teams), k: "команд" },
    { v: String(stats.chars), k: "персонажей" },
    { v: fmtInt(stats.bestDpr), k: "лучший DPR" },
    { v: fmtInt(stats.bestDps), k: "лучший DPS" },
  ];

  return (
    <div className="flex min-h-screen flex-col bg-[#141c2b] text-[#e8e2d5]">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-72 bg-[radial-gradient(1200px_360px_at_50%_-120px,#1e2c47_0%,transparent_70%)]"
      />
      <div className="mx-auto w-full max-w-6xl flex-1 px-4 pt-8 pb-12 sm:px-6">
        <header className="mb-6">
          <div className="flex items-center gap-3">
            <span
              title="Проект в активной разработке: интерфейс и данные могут меняться"
              className="inline-flex items-center gap-2 rounded-full border border-[#8a6d3b] bg-[#2a2113] px-3 py-1 text-[11px] font-semibold tracking-widest text-[#e5c07b] uppercase"
            >
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#e5c07b] opacity-60" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-[#e5c07b]" />
              </span>
              WIP — Alpha
            </span>
          </div>
          <h1 className="mt-3 text-2xl font-semibold tracking-wide text-[#d3bc8e]">
            Genshin Impact — Showcase команд
          </h1>
          <p className="mt-2 text-[13.5px] text-[#9aa5b8]">
            Динамическая страница: загрузите xlsx, CSV или ссылку на лист Google-таблицы — команды
            будут извлечены автоматически (только видимые значения листа). Парсинг выполняется
            целиком в браузере, сервер не требуется.
          </p>
        </header>

        <SourcePanel
          onFile={onFile}
          onLink={onLink}
          onDemo={onDemo}
          onPickSheet={onPickSheet}
          busy={busy}
          error={error}
          notice={notice}
          sourceLabel={sourceLabel}
          pendingSheets={pendingSheets}
        />

        <div className="mt-5">
          <SlotLegend grid={data.grid} />
        </div>

        <section aria-label="Статистика" className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {statCells.map((s) => (
            <div
              key={s.k}
              className="rounded-xl border border-[#2f3d59] bg-[#1d2739] px-4 py-3"
            >
              <div className="text-xl font-semibold tabular-nums text-[#d3bc8e]">{s.v}</div>
              <div className="mt-1 text-[11px] tracking-wider text-[#9aa5b8] uppercase">
                {s.k}
              </div>
            </div>
          ))}
        </section>

        <section aria-label="Управление списком" className="mt-5 flex flex-wrap gap-2.5">
          <Input
            type="search"
            aria-label="Поиск по командам"
            placeholder="Поиск: команда, персонаж, оружие, сет, слот…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="min-w-56 flex-1 border-[#2f3d59] bg-[#1d2739] text-[13.5px] text-[#e8e2d5] placeholder:text-[#6b7893]"
          />
          <Select value={sortMode} onValueChange={(v) => setSortMode(v as SortMode)}>
            <SelectTrigger
              aria-label="Сортировка"
              className="w-56 border-[#2f3d59] bg-[#1d2739] text-[13.5px] text-[#e8e2d5]"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="border-[#2f3d59] bg-[#1d2739] text-[#e8e2d5]">
              <SelectItem value="dpr">Сортировка: DPR ↓</SelectItem>
              <SelectItem value="dps">Сортировка: DPS ↓</SelectItem>
              <SelectItem value="time">Сортировка: время ротации ↑</SelectItem>
              <SelectItem value="name">Сортировка: имя ↑</SelectItem>
            </SelectContent>
          </Select>
        </section>

        <p className="mt-3 text-[12.5px] text-[#9aa5b8]" aria-live="polite">
          Показано команд: {visible.length} из {teams.length}
          {data.slots_total > teams.length && ` (слотов в сетке: ${data.slots_total})`}
        </p>

        <main>
          {visible.length > 0 ? (
            <div className="mt-2 grid grid-cols-[repeat(auto-fill,minmax(min(420px,100%),1fr))] gap-4">
              {visible.map((t) => (
                <TeamCard key={t.slot} team={t} isTopDps={t.dps === stats.bestDps && t.dps > 0} />
              ))}
            </div>
          ) : (
            <p className="rounded-xl border border-[#2f3d59] bg-[#1d2739] p-10 text-center text-[15px] text-[#9aa5b8]">
              Ничего не найдено
            </p>
          )}
        </main>
      </div>

      <footer className="mt-auto border-t border-[#2f3d59] bg-[#101724] py-4 text-center text-[11.5px] text-[#9aa5b8]">
        Данные: формат showcase-simple/1 · парсинг в браузере · страница совместима со
        статическим хостингом (GitHub Pages)
        {process.env.NODE_ENV === "development" && (
          <>
            <br />
            <a
              href="/showcase-site-source.zip"
              download
              className="mt-1 inline-block rounded-md border border-[#2f3d59] bg-[#1d2739] px-3 py-1.5 text-[12px] text-[#d3bc8e] hover:border-[#d3bc8e]"
            >
              ⬇ Скачать исходники сайта (showcase-site-source.zip)
            </a>
          </>
        )}
      </footer>
    </div>
  );
}
