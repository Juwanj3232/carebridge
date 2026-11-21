import { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertCircle, Clock, ListChecks, MessageCircle, Pill, Search, Send, ShieldCheck, Siren } from 'lucide-react';
import { ArcElement, Chart as ChartJS, Legend, Tooltip } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import { api, money } from '../lib/api.js';
import { t } from '../lib/i18n.js';

ChartJS.register(ArcElement, Tooltip, Legend);

export default function AfterVisit({ lang, visitId, showToast }) {
  const s = t(lang);
  const [generic, setGeneric] = useState(true);
  const [visit, setVisit] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    if (!visitId) return;
    try { setVisit(await api(`patient/visits/${visitId}?generic=${generic ? 1 : 0}`)); setError(null); } catch (e) { setError(e.message); }
  }, [visitId, generic]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {   // pick up the doctor's approval and care-team replies without a reload
    const id = window.setInterval(load, 5000);
    return () => window.clearInterval(id);
  }, [load]);

  if (!visitId) return <Empty text={s.noVisit} />;
  if (error) return <Empty text={error} />;
  if (!visit) return <Empty text="…" />;

  if (visit.safety.level === 'emergency' && !visit.summary) {
    return (
      <div role="alert" className="card p-6 border-2 border-rose-500 bg-rose-50 max-w-2xl mx-auto space-y-2">
        <h2 className="text-xl font-extrabold text-rose-900 flex items-center gap-2"><Siren className="w-6 h-6" /> {visit.safety.patient_message.title}</h2>
        <p className="text-rose-950">{visit.safety.patient_message.body}</p>
      </div>
    );
  }

  if (!visit.summary) {
    return (
      <div className="card p-8 max-w-2xl mx-auto text-center space-y-3 animate-fade-up">
        <Clock className="w-10 h-10 mx-auto text-teal-600" />
        <h2 className="text-lg font-bold">{s.waitingTitle}</h2>
        <p className="text-sm text-slate-600">{s.waitingBody}</p>
        <p className="text-xs text-slate-400">{visit.name}</p>
      </div>
    );
  }

  const sm = visit.summary;
  const b = visit.billing;
  return (
    <Approved s={s} visit={visit} sm={sm} b={b} generic={generic} setGeneric={setGeneric} load={load} showToast={showToast} />
  );
}

