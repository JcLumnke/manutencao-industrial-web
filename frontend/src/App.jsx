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
      <div className="severity-gauge" style={{ textAlign: 'center' }}>
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
        <p style={{ marginTop: '10px', fontSize: '12px' }}>Risk & Confidence</p>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="hero">
        <h1>Diagnóstico de Manutenção</h1>
        <p>Envie os sintomas e receba Causa, Risco e Ação recomendada.</p>
      </header>

      <nav className="tabs" style={{ display: 'flex', gap: '20px', padding: '10px 10% 0', borderBottom: '1px solid #ddd', background: '#fff' }}>
        {['diagnostico', 'historico', 'dashboard', 'novo registro'].map(tab => (
          <button 
            key={tab} 
            onClick={() => setActiveTab(tab)}
            style={{ 
              padding: '10px 20px', border: 'none', background: 'none', cursor: 'pointer',
              borderBottom: activeTab === tab ? '2px solid #004a8c' : 'none',
              fontWeight: activeTab === tab ? 'bold' : 'normal',
              textTransform: 'capitalize'
            }}
          >
            {tab}
          </button>
        ))}
      </nav>

      <main className="container" style={{ display: activeTab === 'diagnostico' ? 'grid' : 'block', padding: '20px 10%' }}>
        {activeTab === 'diagnostico' ? (
          <>
            <form className="panel form" onSubmit={handleSubmit}>
              <label>Equipment Name (equipamento)</label>
              <input value={equipmentName} onChange={(e)=>setEquipmentName(e.target.value)} placeholder="Prensa hidraulica" />

              <label>Symptoms (sintomas)</label>
              <textarea value={symptoms} onChange={(e)=>setSymptoms(e.target.value)} placeholder="Descreva os sintomas..." required rows={6} />

              <label>Machine ID (opcional)</label>
              <input value={machineId} onChange={(e)=>setMachineId(e.target.value)} placeholder="14" />

              <button className="primary" type="submit" disabled={loading}>{loading ? 'Analisando...' : 'Enviar para diagnóstico'}</button>
              {error && <div className="error">{error}</div>}
            </form>

            <section className="panel result">
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <h2>Resultado <small style={{ color: '#1890ff' }}>(para "{equipmentName || 'machine'}")</small></h2>
                {diagnosis && <button className="export">Exportar CSV</button>}
              </div>

              {diagnosis ? (
                <div className="grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                  <div className="card">
                    <h3>Causa provável</h3>
                    {diagnosis.probable_causes?.map((c, i) => (
                      <div key={i} style={{ marginBottom: '15px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                          <span>{c.cause}</span>
                          <span>{c.likelihood}%</span>
                        </div>
                        <div style={{ background: '#eee', height: '8px', borderRadius: '4px', marginTop: '5px' }}>
                          <div style={{ background: '#ff7a45', width: `${c.likelihood}%`, height: '100%', borderRadius: '4px' }} />
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="card">
                    <h3>Risco</h3>
                    <p>Severidade: <strong>{diagnosis.severity}</strong></p>
                    {renderSeverityChart(diagnosis.severity, diagnosis.confidence)}
                  </div>
                </div>
              ) : <p className="muted">Aguardando entrada...</p>}
            </section>
          </>
        ) : (
          <div className="panel" style={{ textAlign: 'center', padding: '50px' }}>
            <h2>{activeTab.toUpperCase()}</h2>
            <p className="muted">Feature in development.</p>
          </div>
        )}
      </main>
    </div>
  )
}