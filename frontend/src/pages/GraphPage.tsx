import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import graphSummary from '../../../artifacts/graph/graph_summary.json';

const summary = graphSummary.graph_metrics;
const topAccounts = graphSummary.top_fraud_linked_accounts.slice(0, 5);
const nodes = [
  { id: 'A', label: 'Account Cluster', x: 20, y: 40 },
  { id: 'B', label: 'Receiver 1', x: 46, y: 20 },
  { id: 'C', label: 'Receiver 2', x: 72, y: 36 },
  { id: 'D', label: 'Cross-border', x: 62, y: 68 },
  { id: 'E', label: 'Dormant Origin', x: 24, y: 72 },
];

export function GraphPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Network analysis</p>
        <h2 className="mt-2 text-3xl font-semibold text-white">Fraud ring relationship graph</h2>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.4fr_0.6fr]">
        <Card>
          <CardHeader>
            <CardTitle>Entity graph</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="relative h-[420px] overflow-hidden rounded-2xl border border-slate-800 bg-[radial-gradient(circle_at_center,_rgba(59,130,246,0.18),_transparent_50%)]">
              <svg viewBox="0 0 100 100" className="h-full w-full">
                <line x1="20" y1="40" x2="46" y2="20" stroke="#60a5fa" strokeWidth="1.5" opacity="0.9" />
                <line x1="46" y1="20" x2="72" y2="36" stroke="#60a5fa" strokeWidth="1.5" opacity="0.9" />
                <line x1="72" y1="36" x2="62" y2="68" stroke="#60a5fa" strokeWidth="1.5" opacity="0.9" />
                <line x1="20" y1="40" x2="24" y2="72" stroke="#60a5fa" strokeWidth="1.5" opacity="0.9" />
                <line x1="24" y1="72" x2="62" y2="68" stroke="#60a5fa" strokeWidth="1.5" opacity="0.9" />
                {nodes.map((node) => (
                  <g key={node.id} transform={`translate(${node.x}, ${node.y})`}>
                    <circle r="8" fill="#1d4ed8" opacity="0.9" />
                    <text x="0" y="15" textAnchor="middle" fill="#e2e8f0" fontSize="4">{node.label}</text>
                  </g>
                ))}
              </svg>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Network insights</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              ['Connected entities', summary.node_count.toLocaleString()],
              ['Unusual flows', summary.edge_count.toLocaleString()],
              ['Fraud-linked relationships', summary.fraud_linked_relationship_count.toString()],
              ['Largest cluster', `${summary.largest_weakly_connected_component_size} accounts`],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl border border-slate-800 bg-slate-950/40 p-3">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{label}</div>
                <div className="mt-2 text-lg font-semibold text-white">{value}</div>
              </div>
            ))}
            <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-3">
              <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Top suspicious accounts</div>
              <div className="mt-3 space-y-2">
                {topAccounts.map((account) => (
                  <div key={account.account_id} className="flex items-center justify-between gap-3 text-sm text-slate-300">
                    <span>{account.account_id}</span>
                    <span className="text-amber-300">{(account.fraud_linked_ratio * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
