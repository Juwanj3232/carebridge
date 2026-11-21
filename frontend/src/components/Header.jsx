import { ChevronDown, HeartPulse, Languages, Lock, MonitorSmartphone, Moon, Sun, Type } from 'lucide-react';
import { LANGUAGES, t } from '../lib/i18n.js';

const TABS = [
  { id: 'checkin', n: 1, key: 'tabCheckin' },
  { id: 'clinic', n: 2, key: 'tabClinic', staff: true },
  { id: 'after', n: 3, key: 'tabAfter' },
  { id: 'clinics', n: null, key: 'tabClinics', staff: true },
];

export default function Header({ tab, go, lang, setLang, largeText, setLargeText, kiosk, setKiosk, staff, theme, setTheme }) {
  const s = t(lang);
  return (
    <header className="bg-white dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-800 sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-red-700 text-white flex items-center justify-center shadow-sm">
            <HeartPulse className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight">CareBridge</span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-red-100 dark:bg-red-950/70 text-red-800 dark:text-red-200">{s.badge}</span>
            </div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 hidden sm:block">{s.clinicName}</p>
          </div>
        </div>

        <nav aria-label="Visit steps" className="inline-flex flex-wrap rounded-xl bg-neutral-100 dark:bg-neutral-800 p-1 border border-neutral-200 dark:border-neutral-800">
          {TABS.filter((x) => !(kiosk && x.staff)).map((x) => {
            const active = tab === x.id;
            return (
              <button key={x.id} type="button" onClick={() => go(x.id)} aria-current={active ? 'page' : undefined}
                className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition flex items-center gap-1.5 ${
                  active ? 'bg-red-700 text-white' : 'text-neutral-600 dark:text-neutral-300 hover:bg-white dark:hover:bg-neutral-800 hover:text-neutral-900 dark:hover:text-neutral-100'}`}>
                {x.n && (
                  <span className={`w-5 h-5 rounded-full text-[11px] flex items-center justify-center font-bold ${active ? 'bg-white/20' : 'bg-neutral-200 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-200'}`}>{x.n}</span>
                )}
                <span>{s[x.key]}</span>
                {x.id === 'clinic' && !staff && <Lock className="w-3.5 h-3.5 opacity-70" aria-label="sign-in required" />}
              </button>
            );
          })}
        </nav>

        <div className="flex items-center gap-1.5">
          <label className="btn-ghost !px-2.5 !py-1.5 !text-xs relative cursor-pointer focus-within:ring-2 focus-within:ring-red-600"
            title={s.langMenu}>
            <Languages className="w-4 h-4 shrink-0" aria-hidden="true" />
            <select value={lang} onChange={(e) => setLang(e.target.value)} aria-label={s.langMenu}
              className="appearance-none bg-transparent pr-4 font-semibold cursor-pointer focus:outline-none">
              {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
            </select>
            <ChevronDown className="w-3.5 h-3.5 absolute right-2 pointer-events-none" aria-hidden="true" />
          </label>
          <button type="button" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} aria-pressed={theme === 'dark'}
            className="btn-ghost !px-2.5 !py-1.5 !text-xs" title={theme === 'dark' ? s.lightMode : s.darkMode}
            aria-label={theme === 'dark' ? s.lightMode : s.darkMode}>
            {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
          <button type="button" onClick={() => setLargeText(!largeText)} aria-pressed={largeText || kiosk}
            className={`btn-ghost !px-3 !py-1.5 !text-xs ${largeText || kiosk ? '!bg-red-50 dark:bg-red-950/40 !border-red-300 dark:border-red-900 !text-red-900 dark:text-red-200' : ''}`}>
            <Type className="w-4 h-4" /> {s.largeText}
          </button>
          <button type="button" onClick={() => setKiosk(!kiosk)} aria-pressed={kiosk}
            className={`btn-ghost !px-3 !py-1.5 !text-xs ${kiosk ? '!bg-red-50 dark:bg-red-950/40 !border-red-300 dark:border-red-900 !text-red-900 dark:text-red-200' : ''}`}
            title={s.kioskTitle}>
            <MonitorSmartphone className="w-4 h-4" /> {s.kiosk}
          </button>
        </div>
      </div>
    </header>
  );
}
