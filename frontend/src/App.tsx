import { useState, useEffect } from 'react'
import './index.css'
import Dashboard from './components/Dashboard'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')

  return (
    <div className="app-container">
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ margin: 0, color: '#58a6ff' }}>Trend Classifier</h1>
          <p style={{ margin: 0, color: 'var(--text-secondary)' }}>Market Sentiment Analysis via LLM</p>
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button 
            onClick={() => setActiveTab('dashboard')}
            style={{ 
              background: activeTab === 'dashboard' ? 'var(--accent-color)' : 'transparent',
              color: activeTab === 'dashboard' ? '#000' : 'var(--text-primary)',
              border: '1px solid var(--accent-color)',
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 600
            }}
          >
            Dashboard
          </button>
          <button 
            onClick={() => setActiveTab('terminal')}
            style={{ 
              background: activeTab === 'terminal' ? 'var(--accent-color)' : 'transparent',
              color: activeTab === 'terminal' ? '#000' : 'var(--text-primary)',
              border: '1px solid var(--accent-color)',
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 600
            }}
          >
            Terminal Logs
          </button>
        </div>
      </header>

      {activeTab === 'dashboard' ? (
        <Dashboard />
      ) : (
        <div className="glass-panel">
          <h2>Extraction Logs</h2>
          <p>Run <code>python main.py</code> in your local terminal to see the extraction process.</p>
          <div className="terminal-container">
             <div className="terminal-line info">[*] Initializing database...</div>
             <div className="terminal-line">[*] Connecting to Outlook mailbox...</div>
             <div className="terminal-line">[*] Found 180 emails to process.</div>
             <div className="terminal-line info">... waiting for local python script execution (placeholder) ...</div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
