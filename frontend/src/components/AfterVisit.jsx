import { useCallback, useEffect, useRef, useState } from 'react';
import { AlertCircle, Clock, FastForward, ListChecks, MessageCircle, MessageSquareText, Pill, Search, Send, ShieldCheck, Siren } from 'lucide-react';
import { api, money } from '../lib/api.js';
import { t } from '../lib/i18n.js';

// Shows the patient's own approved summary. Until their clinician approves one, it shows the seeded
// sample summary (a synthetic test patient) so this page always has a summary to review.
export default function AfterVisit({ lang, visitId, showToast }) {
  const s = t(lang);
  const [generic, setGeneric] = useState(true);
  const [own, setOwn] = useState(null);
  const [sample, setSample] = useState(null);
  const [loaded, setLoaded] = useState(false);

  const load = useCallback(async () => {
    const qs = `?generic=${generic ? 1 : 0}`;
    let mine = null;
    if (visitId) {
      try { mine = await api(`patient/visits/${visitId}${qs}`); } catch { mine = null; }
    }
    setOwn(mine);
    if (!mine?.summary && mine?.safety.level !== 'emergency') {
      try {
        const { visit_id: id } = await api('sample-visit');
        setSample(id ? await api(`patient/visits/${id}${qs}`) : null);
      } catch { setSample(null); }
    }
    setLoaded(true);
  }, [visitId, generic]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {   // pick up the doctor's approval and care-team replies without a reload
    const id = window.setInterval(load, 5000);
    return () => window.clearInterval(id);
  }, [load]);

  if (own && own.safety.level === 'emergency' && !own.summary) {
    return (
      <div role="alert" className="card p-6 border-2 border-rose-500 bg-rose-50 dark:bg-rose-950/40 max-w-2xl mx-auto space-y-2">
        <h2 className="text-xl font-extrabold text-rose-900 dark:text-rose-200 flex items-center gap-2"><Siren className="w-6 h-6" /> {own.safety.patient_message.title}</h2>
        <p className="text-rose-950 dark:text-rose-200">{own.safety.patient_message.body}</p>
      </div>
    );
  }

  const shown = own?.summary ? own : sample;
  if (!shown) {
    if (!loaded) return <Empty text="…" />;
    if (!own) return <Empty text={s.noVisit} />;
    return (
      <div className="card p-8 max-w-2xl mx-auto text-center space-y-3 animate-fade-up">
        <Clock className="w-10 h-10 mx-auto text-red-600 dark:text-red-400" />
        <h2 className="text-lg font-bold">{s.waitingTitle}</h2>
        <p className="text-sm text-neutral-600 dark:text-neutral-300">{s.waitingBody}</p>
        <p className="text-xs text-neutral-400 dark:text-neutral-500">{own.name}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {shown !== own && (
        <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-900/60 px-4 py-3 text-sm text-neutral-950 dark:text-neutral-100 flex items-start gap-2.5">
          <Clock className="w-4 h-4 mt-0.5 text-neutral-700 dark:text-neutral-200 shrink-0" />
          <p>{own && <strong>{s.waitingTitle}. </strong>}{s.sampleNote}</p>
        </div>
      )}
      <Approved s={s} visit={shown} sm={shown.summary} b={shown.billing} generic={generic} setGeneric={setGeneric} load={load} showToast={showToast} />
    </div>
  );
}

function Approved({ s, visit, sm, b, generic, setGeneric, load, showToast }) {
  return (
    <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-up">
      <div className="lg:col-span-2 space-y-6">
        <div className="card p-5 sm:p-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-neutral-100 dark:border-neutral-800 pb-3">
            <div>
              <h2 className="text-lg font-bold">{s.afterTitle}</h2>
              <p className="text-xs text-neutral-500 dark:text-neutral-400">{visit.name} · {b?.plan}</p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-100 dark:bg-emerald-950/70 text-emerald-800 dark:text-emerald-200 inline-flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> {s.approvedBy} {visit.approved_by}
            </span>
          </div>

          {/* The most important part of the page: what the patient does next. */}
          <div className="rounded-2xl border-2 border-red-600 bg-red-50 dark:bg-red-950/40 p-5">
            <h3 className="text-lg sm:text-xl font-extrabold text-red-900 dark:text-red-200 flex items-center gap-2">
              <ListChecks className="w-6 h-6 text-red-700 dark:text-red-400" /> {s.nextSteps}
            </h3>
            <ol className="mt-3 space-y-3">
              {sm.next_steps.map((i, k) => (
                <li key={k} className="flex items-start gap-3">
                  <span className="shrink-0 w-7 h-7 rounded-full bg-red-700 text-white text-sm font-bold flex items-center justify-center">{k + 1}</span>
                  <span className="text-base text-neutral-900 dark:text-neutral-100 leading-relaxed pt-0.5">{i.text}</span>
                </li>
              ))}
            </ol>
          </div>

          <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl p-4">
            <span className="eyebrow text-red-800 dark:text-red-200">{s.whatYouHave}</span>
            <h3 className="text-base font-bold mt-1">{sm.diagnosis_title}</h3>
            <p className="text-sm text-neutral-700 dark:text-neutral-200 mt-1 leading-relaxed">{sm.what_you_have.text}</p>
          </div>

          <div className={`grid grid-cols-1 gap-4 ${sm.what_we_found?.length ? 'sm:grid-cols-2' : ''}`}>
            {sm.what_we_found?.length > 0 && (
              <div className="bg-neutral-50 dark:bg-neutral-900/60 rounded-xl border border-neutral-200 dark:border-neutral-800 p-4">
                <h4 className="eyebrow text-neutral-600 dark:text-neutral-300 mb-2 flex items-center gap-1.5"><Search className="w-4 h-4 text-red-700 dark:text-red-400" /> {s.whatWeFound}</h4>
                <ul className="text-sm text-neutral-700 dark:text-neutral-200 space-y-1.5 list-disc list-inside">{sm.what_we_found.map((i, k) => <li key={k}>{i.text}</li>)}</ul>
              </div>
            )}
            <div className="bg-rose-50/60 dark:bg-rose-950/40 rounded-xl border border-rose-200 dark:border-rose-900 p-4">
              <h4 className="eyebrow text-rose-800 dark:text-rose-200 mb-2 flex items-center gap-1.5"><AlertCircle className="w-4 h-4 text-rose-600 dark:text-rose-400" /> {s.whenToCall}</h4>
              <ul className="text-sm text-rose-950 dark:text-rose-200 space-y-1.5 list-disc list-inside">{sm.warning_signs.map((i, k) => <li key={k}>{i.text}</li>)}</ul>
            </div>
          </div>
          <p className="text-sm font-semibold text-neutral-800 dark:text-neutral-100 border-t border-neutral-100 dark:border-neutral-800 pt-3">{sm.footer}</p>
        </div>

        {b && (
          <div className="card p-5 sm:p-6">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
              <div>
                <h3 className="text-base font-bold flex items-center gap-2"><Pill className="w-4 h-4 text-red-700 dark:text-red-400" /> {s.pharmacy}</h3>
                <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">{b.plan}</p>
              </div>
              {b.has_brand_option && (
                <button type="button" onClick={() => setGeneric(!generic)} aria-pressed={generic}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${generic ? 'bg-emerald-100 dark:bg-emerald-950/70 hover:bg-emerald-200 dark:hover:bg-emerald-900/60 text-emerald-900 dark:text-emerald-200' : 'bg-amber-100 dark:bg-amber-950/70 hover:bg-amber-200 dark:hover:bg-amber-900/60 text-amber-900 dark:text-amber-200'}`}>
                  {generic ? s.genericOn : s.genericOff}
                </button>
              )}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs sm:text-sm">
                <thead>
                  <tr className="border-b border-neutral-200 dark:border-neutral-800 text-neutral-500 dark:text-neutral-400 text-xs uppercase">
                    <th className="py-2 pr-2 font-semibold">{s.item}</th>
                    <th className="py-2 px-2 font-semibold text-right">{s.billed}</th>
                    <th className="py-2 px-2 font-semibold text-right">{s.covered}</th>
                    <th className="py-2 pl-2 font-semibold text-right">{s.youPay}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800">
                  {b.items.map((i) => (
                    <tr key={i.kind}>
                      <td className="py-2.5 pr-2 font-medium text-neutral-800 dark:text-neutral-100">{i.label}</td>
                      <td className="py-2.5 px-2 text-right text-neutral-500 dark:text-neutral-400">{money(i.billed)}</td>
                      <td className="py-2.5 px-2 text-right text-red-700 dark:text-red-400 font-medium">-{money(i.covered)}</td>
                      <td className="py-2.5 pl-2 text-right font-bold">{money(i.patient)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-900/60 p-4 space-y-2 text-sm">
              <div className="flex justify-between text-neutral-600 dark:text-neutral-300"><span>{s.totalBilled}</span><span className="font-semibold">{money(b.total_billed)}</span></div>
              <div className="flex justify-between text-red-700 dark:text-red-400"><span>{s.insCovered}</span><span className="font-bold">-{money(b.total_covered)}</span></div>
              <div className="flex justify-between text-base font-extrabold pt-2 border-t border-neutral-200 dark:border-neutral-800"><span>{s.oop}</span><span className="text-rose-600 dark:text-rose-400">{money(b.total_patient)}</span></div>
            </div>
            <p className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-3">{b.disclaimer}</p>
          </div>
        )}
      </div>

      <div className="space-y-6">
        {visit.followup && <FollowUp s={s} visit={visit} reload={load} showToast={showToast} />}
        {b && (
          <div className="bg-amber-50 dark:bg-amber-950/40 rounded-2xl border border-amber-200 dark:border-amber-900 p-4 space-y-1">
            <h4 className="eyebrow text-amber-900 dark:text-amber-200">{s.costTip}</h4>
            <p className="text-xs text-amber-950 dark:text-amber-200 leading-relaxed">{b.tip}</p>
          </div>
        )}
        <AskBox s={s} visit={visit} reload={load} showToast={showToast} />
      </div>
    </section>
  );
}

// The follow-up agent's text thread: day-0 "summary is ready", day-3 check-in, the patient's replies,
// and care-team answers. The server safety-screens every reply and decides what goes to staff.
function FollowUp({ s, visit, reload, showToast }) {
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const f = visit.followup;
  const threadRef = useRef(null);   // keep the newest text in view without scrolling the whole page
  useEffect(() => { if (threadRef.current) threadRef.current.scrollTop = threadRef.current.scrollHeight; }, [f.messages.length]);

  const post = async (path, body) => {
    setBusy(true);
    try { await api(`patient/visits/${visit.id}/${path}`, { method: 'POST', body }); await reload(); return true; }
    catch (err) { showToast(err.message); return false; }
    finally { setBusy(false); }
  };
  const send = async (e) => {
    e.preventDefault();
    if (await post('followup', { message: text })) setText('');
  };

  let lastDay = null;
  return (
    <div className="card p-5 space-y-3">
      <div>
        <h3 className="text-base font-bold flex items-center gap-2"><MessageSquareText className="w-4 h-4 text-red-700 dark:text-red-400" /> {s.fuTitle}</h3>
        <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">{s.fuSub}</p>
      </div>
      <div ref={threadRef} className="space-y-2 max-h-96 overflow-y-auto rounded-xl bg-neutral-50 dark:bg-neutral-900/60 border border-neutral-200 dark:border-neutral-800 p-3">
        {f.messages.map((m) => {
          const dayLabel = m.day !== lastDay ? <p className="text-center text-[11px] font-semibold text-neutral-400 dark:text-neutral-500 uppercase tracking-wide pt-1">{s.fuDay} {m.day}</p> : null;
          lastDay = m.day;
          const mine = m.from === 'patient';
          return (
            <div key={m.id} className="space-y-1">
              {dayLabel}
              <div className={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] text-sm px-3 py-2 rounded-2xl ${mine
                  ? 'bg-neutral-900 dark:bg-neutral-700 text-white rounded-br-sm'
                  : m.from === 'care_team' ? 'bg-white dark:bg-neutral-900 border border-red-300 dark:border-red-900 text-neutral-900 dark:text-neutral-100 rounded-bl-sm' : 'bg-red-600 text-white rounded-bl-sm'}`}>
                  {m.from === 'care_team' && <p className="text-[11px] font-bold text-red-800 dark:text-red-200 mb-0.5">{s.fuCareTeam} · {m.by}</p>}
                  {m.text}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      {!f.checkin_sent_at && (
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-neutral-600 dark:text-neutral-300">
          <span className="flex items-center gap-1.5"><Clock className="w-3.5 h-3.5 text-red-700 dark:text-red-400" />
            {s.fuScheduled} {new Date(f.due_at).toLocaleDateString(visit.language || 'en', { weekday: 'short', month: 'short', day: 'numeric' })}</span>
          <button type="button" className="btn-ghost !py-1 !px-2.5 !text-xs" disabled={busy} onClick={() => post('followup/send-now', {})}>
            <FastForward className="w-3.5 h-3.5" /> {s.fuSendNow}
          </button>
        </div>
      )}
      <form onSubmit={send} className="flex gap-2">
        <input className="field" value={text} onChange={(e) => setText(e.target.value)} placeholder={s.fuPh} aria-label={s.fuPh} />
        <button type="submit" className="btn-primary !px-3" disabled={busy || !text.trim()} aria-label={s.fuSend}><Send className="w-4 h-4" /></button>
      </form>
    </div>
  );
}

function AskBox({ s, visit, reload, showToast }) {
  const [q, setQ] = useState('');
  const [busy, setBusy] = useState(false);
  const ask = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const r = await api(`patient/visits/${visit.id}/ask`, { method: 'POST', body: { question: q } });
      if (r.escalated) showToast(s.sentToTeam);
      setQ('');
      reload();
    } catch (err) {
      showToast(err.message);
    } finally { setBusy(false); }
  };
  return (
    <div className="card p-5 space-y-3">
      <div>
        <h3 className="text-base font-bold flex items-center gap-2"><MessageCircle className="w-4 h-4 text-red-700 dark:text-red-400" /> {s.askTitle}</h3>
        <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">{s.askSub}</p>
      </div>
      <div className="space-y-3 max-h-80 overflow-y-auto">
        {visit.questions.map((x) => (
          <div key={x.id} className="space-y-1.5">
            <p className="text-sm bg-neutral-900 dark:bg-neutral-700 text-white rounded-xl rounded-br-sm px-3 py-2 ml-6">{x.question}</p>
            <p className={`text-sm rounded-xl rounded-bl-sm px-3 py-2 mr-6 ${x.kind === 'emergency' ? 'bg-rose-100 dark:bg-rose-950/70 text-rose-950 dark:text-rose-200 font-semibold' : x.escalated ? 'bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-950 dark:text-amber-200' : 'bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-neutral-800 dark:text-neutral-100'}`}>{x.answer}</p>
            {x.reply && (
              <p className="text-sm rounded-xl px-3 py-2 mr-6 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800"><strong>{s.careTeamReply} ({x.reply.by}):</strong> {x.reply.text}</p>
            )}
          </div>
        ))}
      </div>
      <form onSubmit={ask} className="flex gap-2">
        <input className="field" value={q} onChange={(e) => setQ(e.target.value)} placeholder={s.askPh} aria-label={s.askTitle} />
        <button type="submit" className="btn-primary !px-3" disabled={busy || !q.trim()} aria-label={s.ask}><Send className="w-4 h-4" /></button>
      </form>
    </div>
  );
}

function Empty({ text }) {
  return <div className="card p-8 text-center text-neutral-500 dark:text-neutral-400 text-sm max-w-2xl mx-auto">{text}</div>;
}
