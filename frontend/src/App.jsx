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
          width: '140px', height: '140px', borderRadius: '50%',
          background: `conic-gradient(${color} ${confPct}%, #eee 0)`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto',
          boxShadow: '0 4px 10px rgba(0,0,0,0.1)'
        }}>
          <div style={{ width: '110px', height: '110px', background: 'white', borderRadius: '50%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ fontSize: '24px', fontWeight: 'bold', color: '#333' }}>{confPct}%</span>
            <small style={{ fontSize: '12px', color: '#666', textTransform: 'uppercase' }}>{severity}</small>
          </div>
        </div>
        <p style={{ marginTop: '15px', fontSize: '14px', fontWeight: '600', color: '#555' }}>Risco e Confiança</p>
      </div>
    );
  }

  return (
    <div className="app" style={{ fontFamily: 'sans-serif', backgroundColor: '#f4f7f6', minHeight: '100vh' }}>
      <header className="hero" style={{ backgroundColor: '#004a8c', color: 'white', padding: '40px 20px', textAlign: 'center' }}>
        <h1 style={{ margin: 0 }}>Diagnóstico de Manutenção</h1>
        <p style={{ opacity: 0.9 }}>Análise Industrial com Inteligência Artificial</p>
      </header>

      <nav className="tabs" style={{ display: 'flex', justifyContent: 'center', gap: '40px', background: '#fff', borderBottom: '1px solid #ddd', padding: '0 20px' }}>
        {['diagnóstico', 'histórico', 'dashboard'].map(tab => (
          <button 
            key={tab} 
            onClick={() => setActiveTab(tab)}
            style={{ 
              padding: '20px 10px', border: 'none', background: 'none', cursor: 'pointer',
              borderBottom: activeTab === tab ? '4px solid #004a8c' : '4px solid transparent',
              fontWeight: activeTab === tab ? 'bold' : 'normal',
              textTransform: 'uppercase', color: activeTab === tab ? '#004a8c' : '#666',
              transition: 'all 0.3s'
            }}
          >
            {tab}
          </button>
        ))}
      </nav>

      <main className="container" style={{ maxWidth: '1200px', margin: '0 auto', padding: '30px 20px' }}>
        {activeTab === 'diagnóstico' ? (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '30px' }}>
            <form className="panel form" onSubmit={handleSubmit} style={{ background: 'white', padding: '25px', borderRadius: '8px', boxShadow: '0 2px 5px rgba(0,0,0,0.05)', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: '#444' }}>Nome do Equipamento</label>
                <input style={{ width: '100%', padding: '12px', borderRadius: '4px', border: '1px solid #ccc' }} value={equipmentName} onChange={(e)=>setEquipmentName(e.target.value)} placeholder="Ex: Prensa Hidráulica" />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: '#444' }}>Sintomas</label>
                <textarea style={{ width: '100%', padding: '12px', borderRadius: '4px', border: '1px solid #ccc' }} value={symptoms} onChange={(e)=>setSymptoms(e.target.value)} placeholder="Descreva o que está acontecendo..." required rows={8} />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: '#444' }}>ID da Máquina (Opcional)</label>
                <input style={{ width: '100%', padding: '12px', borderRadius: '4px', border: '1px solid #ccc' }} value={machineId} onChange={(e)=>setMachineId(e.target.value)} placeholder="Ex: M-102" />
              </div>

              <button className="primary" type="submit" disabled={loading} style={{ padding: '15px', backgroundColor: '#004a8c', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
                {loading ? 'Analisando dados...' : 'Gerar Diagnóstico'}
              </button>
              {error && <div style={{ color: 'red', fontSize: '14px' }}>{error}</div>}
            </form>

            <section className="panel result" style={{ background: 'white', padding: '25px', borderRadius: '8px', boxShadow: '0 2px 5px rgba(0,0,0,0.05)' }}>
              <h2 style={{ borderBottom: '2px solid #f0f0f0', paddingBottom: '10px' }}>
                Resultado <span style={{ color: '#1890ff', fontSize: '18px' }}>{equipmentName ? `para ${equipmentName}` : ''}</span>
              </h2>
              
              {diagnosis ? (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '25px', marginTop: '20px' }}>
                  <div>
                    <h3 style={{ fontSize: '16px', color: '#333' }}>Causas Prováveis</h3>
                    {diagnosis.probable_causes?.map((c, i) => (
                      <div key={i} style={{ marginBottom: '18px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '5px' }}>
                          <span>{c.cause}</span>
                          <span style={{ fontWeight: 'bold' }}>{c.likelihood}%</span>
                        </div>
                        <div style={{ background: '#eee', height: '10px', borderRadius: '5px' }}>
                          <div style={{ background: 'linear-gradient(90deg, #004a8c, #1890ff)', width: `${c.likelihood}%`, height: '100%', borderRadius: '5px' }} />
                        </div>
                      </div>
                    ))}
                  </div>
                  <div>
                    <h3 style={{ fontSize: '16px', color: '#333', textAlign: 'center' }}>Avaliação de Risco</h3>
                    {renderSeverityChart(diagnosis.severity, diagnosis.confidence)}
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '50px', color: '#999' }}>
                  <p>Aguardando a descrição dos sintomas para gerar o laudo técnico.</p>
                </div>
              )}
            </section>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '100px', background: 'white', borderRadius: '8px', boxShadow: '0 2px 5px rgba(0,0,0,0.05)' }}>
            <h2 style={{ textTransform: 'uppercase', color: '#004a8c' }}>{activeTab}</h2>
            <p style={{ color: '#999' }}>Integração com banco de dados em processamento.</p>
          </div>
        )}
      </main>
    </div>
  )
}