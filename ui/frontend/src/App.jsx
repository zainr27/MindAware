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
  const pollingIntervalRef = useRef(null)
  const maxHistory = 20
  const POLL_INTERVAL = 500 // Poll every 500ms for real-time updates

  useEffect(() => {
    console.log('🚀 Starting MindAware UI polling...')
    
    // Test connection immediately
    fetch('http://127.0.0.1:8000/health')
      .then(res => res.json())
      .then(data => console.log('✅ API connection test:', data))
      .catch(err => console.error('❌ API connection failed:', err))
    
    startPolling()
    fetchInitialData()
    
    return () => {
      stopPolling()
    }
  }, [])

  const startPolling = () => {
    // Immediate first poll
    pollEEGData()
    
    // Set up polling interval
    pollingIntervalRef.current = setInterval(() => {
      pollEEGData()
    }, POLL_INTERVAL)
  }

  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
  }

  const pollEEGData = async () => {
    try {
      // Poll the EEG state endpoint - gets actual values from main.py's adapter
      const response = await fetch('/api/eeg/state')
      
      if (response.ok) {
        const data = await response.json()
        console.log('📊 EEG Data received:', data) // Debug log
        
        // Extract cognitive state from EEG adapter response (actual values from main.py)
        if (data.focus !== undefined) {
          const cognitiveState = {
            focus: parseFloat(data.focus) || 0,
            fatigue: parseFloat(data.fatigue) || 0,
            overload: parseFloat(data.overload) || 0,
            stress: parseFloat(data.stress) || 0
          }
          
          console.log('✅ Setting cognitive state:', cognitiveState) // Debug log
          setCognitiveState(cognitiveState)
          setHistory(prev => {
            const newHistory = [...prev, cognitiveState]
            return newHistory.slice(-maxHistory)
          })
        } else {
          console.warn('⚠️ No focus field in response:', data)
        }
        
        setConnected(true)
      } else {
        console.error('❌ Bad response:', response.status, response.statusText)
        setConnected(false)
      }
    } catch (error) {
      console.error('❌ Error polling EEG data:', error)
      setConnected(false)
    }
    
    // Fetch drone telemetry (altitude, rotation)
    try {
      const telemetryResponse = await fetch('/api/tools/status')
      if (telemetryResponse.ok) {
        const telemetryData = await telemetryResponse.json()
        console.log('🚁 Telemetry received:', telemetryData) // Debug log
        // Convert to telemetry format expected by DroneStatus component
        setTelemetry({
          altitude_m: telemetryData.current_altitude || 0,
          rotation_deg: telemetryData.current_rotation || 0,
          battery: 100
        })
      } else {
        console.error('❌ Bad telemetry response:', telemetryResponse.status)
      }
    } catch (error) {
      console.error('❌ Error fetching telemetry:', error)
    }
    
    // Fetch recent decisions (from main.py's logger)
    try {
      const logsResponse = await fetch('/api/logs?count=10')
      if (logsResponse.ok) {
        const logsData = await logsResponse.json()
        console.log('📝 Logs received:', logsData.logs?.length || 0, 'decisions') // Debug log
        setDecisions(logsData.logs || [])
      } else {
        console.error('❌ Bad logs response:', logsResponse.status)
      }
    } catch (error) {
      console.error('❌ Error fetching decisions:', error)
    }
  }

  const fetchInitialData = async () => {
    console.log('📡 Fetching initial data...')
    try {
      // Fetch recent logs using /api proxy
      const logsResponse = await fetch('/api/logs?count=5')
      if (logsResponse.ok) {
        const logsData = await logsResponse.json()
        console.log('✅ Initial logs loaded:', logsData.logs?.length || 0)
        setDecisions(logsData.logs || [])
      } else {
        console.error('❌ Failed to fetch initial logs:', logsResponse.status)
      }
    } catch (error) {
      console.error('❌ Error fetching initial data:', error)
    }
    
    // Also fetch initial EEG state
    try {
      const eegResponse = await fetch('/api/eeg/state')
      if (eegResponse.ok) {
        const eegData = await eegResponse.json()
        console.log('✅ Initial EEG state loaded:', eegData)
        if (eegData.focus !== undefined) {
          setCognitiveState({
            focus: parseFloat(eegData.focus) || 0,
            fatigue: parseFloat(eegData.fatigue) || 0,
            overload: parseFloat(eegData.overload) || 0,
            stress: parseFloat(eegData.stress) || 0
          })
        }
      }
    } catch (error) {
      console.error('❌ Error fetching initial EEG state:', error)
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
        {/* Debug Panel - remove after testing */}
        <div style={{ 
          padding: '1rem', 
          backgroundColor: '#1f2937', 
          marginBottom: '1rem',
          borderRadius: '8px',
          fontSize: '0.85rem'
        }}>
          <strong>🔍 Debug Info:</strong>
          <div>Connected: {connected ? '✅' : '❌'}</div>
          <div>Focus: {cognitiveState.focus.toFixed(3)}</div>
          <div>Fatigue: {cognitiveState.fatigue.toFixed(3)}</div>
          <div>History: {history.length} points</div>
          <div>Decisions: {decisions.length} entries</div>
          <div>Telemetry: {telemetry ? `${telemetry.altitude_m}m, ${telemetry.rotation_deg}°` : 'null'}</div>
        </div>
        
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

