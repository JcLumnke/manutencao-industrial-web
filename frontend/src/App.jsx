import React, { useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'https://manutencao-industrial-julio.squareweb.app'

function SafeJsonPreview({ data }) {
  return (
    <pre className="raw">{JSON.stringify(data, null, 2)}</pre>
  )
}

export default function App() {
  const [symptoms, setSymptoms] = useState('')
  const [machineId, setMachineId] = useState('')
  const [equipmentName, setEquipmentName] = useState('') // New state for equipment name
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
        // Added equipment_name to the payload
        body: JSON.stringify({ 
          symptoms, 
          equipment_name: equipmentName || 'Not specified',
          machine_id: machineId || undefined 
        })
      })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(`Erro ${res.status}: ${text}`)
      }
      const json = await res.json()
      // backend returns { diagnosis: {...}, raw_output: '...' }
      setDiagnosis(json.diagnosis || json)
    } catch (err) {
      console.error(err)
      setError(err.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  // Function to export diagnosis to CSV
  function exportToCSV() {
    if (!diagnosis) return;
    
    const rows = [
      ["Field", "Value"],
      ["Equipment", equipmentName || "N/A"],
      ["Machine ID", machineId || "N/A"],
      ["Summary", diagnosis.summary || ""],
      ["Severity", diagnosis.severity || ""],
      ["Confidence", diagnosis.confidence || ""],
      ["---", "---"],
      ["Probable Causes", "Likelihood"]
    ];

    if (diagnosis.probable_causes) {
      diagnosis.probable_causes.forEach(c => {
        rows.push([c.cause || c.name || c, `${c.likelihood || 0}%`]);
      });
    }

    const csvContent = "data:text/csv;charset=utf-8," 
      + rows.map(e => e.join(",")).join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `report_${equipmentName || 'machine'}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function renderCauses(list) {
    if (!list || !list.length) return <em>— não informado —</em>
    return (
      <div className="causes-list">
        {list.map((c, i) => {
          const name = c.cause ?? c.name ?? c;
          const pct = c.likelihood ?? 0;
          return (
            <div key={i} style={{ marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                <span>{name}</span>
                <span>{pct}%</span>
              </div>
              {/* Visual progress bar for likelihood */}
              <div style={{ background: '#eee', borderRadius: '4px', height: '8px', marginTop: '4px' }}>
                <div style={{ 
                  background: pct > 70 ? '#ff4d4f' : '#1890ff', 
                  width: `${pct}%`, 
                  height: '100%', 
                  borderRadius: '4px',
                  transition: 'width 1s ease-in-out'
                }} />
              </div>
            </div>
          );
        })}
      </div>
    )
  }

  return (
    <div className="app">
      <header className="hero">
        <h1>Diagnóstico de Manutenção</h1>
        <p className="subtitle">Envie os sintomas e receba Causa, Risco e Ação recomendada.</p>
      </header>

      <main className="container">
        <form className="panel form" onSubmit={handleSubmit}>
          <label>Equipment Name (equipamento)</label>
          <input value={equipmentName} onChange={(e)=>setEquipmentName(e.target.value)} placeholder="Ex: Motor Principal, Prensa Hidráulica..." />

          <label>Symptoms (sintomas)</label>
          <textarea value={symptoms} onChange={(e)=>setSymptoms(e.target.value)} placeholder="Descreva os sintomas da máquina..." required rows={8} />

          <label>Machine ID (opcional)</label>
          <input value={machineId} onChange={(e)=>setMachineId(e.target.value)} placeholder="ID da máquina (ex: M-1234)" />

          <div className="actions">
            <button className="primary" type="submit" disabled={loading}>{loading ? 'Analisando...' : 'Enviar para diagnóstico'}</button>
          </div>

          {error && <div className="error">{error}</div>}
        </form>

        <section className="panel result">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2>Resultado</h2>
            {diagnosis && (
              <button onClick={exportToCSV} className="secondary" style={{ padding: '4px 12px', fontSize: '0.8rem', cursor: 'pointer' }}>
                📥 Exportar CSV
              </button>
            )}
          </div>
          
          {!diagnosis && <p className="muted">Nenhum diagnóstico gerado ainda.</p>}

          {diagnosis && (
            <div className="grid">
              <div className="card">
                <h3>Causa provável</h3>
                {renderCauses(diagnosis.probable_causes)}
              </div>

              <div className="card">
                <h3>Risco</h3>
                <p><strong>Severidade:</strong> <span style={{ color: diagnosis.severity === 'critical' ? 'red' : 'inherit' }}>{diagnosis.severity ?? '—'}</span></p>
                <p><strong>Confiança:</strong> {diagnosis.confidence ? (diagnosis.confidence * 100).toFixed(0) + '%' : '—'}</p>
              </div>

              <div className="card large">
                <h3>Ações recomendadas</h3>
                {diagnosis.recommended_actions && diagnosis.recommended_actions.length ? (
                  <ol>
                    {diagnosis.recommended_actions.map((a, i) => <li key={i}>{a}</li>)}
                  </ol>
                ) : <p className="muted">— não informado —</p>}
              </div>
            </div>
          )}

          {diagnosis && (
            <>
              <h4>Resumo</h4>
              <p className="summary">{diagnosis.summary ?? '—'}</p>

              <details>
                <summary>Mostrar resposta bruta</summary>
                <SafeJsonPreview data={diagnosis} />
              </details>
            </>
          )}
        </section>
      </main>

      <footer className="footer">Conectado a: <a href={API_URL} target="_blank" rel="noreferrer">{API_URL}</a></footer>
    </div>
  )
}