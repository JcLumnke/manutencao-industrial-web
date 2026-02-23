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
        body: JSON.stringify({ symptoms, machine_id: machineId || undefined })
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

  function renderCauses(list) {
    if (!list || !list.length) return <em>— não informado —</em>
    return (
      <ul>
        {list.map((c, i) => (
          <li key={i}>{c.cause ?? c.name ?? c} {c.likelihood ? `(${c.likelihood}%)` : ''}</li>
        ))}
      </ul>
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
          <h2>Resultado</h2>
          {!diagnosis && <p className="muted">Nenhum diagnóstico gerado ainda.</p>}

          {diagnosis && (
            <div className="grid">
              <div className="card">
                <h3>Causa provável</h3>
                {renderCauses(diagnosis.probable_causes)}
              </div>

              <div className="card">
                <h3>Risco</h3>
                <p><strong>Severidade:</strong> {diagnosis.severity ?? '—'}</p>
                <p><strong>Confiança:</strong> {diagnosis.confidence ?? '—'}</p>
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
