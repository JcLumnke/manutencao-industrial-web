import React, { useState } from 'react'

// Backend URL from environment or fallback
const API_URL = import.meta.env.VITE_API_URL || 'https://manutencao-industrial-julio.squareweb.app'

export default function App() {
  // Tabs: Diagnostico (Functional), Historico (View), Dashboard (Charts)
  const [activeTab, setActiveTab] = useState('diagnostico')
  const [symptoms, setSymptoms] = useState('')
  const [machineId, setMachineId] = useState('')
  const [equipmentName, setEquipmentName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [diagnosis, setDiagnosis] = useState(null)

  // Submits the new diagnosis request to the Gemini API
  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setDiagnosis(null)
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/diagnose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          symptoms, 
          equipment_name: equipmentName || 'Industrial Machine',
          machine_id: machineId || undefined 
        })
      })
      if (!res.ok) throw new Error(`API Status: ${res.status}`)
      const json = await res.json()
      setDiagnosis(json.diagnosis || json)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Renders the Pizza Chart for confidence and severity
  function renderRiskGauge(severity, confidence) {
    const pct = Math.round((confidence || 0) * 100);
    const gaugeColor = severity === 'critical' ? '#ff4d4f' : '#faad14';
    return (
      <div className="gauge-container" style={{ textAlign: 'center' }}>
        <div style={{
          width: '130px', height: '130px', borderRadius: '50%',
          background: `conic-gradient(${gaugeColor} ${pct}%, #f0f0f0 0)`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto'
        }}>
          <div style={{ width: '100px', height: '100px', background: '#fff', borderRadius: '50%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', boxShadow: 'inset 0 0 10px rgba(0,0,0,0.1)' }}>
            <span style={{ fontSize: '22px', fontWeight: 'bold' }}>{pct}%</span>
            <small style={{ fontSize: '11px', color: '#888', textTransform: 'uppercase' }}>{severity}</small>
          </div>
        </div>
        <p style={{ marginTop: '12px', fontWeight: '600', color: '#444' }}>Risk & Confidence</p>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="hero">
        <h1>Diagnóstico de Manutenção</h1>
        <p className="subtitle">AI-Powered Industrial Failure Analysis</p>
      </header>

      {/* Main Navigation - Removed "Novo Registro" as requested */}
      <nav className="tabs-nav" style={{ display: 'flex', justifyContent: 'center', gap: '30px', background: '#fff', borderBottom: '1px solid #eee' }}>
        {['diagnostico', 'historico', 'dashboard'].map(t => (
          <button 
            key={t} 
            onClick={() => setActiveTab(t)}
            style={{ 
              padding: '15px 25px', border: 'none', background: 'none', cursor: 'pointer',
              borderBottom: activeTab === t ? '3px solid #004a8c' : '3px solid transparent',
              color: activeTab === t ? '#004a8c' : '#666',
              fontWeight: activeTab === t ? '700' : '400',
              textTransform: 'uppercase', letterSpacing: '1px'
            }}
          >
            {t}
          </button>
        ))}
      </nav>

      <main className="main-content" style={{ padding: '30px 10%' }}>
        {activeTab === 'diagnostico' && (
          <div className="diagnose-view" style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '30px' }}>
            {/* Input Form */}
            <form className="panel input-panel" onSubmit={handleSubmit}>
              <div className="field">
                <label>Equipment Name</label>
                <input value={equipmentName} onChange={(e)=>setEquipmentName(e.target.value)} placeholder="e.g. Prensa Hidraulica" />
              </div>
              <div className="field">
                <label>Symptoms</label>
                <textarea value={symptoms} onChange={(e)=>setSymptoms(e.target.value)} placeholder="Describe machine behavior..." required rows={6} />
              </div>
              <div className="field">
                <label>Machine ID (Optional)</label>
                <input value={machineId} onChange={(e)=>setMachineId(e.target.value)} placeholder="e.g. 45" />
              </div>
              <button className="btn-primary" type="submit" disabled={loading}>
                {loading ? 'Analyzing AI Models...' : 'Run Diagnosis'}
              </button>
            </form>

            {/* Result Display */}
            <section className="panel result-panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h2>Results <span style={{ color: '#1890ff', fontSize: '16px' }}>for "{equipmentName || 'System'}"</span></h2>
              </div>

              {diagnosis ? (
                <div className="results-grid">
                  <div className="res-card">
                    <h3>Probable Causes</h3>
                    {diagnosis.probable_causes?.map((c, i) => (
                      <div key={i} className="bar-group" style={{ marginBottom: '15px' }}>
                        <div className="bar-label" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                          <span>{c.cause}</span>
                          <span style={{ fontWeight: 'bold' }}>{c.likelihood}%</span>
                        </div>
                        <div className="bar-bg" style={{ background: '#f0f0f0', height: '10px', borderRadius: '5px', marginTop: '6px' }}>
                          <div className="bar-fill" style={{ background: 'linear-gradient(90deg, #1890ff, #69c0ff)', width: `${c.likelihood}%`, height: '100%', borderRadius: '50px' }} />
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="res-card risk-center">
                    {renderRiskGauge(diagnosis.severity, diagnosis.confidence)}
                  </div>
                </div>
              ) : <div className="empty-state">Waiting for symptoms input to generate AI report.</div>}
            </section>
          </div>
        )}

        {/* Historico and Dashboard views remain as development placeholders */}
        {(activeTab === 'historico' || activeTab === 'dashboard') && (
          <div className="placeholder-view" style={{ textAlign: 'center', padding: '100px', background: '#fff', borderRadius: '12px' }}>
             <h2 style={{ textTransform: 'uppercase', color: '#004a8c' }}>{activeTab}</h2>
             <p style={{ color: '#999' }}>Database integration in progress (Module 3).</p>
          </div>
        )}
      </main>
    </div>
  )
}