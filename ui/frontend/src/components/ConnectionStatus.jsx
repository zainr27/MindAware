import React from 'react'
import './ConnectionStatus.css'

function ConnectionStatus({ connected }) {
  return (
    <div className="connection-status">
      <div className={`connection-dot ${connected ? 'connected' : 'disconnected'}`} />
      <span className="connection-text">
        {connected ? 'Polling EEG Data' : 'Disconnected'}
      </span>
    </div>
  )
}

export default ConnectionStatus

