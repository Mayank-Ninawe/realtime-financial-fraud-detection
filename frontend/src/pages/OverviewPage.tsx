import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import evaluationResults from '../../../reports/evaluation_results.json';
import graphSummary from '../../../artifacts/graph/graph_summary.json';
import { Activity, ArrowUpRight, CircleDollarSign, ShieldAlert, TrendingUp } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const totalTransactions = Number(graphSummary.analysis_window.actual_transaction_rows ?? 200000);
const fraudTransactions = Number(graphSummary.analysis_window.fraud_transaction_rows ?? 147);
const fraudRate = ((fraudTransactions / totalTransactions) * 100).toFixed(2);
const modelAveragePrecision = Number(evaluationResults.realtime_safe.test_average_precision ?? 0.9926);
const threshold = Number(evaluationResults.realtime_safe.threshold ?? 0.00009248);

const trendData = [
  { day: 'Mon', risk: 8 },
  { day: 'Tue', risk: 12 },
  { day: 'Wed', risk: 10 },
  { day: 'Thu', risk: 24 },
  { day: 'Fri', risk: 31 },
  { day: 'Sat', risk: 27 },
  { day: 'Sun', risk: 36 },
];

const metricCards = [
  { label: 'Transactions processed', value: new Intl.NumberFormat('en-US').format(totalTransactions), change: '+0.0%', icon: Activity, tone: 'text-brand-400' },
  { label: 'Fraud rate', value: `${fraudRate}%`, change: 'Model baseline', icon: ShieldAlert, tone: 'text-amber-400' },
  { label: 'Alerts flagged', value: new Intl.NumberFormat('en-US').format(fraudTransactions), change: 'Historical fraud cases', icon: CircleDollarSign, tone: 'text-emerald-400' },
  { label: 'Model confidence', value: `${(modelAveragePrecision * 100).toFixed(1)}%`, change: `Thresh ${threshold.toExponential(3)}`, icon: TrendingUp, tone: 'text-cyan-400' },
];

const priorityAlerts = graphSummary.top_fraud_linked_accounts.slice(0, 3).map((account) => ({
  name: `Account ${account.account_id}`,
  risk: `${(account.fraud_linked_ratio * 100).toFixed(1)}%`,
  detail: `${account.in_degree} inbound links · ${account.fraud_linked_transaction_count} fraud-linked txns`,
}));

export function OverviewPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Overview</p>
          <h2 className="mt-2 text-3xl font-semibold text-white">Financial risk command center</h2>
        </div>
        <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-sm text-emerald-300">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          Active detection run
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metricCards.map(({ label, value, change, icon: Icon, tone }) => (
          <Card key={label} className="overflow-hidden">
            <CardContent className="space-y-4 p-0">
              <div className="flex items-start justify-between px-4 pt-4">
                <div>
                  <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{label}</div>
                  <div className="mt-3 text-3xl font-semibold text-white">{value}</div>
                </div>
                <div className={`rounded-xl bg-slate-800 p-2 ${tone}`}>
                  <Icon size={20} />
                </div>
              </div>
              <div className="flex items-center gap-2 border-t border-slate-800 px-4 pb-4 pt-3 text-sm text-emerald-400">
                <ArrowUpRight size={14} />
                {change} this week
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.6fr_0.8fr]">
        <Card>
          <CardHeader>
            <CardTitle>Risk exposure trend</CardTitle>
            <div className="text-sm text-slate-400">7-day view</div>
          </CardHeader>
          <CardContent className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData} margin={{ left: -10, right: 10, top: 8, bottom: 0 }}>
                <defs>
                  <linearGradient id="riskFill" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="5%" stopColor="#5f9efa" stopOpacity={0.7} />
                    <stop offset="95%" stopColor="#5f9efa" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="day" tickLine={false} axisLine={false} stroke="#64748b" />
                <YAxis tickLine={false} axisLine={false} stroke="#64748b" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '0.75rem' }}
                />
                <Area type="monotone" dataKey="risk" stroke="#5f9efa" strokeWidth={3} fill="url(#riskFill)" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Priority alerts</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {priorityAlerts.length > 0 ? (
              priorityAlerts.map((alert) => (
                <div key={alert.name} className="rounded-xl border border-slate-800 bg-slate-950/40 p-3">
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-medium text-slate-100">{alert.name}</div>
                    <div className="rounded-full bg-red-500/10 px-2 py-1 text-xs font-medium text-red-300">{alert.risk}</div>
                  </div>
                  <div className="mt-2 text-sm text-slate-400">{alert.detail}</div>
                </div>
              ))
            ) : (
              <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-sm text-slate-400">
                No suspicious relationships detected in the current sample window.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
