import React, { useState, useEffect, useCallback } from 'react'
import SignalCard from './components/SignalCard'
import StatsBar from './components/StatsBar'
import TradeRow from './components/TradeRow'
import { useWebSocket } from './hooks/useWebSocket'
import { generateSignal, scanAll, getSignals, getTrades, getPortfolioStats, getWatchlist } from './hooks/useApi'

const TABS = ['Signals', 'Scanner', 'Trades', 'Portfolio']
const TIMEFRAMES = ['15min', 'day', 'swing']

export default function App() {
  const [tab, setTab] = useState('Signals')
  const [signals, setSignals] = useState([])
  const [trades, setTrades] = useState([])
  const [stats, setStats] = useState(null)
  const [watchlist, setWatchlist] = useState([])
  const [loading, setLoading] = useState(false)
  const [symbol, setSymbol] = useState('AAPL')
  const [timeframe, setTimeframe] = useState('day')
  const [accountSize, setAccountSize] = useState(10000)
  const [scanTf, setScanTf] = useState('day')
  const [scanResults, setScanResults] = useState([])

  useWebSocket((msg) => {
    if (msg.type === 'new_signal') setSignals(prev => [msg.data, ...prev])
    if (msg.type === 'trade_closed') { loadTrades(); loadStats() }
  })

  const loadSignals = useCallback(async () => { const data = await getSignals({ limit: 30 }); setSignals(data) }, [])
  const loadTrades = useCallback(async () => { const data = await getTrades(); setTrades(data) }, [])
  const loadStats = useCallback(async () => { const data = await getPortfolioStats(); setStats(data) }, [])

  useEffect(() => {
    loadSignals(); loadTrades(); loadStats()
    getWatchlist().then(d => setWatchlist(d.symbols || []))
  }, [])

  const handleGenerate = async () => {
    setLoading(true)
    try { const sig = await generateSignal(symbol.toUpperCase(), timeframe, accountSize); setSignals(prev => [sig, ...prev]) }
    catch (e) { alert(e.message) }
    finally { setLoading(false) }
  }

  const handleScan = async () => {
    setLoading(true); setScanResults([])
    try { const results = await scanAll(scanTf); setScanResults(results) }
    catch (e) { alert(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div style={{ minHeight: '100vh', padding: 20, maxWidth: 1100, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>Trading Signal Platform</h1>
          <div className="muted" style={{ fontSize: 12 }}>Paper Trading — TradingView Compatible</div>
        </div>
        <LiveDot />
      </div>

      <div style={{ display: 'flex', gap: 4, marginBottom: 20, borderBottom: '1px solid var(--border)', paddingBottom: 12 }}>
        {TABS.map(t => (
          <button key={t} onClick={() => { setTab(t); if (t === 'Trades') loadTrades(); if (t === 'Portfolio') loadStats() }}
            style={{ background: tab === t ? 'var(--blue)' : 'var(--surface2)', color: tab === t ? '#fff' : 'var(--text)', padding: '6px 16px' }}>
            {t}
          </button>
        ))}
      </div>

      {tab === 'Signals' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card" style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <Field label="Symbol">
              <input list="wl" value={symbol} onChange={e => setSymbol(e.target.value)} style={{ width: 110 }} />
              <datalist id="wl">{watchlist.map(s => <option key={s} value={s} />)}</datalist>
            </Field>
            <Field label="Timeframe">
              <select value={timeframe} onChange={e => setTimeframe(e.target.value)}>
                {TIMEFRAMES.map(tf => <option key={tf} value={tf}>{tf}</option>)}
              </select>
            </Field>
            <Field label="Account Size ($)">
              <input type="number" value={accountSize} onChange={e => setAccountSize(Number(e.target.value))} style={{ width: 110 }} />
            </Field>
            <button onClick={handleGenerate} disabled={loading} style={{ background: 'var(--blue)', color: '#fff', height: 34 }}>
              {loading ? 'Analyzing...' : 'Generate Signal'}
            </button>
          </div>
          {signals.length === 0 && <div className="muted" style={{ textAlign: 'center', padding: 40 }}>No signals yet. Generate your first signal above.</div>}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 12 }}>
            {signals.map((s, i) => <SignalCard key={s.id || i} signal={s} onTradeOpened={loadTrades} />)}
          </div>
        </div>
      )}

      {tab === 'Scanner' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card" style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
            <Field label="Timeframe">
              <select value={scanTf} onChange={e => setScanTf(e.target.value)}>
                {TIMEFRAMES.map(tf => <option key={tf} value={tf}>{tf}</option>)}
              </select>
            </Field>
            <button onClick={handleScan} disabled={loading} style={{ background: 'var(--blue)', color: '#fff', height: 34 }}>
              {loading ? `Scanning ${watchlist.length} symbols...` : `Scan Watchlist (${watchlist.length})`}
            </button>
          </div>
          {scanResults.length > 0 && (
            <>
              <ScanSummary results={scanResults} />
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 12 }}>
                {scanResults.filter(s => s.signal !== 'HOLD').sort((a, b) => (b.confidence || 0) - (a.confidence || 0)).map((s, i) => <SignalCard key={i} signal={s} onTradeOpened={loadTrades} />)}
              </div>
              {scanResults.every(s => s.signal === 'HOLD') && <div className="muted" style={{ textAlign: 'center', padding: 40 }}>No actionable signals. Market may be ranging.</div>}
            </>
          )}
        </div>
      )}

      {tab === 'Trades' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ fontSize: 16 }}>Paper Trades ({trades.length})</h2>
            <button onClick={loadTrades} style={{ background: 'var(--surface2)', color: 'var(--text)' }}>Refresh</button>
          </div>
          {trades.length === 0 && <div className="muted" style={{ textAlign: 'center', padding: 40 }}>No trades yet.</div>}
          {trades.map(t => <TradeRow key={t.id} trade={t} onClose={() => { loadTrades(); loadStats() }} />)}
        </div>
      )}

      {tab === 'Portfolio' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <StatsBar stats={stats} />
          {stats && stats.closed_trades > 0 && (
            <div className="card">
              <h3 style={{ marginBottom: 12, fontSize: 14 }}>Performance</h3>
              <div style={{ display: 'flex', gap: 24 }}>
                <Perf label="Winners" value={stats.winners} color="var(--green)" />
                <Perf label="Losers" value={stats.losers} color="var(--red)" />
                <Perf label="Win Rate" value={`${stats.win_rate}%`} color={stats.win_rate >= 50 ? 'var(--green)' : 'var(--red)'} />
                <Perf label="Profit Factor" value={stats.profit_factor} color={stats.profit_factor >= 1.5 ? 'var(--green)' : 'var(--yellow)'} />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function Field({ label, children }) {
  return <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}><label className="muted" style={{ fontSize: 11 }}>{label}</label>{children}</div>
}

function LiveDot() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--green)', boxShadow: '0 0 6px var(--green)', animation: 'pulse 2s infinite' }} />
      <span className="muted" style={{ fontSize: 12 }}>Live</span>
      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }`}</style>
    </div>
  )
}

function ScanSummary({ results }) {
  const buys = results.filter(r => r.signal === 'BUY').length
  const sells = results.filter(r => r.signal === 'SELL').length
  const holds = results.filter(r => r.signal === 'HOLD').length
  return (
    <div className="card" style={{ display: 'flex', gap: 20 }}>
      <span><span className="muted">Total: </span><strong>{results.length}</strong></span>
      <span style={{ color: 'var(--green)' }}>▲ BUY: {buys}</span>
      <span style={{ color: 'var(--red)' }}>▼ SELL: {sells}</span>
      <span className="muted">HOLD: {holds}</span>
    </div>
  )
}

function Perf({ label, value, color }) {
  return <div><div className="muted" style={{ fontSize: 11 }}>{label}</div><div style={{ fontSize: 20, fontWeight: 700, color }}>{value}</div></div>
}
