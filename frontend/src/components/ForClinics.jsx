import { Check, Database, Lock, Minus, ShieldCheck, Sparkles } from 'lucide-react';
import { clinicsText } from '../lib/clinics-i18n.js';

// Judge items #2 (comparison), #4 (EHR plan), #5 (privacy plan). All text comes from lib/clinics-i18n.js in the
// chosen language. The savings calculator and pricing are hidden for now; their logic still lives in backend/savings.py.
export default function ForClinics({ lang }) {
  const c = clinicsText(lang);
  return (
    <section className="space-y-6 animate-fade-up">
      <div className="card p-6 bg-gradient-to-br from-red-700 to-red-900 text-white border-0">
        <p className="eyebrow text-red-200">{c.eyebrow}</p>
        <h1 className="text-2xl sm:text-3xl font-extrabold mt-1">{c.headline}</h1>
        <p className="text-red-100 mt-2 text-sm max-w-3xl">{c.intro}</p>
      </div>

      <div className="card p-5 sm:p-6">
        <h2 className="text-lg font-bold mb-3">{c.compareTitle}</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-200 dark:border-neutral-800 text-xs uppercase text-neutral-500 dark:text-neutral-400">
                <th className="text-left py-2 pr-2 font-semibold">{c.colCapability}</th>
                <th className="py-2 px-2 font-semibold text-red-800 dark:text-red-200">{c.colUs}</th>
                <th className="py-2 pl-2 font-semibold">{c.colThem}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800">
              {c.comparisonRows.map(([cap, us, them]) => (
                <tr key={cap}>
                  <td className="py-2.5 pr-2 font-medium">{cap}</td>
                  <td className="py-2.5 px-2 text-center"><Mark v={us} c={c} /></td>
                  <td className="py-2.5 pl-2 text-center"><Mark v={them} c={c} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-2">{c.compareNote}</p>
      </div>

      <div className="card p-5 sm:p-6">
        <h3 className="text-lg font-bold flex items-center gap-2"><Sparkles className="w-5 h-5 text-red-700 dark:text-red-400" /> {c.safetyTitle}</h3>
        <ul className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-x-8 gap-y-3 text-sm text-neutral-700 dark:text-neutral-200">
          {c.safety.map((x) => <li key={x} className="flex gap-2"><Lock className="w-3.5 h-3.5 text-red-700 dark:text-red-400 shrink-0 mt-0.5" /> {x}</li>)}
        </ul>
      </div>

      {/* Privacy and EHR plans sit in a strip on the page's bottom border: plain promise first, precise detail second. */}
      <div className="border-t-2 border-neutral-200 dark:border-neutral-800 pt-5 space-y-4">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-[11px] text-neutral-500 dark:text-neutral-400">
          <span className="font-bold uppercase tracking-wide text-neutral-600 dark:text-neutral-300">{c.stripTitle}</span>
          <span className="inline-flex items-center gap-1.5"><StatusDot status="live" /> {c.live}</span>
          <span className="inline-flex items-center gap-1.5"><StatusDot status="planned" /> {c.planned}</span>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-10 gap-y-6">
          <FinePrint icon={ShieldCheck} title={c.privacyTitle} lead={c.privacyLead} items={c.privacyItems} c={c} />
          <FinePrint icon={Database} title={c.ehrTitle} lead={c.ehrLead} items={c.ehrItems} c={c} />
        </div>
      </div>
    </section>
  );
}

function Mark({ v, c }) {
  if (v === true) return <Check className="w-5 h-5 text-red-700 dark:text-red-400 inline" aria-label={c.yes} />;
  if (v === false) return <Minus className="w-5 h-5 text-neutral-300 dark:text-neutral-500 inline" aria-label={c.no} />;
  return <span className="text-xs text-neutral-500 dark:text-neutral-400">{c.varies}</span>;
}

function StatusDot({ status }) {
  return <span className={`inline-block w-2 h-2 rounded-full shrink-0 ${status === 'live' ? 'bg-red-600' : 'bg-white dark:bg-neutral-900 ring-1 ring-neutral-400 dark:ring-neutral-600'}`} aria-hidden="true" />;
}

function FinePrint({ icon: Icon, title, lead, items, c }) {
  return (
    <section aria-label={title}>
      <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100 flex items-center gap-2"><Icon className="w-4 h-4 text-red-700 dark:text-red-400" /> {title}</h3>
      <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">{lead}</p>
      <ul className="mt-3 space-y-3">
        {items.map((x) => (
          <li key={x.title} className="flex gap-3">
            <span className="mt-1.5 flex"><StatusDot status={x.status} /></span>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-neutral-800 dark:text-neutral-100">
                {x.title}
                <span className="sr-only"> ({x.status === 'live' ? c.live : c.planned})</span>
              </p>
              <p className="text-xs text-neutral-500 dark:text-neutral-400 leading-relaxed">{x.detail}</p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
