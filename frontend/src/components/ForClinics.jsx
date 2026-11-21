import { Check, Database, Lock, Minus, ShieldCheck, Sparkles } from 'lucide-react';

// Judge items #2 (comparison), #4 (EHR plan), #5 (privacy plan).
// The savings calculator and pricing are hidden for now; their logic still lives in backend/savings.py.
const COMPARISON = [
  ['Digital check-in forms', true, true],
  ['Red-flag safety screen before any AI', true, 'Varies'],
  ['AI priority agenda for the nurse / doctor', true, false],
  ['After-visit explainer approved by the doctor', true, false],
  ['Patient Q&A grounded only in the approved summary', true, false],
  ['Cost & generic-savings breakdown for the patient', true, false],
  ['English & Spanish, phone or clinic kiosk', true, 'Varies'],
];

export default function ForClinics() {
  return (
    <section className="space-y-6 animate-fade-up">
      <div className="card p-6 bg-gradient-to-br from-teal-700 to-teal-900 text-white border-0">
        <p className="eyebrow text-teal-200">Why CareBridge</p>
        <h1 className="text-2xl sm:text-3xl font-extrabold mt-1">Most tools stop at check-in. We help before, during, and after the visit.</h1>
        <p className="text-teal-100 mt-2 text-sm max-w-3xl">We start with independent family medicine clinics, then expand to other specialties.
          Front desk staff can always fill the check-in out with the patient.</p>
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
