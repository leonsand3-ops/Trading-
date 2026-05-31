import React, { useState } from 'react'
import { closeTrade } from '../hooks/useApi'

export default function TradeRow({ trade, onClose }) {
  const [exitPrice, setExitPrice] = useState('')
  const [closing, setClosing] = useState(false)
  const [showClose, setShowClose] = useState(false)
  const isOpen = trade.status === 'open'

  const handleClose = async () => {
    const price = parseFloat(exitPrice)
    if (!price) return
    setClosing(true)
    try { await closeTrade(trade.id, price); onClose?.() }
    catch (e) { alert(e.message) }
    finally { setClosing(false); setShowClose(false) }
  }

  return (
    <div className="card" style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center' }}>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', minWidth: 120 }}>
        <strong>{trade.symbol}</strong>
        <span className={`badge badge-${trade.signal_type?.toLowerCase()}`}>{trade.signal_type}</span>
        <span className={`badge badge-${trade.timeframe}`}>{trade.timeframe}</span>
      </div>
      <Cell label="Entry" value={`$${trade.entry_price}`} />
      {!isOpen && <Cell label="Exit" value={`$${trade.exit_price}`} />}
      <Cell label="Qty" value={trade.quantity} />
      <Cell label="SL" value={trade.stop_loss ? `$${trade.stop_loss}` : '—'} />
      <Cell label="TP" value={trade.take_profit ? `$${trade.take_profit}` : '—'} />
      {!isOpen && trade.pnl != null && (
        <div>
          <div className="muted" style={{ fontSize: 11 }}>P&L</div>
          <div className={trade.pnl >= 0 ? 'pos' : 'neg'} style={{ fontWeight: 700 }}>
            {trade.pnl >= 0 ? '+' : ''}${trade.pnl} ({trade.pnl_pct}%)
          </div>
        </div>
      )}
      {isOpen && !showClose && <button onClick={() => setShowClose(true)} style={{ background: 'var(--red)', color: '#fff', marginLeft: 'auto' }}>Close Trade</button>}
      {isOpen && showClose && (
        <div style={{ display: 'flex', gap: 6, marginLeft: 'auto', alignItems: 'center' }}>
          <input type="number" placeholder="Exit price" value={exitPrice} onChange={e => setExitPrice(e.target.value)} style={{ width: 110 }} />
          <button onClick={handleClose} disabled={closing} style={{ background: 'var(--red)', color: '#fff' }}>{closing ? '...' : 'Confirm'}</button>
          <button onClick={() => setShowClose(false)} style={{ background: 'var(--surface2)', color: 'var(--text)' }}>Cancel</button>
        </div>
      )}
      <div className="muted" style={{ fontSize: 11, width: '100%' }}>
        {new Date(trade.opened_at).toLocaleString()}{trade.closed_at && ` → ${new Date(trade.closed_at).toLocaleString()}`}
      </div>
    </div>
  )
}

function Cell({ label, value }) {
  return <div><div className="muted" style={{ fontSize: 11 }}>{label}</div><div style={{ fontWeight: 500 }}>{value}</div></div>
}
