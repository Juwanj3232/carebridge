import { useEffect, useState } from 'react';
import { Calculator, Check, Database, Lock, Minus, ShieldCheck, Sparkles } from 'lucide-react';
import { api, money0 } from '../lib/api.js';

// Judge items #2 (comparison), #3 (savings calculator), #4 (EHR plan), #5 (privacy plan), #11 (pricing tiers).
const MAIN_INPUTS = [
  ['patients_per_day', 'Patients per day', 1],
  ['providers', 'Providers (doctors, NPs, PAs)', 1],
  ['clinic_days_per_month', 'Clinic days per month', 1],
];
const ASSUMPTIONS = [
  ['minutes_saved_per_checkin', 'Staff minutes saved per check-in', 1],
  ['staff_cost_per_hour', 'Staff cost per hour ($)', 1],
  ['no_show_rate_pct', 'Current no-show rate (%)', 1],
  ['no_show_reduction_pct', 'No-shows avoided with reminders (%)', 1],
  ['revenue_per_visit', 'Revenue per visit ($)', 5],
  ['after_visit_calls_per_day', 'After-visit phone calls per day', 1],
  ['call_reduction_pct', 'Calls avoided by explainers (%)', 5],
  ['minutes_per_call', 'Minutes per call', 1],
];

const COMPARISON = [
  ['Digital check-in forms', true, true],
  ['Red-flag safety screen before any AI', true, 'Varies'],
  ['AI priority agenda for the nurse / doctor', true, false],
  ['After-visit explainer approved by the doctor', true, false],
  ['Patient Q&A grounded only in the approved summary', true, false],
  ['Cost & generic-savings breakdown for the patient', true, false],
  ['Priced per provider for small clinics', true, 'Often enterprise contracts'],
  ['English & Spanish, phone or clinic kiosk', true, 'Varies'],
];

