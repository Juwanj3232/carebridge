import { useCallback, useEffect, useState } from 'react';
import { CheckCircle2 } from 'lucide-react';
import Header from './components/Header.jsx';
import DemoBar from './components/DemoBar.jsx';
import CheckIn from './components/CheckIn.jsx';
import ClinicDashboard from './components/ClinicDashboard.jsx';
import AfterVisit from './components/AfterVisit.jsx';
import ForClinics from './components/ForClinics.jsx';
import { api, session } from './lib/api.js';
import { t } from './lib/i18n.js';
import DotPattern from './components/DotPattern.jsx';

// One app, four views, following the visit: check-in (patient) -> clinic dashboard (staff) -> after-visit (patient),
// plus "For Clinics" (comparison, EHR and privacy plans) for the pitch.
export default function App() {
  const [tab, setTab] = useState('checkin');
  const [lang, setLang] = useState('en');
  const [largeText, setLargeText] = useState(false);
  const [kiosk, setKiosk] = useState(false);
  const [theme, setTheme] = useState(() => (document.documentElement.classList.contains('dark') ? 'dark' : 'light'));
  const [scenarios, setScenarios] = useState([]);
  const [plans, setPlans] = useState([]);
  const [health, setHealth] = useState(null);
  const [apiError, setApiError] = useState(null);
  const [preset, setPreset] = useState(null);          // {intake, nonce} loaded into the check-in form
  const [activeVisitId, setActiveVisitId] = useState(null);
  const [patientVisitId, setPatientVisitId] = useState(null);   // the visit Step 3 shows: the patient's own, or one staff opened
  const [staff, setStaff] = useState(() => session.get('carebridge-staff'));
  const [toast, setToast] = useState(null);

  useEffect(() => {
    Promise.all([api('scenarios'), api('plans'), api('health')])
      .then(([s, p, h]) => { setScenarios(s.scenarios); setPlans(p.plans); setHealth(h); })
      .catch((e) => setApiError(e.message));
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    try { localStorage.setItem('carebridge-theme', theme); } catch { /* storage blocked: the theme still works for this visit */ }
  }, [theme]);

  useEffect(() => {
    document.documentElement.classList.toggle('text-large', largeText || kiosk);
    document.documentElement.lang = lang;
  }, [largeText, kiosk, lang]);

  useEffect(() => {
    if (kiosk && (tab === 'clinic' || tab === 'clinics')) setTab('checkin');
  }, [kiosk, tab]);

  const showToast = useCallback((msg) => {
    setToast(msg);
    window.clearTimeout(window.__cbToast);
    window.__cbToast = window.setTimeout(() => setToast(null), 2600);
  }, []);

  const go = (id) => { setTab(id); window.scrollTo({ top: 0 }); };

  const signIn = (s) => { setStaff(s); session.set('carebridge-staff', s); };
  const signOut = () => { setStaff(null); session.clear('carebridge-staff'); };

  const loadScenario = (s) => {
    setPreset({ intake: s.intake, scenario: s.id, nonce: Date.now() });
    go('checkin');
    const text = t(lang);
    showToast(text.loaded(text.scenarios[s.id] || s.label));
  };

  return (
    <div className="relative isolate min-h-screen flex flex-col">
      {/* Dot grid behind every screen. Fixed, so it stays put while the page scrolls. */}
      <div className="fixed inset-0 -z-10">
        <DotPattern width={20} height={20} cr={1} className="text-neutral-400/80 dark:text-neutral-700" />
      </div>
      <Header tab={tab} go={go} lang={lang} setLang={setLang} largeText={largeText} setLargeText={setLargeText}
        kiosk={kiosk} setKiosk={setKiosk} staff={staff} theme={theme} setTheme={setTheme} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {!kiosk && <DemoBar scenarios={scenarios} onLoad={loadScenario} health={health} lang={lang} />}

        {apiError && (
          <div className="card p-5 border-rose-200 dark:border-rose-900 bg-rose-50 dark:bg-rose-950/40 text-rose-900 dark:text-rose-200 text-sm">
            <strong>Cannot reach the CareBridge API.</strong> {apiError}. Start it from the repo root with
            <code className="mx-1 px-1.5 py-0.5 rounded bg-white dark:bg-neutral-900 border border-rose-200 dark:border-rose-900">python3 server.py</code>
          </div>
        )}

        {tab === 'checkin' && (
          <CheckIn lang={lang} setLang={setLang} plans={plans} preset={preset} kiosk={kiosk} showToast={showToast}
            onCheckedIn={(id) => { setActiveVisitId(id); setPatientVisitId(id); }} goClinic={() => go('clinic')} />
        )}
        {tab === 'clinic' && (
          <ClinicDashboard staff={staff} signIn={signIn} signOut={signOut} activeVisitId={activeVisitId}
            setActiveVisitId={setActiveVisitId} scenarios={scenarios} showToast={showToast} goAfter={() => { setPatientVisitId(activeVisitId); go('after'); }} />
        )}
        {tab === 'after' && <AfterVisit lang={lang} visitId={patientVisitId} showToast={showToast} />}
        {tab === 'clinics' && <ForClinics lang={lang} />}
      </main>

      <footer className="border-t border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 text-xs text-neutral-500 dark:text-neutral-400 flex flex-wrap gap-x-6 gap-y-1 justify-between">
          <span>{t(lang).footer}</span>
          <span>{t(lang).footer911}</span>
        </div>
      </footer>

      {toast && (
        <div role="status" className="fixed bottom-5 right-5 z-50 flex items-center gap-2.5 bg-neutral-900 dark:bg-neutral-700 text-white text-sm font-medium px-4 py-3 rounded-xl shadow-lg animate-fade-up">
          <CheckCircle2 className="w-4 h-4 text-red-400 shrink-0" />
          <span>{toast}</span>
        </div>
      )}
    </div>
  );
}
