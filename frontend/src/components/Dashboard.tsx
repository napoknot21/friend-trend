import { useState, useEffect } from 'react'

export default function Dashboard() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/dashboard')
      .then(res => res.json())
      .then(json => {
        setData(json)
        setLoading(false)
      })
      .catch(err => {
        console.error("Failed to fetch dashboard data:", err)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return <div className="glass-panel">Loading market views... (Make sure the FastAPI server is running)</div>
  }

  if (data.length === 0) {
    return (
      <div className="glass-panel">
        <h2>No data available</h2>
        <p>No extractions found in the database. Did you run the python extraction pipeline yet?</p>
      </div>
    )
  }

  return (
    <div>
      <div className="dashboard-grid">
        {data.map((item: any, idx: number) => {
          const bullishPct = (item.stats.bullish / item.stats.total) * 100
          const bearishPct = (item.stats.bearish / item.stats.total) * 100
          const neutralPct = (item.stats.neutral / item.stats.total) * 100

          return (
            <div key={idx} className="card">
              <header>
                <h2>{item.underlying}</h2>
                <span className={`consensus-badge ${item.consensus}`}>
                  {item.consensus}
                </span>
              </header>
              <div style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>
                {item.stats.total} analysts views
              </div>

              <div className="stats-bar">
                <div className="stats-bar-segment" style={{ width: `${bullishPct}%`, background: 'var(--bullish-color)' }} title={`Bullish: ${bullishPct.toFixed(0)}%`}></div>
                <div className="stats-bar-segment" style={{ width: `${neutralPct}%`, background: 'var(--neutral-color)' }} title={`Neutral: ${neutralPct.toFixed(0)}%`}></div>
                <div className="stats-bar-segment" style={{ width: `${bearishPct}%`, background: 'var(--bearish-color)' }} title={`Bearish: ${bearishPct.toFixed(0)}%`}></div>
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem' }}>
                <span className="stats-label" style={{ color: 'var(--bullish-color)' }}>{item.stats.bullish} Bull</span>
                <span className="stats-label" style={{ color: 'var(--neutral-color)' }}>{item.stats.neutral} Neut</span>
                <span className="stats-label" style={{ color: 'var(--bearish-color)' }}>{item.stats.bearish} Bear</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