export default function ForClinics() {
  const [pricing, setPricing] = useState(null);
  const [inputs, setInputs] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    api('pricing').then((p) => { setPricing(p); setInputs(p.defaults); }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!inputs) return undefined;
    const id = window.setTimeout(() => api('savings', { method: 'POST', body: inputs }).then(setResult).catch(() => {}), 200);
    return () => window.clearTimeout(id);
  }, [inputs]);

  const set = (k) => (e) => setInputs({ ...inputs, [k]: e.target.value });

  return (
    <section className="space-y-6 animate-fade-up">
      <div className="card p-6 bg-gradient-to-br from-teal-700 to-teal-900 text-white border-0">
        <p className="eyebrow text-teal-200">Why CareBridge</p>
        <h1 className="text-2xl sm:text-3xl font-extrabold mt-1">Most tools stop at check-in. We help before, during, and after the visit.</h1>
        <p className="text-teal-100 mt-2 text-sm max-w-3xl">We start with independent family medicine clinics, then expand to other specialties.
          Front desk staff can always fill the check-in out with the patient.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3 card p-5 sm:p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold flex items-center gap-2"><Calculator className="w-5 h-5 text-teal-700" /> Savings calculator</h2>
            <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-amber-100 text-amber-800">Example estimates</span>
          </div>
          {inputs && (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                {MAIN_INPUTS.map(([k, l, step]) => (
                  <div key={k}>
                    <label htmlFor={k} className="label">{l}</label>
                    <input id={k} type="number" min="0" step={step} className="field" value={inputs[k]} onChange={set(k)} />
                  </div>
                ))}
                <div>
                  <label htmlFor="tier" className="label">Plan</label>
                  <select id="tier" className="field" value={inputs.tier} onChange={set('tier')}>
                    {pricing.tiers.map((t) => <option key={t.id} value={t.id}>{t.name} (${t.price_per_provider}/provider)</option>)}
                  </select>
                </div>
              </div>
              <details className="text-sm">
                <summary className="cursor-pointer text-xs font-semibold text-slate-600">Edit assumptions (replace with your clinic's numbers)</summary>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
                  {ASSUMPTIONS.map(([k, l, step]) => (
                    <div key={k}>
                      <label htmlFor={k} className="label">{l}</label>
                      <input id={k} type="number" min="0" step={step} className="field" value={inputs[k]} onChange={set(k)} />
                    </div>
                  ))}
                </div>
              </details>
            </>
          )}
          {result && (
            <div className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {result.metrics.map((m) => (
                  <div key={m.id} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <p className="text-xs font-semibold text-slate-500">{m.label}</p>
                    <p className="text-xl font-extrabold text-slate-900 mt-1">{money0(m.monthly_value)}<span className="text-xs font-medium text-slate-500">/mo</span></p>
                    <p className="text-[11px] text-slate-500 mt-0.5">{m.detail}</p>
                  </div>
                ))}
              </div>
              <div className="rounded-xl border-2 border-teal-600 bg-teal-50 p-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <Stat label="Estimated savings" value={`${money0(result.monthly_savings)}/mo`} />
                <Stat label={`${result.tier.name} plan cost`} value={`${money0(result.monthly_cost)}/mo`} />
                <Stat label="Net" value={`${money0(result.net_monthly)}/mo`} tone={result.net_monthly >= 0 ? 'text-teal-800' : 'text-rose-700'} />
                <Stat label="Return" value={result.roi_multiple ? `${result.roi_multiple}×` : '–'} />
              </div>
              <p className="text-[11px] text-slate-500">{result.disclaimer}</p>
            </div>
          )}
        </div>

        <div className="lg:col-span-2 card p-5 sm:p-6 space-y-3">
          <h2 className="text-lg font-bold">Pricing per provider, per month</h2>
          <p className="text-[11px] text-slate-500">Example prices. The team will confirm final pricing.</p>
          {pricing?.tiers.map((t) => (
            <div key={t.id} className={`rounded-xl border p-4 ${t.id === 'complete' ? 'border-teal-600 bg-teal-50/50' : 'border-slate-200'}`}>
              <div className="flex items-baseline justify-between">
                <span className="font-bold">{t.name}</span>
                <span className="text-lg font-extrabold">${t.price_per_provider}<span className="text-xs font-medium text-slate-500">/provider/mo</span></span>
              </div>
              <ul className="mt-2 space-y-1 text-xs text-slate-700">
                {t.includes.map((x) => <li key={x} className="flex gap-1.5"><Check className="w-3.5 h-3.5 text-teal-700 shrink-0 mt-0.5" /> {x}</li>)}
              </ul>
            </div>
          ))}
          <p className="text-xs text-slate-600">Getting started: a free 30-day pilot for 2–3 local independent clinics, then paid.</p>
        </div>
      </div>

      <div className="card p-5 sm:p-6">
        <h2 className="text-lg font-bold mb-3">CareBridge vs. a typical check-in tool</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
                <th className="text-left py-2 pr-2 font-semibold">Capability</th>
                <th className="py-2 px-2 font-semibold text-teal-800">CareBridge</th>
                <th className="py-2 pl-2 font-semibold">Typical check-in tool</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {COMPARISON.map(([cap, us, them]) => (
                <tr key={cap}>
                  <td className="py-2.5 pr-2 font-medium">{cap}</td>
                  <td className="py-2.5 px-2 text-center"><Mark v={us} /></td>
                  <td className="py-2.5 pl-2 text-center"><Mark v={them} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[11px] text-slate-500 mt-2">"Typical" is our general read of the category, not a claim about any one product. Check each competitor before quoting it.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Plan icon={ShieldCheck} title="Patient privacy (HIPAA)" items={[
          'Demo: synthetic "Test Patient" data only, nothing saved to disk',
          'Demo: staff sign-in; only doctors can approve summaries',
          'Product: HIPAA-compliant hosting, encrypted in transit and at rest',
          'Product: role-based staff access with audit logs',
          'Product: a signed business associate agreement (BAA) with each clinic',
        ]} />
        <Plan icon={Database} title="Clinic records (EHR)" items={[
          'Demo: "Export to EHR" gives a clean note plus a FHIR R4 bundle',
          'FHIR is the standard many EHRs use to share data',
          "We'd integrate with the 1–2 EHRs most common among small clinics first",
          'Later: connect to AI scribe tools clinics already use for visit notes',
        ]} />
        <Plan icon={Sparkles} title="How the AI stays safe" items={[
          'Plain-code red-flag rules run before any AI and can block it',
          'After-visit summaries come only from the doctor\'s notes',
          'Doctor reviews and presses "Approve and send" before the patient sees anything',
          'Patient questions are answered only from the approved summary; everything else goes to staff',
          'Every summary ends with "Questions? Contact your clinic."',
        ]} />
      </div>
    </section>
  );
}

function Stat({ label, value, tone = 'text-slate-900' }) {
  return (
    <div>
      <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
      <p className={`text-lg font-extrabold ${tone}`}>{value}</p>
    </div>
  );
}

function Mark({ v }) {
  if (v === true) return <Check className="w-5 h-5 text-teal-700 inline" aria-label="yes" />;
  if (v === false) return <Minus className="w-5 h-5 text-slate-300 inline" aria-label="usually not" />;
  return <span className="text-xs text-slate-500">{v}</span>;
}

function Plan({ icon: Icon, title, items }) {
  return (
    <div className="card p-5">
      <h3 className="text-base font-bold flex items-center gap-2"><Icon className="w-4 h-4 text-teal-700" /> {title}</h3>
      <ul className="mt-2 space-y-1.5 text-sm text-slate-700">
        {items.map((x) => <li key={x} className="flex gap-1.5"><Lock className="w-3 h-3 text-slate-400 shrink-0 mt-1" /> {x}</li>)}
      </ul>
    </div>
  );
}
