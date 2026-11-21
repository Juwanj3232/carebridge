import { Bot, ShieldCheck } from 'lucide-react';
import { t } from '../lib/i18n.js';

const TONE = {
  ear: 'bg-red-50 dark:bg-red-950/40 hover:bg-red-100 dark:hover:bg-red-900/60 text-red-900 dark:text-red-200 border-red-200 dark:border-red-900',
  bp: 'bg-neutral-50 dark:bg-neutral-900/60 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-900 dark:text-neutral-100 border-neutral-200 dark:border-neutral-800',
  ankle: 'bg-amber-50 dark:bg-amber-950/40 hover:bg-amber-100 dark:hover:bg-amber-900/60 text-amber-900 dark:text-amber-200 border-amber-200 dark:border-amber-900',
  heart: 'bg-neutral-50 dark:bg-neutral-900/60 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-900 dark:text-neutral-100 border-neutral-200 dark:border-neutral-800',
  chest: 'bg-rose-50 dark:bg-rose-950/40 hover:bg-rose-100 dark:hover:bg-rose-900/60 text-rose-900 dark:text-rose-200 border-rose-200 dark:border-rose-900',
};

export default function DemoBar({ scenarios, onLoad, health, lang }) {
  const s = t(lang);
  return (
    <div className="card p-4 flex flex-col lg:flex-row lg:items-center justify-between gap-3">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="eyebrow text-red-700 dark:text-red-400">{s.demoTitle}</span>
          <span className="text-[11px] px-2 py-0.5 rounded-md bg-amber-100 dark:bg-amber-950/70 text-amber-800 dark:text-amber-200 font-semibold inline-flex items-center gap-1">
            <ShieldCheck className="w-3 h-3" /> {s.demoSynthetic}
          </span>
          {health && (
            <span className={`text-[11px] px-2 py-0.5 rounded-md font-semibold inline-flex items-center gap-1 ${health.ai_enabled && !health.limit_reached ? 'bg-emerald-100 dark:bg-emerald-950/70 text-emerald-800 dark:text-emerald-200' : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300'}`}
              title={health.ai_enabled ? `Model: ${health.model} · ${health.calls_today} of ${health.daily_limit} Claude calls used today` : 'Add ANTHROPIC_API_KEY to .env to turn on Claude'}>
              <Bot className="w-3 h-3" /> {!health.ai_enabled ? s.aiOff : health.limit_reached ? s.aiLimit : s.aiOn}
            </span>
          )}
        </div>
        <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">{s.demoHelp}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        {scenarios.map((x) => (
          <button key={x.id} type="button" onClick={() => onLoad(x)}
            className={`px-3 py-1.5 rounded-xl border text-xs font-semibold transition ${TONE[x.id] || TONE.ear}`}>
            {s.scenarios[x.id] || x.label}
          </button>
        ))}
      </div>
    </div>
  );
}
