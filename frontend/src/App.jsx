import React, { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'https://manutencao-industrial-julio.squareweb.app'

export default function App() {
  const [activeTab, setActiveTab] = useState('diagnóstico')
  const [symptoms, setSymptoms] = useState('')
  const [machineId, setMachineId] = useState('')
  const [equipmentName, setEquipmentName] = useState('')
  const [loading, setLoading] = useState(false)
  const [diagnosis, setDiagnosis] = useState(null)
  
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

  // Helper for Severity Pie Chart
  const getSeverityData = () => {
    const counts = { critical: 0, high: 0, medium: 0, low: 0 };
    history.forEach(h => { if (counts[h.severity] !== undefined) counts[h.severity]++; });
    const total = history.length || 1;
    const pcts = {
      critical: (counts.critical / total) * 100,
      high: (counts.high / total) * 100,
      medium: (counts.medium / total) * 100,
      low: (counts.low / total) * 100
    };
    // Cumulative for conic-gradient
    const c1 = pcts.critical;
    const c2 = c1 + pcts.high;
    const c3 = c2 + pcts.medium;
    return `conic-gradient(#ff4d4f 0% ${c1}%, #ff7a45 ${c1}% ${c2}%, #1890ff ${c2}% ${c3}%, #52c41a ${c3}% 100%)`;
  };

  return (
    <div className="app" style={{ fontFamily: 'Segoe UI, sans-serif', backgroundColor: '#f0f2f5', minHeight: '100vh' }}>
      <header style={{ backgroundColor: '#004a8c', color: 'white', padding: '25px 5%', display: 'flex', alignItems: 'center', gap: '20px' }}>
        <div style={{ fontSize: '45px' }}>⚙️</div> 
        <div style={{ textAlign: 'left' }}>
          <h1 style={{ margin: 0, fontSize: '24px' }}>Diagnóstico de Manutenção Industrial</h1>
          <p style={{ margin: 0, opacity: 0.8, fontSize: '14px' }}>AI-Powered Failure Analysis</p>
        </div>
      </header>

      <nav style={{ display: 'flex', justifyContent: 'center', background: '#fff', borderBottom: '1px solid #ddd' }}>
        {['diagnóstico', 'histórico', 'dashboard'].map(t => (
          <button key={t} onClick={() => setActiveTab(t)} style={{ padding: '18px 25px', border: 'none', background: 'none', cursor: 'pointer', borderBottom: activeTab === t ? '4px solid #004a8c' : 'none', textTransform: 'uppercase', fontWeight: 'bold', color: activeTab === t ? '#004a8c' : '#666' }}>{t}</button>
        ))}
      </nav>

      <main style={{ maxWidth: '1200px', margin: '30px auto', padding: '0 20px' }}>
        {activeTab === 'diagnóstico' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '30px' }}>
            <form onSubmit={handleSubmit} style={{ background: '#fff', padding: '25px', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
              <label style={{fontWeight:'bold', color:'#555'}}>Equipamento</label>
              <input style={{ width: '100%', padding: '12px', margin: '8px 0 20px', borderRadius: '6px', border: '1px solid #ddd' }} value={equipmentName} onChange={e => setEquipmentName(e.target.value)} placeholder="Ex: Motor CA" />
              <label style={{fontWeight:'bold', color:'#555'}}>Sintomas Detectados</label>
              <textarea style={{ width: '100%', padding: '12px', margin: '8px 0 20px', borderRadius: '6px', border: '1px solid #ddd' }} rows={6} value={symptoms} onChange={e => setSymptoms(e.target.value)} required />
              <button style={{ width: '100%', padding: '15px', background: '#004a8c', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight:'bold', fontSize:'16px' }}>{loading ? 'ANALISANDO IA...' : 'GERAR DIAGNÓSTICO'}</button>
            </form>

            <section style={{ background: '#fff', padding: '25px', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
              <h2 style={{ borderBottom: '2px solid #f0f2f5', paddingBottom: '15px', color: '#004a8c' }}>Resultado {equipmentName && <small style={{color:'#1890ff'}}>({equipmentName})</small>}</h2>
              {diagnosis ? (
                <div style={{ marginTop: '20px', lineHeight: '1.6' }}>
                  <p><strong>Severidade:</strong> <span style={{ color: diagnosis.severity === 'critical' ? 'red' : '#faad14', textTransform: 'uppercase', fontWeight:'bold' }}>{diagnosis.severity}</span></p>
                  <p><strong>Resumo Técnico:</strong> {diagnosis.summary}</p>
                </div>
              ) : <p style={{ color: '#999', marginTop: '40px', textAlign:'center' }}>Aguardando entrada de dados para análise do Gemini.</p>}
            </section>
          </div>
        )}

        {activeTab === 'histórico' && (
          <div style={{ background: '#fff', padding: '30px', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
            <h2 style={{ color: '#004a8c', marginBottom: '25px' }}>Registros de Consultas</h2>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead><tr style={{ textAlign: 'left', borderBottom: '2px solid #004a8c', color: '#004a8c' }}><th style={{padding:'10px'}}>Data</th><th>Equipamento</th><th>Severidade</th></tr></thead>
              <tbody>
                {history.length > 0 ? history.map(h => (
                  <tr key={h.id} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '15px 10px' }}>{h.date}</td>
                    <td>{h.equipment}</td>
                    <td style={{ color: h.severity === 'critical' ? 'red' : '#faad14', fontWeight:'600' }}>{h.severity}</td>
                  </tr>
                )) : <tr><td colSpan="3" style={{ textAlign: 'center', padding: '40px', color: '#999' }}>Nenhum diagnóstico realizado ainda.</td></tr>}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'dashboard' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '30px' }}>
            {/* Severity Pie Chart with Total in Center */}
            <div style={{ background: '#fff', padding: '25px', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', textAlign:'center' }}>
              <h3 style={{ color: '#004a8c', marginBottom: '30px' }}>Distribuição de Severidade</h3>
              <div style={{ 
                width: '200px', height: '200px', borderRadius: '50%',
                background: getSeverityData(),
                margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: '0 4px 10px rgba(0,0,0,0.1)'
              }}>
                <div style={{ width: '130px', height: '130px', background: 'white', borderRadius: '50%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <span style={{ fontSize: '32px', fontWeight: 'bold', color: '#004a8c' }}>{history.length}</span>
                  <small style={{ color: '#888', textTransform: 'uppercase', fontSize: '10px' }}>Consultas</small>
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'center', gap: '15px', marginTop: '25px', fontSize: '12px' }}>
                {[['Crítica','#ff4d4f'], ['Alta','#ff7a45'], ['Média','#1890ff'], ['Baixa','#52c41a']].map(l => (
                  <div key={l[0]} style={{ display:'flex', alignItems:'center', gap:'5px' }}><div style={{width:'12px', height:'12px', background:l[1], borderRadius:'2px'}}/>{l[0]}</div>
                ))}
              </div>
            </div>

            {/* Equipment Volume Horizontal Chart */}
            <div style={{ background: '#fff', padding: '25px', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
              <h3 style={{ color: '#004a8c', marginBottom: '25px' }}>Volume por Equipamento</h3>
              {Array.from(new Set(history.map(h => h.equipment))).map(equip => {
                const count = history.filter(h => h.equipment === equip).length;
                const pct = history.length > 0 ? (count / history.length) * 100 : 0;
                return (
                  <div key={equip} style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '20px' }}>
                    <div style={{ width: '140px', fontWeight: 'bold', fontSize: '13px', color: '#444', textAlign: 'right', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{equip}</div>
                    <div style={{ flex: 1, background: '#f0f2f5', height: '24px', borderRadius: '4px', position: 'relative' }}>
                      <div style={{ background: '#004a8c', width: `${pct}%`, height: '100%', borderRadius: '4px', transition: 'width 0.8s ease' }} />
                      <span style={{ position: 'absolute', right: '10px', top: '2px', fontSize: '12px', fontWeight: 'bold', color: pct > 90 ? '#fff' : '#004a8c' }}>{count}</span>
                    </div>
                  </div>
                )
              })}
              {history.length === 0 && <p style={{ textAlign: 'center', color: '#999', marginTop: '40px' }}>Realize diagnósticos para ver este gráfico.</p>}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}