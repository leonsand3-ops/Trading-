import React from 'react'

export default function StatsBar({ stats }) {
  if (!stats) return null
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 10 }}>
      <StatCard label="Total Trades" value={stats.total_trades} />
      <StatCard label="Open" value={stats.open_trades} color="var(--yellow)" />
      <StatCard label="Win Rate" value={`${stats.win_rate}%`} color={stats.win_rate >= 50 ? 'var(--green)' : 'var(--red)'} />
      <StatCard label="Total P&L" value={`$${stats.total_pnl}`} color={stats.total_pnl >= 0 ? 'var(--green)' : 'var(--red)'} />
      <StatCard label="Avg P&L" value={`$${stats.avg_pnl}`} color={stats.avg_pnl >= 0 ? 'var(--green)' : 'var(--red)'} />
      <StatCard label="Best Trade" value={`$${stats.best_trade}`} color="var(--green)" />
      <StatCard label="Worst Trade" value={`$${stats.worst_trade}`} color="var(--red)" />
      <StatCard label="Profit Factor" value={stats.profit_factor} color={stats.profit_factor >= 1.5 ? 'var(--green)' : stats.profit_factor >= 1 ? 'var(--yellow)' : 'var(--red)'} />
    </div>
    )
}

function StatCard({ label, value, color }) {
  return (
    <div className="card" style={{ textAlign: 'center' }}>
      <div className="muted" style={{ fontSize: 11, marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: color || 'var(--text)' }}>{value}</div>
    </div>
  )
}
