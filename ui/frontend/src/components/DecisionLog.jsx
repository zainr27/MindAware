import React from 'react'
import './DecisionLog.css'

function DecisionLog({ decisions }) {
  if (!decisions || decisions.length === 0) {
    return (
      <div className="card decision-card">
        <h2>Decision Log</h2>
        <p className="no-decisions">No decisions logged yet...</p>
      </div>
    )
  }

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A'
    const date = new Date(timestamp)
    return date.toLocaleTimeString()
  }

  return (
    <div className="card decision-card">
      <h2>Decision Log</h2>
      
      <div className="decisions-list">
        {decisions.map((decision, idx) => (
          <div key={idx} className="decision-item">
            <div className="decision-header">
              <span className="decision-time">{formatTimestamp(decision.timestamp)}</span>
              <span className={`decision-badge ${decision.model === 'policy_fallback' ? 'policy' : 'llm'}`}>
                {decision.model === 'policy_fallback' || decision.model === 'policy_only' ? 'POLICY' : 'LLM'}
              </span>
            </div>
            
            {decision.llm_reasoning && (
              <div className="decision-reasoning">
                {decision.llm_reasoning}
              </div>
            )}
            
            {decision.actions_taken && decision.actions_taken.length > 0 && (
              <div className="decision-actions">
                <strong>Actions:</strong>
                {decision.actions_taken.map((action, actionIdx) => (
                  <div key={actionIdx} className="action-item">
                    <span className="action-tool">{action.tool}</span>
                    {action.reason && (
                      <span className="action-reason">- {action.reason}</span>
                    )}
                  </div>
                ))}
              </div>
            )}
            
            {decision.cognitive_state && (
              <div className="decision-state">
                <span>F: {(decision.cognitive_state.focus * 100).toFixed(0)}%</span>
                <span>Ftg: {(decision.cognitive_state.fatigue * 100).toFixed(0)}%</span>
                <span>O: {(decision.cognitive_state.overload * 100).toFixed(0)}%</span>
                <span>S: {(decision.cognitive_state.stress * 100).toFixed(0)}%</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default DecisionLog

