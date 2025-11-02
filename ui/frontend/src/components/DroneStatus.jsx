import React from 'react'
import './DroneStatus.css'

function DroneStatus({ telemetry }) {
  if (!telemetry) {
    return (
      <div className="card drone-card">
        <h2>🚁 Binary Drone Control</h2>
        <p className="no-data">Waiting for telemetry data...</p>
      </div>
    )
  }

  const { 
    altitude_m = 0, 
    rotation_deg = 0, 
    battery = 100, 
    mission_progress = 0, 
    status = 'active' 
  } = telemetry || {}

  const getBatteryColor = (battery) => {
    if (battery > 50) return '#10b981'
    if (battery > 20) return '#fbbf24'
    return '#ef4444'
  }

  // Binary altitude states
  const getBinaryState = (altitude) => {
    if (altitude >= 0.9) return 'TAKEOFF' // At 1m = all good
    if (altitude <= 0.1) return 'GROUND' // At 0m = all bad
    return 'TRANSITION' // In between
  }

  const getBinaryStateColor = (altitude) => {
    if (altitude >= 0.9) return '#10b981' // Green - excellent
    if (altitude <= 0.1) return '#ef4444' // Red - critical
    return '#fbbf24' // Yellow - transitioning
  }


  const getStatusBadge = (status) => {
    if (status === 'active') return 'status-active'
    if (status === 'low_battery') return 'status-warning'
    return 'status-error'
  }

  // Ensure values are numbers
  const altitude = parseFloat(altitude_m) || 0
  const bat = parseFloat(battery) || 100
  const mission = parseFloat(mission_progress) || 0
  
  const binaryState = getBinaryState(altitude)

  return (
    <div className="card drone-card">
      <h2>🚁 Binary Drone Control</h2>
      
      {/* Binary State Indicator - PRIMARY DISPLAY */}
      <div className="binary-state-display">
        <div 
          className={`binary-state-badge binary-state-${binaryState.toLowerCase()}`}
          style={{ 
            backgroundColor: getBinaryStateColor(altitude),
            fontSize: '1.5rem',
            fontWeight: 'bold',
            padding: '1rem',
            borderRadius: '12px',
            textAlign: 'center',
            marginBottom: '1rem',
            boxShadow: `0 4px 20px ${getBinaryStateColor(altitude_m)}40`
          }}
        >
          {binaryState === 'TAKEOFF' && '✈️ DRONE IN THE AIR'}
          {binaryState === 'GROUND' && '🔴 GROUNDED'}
          {binaryState === 'TRANSITION' && '⏸️ WAITING FOR DECISION'}
        </div>
        
        {/* Visual representation of binary states */}
        <div className="binary-visual" style={{ 
          display: 'flex', 
          gap: '2rem', 
          marginBottom: '1.5rem',
          justifyContent: 'center'
        }}>
          <div style={{ 
            textAlign: 'center', 
            padding: '1.5rem',
            backgroundColor: altitude >= 0.9 ? '#10b98140' : '#1f293740',
            borderRadius: '12px',
            border: altitude >= 0.9 ? '3px solid #10b981' : '2px solid transparent',
            flex: 1,
            maxWidth: '200px'
          }}>
            <div style={{ fontSize: '3rem' }}>✈️</div>
            <div style={{ fontWeight: 'bold', color: '#10b981', fontSize: '1.2rem', marginTop: '0.5rem' }}>IN THE AIR</div>
            <div style={{ fontSize: '1rem', opacity: 0.7, marginTop: '0.3rem' }}>1.0m altitude</div>
            <div style={{ fontSize: '0.8rem', opacity: 0.6, marginTop: '0.3rem' }}>All parameters optimal</div>
          </div>
          
          <div style={{ 
            textAlign: 'center', 
            padding: '1.5rem',
            backgroundColor: altitude <= 0.1 ? '#ef444440' : '#1f293740',
            borderRadius: '12px',
            border: altitude <= 0.1 ? '3px solid #ef4444' : '2px solid transparent',
            flex: 1,
            maxWidth: '200px'
          }}>
            <div style={{ fontSize: '3rem' }}>🔴</div>
            <div style={{ fontWeight: 'bold', color: '#ef4444', fontSize: '1.2rem', marginTop: '0.5rem' }}>GROUNDED</div>
            <div style={{ fontSize: '1rem', opacity: 0.7, marginTop: '0.3rem' }}>0.0m altitude</div>
            <div style={{ fontSize: '0.8rem', opacity: 0.6, marginTop: '0.3rem' }}>Regain focus to fly</div>
          </div>
        </div>
      </div>

      {/* Current Values */}
      <div style={{ marginBottom: '1.5rem', textAlign: 'center' }}>
        <div className="telemetry-item">
          <span className="telemetry-label" style={{ display: 'block', marginBottom: '0.5rem' }}>Current Altitude</span>
          <span className="telemetry-value" style={{ 
            color: getBinaryStateColor(altitude),
            fontSize: '2rem',
            fontWeight: 'bold',
            display: 'block'
          }}>
            {altitude.toFixed(2)}m
          </span>
        </div>
      </div>

      {/* Binary Altitude Visualization */}
      <div className="binary-altitude-visual" style={{ marginBottom: '1.5rem' }}>
        <div className="indicator-label" style={{ marginBottom: '0.5rem', fontWeight: 'bold' }}>
          Binary Altitude Control
        </div>
        <div style={{ 
          display: 'flex', 
          alignItems: 'flex-end', 
          height: '120px',
          gap: '2rem',
          justifyContent: 'center',
          position: 'relative'
        }}>
          {/* Ground marker */}
          <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: '2px', backgroundColor: '#ef4444', opacity: 0.5 }} />
          <div style={{ position: 'absolute', bottom: 0, left: '1rem', fontSize: '0.8rem', color: '#ef4444' }}>0m (Ground)</div>
          
          {/* 1m marker */}
          <div style={{ position: 'absolute', bottom: '80%', left: 0, right: 0, height: '2px', backgroundColor: '#10b981', opacity: 0.5 }} />
          <div style={{ position: 'absolute', bottom: '80%', left: '1rem', fontSize: '0.8rem', color: '#10b981' }}>1m (Optimal)</div>
          
          {/* Drone visualization */}
          <div style={{ 
            height: `${Math.min(altitude_m * 80, 100)}%`,
            width: '60px',
            backgroundColor: getBinaryStateColor(altitude),
            borderRadius: '8px 8px 0 0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '2rem',
            transition: 'all 0.5s ease',
            boxShadow: `0 -4px 20px ${getBinaryStateColor(altitude_m)}80`
          }}>
            🚁
          </div>
        </div>
      </div>

      {/* Operator Feedback Note */}
      <div style={{ 
        marginBottom: '1.5rem', 
        padding: '1rem', 
        backgroundColor: '#1f293740',
        borderRadius: '8px',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '0.9rem', opacity: 0.8, fontStyle: 'italic' }}>
          💡 Yaw (rotation) is controlled by head movement via EEG
        </div>
      </div>

      {/* Battery and Status */}
      <div className="system-info" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <div>
          <div className="indicator-label">Battery</div>
          <div className="battery-bar" style={{ height: '20px', backgroundColor: '#1f2937', borderRadius: '10px', overflow: 'hidden' }}>
            <div
              className="battery-fill"
              style={{
                width: `${bat}%`,
                height: '100%',
                backgroundColor: getBatteryColor(bat),
                transition: 'width 0.3s ease'
              }}
            />
          </div>
          <div style={{ textAlign: 'center', marginTop: '0.3rem', fontSize: '0.9rem' }}>{bat.toFixed(0)}%</div>
        </div>
        
        <div>
          <div className="indicator-label">Mission</div>
          <div className="mission-progress-bar" style={{ height: '20px', backgroundColor: '#1f2937', borderRadius: '10px', overflow: 'hidden' }}>
            <div
              className="mission-fill"
              style={{ 
                width: `${mission}%`,
                height: '100%',
                backgroundColor: '#3b82f6',
                transition: 'width 0.3s ease'
              }}
            />
          </div>
          <div style={{ textAlign: 'center', marginTop: '0.3rem', fontSize: '0.9rem' }}>{mission.toFixed(0)}%</div>
        </div>
      </div>

      {/* Operator State Summary */}
      <div className="wellness-indicator" style={{ 
        marginTop: '1.5rem', 
        padding: '1rem', 
        backgroundColor: `${getBinaryStateColor(altitude)}20`,
        borderRadius: '8px',
        border: `2px solid ${getBinaryStateColor(altitude)}`
      }}>
        <div className="indicator-label" style={{ marginBottom: '0.5rem' }}>Operator Cognitive State</div>
        <div className="wellness-text" style={{ fontSize: '1.2rem', fontWeight: 'bold', textAlign: 'center' }}>
          {altitude >= 0.9 && <span style={{ color: '#10b981' }}>🟢 All Parameters Optimal</span>}
          {altitude <= 0.1 && <span style={{ color: '#ef4444' }}>🔴 Regain Focus to Fly</span>}
          {altitude > 0.1 && altitude < 0.9 && <span style={{ color: '#fbbf24' }}>⏸️ Waiting for Decision</span>}
        </div>
      </div>
    </div>
  )
}

export default DroneStatus
