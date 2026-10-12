import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, ArrowRight, ShieldCheck } from 'lucide-react';

const alerts = [
  { id: 'ALR-4412', actor: 'Bank account cluster', score: 96, status: 'Escalated', detail: 'High-value outflow pattern with repeated recipient transfers in 14 minutes.' },
  { id: 'ALR-4421', actor: 'Dormant customer reactivation', score: 84, status: 'Reviewing', detail: 'Existing account showed unusual balance rebounds after 21-day inactivity window.' },
  { id: 'ALR-4428', actor: 'Cross-border sweep anomaly', score: 73, status: 'Monitoring', detail: 'Transfer velocity exceeded expected threshold but not linked to known fraud schema.' },
];

export function AlertsPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Fraud alerts</p>
        <h2 className="mt-2 text-3xl font-semibold text-white">Managed risk queue</h2>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {alerts.map((alert) => (
          <Card key={alert.id} className="border border-slate-800">
            <CardHeader>
              <div>
                <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{alert.id}</div>
                <CardTitle className="mt-2">{alert.actor}</CardTitle>
              </div>
              <div className="rounded-full bg-red-500/10 px-2 py-1 text-xs font-medium text-red-300">{alert.status}</div>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Risk score</span>
                <span className="text-lg font-semibold text-white">{alert.score}</span>
              </div>
              <p className="mt-3 text-sm text-slate-300">{alert.detail}</p>
              <div className="mt-4 flex items-center justify-between border-t border-slate-800 pt-3 text-sm">
                <span className="inline-flex items-center gap-2 text-emerald-300">
                  <ShieldCheck size={14} />
                  Investigated
                </span>
                <button className="inline-flex items-center gap-1 text-brand-300 hover:text-brand-200">
                  Review <ArrowRight size={14} />
                </button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Escalation summary</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          {[
            ['Open alerts', '12'],
            ['Resolved today', '27'],
            ['Network-linked cases', '4'],
          ].map(([label, value]) => (
            <div key={label} className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
              <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{label}</div>
              <div className="mt-3 text-3xl font-semibold text-white">{value}</div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
