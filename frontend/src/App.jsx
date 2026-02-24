import React, { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'https://manutencao-industrial-julio.squareweb.app'

export default function App() {
  const [activeTab, setActiveTab] = useState('diagnóstico')
  const [symptoms, setSymptoms] = useState('')
  const [machineId, setMachineId] = useState('')
  const [equipmentName, setEquipmentName] = useState('')
  const [loading, setLoading] = useState(false)
  const [diagnosis, setDiagnosis] = useState(null)
  
  // Logic to persist data in LocalStorage
  const [history, setHistory] = useState(() => {
    const saved = localStorage.getItem('maint_history');
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    localStorage.setItem('maint_history', JSON.stringify(history));
  }, [history]);

  async function handleSubmit(e) {
    e.preventDefault()
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
      const json = await res.json()
      const newDiagnosis = json.diagnosis || json
      
      setDiagnosis(newDiagnosis)
      
      // Add to history dynamically
      const newEntry = {
        id: Date.now(),
        date: new Date().toLocaleDateString('pt-BR'),
        equipment: equipmentName || 'General Machine',
        severity: newDiagnosis.severity || 'low',
        summary: newDiagnosis.summary
      }
      setHistory([newEntry, ...history])
      
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app" style={{ fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif', backgroundColor: '#f4f7f6', minHeight: '100vh' }}>
      <header style={{ backgroundColor: '#004a8c', color: 'white', padding: '20px', textAlign: 'center' }}>
        <h1>Diagnóstico de Manutenção</h1>
      </header>

      <nav style={{ display: 'flex', justifyContent: 'center', background: '#fff', borderBottom: '1px solid #ddd' }}>
        {['diagnóstico', 'histórico', 'dashboard'].map(t => (
          <button key={t} onClick={() => setActiveTab(t)} style={{ padding: '20px', border: 'none', background: 'none', cursor: 'pointer', borderBottom: activeTab === t ? '4px solid #004a8c' : 'none', textTransform: 'uppercase', fontWeight: 'bold', color: activeTab === t ? '#004a8c' : '#666' }}>{t}</button>
        ))}
      </nav>

      <main style={{ maxWidth: '1200px', margin: '30px auto', padding: '0 20px' }}>
        {activeTab === 'diagnóstico' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '30px' }}>
            <form onSubmit={handleSubmit} style={{ background: '#fff', padding: '25px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
              <label style={{fontWeight:'bold'}}>Equipamento</label>
              <input style={{ width: '100%', padding: '10px', margin: '10px 0 20px' }} value={equipmentName} onChange={e => setEquipmentName(e.target.value)} placeholder="Ex: Motor CA" />
              <label style={{fontWeight:'bold'}}>Sintomas</label>
              <textarea style={{ width: '100%', padding: '10px', margin: '10px 0 20px' }} rows={6} value={symptoms} onChange={e => setSymptoms(e.target.value)} required />
              <button style={{ width: '100%', padding: '15px', background: '#004a8c', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight:'bold' }}>{loading ? 'Consultando Gemini...' : 'GERAR DIAGNÓSTICO'}</button>
            </form>

            <section style={{ background: '#fff', padding: '25px', borderRadius: '8px' }}>
              <h2>Laudo Atual</h2>
              {diagnosis ? (
                <div>
                  <p><strong>Severidade:</strong> {diagnosis.severity}</p>
                  <p><strong>Resumo:</strong> {diagnosis.summary}</p>
                  <div style={{ marginTop: '20px', padding: '15px', background: '#e6f7ff', borderLeft: '5px solid #1890ff' }}>
                    <strong>Ações:</strong> {diagnosis.recommended_actions?.join(', ')}
                  </div>
                </div>
              ) : <p>Preencha os dados ao lado.</p>}
            </section>
          </div>
        )}

        {activeTab === 'histórico' && (
          <div style={{ background: '#fff', padding: '30px', borderRadius: '8px' }}>
            <h2>Registros de Consultas</h2>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '20px' }}>
              <thead><tr style={{ textAlign: 'left', borderBottom: '2px solid #004a8c' }}><th>Data</th><th>Equipamento</th><th>Severidade</th></tr></thead>
              <tbody>{history.map(h => (<tr key={h.id} style={{ borderBottom: '1px solid #eee' }}><td style={{ padding: '15px 0' }}>{h.date}</td><td>{h.equipment}</td><td>{h.severity}</td></tr>))}</tbody>
            </table>
          </div>
        )}

        {activeTab === 'dashboard' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px' }}>
            <div style={{ background: '#fff', padding: '20px', borderRadius: '8px', textAlign:'center' }}>
              <h3>Total de Consultas</h3>
              <div style={{ fontSize: '48px', fontWeight: 'bold', color: '#004a8c' }}>{history.length}</div>
            </div>
            <div style={{ background: '#fff', padding: '20px', borderRadius: '8px' }}>
              <h3>Distribuição de Severidade</h3>
              {['critical', 'high', 'medium', 'low'].map(sev => {
                const count = history.filter(h => h.severity === sev).length;
                const pct = history.length > 0 ? (count / history.length) * 100 : 0;
                return (
                  <div key={sev} style={{ marginBottom: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}><span>{sev}</span><span>{count}</span></div>
                    <div style={{ background: '#eee', height: '10px', borderRadius: '5px' }}>
                      <div style={{ background: sev === 'critical' ? 'red' : '#1890ff', width: `${pct}%`, height: '100%', borderRadius: '5px' }} />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}