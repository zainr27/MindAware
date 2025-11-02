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

  const { altitude_m, rotation_deg, battery, mission_progress, status } = telemetry

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

  const getRotationState = (rotation) => {
    // Normalize rotation to 0-180 range for display
    const normalized = rotation % 360
    if (normalized > 170 && normalized < 190) return 'TURNED_AROUND'
    if (normalized < 10 || normalized > 350) return 'FORWARD'
    return 'TURNING'
  }

  const getStatusBadge = (status) => {
    if (status === 'active') return 'status-active'
    if (status === 'low_battery') return 'status-warning'
    return 'status-error'
  }

  const binaryState = getBinaryState(altitude_m)
  const rotationState = getRotationState(rotation_deg)

  return (
    <div className="card drone-card">
      <h2>🚁 Binary Drone Control</h2>
      
      {/* Binary State Indicator - PRIMARY DISPLAY */}
      <div className="binary-state-display">
        <div 
          className={`binary-state-badge binary-state-${binaryState.toLowerCase()}`}
          style={{ 
            backgroundColor: getBinaryStateColor(altitude_m),
            fontSize: '1.5rem',
            fontWeight: 'bold',
            padding: '1rem',
            borderRadius: '12px',
            textAlign: 'center',
            marginBottom: '1rem',
            boxShadow: `0 4px 20px ${getBinaryStateColor(altitude_m)}40`
          }}
        >
          {binaryState === 'TAKEOFF' && '✈️ TAKEOFF - ALL PARAMETERS OPTIMAL'}
          {binaryState === 'GROUND' && '🔴 GROUNDED - ALL PARAMETERS CRITICAL'}
          {binaryState === 'TRANSITION' && '⚡ TRANSITIONING...'}
        </div>
        
        {/* Visual representation of binary states */}
        <div className="binary-visual" style={{ 
          display: 'flex', 
          gap: '1rem', 
          marginBottom: '1.5rem',
          justifyContent: 'center'
        }}>
          <div style={{ 
            textAlign: 'center', 
            padding: '1rem',
            backgroundColor: altitude_m >= 0.9 ? '#10b98140' : '#1f293740',
            borderRadius: '8px',
            border: altitude_m >= 0.9 ? '2px solid #10b981' : '2px solid transparent',
            flex: 1
          }}>
            <div style={{ fontSize: '2rem' }}>✅</div>
            <div style={{ fontWeight: 'bold', color: '#10b981' }}>1.0m</div>
            <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>All Good</div>
          </div>
          
          <div style={{ 
            textAlign: 'center', 
            padding: '1rem',
            backgroundColor: rotationState === 'TURNED_AROUND' ? '#fbbf2440' : '#1f293740',
            borderRadius: '8px',
            border: rotationState === 'TURNED_AROUND' ? '2px solid #fbbf24' : '2px solid transparent',
            flex: 1
          }}>
            <div style={{ fontSize: '2rem' }}>🔄</div>
            <div style={{ fontWeight: 'bold', color: '#fbbf24' }}>180°</div>
            <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>Mixed State</div>
          </div>
          
          <div style={{ 
            textAlign: 'center', 
            padding: '1rem',
            backgroundColor: altitude_m <= 0.1 ? '#ef444440' : '#1f293740',
            borderRadius: '8px',
            border: altitude_m <= 0.1 ? '2px solid #ef4444' : '2px solid transparent',
            flex: 1
          }}>
            <div style={{ fontSize: '2rem' }}>🔴</div>
            <div style={{ fontWeight: 'bold', color: '#ef4444' }}>0.0m</div>
            <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>All Bad</div>
          </div>
        </div>
      </div>

      {/* Current Values */}
      <div className="telemetry-grid" style={{ marginBottom: '1.5rem' }}>
        <div className="telemetry-item">
          <span className="telemetry-label">Current Altitude</span>
          <span className="telemetry-value" style={{ 
            color: getBinaryStateColor(altitude_m),
            fontSize: '1.5rem',
            fontWeight: 'bold'
          }}>
            {altitude_m.toFixed(2)}m
          </span>
        </div>

        <div className="telemetry-item">
          <span className="telemetry-label">Current Rotation</span>
          <span className="telemetry-value" style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
            {rotation_deg.toFixed(0)}°
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
            backgroundColor: getBinaryStateColor(altitude_m),
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

      {/* Rotation Compass - Enhanced */}
      <div className="rotation-indicator" style={{ marginBottom: '1.5rem' }}>
        <div className="indicator-label" style={{ marginBottom: '0.5rem', fontWeight: 'bold' }}>
          Rotation State: {rotationState}
        </div>
        <div className="rotation-compass" style={{ 
          width: '100px', 
          height: '100px', 
          margin: '0 auto',
          border: '3px solid #4a5568',
          borderRadius: '50%',
          position: 'relative',
          backgroundColor: rotationState === 'TURNED_AROUND' ? '#fbbf2420' : '#1a202c'
        }}>
          {/* Cardinal directions */}
          <div style={{ position: 'absolute', top: '5px', left: '50%', transform: 'translateX(-50%)', fontSize: '0.7rem', opacity: 0.5 }}>N</div>
          <div style={{ position: 'absolute', bottom: '5px', left: '50%', transform: 'translateX(-50%)', fontSize: '0.7rem', opacity: 0.5 }}>S</div>
          <div style={{ position: 'absolute', left: '5px', top: '50%', transform: 'translateY(-50%)', fontSize: '0.7rem', opacity: 0.5 }}>W</div>
          <div style={{ position: 'absolute', right: '5px', top: '50%', transform: 'translateY(-50%)', fontSize: '0.7rem', opacity: 0.5 }}>E</div>
          
          {/* Rotating arrow */}
          <div 
            className="rotation-arrow"
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: `translate(-50%, -50%) rotate(${rotation_deg}deg)`,
              transition: 'transform 0.5s ease',
              fontSize: '2.5rem',
              transformOrigin: 'center'
            }}
          >
            ↑
          </div>
        </div>
        <div style={{ textAlign: 'center', marginTop: '0.5rem', fontSize: '0.9rem', opacity: 0.7 }}>
          {rotation_deg.toFixed(0)}° from North
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
                width: `${battery}%`,
                height: '100%',
                backgroundColor: getBatteryColor(battery),
                transition: 'width 0.3s ease'
              }}
            />
          </div>
          <div style={{ textAlign: 'center', marginTop: '0.3rem', fontSize: '0.9rem' }}>{battery.toFixed(0)}%</div>
        </div>
        
        <div>
          <div className="indicator-label">Mission</div>
          <div className="mission-progress-bar" style={{ height: '20px', backgroundColor: '#1f2937', borderRadius: '10px', overflow: 'hidden' }}>
            <div
              className="mission-fill"
              style={{ 
                width: `${mission_progress}%`,
                height: '100%',
                backgroundColor: '#3b82f6',
                transition: 'width 0.3s ease'
              }}
            />
          </div>
          <div style={{ textAlign: 'center', marginTop: '0.3rem', fontSize: '0.9rem' }}>{mission_progress.toFixed(0)}%</div>
        </div>
      </div>

      {/* Operator State Summary */}
      <div className="wellness-indicator" style={{ 
        marginTop: '1.5rem', 
        padding: '1rem', 
        backgroundColor: `${getBinaryStateColor(altitude_m)}20`,
        borderRadius: '8px',
        border: `2px solid ${getBinaryStateColor(altitude_m)}`
      }}>
        <div className="indicator-label" style={{ marginBottom: '0.5rem' }}>Operator Cognitive State</div>
        <div className="wellness-text" style={{ fontSize: '1.2rem', fontWeight: 'bold', textAlign: 'center' }}>
          {altitude_m >= 0.9 && <span style={{ color: '#10b981' }}>🟢 EXCELLENT - All Parameters Optimal</span>}
          {altitude_m <= 0.1 && <span style={{ color: '#ef4444' }}>🔴 CRITICAL - All Parameters Degraded</span>}
          {altitude_m > 0.1 && altitude_m < 0.9 && <span style={{ color: '#fbbf24' }}>🟡 MIXED - Some Parameters Off</span>}
        </div>
      </div>
    </div>
  )
}

export default DroneStatus
