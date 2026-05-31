import { useEffect, useRef } from 'react'

export function useWebSocket(onMessage) {
  const ws = useRef(null)
  const onMsg = useRef(onMessage)
  onMsg.current = onMessage

  useEffect(() => {
    const connect = () => {
      const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
      ws.current = new WebSocket(`${proto}://${window.location.host}/api/ws`)
      ws.current.onmessage = (e) => { try { onMsg.current(JSON.parse(e.data)) } catch {} }
      ws.current.onclose = () => setTimeout(connect, 3000)
    }
    connect()
    return () => ws.current?.close()
  }, [])
}
