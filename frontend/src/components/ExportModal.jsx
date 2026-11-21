import { useEffect, useState } from 'react';
import { Copy, Download, X } from 'lucide-react';

export default function ExportModal({ data, onClose, showToast }) {
  const [view, setView] = useState('text');
  const content = view === 'text' ? data.text : JSON.stringify(data.fhir, null, 2);

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const copy = async () => {
    try { await navigator.clipboard.writeText(content); showToast('Copied'); } catch { showToast('Copy blocked by the browser; select the text instead'); }
  };
  const download = () => {
    const blob = new Blob([content], { type: view === 'text' ? 'text/plain' : 'application/fhir+json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = view === 'text' ? 'carebridge-visit-note.txt' : 'carebridge-fhir-bundle.json';
    a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <div className="fixed inset-0 z-40 bg-neutral-900/50 dark:bg-neutral-700 flex items-center justify-center p-4" onClick={onClose}>
      <div role="dialog" aria-modal="true" aria-label="Export to EHR" className="card w-full max-w-3xl max-h-[90vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-neutral-100 dark:border-neutral-800">
          <div>
            <h2 className="text-base font-bold">Export to EHR</h2>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">{data.note}</p>
          </div>
          <button type="button" onClick={onClose} className="btn-ghost !p-2" aria-label="Close"><X className="w-4 h-4" /></button>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-2 px-4 pt-3">
          <div className="inline-flex rounded-lg bg-neutral-100 dark:bg-neutral-800 p-1">
            {[['text', 'Clinical note (paste into any EHR)'], ['fhir', 'FHIR R4 bundle (JSON)']].map(([k, l]) => (
              <button key={k} type="button" onClick={() => setView(k)}
                className={`px-3 py-1 rounded-md text-xs font-semibold ${view === k ? 'bg-white dark:bg-neutral-900 shadow-sm' : 'text-neutral-600 dark:text-neutral-300'}`}>{l}</button>
            ))}
          </div>
          <div className="flex gap-2">
            <button type="button" onClick={copy} className="btn-ghost !py-1.5 !text-xs"><Copy className="w-3.5 h-3.5" /> Copy</button>
            <button type="button" onClick={download} className="btn-primary !py-1.5 !text-xs"><Download className="w-3.5 h-3.5" /> Download</button>
          </div>
        </div>
        <pre className="m-4 p-4 rounded-xl bg-neutral-950 text-neutral-100 text-xs leading-relaxed overflow-auto whitespace-pre-wrap flex-1">{content}</pre>
      </div>
    </div>
  );
}
