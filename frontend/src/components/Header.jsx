import { ChevronDown, HeartPulse, Languages, Lock, MonitorSmartphone, Type } from 'lucide-react';
import { LANGUAGES, t } from '../lib/i18n.js';

const TABS = [
  { id: 'checkin', n: 1, key: 'tabCheckin' },
  { id: 'clinic', n: 2, key: 'tabClinic', staff: true },
  { id: 'after', n: 3, key: 'tabAfter' },
  { id: 'clinics', n: null, key: 'tabClinics', staff: true },
];

export default function Header({ tab, go, lang, setLang, largeText, setLargeText, kiosk, setKiosk, staff }) {
  const s = t(lang);
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-teal-700 text-white flex items-center justify-center shadow-sm">
            <HeartPulse className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight">CareBridge</span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-teal-100 text-teal-800">{s.badge}</span>
            </div>
            <p className="text-xs text-slate-500 hidden sm:block">{s.clinicName}</p>
          </div>
        </div>

        <nav aria-label="Visit steps" className="inline-flex flex-wrap rounded-xl bg-slate-100 p-1 border border-slate-200">
          {TABS.filter((x) => !(kiosk && x.staff)).map((x) => {
            const active = tab === x.id;
            return (
              <button key={x.id} type="button" onClick={() => go(x.id)} aria-current={active ? 'page' : undefined}
                className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition flex items-center gap-1.5 ${
                  active ? 'bg-teal-700 text-white' : 'text-slate-600 hover:bg-white hover:text-slate-900'}`}>
                {x.n && (
                  <span className={`w-5 h-5 rounded-full text-[11px] flex items-center justify-center font-bold ${active ? 'bg-white/20' : 'bg-slate-200 text-slate-700'}`}>{x.n}</span>
                )}
                <span>{s[x.key]}</span>
                {x.id === 'clinic' && !staff && <Lock className="w-3.5 h-3.5 opacity-70" aria-label="sign-in required" />}
              </button>
            );
          })}
        </nav>

        <div className="flex items-center gap-1.5">
          <label className="btn-ghost !px-2.5 !py-1.5 !text-xs relative cursor-pointer focus-within:ring-2 focus-within:ring-teal-600"
            title={s.langMenu}>
            <Languages className="w-4 h-4 shrink-0" aria-hidden="true" />
            <select value={lang} onChange={(e) => setLang(e.target.value)} aria-label={s.langMenu}
              className="appearance-none bg-transparent pr-4 font-semibold cursor-pointer focus:outline-none">
              {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
            </select>
            <ChevronDown className="w-3.5 h-3.5 absolute right-2 pointer-events-none" aria-hidden="true" />
          </label>
          <button type="button" onClick={() => setLargeText(!largeText)} aria-pressed={largeText || kiosk}
            className={`btn-ghost !px-3 !py-1.5 !text-xs ${largeText || kiosk ? '!bg-teal-50 !border-teal-300 !text-teal-900' : ''}`}>
            <Type className="w-4 h-4" /> {s.largeText}
          </button>
          <button type="button" onClick={() => setKiosk(!kiosk)} aria-pressed={kiosk}
            className={`btn-ghost !px-3 !py-1.5 !text-xs ${kiosk ? '!bg-teal-50 !border-teal-300 !text-teal-900' : ''}`}
            title={s.kioskTitle}>
            <MonitorSmartphone className="w-4 h-4" /> {s.kiosk}
          </button>
        </div>
      </div>
    </header>
  );
}
