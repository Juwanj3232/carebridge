import { useCallback, useEffect, useState } from 'react';
import {
  ArrowRight, CheckCircle, FileOutput, Lock, LogOut, MessageSquareText, MessageSquareWarning, Quote, RefreshCw,
  Send, ShieldAlert, Siren, Sparkles, Stethoscope,
} from 'lucide-react';
import { api, money, timeAgo } from '../lib/api.js';
import ExportModal from './ExportModal.jsx';

const LEVEL = {
  emergency: { label: 'RED FLAG', cls: 'bg-rose-600 text-white', row: 'border-rose-400 bg-rose-50' },
  urgent_review: { label: 'Nurse check', cls: 'bg-amber-400 text-amber-950', row: 'border-amber-300 bg-amber-50' },
  routine: { label: 'Routine', cls: 'bg-emerald-100 text-emerald-800', row: 'border-slate-200 bg-white' },
};
const PRIORITY = {
  urgent: 'bg-rose-600 text-white', high: 'bg-amber-100 text-amber-900', normal: 'bg-sky-100 text-sky-900', routine: 'bg-slate-100 text-slate-600',
};

export default function ClinicDashboard({ staff, signIn, signOut, activeVisitId, setActiveVisitId, scenarios, showToast, goAfter }) {
  const [queue, setQueue] = useState([]);
  const [inbox, setInbox] = useState({ alerts: [], questions: [], followups: [] });
  const [visit, setVisit] = useState(null);
  const [exportData, setExportData] = useState(null);
  const token = staff?.token;

  const call = useCallback(async (path, opts = {}) => {
    try {
      return await api(path, { ...opts, token });
    } catch (e) {
      if (e.status === 401) signOut();
      throw e;
    }
  }, [token, signOut]);

  const refresh = useCallback(async () => {
    if (!token) return;
    const [q, i] = await Promise.all([call('staff/queue'), call('staff/inbox')]);
    setQueue(q.queue);
    setInbox(i);
  }, [token, call]);

  useEffect(() => {
    if (!token) return undefined;
    refresh().catch(() => {});
    const id = window.setInterval(() => refresh().catch(() => {}), 5000);
    return () => window.clearInterval(id);
  }, [token, refresh]);

  // Keep a visit selected: the one the patient just checked in, else the top of the queue.
  useEffect(() => {
    if (!queue.length) return;
    if (!activeVisitId || !queue.some((v) => v.id === activeVisitId)) setActiveVisitId(queue[0].id);
  }, [queue, activeVisitId, setActiveVisitId]);

  const loadVisit = useCallback(async () => {
    if (!token || !activeVisitId) return;
    try { setVisit(await call(`staff/visits/${activeVisitId}`)); } catch { setVisit(null); }
  }, [token, activeVisitId, call]);

  useEffect(() => { loadVisit(); }, [loadVisit]);

  if (!staff) return <LoginCard signIn={signIn} />;

  const resolve = async (q, reply) => {
    await call(`staff/visits/${q.visit_id}/questions/${q.id}/resolve`, { method: 'POST', body: { reply } });
    showToast('Reply sent to patient');
    refresh();
  };
  const resolveFollowup = async (f, reply) => {
    await call(`staff/visits/${f.visit_id}/followups/${f.id}/resolve`, { method: 'POST', body: { reply } });
    showToast('Reply texted to patient');
    refresh();
  };
  const openExport = async () => setExportData(await call(`staff/visits/${visit.id}/export`));
  const resetDemo = async () => {
    await call('staff/reset-demo', { method: 'POST', body: {} });
    setActiveVisitId(null);
    showToast('Demo queue reset');
    refresh();
  };

  return (
    <section className="space-y-6 animate-fade-up">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm text-slate-600">
          <Lock className="w-4 h-4 text-teal-700" /> Signed in as <strong className="text-slate-900">{staff.user.name}</strong>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100">{staff.user.role.replace('_', ' ')}</span>
        </div>
        <div className="flex gap-2">
          <button type="button" className="btn-ghost !py-1.5 !text-xs" onClick={resetDemo}><RefreshCw className="w-3.5 h-3.5" /> Reset demo queue</button>
          <button type="button" className="btn-ghost !py-1.5 !text-xs" onClick={signOut}><LogOut className="w-3.5 h-3.5" /> Sign out</button>
        </div>
      </div>

      <Inbox inbox={inbox} resolve={resolve} resolveFollowup={resolveFollowup} select={setActiveVisitId} />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        <aside className="xl:col-span-3 card p-4 space-y-2 h-fit">
          <h2 className="eyebrow text-slate-500 mb-1">Today's check-ins ({queue.length})</h2>
          {queue.map((v) => (
            <button key={v.id} type="button" onClick={() => setActiveVisitId(v.id)}
              className={`w-full text-left rounded-xl border p-3 transition ${LEVEL[v.level].row} ${v.id === activeVisitId ? 'ring-2 ring-teal-600' : 'hover:border-slate-400'}`}>
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-bold truncate">{v.name}</span>
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${LEVEL[v.level].cls}`}>{LEVEL[v.level].label}</span>
              </div>
              <p className="text-xs text-slate-600 truncate mt-0.5">{v.chief_complaint}</p>
              <p className="text-[11px] text-slate-500 mt-1 flex flex-wrap gap-x-2">
                <span>{timeAgo(v.created_at)}</span><span>{v.channel}</span>{v.language === 'es' && <span>Español</span>}
                <span>{v.status.replaceAll('_', ' ')}</span>
                {v.open_questions > 0 && <span className="text-amber-700 font-semibold">{v.open_questions} question(s)</span>}
                {v.open_followups > 0 && <span className="text-amber-700 font-semibold">{v.open_followups} follow-up reply(s)</span>}
              </p>
            </button>
          ))}
        </aside>

        <div className="xl:col-span-9">
          {visit ? (
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
              <Brief visit={visit} openExport={openExport} />
              <WrapUp key={visit.id} visit={visit} staff={staff} call={call} scenarios={scenarios}
                onChange={(v) => { setVisit(v); refresh(); }} showToast={showToast} goAfter={goAfter} />
            </div>
          ) : (
            <div className="card p-8 text-center text-slate-500 text-sm">Select a patient from the queue.</div>
          )}
        </div>
      </div>

      {exportData && <ExportModal data={exportData} onClose={() => setExportData(null)} showToast={showToast} />}
    </section>
  );
}

function LoginCard({ signIn }) {
  const [username, setUsername] = useState('dr.demo');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try { signIn(await api('login', { method: 'POST', body: { username, password } })); } catch (err) { setError(err.message); } finally { setBusy(false); }
  };
  return (
    <section className="max-w-md mx-auto card p-6 space-y-4 animate-fade-up">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-teal-700 text-white flex items-center justify-center"><Lock className="w-5 h-5" /></div>
        <div>
          <h1 className="text-lg font-bold">Clinic staff sign-in</h1>
          <p className="text-xs text-slate-500">The dashboard shows patient information, so staff must sign in.</p>
        </div>
      </div>
      <form onSubmit={submit} className="space-y-3">
        <div>
          <label htmlFor="user" className="label">Username</label>
          <select id="user" className="field" value={username} onChange={(e) => setUsername(e.target.value)}>
            <option value="dr.demo">dr.demo (doctor: can approve summaries)</option>
            <option value="nurse.demo">nurse.demo (nurse)</option>
            <option value="frontdesk.demo">frontdesk.demo (front desk)</option>
          </select>
        </div>
        <div>
          <label htmlFor="pw" className="label">Password</label>
          <input id="pw" type="password" className="field" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
        </div>
        {error && <p className="text-sm text-rose-700">{error}</p>}
        <button type="submit" className="btn-primary w-full" disabled={busy || !password}>Sign in</button>
      </form>
      <p className="text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded-xl p-3">
        Demo password: <code className="font-semibold">carebridge-demo</code> (printed when the server starts). A real deployment uses the clinic's
        own sign-in with multi-factor authentication.
      </p>
    </section>
  );
}

const FOLLOWUP_TONE = {
  red: { card: 'border-2 border-rose-500 bg-rose-50', label: 'text-rose-900', tag: 'RED FLAG', tagCls: 'bg-rose-600 text-white' },
  amber: { card: 'border border-amber-300 bg-amber-50', label: 'text-amber-900', tag: 'Needs a call', tagCls: 'bg-amber-400 text-amber-950' },
  request: { card: 'border border-sky-200 bg-sky-50', label: 'text-sky-900', tag: 'Request', tagCls: 'bg-sky-100 text-sky-900' },
};

// Shows only what staff must act on after the visit: follow-up texts the agent flagged and escalated patient
// questions. Check-in safety alerts stay visible as badges in the queue and brief. Hidden when empty.
function Inbox({ inbox, resolve, resolveFollowup, select }) {
  const [replies, setReplies] = useState({});
  const followups = inbox.followups || [];
  if (!inbox.questions.length && !followups.length) return null;
  const replyBox = (id, onSend, label) => (
    <div className="flex gap-2 mt-2">
      <input className="field !py-1.5" placeholder={label} value={replies[id] || ''}
        onChange={(e) => setReplies({ ...replies, [id]: e.target.value })} />
      <button type="button" className="btn-primary !py-1.5 !px-3 !text-xs" disabled={!replies[id]?.trim()}
        onClick={() => { onSend(replies[id]); setReplies({ ...replies, [id]: '' }); }}><Send className="w-3.5 h-3.5" /> Reply</button>
    </div>
  );
  return (
    <div className="space-y-2">
      {followups.map((f) => {
        const tone = FOLLOWUP_TONE[f.level] || FOLLOWUP_TONE.amber;
        return (
          <div key={f.id} role={f.level === 'red' ? 'alert' : undefined} className={`rounded-2xl p-4 ${tone.card}`}>
            <div className="flex flex-wrap items-center gap-2">
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${tone.tagCls}`}>{tone.tag}</span>
              <p className={`text-xs font-bold flex items-center gap-1.5 ${tone.label}`}>
                <MessageSquareText className="w-4 h-4" /> Follow-up text, day {f.day} · {f.name} · {timeAgo(f.created_at)}
              </p>
              <button type="button" className="ml-auto text-xs font-semibold text-teal-800 hover:underline" onClick={() => select(f.visit_id)}>Open brief</button>
            </div>
            <p className="text-sm text-slate-900 mt-1">"{f.message}"</p>
            <p className="text-xs text-slate-600 mt-0.5">{f.reason}</p>
            {replyBox(f.id, (r) => resolveFollowup(f, r), 'Text a reply to the patient')}
          </div>
        );
      })}
      {inbox.questions.map((q) => (
        <div key={q.id} className="card p-4 border-amber-200">
          <p className="text-xs font-bold text-amber-800 flex items-center gap-1.5">
            <MessageSquareWarning className="w-4 h-4" /> Patient question for the care team · {q.name} · {timeAgo(q.created_at)}
          </p>
          <p className="text-sm text-slate-900 mt-1">"{q.question}"</p>
          <p className="text-xs text-slate-500 mt-0.5">Not covered by the approved summary, so the assistant did not answer it.</p>
          {replyBox(q.id, (r) => resolve(q, r), 'Type a reply to the patient')}
        </div>
      ))}
    </div>
  );
}

