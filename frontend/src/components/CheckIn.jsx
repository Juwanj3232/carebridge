import { useEffect, useState } from 'react';
import { AlertTriangle, ArrowRight, ClipboardEdit, Languages, Phone, RotateCcw, Siren, Sparkles, UserRound } from 'lucide-react';
import { api } from '../lib/api.js';
import { DURATIONS, LANGUAGES, t } from '../lib/i18n.js';

const EMPTY = { name: '', insurance: 'ppo', symptoms: '', duration: '4-7 days', severity: 5, meds: '', allergies: '', reading_level: 'simple',
  needs_interpreter: false, interpreter_language: '', callback_phone: '' };

function severityTone(n) {
  if (n >= 8) return 'bg-rose-100 dark:bg-rose-950/70 text-rose-800 dark:text-rose-200';
  if (n >= 5) return 'bg-amber-100 dark:bg-amber-950/70 text-amber-800 dark:text-amber-200';
  return 'bg-emerald-100 dark:bg-emerald-950/70 text-emerald-800 dark:text-emerald-200';
}

export default function CheckIn({ lang, setLang, plans, preset, kiosk, showToast, onCheckedIn, goClinic }) {
  const s = t(lang);
  const [form, setForm] = useState(EMPTY);
  const [scenario, setScenario] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (preset) {
      setForm({ ...EMPTY, ...preset.intake, reading_level: form.reading_level });
      setScenario(preset.scenario);
      setResult(null);
      setError(null);
    }
  }, [preset]); // eslint-disable-line react-hooks/exhaustive-deps

  const set = (k) => (e) => setForm({ ...form, [k]: k === 'severity' ? Number(e.target.value) : e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const r = await api('intake', {
        method: 'POST',
        body: { ...form, language: lang, channel: kiosk ? 'kiosk' : 'phone', scenario,
          interpreter_language: form.needs_interpreter ? form.interpreter_language : '',
          callback_phone: kiosk ? '' : form.callback_phone },
      });
      setResult(r);
      onCheckedIn(r.visit_id);
      showToast(r.safety.level === 'emergency' ? 'Red-flag alert sent to clinic staff' : 'Checked in. Clinic brief is ready for staff.');
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const startOver = () => { setForm(EMPTY); setScenario(null); setResult(null); window.scrollTo({ top: 0 }); };

  return (
    <section className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fade-up">
      <form onSubmit={submit} className="card p-5 sm:p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-neutral-100 dark:border-neutral-800 pb-3">
          <div>
            <h1 className="text-lg font-bold">{s.checkinTitle}</h1>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">{s.checkinSub}</p>
          </div>
          <ClipboardEdit className="w-5 h-5 text-red-600 dark:text-red-400 shrink-0" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label htmlFor="name" className="label">{s.name}</label>
            <input id="name" className="field" value={form.name} onChange={set('name')} placeholder="Test Patient …" autoComplete="off" />
          </div>
          <div>
            <label htmlFor="insurance" className="label">{s.insurance}</label>
            <select id="insurance" className="field" value={form.insurance} onChange={set('insurance')}>
              {plans.map((p) => <option key={p.id} value={p.id}>{p.label} ({p.short})</option>)}
            </select>
          </div>
        </div>

        <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50/70 dark:bg-neutral-900/60 p-3 space-y-2">
          <label htmlFor="pref-lang" className="label flex items-center gap-1.5"><Languages className="w-3.5 h-3.5 text-red-700 dark:text-red-400" /> {s.prefLang}</label>
          <select id="pref-lang" className="field" value={form.needs_interpreter ? 'other' : lang}
            onChange={(e) => {
              if (e.target.value === 'other') setForm({ ...form, needs_interpreter: true });
              else { setForm({ ...form, needs_interpreter: false, interpreter_language: '' }); setLang(e.target.value); }
            }}>
            {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
            <option value="other">{s.prefLangOther}</option>
          </select>
          {form.needs_interpreter && (
            <div>
              <label htmlFor="interpreter" className="label">{s.prefLangWhich}</label>
              <input id="interpreter" className="field" maxLength={40} required value={form.interpreter_language}
                onChange={set('interpreter_language')} placeholder={s.prefLangWhichPh} />
            </div>
          )}
          <p className="text-[11px] text-neutral-500 dark:text-neutral-400">{form.needs_interpreter ? s.prefLangOtherHelp : s.prefLangHelp}</p>
        </div>

        <div>
          <label htmlFor="symptoms" className="label">{s.symptoms}</label>
          <textarea id="symptoms" rows={4} required className="field leading-relaxed" value={form.symptoms} onChange={set('symptoms')} placeholder={s.symptomsPh} />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="duration" className="label">{s.duration}</label>
            <select id="duration" className="field" value={form.duration} onChange={set('duration')}>
              {DURATIONS.map((d) => <option key={d} value={d}>{s.durations[d]}</option>)}
            </select>
          </div>
          <div>
            <div className="flex items-center justify-between mb-1">
              <label htmlFor="severity" className="text-xs font-semibold text-neutral-600 dark:text-neutral-300">{s.severity}</label>
              <span className={`text-xs font-bold px-2 py-0.5 rounded-md ${severityTone(form.severity)}`}>{form.severity} / 10</span>
            </div>
            <input id="severity" type="range" min="1" max="10" value={form.severity} onChange={set('severity')} className="w-full accent-red-700 cursor-pointer mt-1.5" />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label htmlFor="meds" className="label">{s.meds}</label>
            <input id="meds" className="field" value={form.meds} onChange={set('meds')} placeholder={s.medsPh} />
          </div>
          <div>
            <label htmlFor="allergies" className="label">{s.allergies}</label>
            <input id="allergies" className="field" value={form.allergies} onChange={set('allergies')} placeholder={s.allergiesPh} />
          </div>
          <div>
            <label htmlFor="reading" className="label">{s.reading}</label>
            <select id="reading" className="field" value={form.reading_level} onChange={set('reading_level')}>
              <option value="simple">{s.simple}</option>
              <option value="standard">{s.standard}</option>
            </select>
          </div>
        </div>

        {!kiosk && (
          <div>
            <label htmlFor="callback" className="label">{s.callback}</label>
            <input id="callback" type="tel" autoComplete="tel" maxLength={25} className="field" value={form.callback_phone}
              onChange={set('callback_phone')} placeholder={s.callbackPh} aria-describedby="callback-help" />
            <p id="callback-help" className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-1">{s.callbackHelp}</p>
          </div>
        )}

        {error && <p className="text-sm text-rose-700 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 rounded-xl px-3 py-2">{error}</p>}

        <button type="submit" disabled={busy || !form.symptoms.trim()} className="btn-primary w-full">
          <Sparkles className="w-4 h-4" /> {busy ? s.submitting : s.submit}
        </button>
        <p className="text-xs text-neutral-500 dark:text-neutral-400 flex items-center gap-1.5"><UserRound className="w-3.5 h-3.5" /> {s.frontDeskHelp}</p>
      </form>

      <ResultPanel s={s} result={result} kiosk={kiosk} goClinic={goClinic} startOver={startOver} />
    </section>
  );
}

function ResultPanel({ s, result, kiosk, goClinic, startOver }) {
  if (!result) {
    return (
      <div className="card p-6 flex flex-col items-center justify-center text-center text-neutral-500 dark:text-neutral-400 min-h-[18rem]">
        <ClipboardEdit className="w-8 h-8 text-neutral-300 dark:text-neutral-500 mb-3" />
        <p className="text-sm max-w-sm">{s.prepEmpty}</p>
      </div>
    );
  }
  const level = result.safety.level;
  const msg = result.safety.patient_message;
  const prep = result.patient_prep;

  return (
    <div className="card p-5 sm:p-6 flex flex-col justify-between gap-4 animate-fade-up">
      <div className="space-y-4">
        {level === 'emergency' && (
          <div role="alert" className="rounded-2xl border-2 border-rose-500 bg-rose-50 dark:bg-rose-950/40 p-5 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-full bg-rose-600 text-white flex items-center justify-center animate-pulse"><Siren className="w-6 h-6" /></div>
              <h2 className="text-xl font-extrabold text-rose-900 dark:text-rose-200">{msg.title}</h2>
            </div>
            <p className="text-base text-rose-950 dark:text-rose-200 leading-relaxed">{msg.body}</p>
            {msg.crisis && <p className="text-base font-semibold text-rose-950 dark:text-rose-200">{msg.crisis}</p>}
            <a href="tel:911" className="btn-danger w-full !text-base"><Phone className="w-5 h-5" /> Call 911</a>
            <p className="text-xs text-rose-800 dark:text-rose-200">Clinic staff have already been alerted on their dashboard.</p>
          </div>
        )}

        {level === 'urgent_review' && (
          <div role="alert" className="rounded-2xl border-2 border-amber-400 bg-amber-50 dark:bg-amber-950/40 p-4 space-y-1.5">
            <h2 className="text-base font-bold text-amber-900 dark:text-amber-200 flex items-center gap-2"><AlertTriangle className="w-5 h-5" /> {msg.title}</h2>
            <p className="text-sm text-amber-950 dark:text-amber-200 leading-relaxed">{msg.body}</p>
            {msg.phone && (
              <a href={`tel:${msg.phone.replace(/[^\d+]/g, '')}`} className="btn-dark w-full !mt-3"><Phone className="w-4 h-4" /> {s.callClinic} {msg.phone}</a>
            )}
          </div>
        )}

        {prep && (
          <>
            <div className="flex items-center justify-between border-b border-neutral-100 dark:border-neutral-800 pb-3">
              <div>
                <h2 className="text-lg font-bold">{s.prepTitle}</h2>
                <p className="text-xs text-neutral-500 dark:text-neutral-400">{s.prepSub}</p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-100 dark:bg-emerald-950/70 text-emerald-800 dark:text-emerald-200">Organized</span>
            </div>
            <div className="bg-red-50/70 dark:bg-red-950/40 border border-red-200 dark:border-red-900 rounded-xl p-4 space-y-2">
              <h3 className="eyebrow text-red-800 dark:text-red-200">{s.plainSummary}</h3>
              <p className="text-sm text-neutral-800 dark:text-neutral-100 leading-relaxed">{prep.summary}</p>
            </div>
            <div>
              <h3 className="eyebrow text-neutral-500 dark:text-neutral-400 mb-2">{s.keyDetails}</h3>
              <ul className="space-y-2 text-sm text-neutral-700 dark:text-neutral-200">
                {prep.key_points.map((k) => (
                  <li key={k.label} className="flex items-start gap-2"><span className="text-red-700 dark:text-red-400 font-bold">•</span><span><strong>{k.label}:</strong> {k.value}</span></li>
                ))}
              </ul>
            </div>
            <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 rounded-xl p-4">
              <h3 className="eyebrow text-amber-800 dark:text-amber-200 mb-1.5">{s.questions}</h3>
              <ul className="space-y-1 text-sm text-amber-950 dark:text-amber-200 list-disc list-inside">
                {prep.questions.map((q) => <li key={q}>{q}</li>)}
              </ul>
            </div>
          </>
        )}
      </div>

      {kiosk ? (
        <button type="button" onClick={startOver} className="btn-dark w-full !text-base"><RotateCcw className="w-4 h-4" /> {s.startOver}</button>
      ) : (
        <button type="button" onClick={goClinic} className="btn-dark w-full">
          Open the Clinic Dashboard (Step 2, staff view) <ArrowRight className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
