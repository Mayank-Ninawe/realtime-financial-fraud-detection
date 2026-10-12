import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import evaluationResults from '../../../reports/evaluation_results.json';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const realtime = evaluationResults.realtime_safe;
const metrics = [
  { name: 'Precision', value: Number(realtime.test_precision ?? 0.4553) },
  { name: 'Recall', value: Number(realtime.test_recall ?? 1.0) },
  { name: 'Average Precision', value: Number(realtime.test_average_precision ?? 0.9926) },
  { name: 'Threshold', value: Number(realtime.threshold ?? 0.00009248) },
  { name: 'TPR', value: Number((realtime.true_positives / (realtime.true_positives + realtime.false_negatives || 1)).toFixed(4)) },
];

export function PerformancePage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Model performance</p>
        <h2 className="mt-2 text-3xl font-semibold text-white">Realtime-safe model health</h2>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader>
            <CardTitle>Evaluation metrics</CardTitle>
          </CardHeader>
          <CardContent className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metrics} margin={{ left: -8, right: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" tickLine={false} axisLine={false} stroke="#64748b" />
                <YAxis tickLine={false} axisLine={false} stroke="#64748b" domain={[0, 'dataMax + 0.1']} />
                <Tooltip
                  formatter={(value) => Number(value) < 1 ? Number(value).toFixed(4) : Number(value).toFixed(2)}
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '0.75rem' }}
                />
                <Bar dataKey="value" fill="#5f9efa" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Model profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              ['Model', 'realtime_safe_xgboost'],
              ['Threshold', Number(realtime.threshold ?? 0.00009248).toExponential(4)],
              ['Preferred deployment', 'Yes'],
              ['Shadow model', 'leakage_suspect_xgboost'],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl border border-slate-800 bg-slate-950/40 p-3">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{label}</div>
                <div className="mt-2 text-base font-medium text-white">{value}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
