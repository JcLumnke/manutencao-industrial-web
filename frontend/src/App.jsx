import React, { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'https://manutencao-industrial-julio.squareweb.app'

export default function App() {
  const [activeTab, setActiveTab] = useState('diagnóstico')
  const [symptoms, setSymptoms] = useState('')
  const [machineId, setMachineId] = useState('')
  const [equipmentName, setEquipmentName] = useState('')
  const [loading, setLoading] = useState(false)
  const [diagnosis, setDiagnosis] = useState(null)
  
  // Persistence logic
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
    <div className="app" style={{ fontFamily: 'Segoe UI, sans-serif', backgroundColor: '#f0f2f5', minHeight: '100vh' }}>
      {/* Updated Header with Industrial Icon */}
      <header style={{ backgroundColor: '#004a8c', color: 'white', padding: '30px 10%', display: 'flex', alignItems: 'center', gap: '20px' }}>
        <div style={{ fontSize: '50px' }}>⚙️</div> 
        <div style={{ textAlign: 'left' }}>
          <h1 style={{ margin: 0 }}>Diagnóstico de Manutenção Industrial</h1>
          <p style={{ margin: 0, opacity: 0.8 }}>AI-Powered Failure Analysis</p>
        </div>
      </header>

      <nav style={{ display: 'flex', justifyContent: 'center', background: '#fff', borderBottom: '1px solid #ddd' }}>
        {['diagnóstico', 'histórico', 'dashboard'].map(t => (
          <button key={t} onClick={() => setActiveTab(t)} style={{ padding: '20px', border: 'none', background: 'none', cursor: 'pointer', borderBottom: activeTab === t ? '4px solid #004a8c' : 'none', textTransform: 'uppercase', fontWeight: 'bold', color: activeTab === t ? '#004a8c' : '#666' }}>{t}</button>
        ))}
      </nav>

      <main style={{ maxWidth: '1200px', margin: '30px auto', padding: '0 20px' }}>
        {activeTab === 'diagnóstico' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '30px' }}>
            <form onSubmit={handleSubmit} style={{ background: '#fff', padding: '25px', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
              <label style={{fontWeight:'bold'}}>Nome do Equipamento</label>
              <input style={{ width: '100%', padding: '12px', margin: '10px 0 20px', borderRadius: '6px', border: '1px solid #ccc' }} value={equipmentName} onChange={e => setEquipmentName(e.target.value)} placeholder="Ex: Torno CNC" />
              <label style={{fontWeight:'bold'}}>Sintomas</label>
              <textarea style={{ width: '100%', padding: '12px', margin: '10px 0 20px', borderRadius: '6px', border: '1px solid #ccc' }} rows={6} value={symptoms} onChange={e => setSymptoms(e.target.value)} required />
              <button style={{ width: '100%', padding: '15px', background: '#004a8c', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight:'bold' }}>{loading ? 'ANALISANDO IA...' : 'GERAR DIAGNÓSTICO'}</button>
            </form>

            <section style={{ background: '#fff', padding: '25px', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
              <h2 style={{ borderBottom: '2px solid #eee', paddingBottom: '10px' }}>Resultado {equipmentName && <small style={{color:'#1890ff'}}>({equipmentName})</small>}</h2>
              {diagnosis ? (
                <div style={{ marginTop: '20px' }}>
                  <p><strong>Severidade:</strong> <span style={{ color: diagnosis.severity === 'critical' ? 'red' : 'orange' }}>{diagnosis.severity}</span></p>
                  <p><strong>Resumo:</strong> {diagnosis.summary}</p>
                </div>
              ) : <p style={{ color: '#999', marginTop: '20px' }}>Preencha os sintomas para análise.</p>}
            </section>
          </div>
        )}

        {activeTab === 'histórico' && (
          <div style={{ background: '#fff', padding: '30px', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
            <h2>Registros de Severidade</h2>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '20px' }}>
              <thead><tr style={{ textAlign: 'left', borderBottom: '2px solid #004a8c' }}><th>Data</th><th>Equipamento</th><th>Severidade</th></tr></thead>
              <tbody>
                {history.length > 0 ? history.map(h => (
                  <tr key={h.id} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '15px 0' }}>{h.date}</td>
                    <td>{h.equipment}</td>
                    <td style={{ color: h.severity === 'critical' ? 'red' : 'inherit' }}>{h.severity}</td>
                  </tr>
                )) : <tr><td colSpan="3" style={{ textAlign: 'center', padding: '30px', color: '#999' }}>Nenhum registro no histórico.</td></tr>}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'dashboard' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px' }}>
            <div style={{ background: '#fff', padding: '25px', borderRadius: '12px', textAlign:'center', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
              <h3>Total de Consultas</h3>
              <div style={{ fontSize: '64px', fontWeight: 'bold', color: '#004a8c' }}>{history.length}</div>
            </div>
            <div style={{ background: '#fff', padding: '25px', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
              <h3>Volume por Equipamento</h3>
              {Array.from(new Set(history.map(h => h.equipment))).map(equip => {
                const count = history.filter(h => h.equipment === equip).length;
                const pct = (count / history.length) * 100;
                return (
                  <div key={equip} style={{ marginBottom: '15px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}><span>{equip}</span><span>{count}</span></div>
                    <div style={{ background: '#eee', height: '10px', borderRadius: '5px' }}>
                      <div style={{ background: '#004a8c', width: `${pct}%`, height: '100%', borderRadius: '5px' }} />
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