function Brief({ visit, openExport }) {
  const b = visit.brief;
  const lvl = LEVEL[visit.safety.level];
  return (
    <div className="lg:col-span-3 card p-5 sm:p-6 space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold">Provider pre-visit brief</h2>
            <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${lvl.cls}`}>{lvl.label}</span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {visit.intake.name} · {visit.intake.insurance.toUpperCase()} · checked in {timeAgo(visit.created_at)} via {visit.intake.channel}
            {visit.intake.language === 'es' && ' · prefers Spanish'}
          </p>
        </div>
        <button type="button" onClick={openExport} className="btn-ghost !py-1.5 !text-xs"><FileOutput className="w-4 h-4" /> Export to EHR</button>
      </div>

      {visit.safety.level !== 'routine' && (
        <div className={`rounded-xl border-2 p-3 text-sm flex items-start gap-2 ${visit.safety.level === 'emergency' ? 'border-rose-500 bg-rose-50 text-rose-950' : 'border-amber-400 bg-amber-50 text-amber-950'}`}>
          <ShieldAlert className="w-5 h-5 shrink-0" />
          <div>
            <p className="font-bold">Safety screen (plain-code rules, ran before any AI)</p>
            <p>{visit.safety.staff_message}</p>
            {!visit.safety.ai_allowed && <p className="text-xs mt-1">AI was not used for this check-in.</p>}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {[['Chief complaint', b.chief_complaint], ['Onset & severity', b.onset], ['Meds / allergies', `${b.meds} · Allergies: ${b.allergies}`]].map(([k, v]) => (
          <div key={k} className="bg-slate-50 rounded-xl border border-slate-200 p-3.5">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{k}</span>
            <p className="text-sm font-bold text-slate-900 mt-1">{v}</p>
          </div>
        ))}
      </div>

      <div>
        <h3 className="eyebrow text-slate-500 mb-2 flex items-center gap-2">
          AI priority agenda
          <span className="normal-case tracking-normal font-medium text-[11px] px-1.5 py-0.5 rounded bg-slate-100">{b.agenda_source === 'claude' ? 'Claude, grounded in patient words' : 'rules'}</span>
        </h3>
        <ol className="space-y-2">
          {b.agenda.map((a, i) => (
            <li key={i} className="flex items-start gap-3 rounded-xl border border-slate-200 p-3">
              <span className="w-6 h-6 rounded-full bg-slate-900 text-white text-xs font-bold flex items-center justify-center shrink-0">{i + 1}</span>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${PRIORITY[a.priority]}`}>{a.priority}</span>
                  <span className="text-sm font-semibold text-slate-900">{a.item}</span>
                </div>
                <p className="text-xs text-slate-500 mt-1 flex items-start gap-1"><Quote className="w-3 h-3 mt-0.5 shrink-0" /> {a.source}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>

      <div>
        <h3 className="eyebrow text-slate-500 mb-2">Structured intake (from the patient's words)</h3>
        <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 text-sm text-slate-800 space-y-2">
          <p><strong>HPI:</strong> {b.hpi}</p>
          <p className="text-xs text-slate-600"><strong>Tags:</strong> {b.tags.join(' • ')}</p>
        </div>
      </div>

      <div className="bg-teal-50 border border-teal-200 rounded-xl p-4">
        <h3 className="eyebrow text-teal-800 mb-1.5">Rooming checks</h3>
        <ul className="text-sm text-teal-950 space-y-1 list-disc list-inside">{b.checks.map((c) => <li key={c}>{c}</li>)}</ul>
      </div>
    </div>
  );
}

