import React, { useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'https://manutencao-industrial-julio.squareweb.app'

export default function App() {
  const [activeTab, setActiveTab] = useState('diagnostico')
  const [symptoms, setSymptoms] = useState('')
  const [machineId, setMachineId] = useState('')
  const [equipmentName, setEquipmentName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [diagnosis, setDiagnosis] = useState(null)

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
          equipment_name: equipmentName || 'Machine',
          machine_id: machineId || undefined 
        })
      })
      if (!res.ok) throw new Error(`Status ${res.status}`)
      const json = await res.json()
      setDiagnosis(json.diagnosis || json)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function renderSeverityChart(severity, confidence) {
    const confPct = Math.round((confidence || 0) * 100);
    const color = severity === 'critical' ? '#ff4d4f' : '#faad14';
    return (
      <div style={{ textAlign: 'center', marginTop: '20px' }}>
        <div style={{
          width: '120px', height: '120px', borderRadius: '50%',
          background: `conic-gradient(${color} ${confPct}%, #eee 0)`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto'
        }}>
          <div style={{ width: '90px', height: '90px', background: 'white', borderRadius: '50%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ fontSize: '20px', fontWeight: 'bold' }}>{confPct}%</span>
            <small style={{ fontSize: '10px', color: '#666' }}>{severity}</small>
          </div>
        </div>
        <p style={{ marginTop: '10px', fontSize: '12px', fontWeight: 'bold' }}>Risk & Confidence</p>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="hero">
        <h1>Diagnóstico de Manutenção</h1>
        <p>AI-Powered Industrial Failure Analysis</p>
      </header>

      <nav className="tabs" style={{ display: 'flex', justifyContent: 'center', gap: '20px', background: '#fff', borderBottom: '1px solid #ddd' }}>
        {['diagnostico', 'historico', 'dashboard'].map(tab => (
          <button 
            key={tab} 
            onClick={() => setActiveTab(tab)}
            style={{ 
              padding: '15px 30px', border: 'none', background: 'none', cursor: 'pointer',
              borderBottom: activeTab === tab ? '3px solid #004a8c' : 'none',
              fontWeight: activeTab === tab ? 'bold' : 'normal',
              textTransform: 'uppercase', color: activeTab === tab ? '#004a8c' : '#666'
            }}
          >
            {tab}
          </button>
        ))}
      </nav>

      <main className="container">
        {activeTab === 'diagnostico' ? (
          <div className="grid-main" style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '30px', marginTop: '20px' }}>
            <form className="panel form" onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Equipment Name</label>
                <input style={{ width: '100%', padding: '10px' }} value={equipmentName} onChange={(e)=>setEquipmentName(e.target.value)} placeholder="e.g. Prensa Hidraulica" />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Symptoms</label>
                <textarea style={{ width: '100%', padding: '10px' }} value={symptoms} onChange={(e)=>setSymptoms(e.target.value)} placeholder="Describe machine behavior..." required rows={6} />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Machine ID (Optional)</label>
                <input style={{ width: '100%', padding: '10px' }} value={machineId} onChange={(e)=>setMachineId(e.target.value)} placeholder="e.g. 45" />
              </div>

              <button className="primary" type="submit" disabled={loading} style={{ padding: '12px', cursor: 'pointer' }}>
                {loading ? 'Analyzing...' : 'Run Diagnosis'}
              </button>
            </form>

            <section className="panel result">
              <h2>Results <span style={{ color: '#1890ff', fontSize: '18px' }}>for "{equipmentName || 'System'}"</span></h2>
              
              {diagnosis ? (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '20px' }}>
                  <div className="card">
                    <h3>Probable Causes</h3>
                    {diagnosis.probable_causes?.map((c, i) => (
                      <div key={i} style={{ marginBottom: '15px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                          <span>{c.cause}</span>
                          <span style={{ fontWeight: 'bold' }}>{c.likelihood}%</span>
                        </div>
                        <div style={{ background: '#eee', height: '10px', borderRadius: '5px', marginTop: '5px' }}>
                          <div style={{ background: '#1890ff', width: `${c.likelihood}%`, height: '100%', borderRadius: '5px' }} />
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="card">
                    <h3>Assessment</h3>
                    {renderSeverityChart(diagnosis.severity, diagnosis.confidence)}
                  </div>
                </div>
              ) : <p className="muted" style={{ marginTop: '20px' }}>Waiting for symptoms input to generate AI report.</p>}
            </section>
          </div>
        ) : (
          <div className="panel" style={{ textAlign: 'center', padding: '100px', marginTop: '20px' }}>
            <h2 style={{ textTransform: 'uppercase' }}>{activeTab}</h2>
            <p className="muted">Feature in development.</p>
          </div>
        )}
      </main>
    </div>
  )
}