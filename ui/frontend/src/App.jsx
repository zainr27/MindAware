import React, { useState, useEffect, useRef } from 'react'
import './App.css'
import CognitiveMetrics from './components/CognitiveMetrics'
import DecisionLog from './components/DecisionLog'
import DroneStatus from './components/DroneStatus'
import ConnectionStatus from './components/ConnectionStatus'

function App() {
  const [cognitiveState, setCognitiveState] = useState({
    focus: 0,
    fatigue: 0,
    overload: 0,
    stress: 0
  })
  const [telemetry, setTelemetry] = useState(null)
  const [decisions, setDecisions] = useState([])
  const [connected, setConnected] = useState(false)
  const [history, setHistory] = useState([])
  const wsRef = useRef(null)
  const maxHistory = 20

  useEffect(() => {
    connectWebSocket()
    fetchInitialData()
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const connectWebSocket = () => {
    const ws = new WebSocket('ws://localhost:8000/ws')
    
    ws.onopen = () => {
      console.log('WebSocket connected')
      setConnected(true)
      ws.send(JSON.stringify({ command: 'subscribe', channel: 'all' }))
    }
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      
      switch (message.type) {
        case 'cognitive_state':
          setCognitiveState(message.data)
          setHistory(prev => {
            const newHistory = [...prev, message.data]
            return newHistory.slice(-maxHistory)
          })
          break
        
        case 'telemetry':
          setTelemetry(message.data)
          break
        
        case 'decision':
          setDecisions(prev => [message.data, ...prev].slice(0, 10))
          break
        
        case 'connection':
          console.log('Connection status:', message.status)
          break
        
        default:
          console.log('Unknown message type:', message.type)
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setConnected(false)
    }
    
    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setConnected(false)
      // Attempt reconnection after 5 seconds
      setTimeout(connectWebSocket, 5000)
    }
    
    wsRef.current = ws
  }

  const fetchInitialData = async () => {
    try {
      // Fetch recent logs
      const logsResponse = await fetch('/api/logs?count=5')
      const logsData = await logsResponse.json()
      setDecisions(logsData.logs || [])
    } catch (error) {
      console.error('Error fetching initial data:', error)
    }
  }

  // Binary thresholds matching policy
  const FOCUS_HIGH = 0.6
  const FOCUS_LOW = 0.4
  const NEGATIVE_HIGH = 0.6
  const NEGATIVE_LOW = 0.4

  const getStatusSeverity = () => {
    const { focus, fatigue, overload, stress } = cognitiveState
    
    // Check if ALL good
    const allGood = (focus >= FOCUS_HIGH && fatigue <= NEGATIVE_LOW && 
                     overload <= NEGATIVE_LOW && stress <= NEGATIVE_LOW)
    
    // Check if ALL bad
    const allBad = (focus <= FOCUS_LOW && fatigue >= NEGATIVE_HIGH && 
                    overload >= NEGATIVE_HIGH && stress >= NEGATIVE_HIGH)
    
    if (allGood) return 'excellent'
    if (allBad) return 'critical'
    return 'mixed'
  }

  const getStatusDescription = (severity) => {
    if (severity === 'excellent') return '✈️ Drone at 1m - All parameters optimal'
    if (severity === 'critical') return '🔴 Drone grounded - All parameters critical'
    return '🔄 Drone rotating - Mixed cognitive state'
  }

  const statusSeverity = getStatusSeverity()

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <h1 className="title">
            <span className="icon">🧠</span>
            MindAware
            <span className="subtitle">Binary Cognitive Control</span>
          </h1>
          <ConnectionStatus connected={connected} />
        </div>
      </header>

      <main className="main-content">
        <div className="grid">
          <div className="card status-card">
            <h2>Binary Control Status</h2>
            <div className={`status-indicator status-${statusSeverity}`} style={{
              backgroundColor: statusSeverity === 'excellent' ? '#10b981' : 
                              statusSeverity === 'critical' ? '#ef4444' : '#fbbf24',
              padding: '1.5rem',
              borderRadius: '12px',
              fontSize: '1.5rem',
              fontWeight: 'bold',
              textAlign: 'center',
              marginBottom: '1rem',
              boxShadow: statusSeverity === 'excellent' ? '0 4px 20px #10b98140' : 
                         statusSeverity === 'critical' ? '0 4px 20px #ef444440' : 
                         '0 4px 20px #fbbf2440'
            }}>
              {statusSeverity.toUpperCase()}
            </div>
            <p className="status-description" style={{ 
              fontSize: '1.1rem', 
              textAlign: 'center',
              fontWeight: '500'
            }}>
              {getStatusDescription(statusSeverity)}
            </p>
            
            {/* Binary control explanation */}
            <div style={{ 
              marginTop: '1.5rem', 
              padding: '1rem', 
              backgroundColor: '#1f2937',
              borderRadius: '8px',
              fontSize: '0.85rem'
            }}>
              <div style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>How Binary Control Works:</div>
              <ul style={{ margin: 0, paddingLeft: '1.2rem', lineHeight: '1.6' }}>
                <li><strong style={{ color: '#10b981' }}>ALL GOOD</strong>: Focus ≥60% + All negatives ≤40% → <strong>Takeoff to 1m</strong></li>
                <li><strong style={{ color: '#ef4444' }}>ALL BAD</strong>: Focus ≤40% + All negatives ≥60% → <strong>Land to 0m</strong></li>
                <li><strong style={{ color: '#fbbf24' }}>MIXED</strong>: Some parameters good, some bad → <strong>Rotate 180°</strong></li>
              </ul>
            </div>
          </div>

          <CognitiveMetrics 
            cognitiveState={cognitiveState}
            history={history}
          />

          <DroneStatus telemetry={telemetry} />

          <DecisionLog decisions={decisions} />
        </div>
      </main>

      <footer className="footer">
        <p>MindAware Agent v1.0.0 | Binary BCI-Driven Drone Control</p>
        <p style={{ fontSize: '0.8rem', opacity: 0.7, marginTop: '0.3rem' }}>
          Three States: ✅ Up (1m) | 🔄 Rotating (180°) | 🔴 Down (0m)
        </p>
      </footer>
    </div>
  )
}

export default App

