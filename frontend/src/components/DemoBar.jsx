import { Bot, ShieldCheck } from 'lucide-react';

const TONE = {
  ear: 'bg-teal-50 hover:bg-teal-100 text-teal-900 border-teal-200',
  bp: 'bg-sky-50 hover:bg-sky-100 text-sky-900 border-sky-200',
  ankle: 'bg-amber-50 hover:bg-amber-100 text-amber-900 border-amber-200',
  heart: 'bg-violet-50 hover:bg-violet-100 text-violet-900 border-violet-200',
  chest: 'bg-rose-50 hover:bg-rose-100 text-rose-900 border-rose-200',
};

export default function DemoBar({ scenarios, onLoad, health }) {
  return (
    <div className="card p-4 flex flex-col lg:flex-row lg:items-center justify-between gap-3">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="eyebrow text-teal-700">Quick demo scenarios</span>
          <span className="text-[11px] px-2 py-0.5 rounded-md bg-amber-100 text-amber-800 font-semibold inline-flex items-center gap-1">
            <ShieldCheck className="w-3 h-3" /> Synthetic test patients only
          </span>
          {health && (
            <span className={`text-[11px] px-2 py-0.5 rounded-md font-semibold inline-flex items-center gap-1 ${health.ai_enabled ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}`}
              title={health.ai_enabled ? `Model: ${health.model}` : 'Add ANTHROPIC_API_KEY to .env to turn on Claude'}>
              <Bot className="w-3 h-3" /> {health.ai_enabled ? 'AI: Claude on' : 'AI: rules mode (no key)'}
            </span>
          )}
        </div>
        <p className="text-xs text-slate-500 mt-0.5">Load a family-medicine case, or type your own symptoms below. The last two show the safety screen.</p>
      </div>
      <div className="flex flex-wrap gap-2">
        {scenarios.map((s) => (
          <button key={s.id} type="button" onClick={() => onLoad(s)}
            className={`px-3 py-1.5 rounded-xl border text-xs font-semibold transition ${TONE[s.id] || TONE.ear}`}>
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
}
