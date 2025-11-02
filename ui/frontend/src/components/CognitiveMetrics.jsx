import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine } from 'recharts'
import './CognitiveMetrics.css'

function CognitiveMetrics({ cognitiveState, history }) {
  const { focus, fatigue, overload, stress } = cognitiveState

  // Binary thresholds
  const FOCUS_HIGH = 0.6
  const FOCUS_LOW = 0.4
  const NEGATIVE_HIGH = 0.6
  const NEGATIVE_LOW = 0.4

  // Check if ALL good or ALL bad
  const allGood = (focus >= FOCUS_HIGH && fatigue <= NEGATIVE_LOW && 
                   overload <= NEGATIVE_LOW && stress <= NEGATIVE_LOW)
  const allBad = (focus <= FOCUS_LOW && fatigue >= NEGATIVE_HIGH && 
                  overload >= NEGATIVE_HIGH && stress >= NEGATIVE_HIGH)

  const getMetricColor = (value, inverted = false) => {
    if (inverted) {
      if (value >= NEGATIVE_HIGH) return '#ef4444' // Critical
      if (value <= NEGATIVE_LOW) return '#10b981'  // Good
      return '#fbbf24' // Mixed
    } else {
      if (value >= FOCUS_HIGH) return '#10b981'  // Good
      if (value <= FOCUS_LOW) return '#ef4444'   // Critical
      return '#fbbf24' // Mixed
    }
  }

  const metrics = [
    { 
      name: 'Focus', 
      value: focus, 
      color: getMetricColor(focus), 
      inverted: false,
      threshold: focus >= FOCUS_HIGH ? '✅' : focus <= FOCUS_LOW ? '❌' : '⚠️',
      thresholdText: `${FOCUS_HIGH}+ good, ${FOCUS_LOW}- critical`
    },
    { 
      name: 'Fatigue', 
      value: fatigue, 
      color: getMetricColor(fatigue, true), 
      inverted: true,
      threshold: fatigue <= NEGATIVE_LOW ? '✅' : fatigue >= NEGATIVE_HIGH ? '❌' : '⚠️',
      thresholdText: `${NEGATIVE_LOW}- good, ${NEGATIVE_HIGH}+ critical`
    },
    { 
      name: 'Overload', 
      value: overload, 
      color: getMetricColor(overload, true), 
      inverted: true,
      threshold: overload <= NEGATIVE_LOW ? '✅' : overload >= NEGATIVE_HIGH ? '❌' : '⚠️',
      thresholdText: `${NEGATIVE_LOW}- good, ${NEGATIVE_HIGH}+ critical`
    },
    { 
      name: 'Stress', 
      value: stress, 
      color: getMetricColor(stress, true), 
      inverted: true,
      threshold: stress <= NEGATIVE_LOW ? '✅' : stress >= NEGATIVE_HIGH ? '❌' : '⚠️',
      thresholdText: `${NEGATIVE_LOW}- good, ${NEGATIVE_HIGH}+ critical`
    },
  ]

  // Prepare chart data
  const chartData = history.map((state, idx) => ({
    index: idx,
    focus: state.focus,
    fatigue: state.fatigue,
    overload: state.overload,
    stress: state.stress
  }))

  return (
    <div className="card cognitive-card">
      <h2>🧠 Cognitive State Monitor</h2>
      
      {/* Binary Decision Indicator */}
      <div style={{ 
        padding: '1rem', 
        marginBottom: '1rem',
        borderRadius: '8px',
        backgroundColor: allGood ? '#10b98120' : allBad ? '#ef444420' : '#fbbf2420',
        border: `2px solid ${allGood ? '#10b981' : allBad ? '#ef4444' : '#fbbf24'}`,
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '1.2rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
          {allGood && '✅ ALL PARAMETERS OPTIMAL'}
          {allBad && '❌ ALL PARAMETERS CRITICAL'}
          {!allGood && !allBad && '⚠️ MIXED STATE'}
        </div>
        <div style={{ fontSize: '0.9rem', opacity: 0.8 }}>
          {allGood && 'Drone Command: TAKEOFF to 1m'}
          {allBad && 'Drone Command: LAND to ground'}
          {!allGood && !allBad && 'Drone Command: TURN_AROUND 180°'}
        </div>
      </div>
      
      <div className="metrics-grid">
        {metrics.map((metric) => (
          <div key={metric.name} className="metric-item">
            <div className="metric-header">
              <span className="metric-name">
                {metric.threshold} {metric.name}
              </span>
              <span className="metric-value" style={{ color: metric.color, fontSize: '1.2rem', fontWeight: 'bold' }}>
                {(metric.value * 100).toFixed(0)}%
              </span>
            </div>
            <div style={{ position: 'relative' }}>
              <div className="metric-bar" style={{ position: 'relative' }}>
                {/* Threshold markers */}
                {metric.name === 'Focus' && (
                  <>
                    <div style={{ 
                      position: 'absolute', 
                      left: `${FOCUS_HIGH * 100}%`, 
                      top: 0, 
                      bottom: 0, 
                      width: '2px', 
                      backgroundColor: '#10b981',
                      zIndex: 1
                    }} />
                    <div style={{ 
                      position: 'absolute', 
                      left: `${FOCUS_LOW * 100}%`, 
                      top: 0, 
                      bottom: 0, 
                      width: '2px', 
                      backgroundColor: '#ef4444',
                      zIndex: 1
                    }} />
                  </>
                )}
                {metric.name !== 'Focus' && (
                  <>
                    <div style={{ 
                      position: 'absolute', 
                      left: `${NEGATIVE_LOW * 100}%`, 
                      top: 0, 
                      bottom: 0, 
                      width: '2px', 
                      backgroundColor: '#10b981',
                      zIndex: 1
                    }} />
                    <div style={{ 
                      position: 'absolute', 
                      left: `${NEGATIVE_HIGH * 100}%`, 
                      top: 0, 
                      bottom: 0, 
                      width: '2px', 
                      backgroundColor: '#ef4444',
                      zIndex: 1
                    }} />
                  </>
                )}
                <div
                  className="metric-fill"
                  style={{
                    width: `${metric.value * 100}%`,
                    backgroundColor: metric.color,
                    transition: 'width 0.3s ease, background-color 0.3s ease'
                  }}
                />
              </div>
              <div style={{ fontSize: '0.7rem', opacity: 0.6, marginTop: '0.2rem' }}>
                {metric.thresholdText}
              </div>
            </div>
          </div>
        ))}
      </div>

      {chartData.length > 0 && (
        <div className="chart-container">
          <h3>Trend History (Binary Thresholds)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="index" stroke="rgba(255,255,255,0.5)" />
              <YAxis domain={[0, 1]} stroke="rgba(255,255,255,0.5)" />
              
              {/* Threshold reference lines */}
              <ReferenceLine y={FOCUS_HIGH} stroke="#10b981" strokeDasharray="3 3" strokeOpacity={0.5} label={{ value: 'Good ↑', fill: '#10b981', fontSize: 10 }} />
              <ReferenceLine y={FOCUS_LOW} stroke="#ef4444" strokeDasharray="3 3" strokeOpacity={0.5} label={{ value: 'Critical ↓', fill: '#ef4444', fontSize: 10 }} />
              
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(0,0,0,0.9)', 
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px'
                }}
                formatter={(value) => `${(value * 100).toFixed(0)}%`}
              />
              <Legend />
              <Line type="monotone" dataKey="focus" stroke="#10b981" strokeWidth={2} dot={false} name="Focus" />
              <Line type="monotone" dataKey="fatigue" stroke="#ef4444" strokeWidth={2} dot={false} name="Fatigue" />
              <Line type="monotone" dataKey="overload" stroke="#fbbf24" strokeWidth={2} dot={false} name="Overload" />
              <Line type="monotone" dataKey="stress" stroke="#f97316" strokeWidth={2} dot={false} name="Stress" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
      
      {/* Legend for binary logic */}
      <div style={{ 
        marginTop: '1rem', 
        padding: '0.75rem', 
        backgroundColor: '#1f2937', 
        borderRadius: '8px',
        fontSize: '0.85rem'
      }}>
        <div style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>Binary Decision Logic:</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', fontSize: '0.75rem' }}>
          <div>
            <span style={{ color: '#10b981' }}>✅ ALL GOOD:</span>
            <div style={{ opacity: 0.7 }}>Focus ≥60%</div>
            <div style={{ opacity: 0.7 }}>Negatives ≤40%</div>
            <div style={{ color: '#10b981', fontWeight: 'bold' }}>→ Takeoff 1m</div>
          </div>
          <div>
            <span style={{ color: '#ef4444' }}>❌ ALL BAD:</span>
            <div style={{ opacity: 0.7 }}>Focus ≤40%</div>
            <div style={{ opacity: 0.7 }}>Negatives ≥60%</div>
            <div style={{ color: '#ef4444', fontWeight: 'bold' }}>→ Land 0m</div>
          </div>
          <div>
            <span style={{ color: '#fbbf24' }}>⚠️ MIXED:</span>
            <div style={{ opacity: 0.7 }}>Some good</div>
            <div style={{ opacity: 0.7 }}>Some bad</div>
            <div style={{ color: '#fbbf24', fontWeight: 'bold' }}>→ Rotate 180°</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CognitiveMetrics

