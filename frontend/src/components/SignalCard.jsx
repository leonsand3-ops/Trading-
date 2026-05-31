import React, { useState } from 'react'
import { openTrade } from '../hooks/useApi'

export default function SignalCard({ signal, onTradeOpened }) {
  const [loading, setLoading] = useState(false)
  const [opened, setOpened] = useState(false)
  const s = signal.signal || signal.signal_type
  const conf = signal.confidence ? Math.round(signal.confidence * 100) : null
  const pct = signal.stop_loss && signal.price ? Math.abs(((signal.stop_loss - signal.price) / signal.price) * 100).toFixed(2) : null

  const handleOpen = async () => {
    setLoading(true)
    try { await openTrade(signal.id, signal.account_size); setOpened(true); onTradeOpened?.() }
    catch (e) { alert(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <strong style={{ fontSize: 16 }}>{signal.symbol}</strong>
          <span className={`badge badge-${s?.toLowerCase()}`}>{s}</span>
          <span className={`badge badge-${signal.timeframe}`}>{signal.timeframe}</span>
        </div>
        {conf && <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: conf >= 70 ? 'var(--green)' : conf >= 55 ? 'var(--yellow)' : 'var(--text-muted)' }}>{conf}%</div>
          <div className="muted" style={{ fontSize: 11 }}>confidence</div>
        </div>}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
        <PriceBox label="Entry" value={signal.price} />
        <PriceBox label="Stop Loss" value={signal.stop_loss} sub={pct ? `-${pct}%` : null} color="var(--red)" />
        <PriceBox label="Take Profit" value={signal.take_profit} color="var(--green)" />
      </div>
      <div style={{ display: 'flex', gap: 16, fontSize: 12 }}>
        {signal.risk_reward && <Stat label="R/R" value={`1 : ${signal.risk_reward}`} />}
        {signal.position_size > 0 && <Stat label="Qty" value={signal.position_size} />}
        {signal.risk_amount > 0 && <Stat label="Risk $" value={`$${signal.risk_amount}`} />}
      </div>
      {signal.reasoning && <p style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.4 }}>{signal.reasoning}</p>}
      {signal.id && s !== 'HOLD' && (
        <button onClick={handleOpen} disabled={loading || opened}
          style={{ background: s === 'BUY' ? 'var(--green)' : 'var(--red)', color: '#fff', alignSelf: 'flex-start' }}>
          {opened ? 'Trade Opened ✓' : loading ? 'Opening...' : 'Open Paper Trade'}
        </button>
      )}
      {signal.created_at && <div className="muted" style={{ fontSize: 11 }}>{new Date(signal.created_at).toLocaleString()}</div>}
    </div>
  )
}

function PriceBox({ label, value, sub, color }) {
  return (
    <div style={{ background: 'var(--surface2)', borderRadius: 6, padding: '8px 10px' }}>
      <div className="muted" style={{ fontSize: 11, marginBottom: 2 }}>{label}</div>
      <div style={{ fontWeight: 600, color: color || 'var(--text)' }}>
        {value != null ? value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 }) : '—'}
      </div>
      {sub && <div style={{ fontSize: 10, color }}>{sub}</div>}
    </div>
  )
}

function Stat({ label, value }) {
  return <div><span className="muted">{label}: </span><span style={{ fontWeight: 600 }}>{value}</span></div>
}