const SECTIONS = [['what_we_found', 'What we found'], ['next_steps', 'Next steps at home'], ['warning_signs', 'When to call the clinic']];

function WrapUp({ visit, staff, call, scenarios, onChange, showToast, goAfter }) {
  const scenarioOutcome = scenarios.find((s) => s.id === visit.scenario)?.outcome;
  const [form, setForm] = useState(() => visit.outcome || scenarioOutcome || {
    diagnosis: '', rx_generic: '', rx_brand: '', notes: '', visit_fee: 130, test_name: '', test_fee: 0, rx_generic_price: 0, rx_brand_price: 0,
  });
  const [draft, setDraft] = useState(visit.summary_draft);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const isDoctor = staff.user.role === 'doctor';

  useEffect(() => { setDraft(visit.summary_draft); }, [visit.summary_draft]);

  if (visit.safety.level === 'emergency' && !visit.outcome) {
    return (
      <div className="lg:col-span-2 card p-5 space-y-3 border-rose-300">
        <h2 className="text-base font-bold text-rose-900 flex items-center gap-2"><Siren className="w-5 h-5" /> Emergency path</h2>
        <p className="text-sm text-slate-700">The patient was told to tell the front desk right away or call 911. Follow the clinic's emergency protocol.
          No AI summary is generated for red-flag check-ins.</p>
      </div>
    );
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const generate = async () => {
    setBusy(true); setError(null);
    try {
      const v = await call(`staff/visits/${visit.id}/outcome`, { method: 'POST', body: form });
      onChange(v); setDraft(v.summary_draft);
      showToast('Draft ready. Review it, then approve and send.');
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const approve = async () => {
    setBusy(true); setError(null);
    try {
      const v = await call(`staff/visits/${visit.id}/approve`, { method: 'POST', body: { summary: draft } });
      onChange(v);
      showToast('Approved and sent to the patient');
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const editItem = (key, i, text) => setDraft({ ...draft, [key]: draft[key].map((x, j) => (j === i ? { ...x, text } : x)) });

  return (
    <div className="lg:col-span-2 card p-5 sm:p-6 space-y-4 h-fit">
      <div className="border-b border-slate-100 pb-3">
        <h2 className="text-base font-bold flex items-center gap-2"><Stethoscope className="w-4 h-4 text-teal-700" /> Complete visit</h2>
        <p className="text-xs text-slate-500 mt-0.5">The patient summary is written only from these notes. It reaches the patient after a doctor approves it.</p>
      </div>

      <div>
        <label htmlFor="dx" className="label">Diagnosis</label>
        <input id="dx" className="field font-medium" value={form.diagnosis} onChange={set('diagnosis')} />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label htmlFor="rxg" className="label">Prescription (generic)</label>
          <input id="rxg" className="field" value={form.rx_generic} onChange={set('rx_generic')} />
        </div>
        <div>
          <label htmlFor="rxb" className="label">Brand alternative</label>
          <input id="rxb" className="field" value={form.rx_brand} onChange={set('rx_brand')} />
        </div>
      </div>
      <div>
        <label htmlFor="notes" className="label">Visit notes (shorthand is fine)</label>
        <textarea id="notes" rows={4} className="field !text-xs leading-relaxed font-mono" value={form.notes} onChange={set('notes')} />
      </div>
      <details className="text-xs">
        <summary className="cursor-pointer font-semibold text-slate-600">Billing details (demo prices)</summary>
        <div className="grid grid-cols-2 gap-2 mt-2">
          {[['visit_fee', 'Visit fee'], ['test_name', 'Test name'], ['test_fee', 'Test fee'], ['rx_generic_price', 'Generic price'], ['rx_brand_price', 'Brand price']].map(([k, l]) => (
            <div key={k} className={k === 'test_name' ? 'col-span-2' : ''}>
              <label htmlFor={k} className="label">{l}</label>
              <input id={k} className="field !py-1.5" value={form[k] ?? ''} onChange={set(k)} inputMode={k === 'test_name' ? 'text' : 'decimal'} />
            </div>
          ))}
        </div>
      </details>

      <button type="button" className="btn-primary w-full" onClick={generate} disabled={busy || !form.diagnosis || !form.notes}>
        <Sparkles className="w-4 h-4" /> {draft ? 'Redraft patient summary' : 'Draft patient summary'}
      </button>

      {draft && (
        <div className="space-y-3 border-t border-slate-100 pt-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold">Review before sending</h3>
            <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${visit.summary_approved ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>
              {visit.summary_approved ? `Sent · ${visit.approved_by}` : 'Draft · patient cannot see this'}
            </span>
          </div>
          <p className="text-[11px] text-slate-500">Written by {draft.generated_by === 'claude' ? 'Claude' : 'the shorthand rules'}. Each line shows the note text it came from.</p>
          {draft.note_for_clinician && <p className="text-xs bg-amber-50 border border-amber-200 rounded-lg p-2 text-amber-900">{draft.note_for_clinician}</p>}
          <div className="rounded-xl bg-teal-50/70 border border-teal-200 p-3">
            <p className="text-sm font-bold">{draft.diagnosis_title}</p>
            <p className="text-xs text-slate-700 mt-1">{draft.what_you_have.text}</p>
          </div>
          {SECTIONS.map(([key, label]) => draft[key]?.length > 0 && (
            <div key={key}>
              <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">{label}</p>
              {draft[key].map((item, i) => (
                <div key={i} className="mb-2">
                  <textarea rows={2} className="field !text-xs !py-1.5" value={item.text} onChange={(e) => editItem(key, i, e.target.value)} disabled={!isDoctor} />
                  <p className="text-[11px] text-slate-500 mt-0.5 flex items-start gap-1"><Quote className="w-3 h-3 mt-0.5 shrink-0" /> {item.source}</p>
                </div>
              ))}
            </div>
          ))}
          {draft.dropped_ungrounded?.length > 0 && (
            <div className="text-xs bg-slate-50 border border-slate-200 rounded-lg p-2">
              <p className="font-semibold text-slate-700">Removed automatically: AI lines not found in your notes</p>
              <ul className="list-disc list-inside text-slate-500">{draft.dropped_ungrounded.map((d, i) => <li key={i}>{d.text}</li>)}</ul>
            </div>
          )}
          <p className="text-xs text-slate-600 italic">{draft.footer}</p>
          {error && <p className="text-sm text-rose-700">{error}</p>}
          {isDoctor ? (
            <button type="button" className="btn-dark w-full" onClick={approve} disabled={busy}>
              <CheckCircle className="w-4 h-4" /> {visit.summary_approved ? 'Re-approve and send update' : 'Approve and send to patient'}
            </button>
          ) : (
            <p className="text-xs text-slate-500 bg-slate-50 rounded-lg p-2">Only a doctor can approve. Sign in as dr.demo to send it.</p>
          )}
          {visit.summary_approved && (
            <button type="button" className="btn-ghost w-full" onClick={goAfter}>View as the patient (Step 3) <ArrowRight className="w-4 h-4" /></button>
          )}
          {visit.billing && (
            <p className="text-xs text-slate-500">Patient's estimated cost: <strong>{money(visit.billing.total_patient)}</strong> of {money(visit.billing.total_billed)} billed.</p>
          )}
        </div>
      )}
      {!draft && error && <p className="text-sm text-rose-700">{error}</p>}
    </div>
  );
}
