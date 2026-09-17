"use client";

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { fmt1, fmtInt, parseSlot, splitCons } from "@/lib/showcase/format";
import type { TeamBlock } from "@/lib/showcase/types";

const CHAR_COLORS = ["#d4b483", "#b08cff", "#6fc3df", "#a6c96a", "#f2a3a3", "#f2d16b"];

interface TeamCardProps {
  team: TeamBlock;
  isTopDps: boolean;
}

export function TeamCard({ team, isTopDps }: TeamCardProps) {
  const slot = parseSlot(team.slot);
  const slotTip = slot
    ? `Позиция карточки в сетке листа: ряд ${slot.row}, колонка ${slot.col}. ` +
      (team.anchor
        ? `Якорь — ячейка ${team.anchor} (заголовок «Team»)` +
          (team.range ? `; карточка занимает диапазон ${team.range}` : "")
        : "") +
      "."
    : "Позиция карточки в сетке листа.";

  return (
    <article
      className="relative overflow-hidden rounded-xl border border-[#2f3d59] bg-gradient-to-b from-[#24304a] to-[#1d2739] p-4 pt-5 transition-colors hover:border-[#a68b5c] sm:p-5"
      aria-label={`Команда ${team.team_name ?? "без названия"}`}
    >
      <div
        aria-hidden
        className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-transparent via-[#a68b5c] to-transparent opacity-75"
      />

      <header className="mb-3 flex items-start justify-between gap-2">
        <h2 className="text-[15px] leading-snug font-semibold text-[#d3bc8e] sm:text-base">
          {team.team_name ?? "—"}
        </h2>
        <div className="flex shrink-0 items-center gap-1.5">
          {isTopDps && (
            <span className="rounded-md bg-[#d3bc8e] px-2 py-0.5 text-[10.5px] font-bold tracking-wide whitespace-nowrap text-[#1c2333]">
              Топ DPS
            </span>
          )}
          <TooltipProvider delayDuration={80}>
            <Tooltip>
              <TooltipTrigger asChild>
                <span
                  tabIndex={0}
                  className="cursor-help rounded-md border border-[#2f3d59] px-2 py-1 text-[11px] whitespace-nowrap text-[#9aa5b8]"
                >
                  слот {team.slot}
                </span>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-64 text-left text-xs leading-relaxed">
                {slotTip}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </header>

      <div className="mb-2.5 flex flex-wrap gap-1.5 text-[12.5px] text-[#9aa5b8]">
        <span
          className="rounded-lg border border-[#2f3d59] bg-black/25 px-2.5 py-1"
          title={team.total_dpr != null ? String(team.total_dpr) : undefined}
        >
          DPR <b className="font-semibold text-[#e8e2d5] tabular-nums">{fmtInt(team.total_dpr)}</b>
        </span>
        <span className="rounded-lg border border-[#2f3d59] bg-black/25 px-2.5 py-1">
          DPS <b className="font-semibold text-[#e8e2d5] tabular-nums">{fmtInt(team.dps)}</b>
        </span>
        <span className="rounded-lg border border-[#2f3d59] bg-black/25 px-2.5 py-1">
          ротация <b className="font-semibold text-[#e8e2d5] tabular-nums">{fmt1(team.rotation_time_s)}с</b>
        </span>
        <span className="rounded-lg border border-[#2f3d59] bg-black/25 px-2.5 py-1">
          героев <b className="font-semibold text-[#e8e2d5] tabular-nums">{team.characters.length}</b>
        </span>
      </div>

      <div className="mb-2.5 flex h-2 overflow-hidden rounded-full bg-black/30" aria-hidden>
        {team.characters.map((c, i) => (
          <div
            key={c.name}
            style={{
              width: `${((c.damage_share ?? 0) * 100).toFixed(2)}%`,
              background: CHAR_COLORS[i % CHAR_COLORS.length],
            }}
          />
        ))}
      </div>

      <ul className="mb-1">
        {team.characters.map((c, i) => {
          const color = CHAR_COLORS[i % CHAR_COLORS.length];
          const share =
            c.damage_share != null
              ? c.damage_share * 100
              : team.total_dpr
                ? (c.damage ?? 0) / team.total_dpr * 100
                : 0;
          const gear = [c.weapon, c.artifact_set, c.er_requirement]
            .filter(Boolean)
            .join(" · ");
          const { cons, base } = splitCons(c.name);
          return (
            <li key={c.name} className="flex items-start justify-between gap-3 border-t border-black/25 py-2">
              <div className="min-w-0">
                <div className="flex items-center gap-2 text-[13px] font-semibold text-[#e8e2d5]">
                  <span
                    aria-hidden
                    className="h-2.5 w-2.5 shrink-0 rounded-full"
                    style={{ background: color }}
                  />
                  {cons && <span className="text-[11.5px] text-[#d3bc8e]">{cons}</span>}
                  <span className="truncate">{base}</span>
                </div>
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-black/30">
                  <div
                    className="h-full"
                    style={{ width: `${Math.min(100, share).toFixed(1)}%`, background: color }}
                  />
                </div>
                {gear && <div className="mt-1 text-[11px] text-[#9aa5b8]">{gear}</div>}
              </div>
              <div className="shrink-0 text-right tabular-nums">
                <div className="text-[13px] font-semibold text-[#e8e2d5]">{fmtInt(c.damage)}</div>
                <div className="text-[11px] text-[#9aa5b8]">
                  {share.toFixed(1)}% · {fmt1(c.field_time_s)}с
                </div>
              </div>
            </li>
          );
        })}
      </ul>

      {team.rotation && (
        <div className="mt-2 rounded-lg border border-[#2f3d59] border-l-[3px] border-l-[#a68b5c] bg-black/25 px-3 py-2 text-[12.5px] leading-relaxed text-[#e8e2d5]">
          <span className="mb-1 block text-[10.5px] tracking-wider text-[#d3bc8e] uppercase">
            Ротация · {fmt1(team.rotation_time_s)}с
          </span>
          {team.rotation}
        </div>
      )}

      {team.extra_info && (
        <p className="mt-2 text-[11.5px] leading-relaxed whitespace-pre-line text-[#9aa5b8]">
          {team.extra_info}
        </p>
      )}

      <footer className="mt-2.5 flex items-center justify-between text-[11px] text-[#9aa5b8]">
        <span>{team.author ? `by ${team.author}` : ""}</span>
        <span>{team.date ?? ""}</span>
      </footer>
    </article>
  );
}
