const BASE = '/api'

export async function generateSignal(symbol, timeframe, accountSize) {
  const res = await fetch(`${BASE}/signals/generate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ symbol, timeframe, account_size: accountSize }) })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function scanAll(timeframe) {
  const res = await fetch(`${BASE}/signals/scan?timeframe=${timeframe}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getSignals(params = {}) {
  const res = await fetch(`${BASE}/signals?${new URLSearchParams(params)}`)
  return res.json()
}

export async function openTrade(signalId, accountSize) {
  const res = await fetch(`${BASE}/trades/open`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ signal_id: signalId, account_size: accountSize }) })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function closeTrade(tradeId, exitPrice, notes) {
  const res = await fetch(`${BASE}/trades/${tradeId}/close`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ exit_price: exitPrice, notes }) })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getTrades(status) {
  const res = await fetch(`${BASE}/trades${status ? '?status=' + status : ''}`)
  return res.json()
}

export async function getPortfolioStats() {
  const res = await fetch(`${BASE}/portfolio/stats`)
  return res.json()
}

export async function getWatchlist() {
  const res = await fetch(`${BASE}/watchlist`)
  return res.json()
}