function Approved({ s, visit, sm, b, generic, setGeneric, load, showToast }) {
  // Same object between 5-second refreshes, so the chart doesn't re-animate every poll.
  const chartData = useMemo(() => b && ({
    labels: [s.insCovered, s.oop],
    datasets: [{ data: [b.total_covered, b.total_patient], backgroundColor: ['#0f766e', '#e11d48'], borderWidth: 0 }],
  }), [b?.total_covered, b?.total_patient, s.insCovered, s.oop]); // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-up">
      <div className="lg:col-span-2 space-y-6">
        <div className="card p-5 sm:p-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-lg font-bold">{s.afterTitle}</h2>
              <p className="text-xs text-slate-500">{visit.name} · {b?.plan}</p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 inline-flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> {s.approvedBy} {visit.approved_by}
            </span>
          </div>

          <div className="bg-teal-50/70 border border-teal-200 rounded-xl p-4">
            <span className="eyebrow text-teal-800">{s.whatYouHave}</span>
            <h3 className="text-base font-bold mt-1">{sm.diagnosis_title}</h3>
            <p className="text-sm text-slate-700 mt-1 leading-relaxed">{sm.what_you_have.text}</p>
          </div>

          {sm.what_we_found?.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <h4 className="eyebrow text-slate-600 mb-2 flex items-center gap-1.5"><Search className="w-4 h-4 text-teal-700" /> {s.whatWeFound}</h4>
              <ul className="text-sm text-slate-700 space-y-1.5 list-disc list-inside">{sm.what_we_found.map((i, k) => <li key={k}>{i.text}</li>)}</ul>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-slate-50 rounded-xl border border-slate-200 p-4">
              <h4 className="eyebrow text-slate-600 mb-2 flex items-center gap-1.5"><ListChecks className="w-4 h-4 text-teal-700" /> {s.nextSteps}</h4>
              <ul className="text-sm text-slate-700 space-y-1.5 list-disc list-inside">{sm.next_steps.map((i, k) => <li key={k}>{i.text}</li>)}</ul>
            </div>
            <div className="bg-rose-50/60 rounded-xl border border-rose-200 p-4">
              <h4 className="eyebrow text-rose-800 mb-2 flex items-center gap-1.5"><AlertCircle className="w-4 h-4 text-rose-600" /> {s.whenToCall}</h4>
              <ul className="text-sm text-rose-950 space-y-1.5 list-disc list-inside">{sm.warning_signs.map((i, k) => <li key={k}>{i.text}</li>)}</ul>
            </div>
          </div>
          <p className="text-sm font-semibold text-slate-800 border-t border-slate-100 pt-3">{sm.footer}</p>
        </div>

        {b && (
          <div className="card p-5 sm:p-6">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
              <h3 className="text-base font-bold flex items-center gap-2"><Pill className="w-4 h-4 text-teal-700" /> {s.pharmacy}</h3>
              {b.has_brand_option && (
                <button type="button" onClick={() => setGeneric(!generic)} aria-pressed={generic}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${generic ? 'bg-emerald-100 hover:bg-emerald-200 text-emerald-900' : 'bg-amber-100 hover:bg-amber-200 text-amber-900'}`}>
                  {generic ? s.genericOn : s.genericOff}
                </button>
              )}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs sm:text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 text-xs uppercase">
                    <th className="py-2 pr-2 font-semibold">{s.item}</th>
                    <th className="py-2 px-2 font-semibold text-right">{s.billed}</th>
                    <th className="py-2 px-2 font-semibold text-right">{s.covered}</th>
                    <th className="py-2 pl-2 font-semibold text-right">{s.youPay}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {b.items.map((i) => (
                    <tr key={i.kind}>
                      <td className="py-2.5 pr-2 font-medium text-slate-800">{i.label}</td>
                      <td className="py-2.5 px-2 text-right text-slate-500">{money(i.billed)}</td>
                      <td className="py-2.5 px-2 text-right text-teal-700 font-medium">-{money(i.covered)}</td>
                      <td className="py-2.5 pl-2 text-right font-bold">{money(i.patient)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-[11px] text-slate-500 mt-3">{b.disclaimer}</p>
          </div>
        )}
      </div>

      <div className="space-y-6">
        {b && (
          <div className="card p-5">
            <h3 className="text-base font-bold">{s.moneyTitle}</h3>
            <p className="text-xs text-slate-500 mt-0.5 mb-4">{b.plan}</p>
            <div className="relative h-56">
              <Doughnut
                data={chartData}
                options={{ responsive: true, maintainAspectRatio: false, cutout: '66%', plugins: { legend: { position: 'bottom' } } }}
              />
            </div>
            <div className="mt-4 pt-4 border-t border-slate-100 space-y-2 text-sm">
              <div className="flex justify-between text-slate-600"><span>{s.totalBilled}</span><span className="font-semibold">{money(b.total_billed)}</span></div>
              <div className="flex justify-between text-teal-700"><span>{s.insCovered}</span><span className="font-bold">-{money(b.total_covered)}</span></div>
              <div className="flex justify-between text-base font-extrabold pt-2 border-t border-slate-200"><span>{s.oop}</span><span className="text-rose-600">{money(b.total_patient)}</span></div>
            </div>
          </div>
        )}
        {b && (
          <div className="bg-amber-50 rounded-2xl border border-amber-200 p-4 space-y-1">
            <h4 className="eyebrow text-amber-900">{s.costTip}</h4>
            <p className="text-xs text-amber-950 leading-relaxed">{b.tip}</p>
          </div>
        )}
        <AskBox s={s} visit={visit} reload={load} showToast={showToast} />
      </div>
    </section>
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
        <h3 className="text-base font-bold flex items-center gap-2"><MessageCircle className="w-4 h-4 text-teal-700" /> {s.askTitle}</h3>
        <p className="text-xs text-slate-500 mt-0.5">{s.askSub}</p>
      </div>
      <div className="space-y-3 max-h-80 overflow-y-auto">
        {visit.questions.map((x) => (
          <div key={x.id} className="space-y-1.5">
            <p className="text-sm bg-slate-900 text-white rounded-xl rounded-br-sm px-3 py-2 ml-6">{x.question}</p>
            <p className={`text-sm rounded-xl rounded-bl-sm px-3 py-2 mr-6 ${x.kind === 'emergency' ? 'bg-rose-100 text-rose-950 font-semibold' : x.escalated ? 'bg-amber-50 border border-amber-200 text-amber-950' : 'bg-teal-50 border border-teal-200 text-slate-800'}`}>{x.answer}</p>
            {x.reply && (
              <p className="text-sm rounded-xl px-3 py-2 mr-6 bg-white border border-slate-200"><strong>{s.careTeamReply} ({x.reply.by}):</strong> {x.reply.text}</p>
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
  return <div className="card p-8 text-center text-slate-500 text-sm max-w-2xl mx-auto">{text}</div>;
}
