import React, { useState, useEffect } from 'react'
import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable' // Mudança aqui: importação direta do autoTable

const API_URL = import.meta.env.VITE_API_URL || 'https://manutencao-industrial-julio.squareweb.app'

export default function App() {
  const [activeTab, setActiveTab] = useState('diagnóstico')
  const [symptoms, setSymptoms] = useState('')
  const [equipmentName, setEquipmentName] = useState('')
  const [loading, setLoading] = useState(false)
  const [diagnosis, setDiagnosis] = useState(null)
  const [usuario, setUsuario] = useState(() => localStorage.getItem('maint_user') || 'Julio')
  const [history, setHistory] = useState([])

  useEffect(() => {
    localStorage.setItem('maint_user', usuario)
    fetchHistory()
  }, [usuario])

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_URL}/history?usuario=${usuario}`)
      const data = await res.json()
      setHistory(data)
    } catch (err) {
      console.error("Erro ao buscar histórico:", err)
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/diagnose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          symptoms, 
          equipment_name: equipmentName || 'Equipamento',
          usuario: usuario 
        })
      })
      const json = await res.json()
      setDiagnosis(json.diagnosis)
      fetchHistory()
    } catch (err) {
      alert("Erro na conexão com o servidor.")
    } finally {
      setLoading(false)
    }
  }

  const exportPDF = (item) => {
    const doc = new jsPDF()
    // Resolvemos o problema do item que vem direto da IA vs o que vem do Banco
    const rawData = item.full_data || item
    
    doc.setFontSize(18)
    doc.setTextColor(0, 74, 140)
    doc.text('LAUDO TÉCNICO DE MANUTENÇÃO IA', 20, 20)
    
    doc.setFontSize(10)
    doc.setTextColor(100)
    const dataExibicao = item.date && item.date !== "Recente" ? new Date(item.date).toLocaleString('pt-BR') : "Gerado Agora"
    
    doc.text(`Data: ${dataExibicao}`, 20, 30)
    doc.text(`Responsável: ${item.user || usuario}`, 20, 35)
    doc.text(`Ativo: ${item.equipment || equipmentName}`, 20, 40)

    // Chamada corrigida do autoTable que evita o erro de "not a function"
    autoTable(doc, {
      startY: 50,
      head: [['Campo', 'Detalhes']],
      body: [
        ['Severidade', (item.severity || rawData.severity || 'N/A').toUpperCase()],
        ['Componente Foco', rawData.componente_foco || 'Geral'],
        ['Parecer Técnico', rawData.summary || item.diagnosis || 'Não disponível'],
        ['Impacto Operacional', rawData.impacto_operacional || 'Não informado'],
        ['Segurança LOTO', rawData.seguranca_loto || 'Seguir normas padrão']
      ],
      theme: 'striped',
      headStyles: { fillColor: [0, 74, 140] },
      columnStyles: {
        1: { cellWidth: 130 } // Dá mais espaço para o texto longo do laudo
      },
      styles: { overflow: 'linebreak' } // Garante que as 300 palavras quebrem linha
    })

    doc.save(`Laudo_${item.equipment || 'Analise'}_${usuario}.pdf`)
  }

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
    const c1 = pcts.critical;
    const c2 = c1 + pcts.high;
    const c3 = c2 + pcts.medium;
    return `conic-gradient(#ff4d4f 0% ${c1}%, #ff7a45 ${c1}% ${c2}%, #1890ff ${c2}% ${c3}%, #52c41a ${c3}% 100%)`;
  };

  return (
    <div className="app" style={{ fontFamily: 'Segoe UI, sans-serif', backgroundColor: '#f0f2f5', minHeight: '100vh' }}>
      <header style={{ backgroundColor: '#004a8c', color: 'white', padding: '25px 5%', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ fontSize: '45px' }}>⚙️</div> 
          <div style={{ textAlign: 'left' }}>
            <h1 style={{ margin: 0, fontSize: '24px' }}>Diagnóstico de Manutenção Industrial</h1>
            <p style={{ margin: 0, opacity: 0.8, fontSize: '14px' }}>AI-Powered Reliability Engineering</p>
          </div>
        </div>
        
        <div style={{ textAlign: 'right' }}>
          <label style={{ fontSize: '12px', display: 'block', opacity: 0.8 }}>TÉCNICO RESPONSÁVEL</label>
          <input 
            type="text" 
            value={usuario} 
            onChange={e => setUsuario(e.target.value)}
            style={{ padding: '8px', borderRadius: '4px', border: 'none', fontWeight: 'bold', color: '#004a8c', width: '150px' }}
          />
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
              <label style={{fontWeight:'bold', color:'#555'}}>Equipamento / Ativo</label>
              <input style={{ width: '100%', padding: '12px', margin: '8px 0 20px', borderRadius: '6px', border: '1px solid #ddd' }} value={equipmentName} onChange={e => setEquipmentName(e.target.value)} placeholder="Ex: Bomba de Recalque 02" required />
              
              <label style={{fontWeight:'bold', color:'#555'}}>Relato de Sintomas / Anomalias</label>
              <textarea style={{ width: '100%', padding: '12px', margin: '8px 0 20px', borderRadius: '6px', border: '1px solid #ddd' }} rows={6} value={symptoms} onChange={e => setSymptoms(e.target.value)} placeholder="Descreva ruídos, vibrações, temperatura ou falhas elétricas..." required />
              
              <button disabled={loading} style={{ width: '100%', padding: '15px', background: loading ? '#ccc' : '#004a8c', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight:'bold', fontSize:'16px' }}>
                {loading ? 'PROCESSANDO LAUDO...' : 'GERAR LAUDO TÉCNICO'}
              </button>
            </form>

            <section style={{ background: '#fff', padding: '25px', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '2px solid #f0f2f5', paddingBottom: '15px' }}>
                <h2 style={{ color: '#004a8c', margin: 0 }}>Resultado da Análise</h2>
                {diagnosis && (
                  <button onClick={() => exportPDF(diagnosis)} style={{ background: '#52c41a', color: '#fff', border: 'none', padding: '5px 15px', borderRadius: '4px', cursor: 'pointer' }}>
                    📄 EXPORTAR PDF
                  </button>
                )}
              </div>
              {diagnosis ? (
                <div style={{ marginTop: '20px', lineHeight: '1.6' }}>
                  <p><strong>Severidade:</strong> <span style={{ color: diagnosis.severity === 'critical' ? 'red' : '#faad14', fontWeight:'bold' }}>{diagnosis.severity.toUpperCase()}</span></p>
                  <p><strong>Parecer:</strong> {diagnosis.summary}</p>
                  <div style={{ background: '#f9f9f9', padding: '15px', borderRadius: '8px', marginTop: '15px' }}>
                     <p><strong>Impacto:</strong> {diagnosis.impacto_operacional}</p>
                     <p><strong>Segurança:</strong> {diagnosis.seguranca_loto}</p>
                  </div>
                </div>
              ) : <p style={{ color: '#999', marginTop: '40px', textAlign:'center' }}>Aguardando entrada para diagnóstico...</p>}
            </section>
          </div>
        )}

        {activeTab === 'histórico' && (
          <div style={{ background: '#fff', padding: '30px', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
            <h2 style={{ color: '#004a8c', marginBottom: '25px' }}>Histórico de {usuario}</h2>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead><tr style={{ textAlign: 'left', borderBottom: '2px solid #004a8c', color: '#004a8c' }}><th style={{padding:'10px'}}>Data</th><th>Equipamento</th><th>Severidade</th><th>Ações</th></tr></thead>
              <tbody>
                {history.map(h => (
                  <tr key={h.id} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '15px 10px' }}>{new Date(h.date).toLocaleDateString()}</td>
                    <td>{h.equipment}</td>
                    <td style={{ color: h.severity === 'critical' ? 'red' : '#faad14', fontWeight:'600' }}>{h.severity}</td>
                    <td>
                      <button onClick={() => exportPDF(h)} style={{ cursor: 'pointer', background: 'none', border: '1px solid #004a8c', color: '#004a8c', borderRadius: '4px', padding: '2px 8px' }}>Gerar PDF</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'dashboard' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '30px' }}>
            <div style={{ background: '#fff', padding: '25px', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', textAlign:'center' }}>
              <h3 style={{ color: '#004a8c', marginBottom: '30px' }}>Severidade em {usuario}</h3>
              <div style={{ width: '200px', height: '200px', borderRadius: '50%', background: getSeverityData(), margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ width: '130px', height: '130px', background: 'white', borderRadius: '50%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <span style={{ fontSize: '32px', fontWeight: 'bold', color: '#004a8c' }}>{history.length}</span>
                  <small style={{ color: '#888', textTransform: 'uppercase', fontSize: '10px' }}>Laudos</small>
                </div>
              </div>
            </div>
            <div style={{ background: '#fff', padding: '25px', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
              <h3 style={{ color: '#004a8c', marginBottom: '25px' }}>Volume por Equipamento</h3>
              {Array.from(new Set(history.map(h => h.equipment))).map(equip => {
                const count = history.filter(h => h.equipment === equip).length;
                const pct = (count / (history.length || 1)) * 100;
                return (
                  <div key={equip} style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '15px' }}>
                    <div style={{ width: '120px', fontSize: '12px' }}>{equip}</div>
                    <div style={{ flex: 1, background: '#eee', height: '15px', borderRadius: '10px' }}>
                      <div style={{ width: `${pct}%`, background: '#004a8c', height: '100%', borderRadius: '10px' }} />
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