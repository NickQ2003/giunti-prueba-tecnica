import { useState, type FormEvent } from 'react'
import { ApiError, processFile } from './api'
import type { Questionnaire } from './types'

export default function App() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<Questionnaire | null>(null)
  const [error, setError] = useState('')
  const [requestId, setRequestId] = useState<string | null>(null)
  const [unmatchedStatements, setUnmatchedStatements] = useState(0)
  const [languageDisagreement, setLanguageDisagreement] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!file || loading) return
    setError('')
    setRequestId(null)
    setResult(null)
    setUnmatchedStatements(0)
    setLanguageDisagreement(false)
    if (!/\.(pdf|docx|xlsx)$/i.test(file.name)) {
      setError('Usa un archivo PDF, DOCX o XLSX.')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('El archivo supera el límite de 10 MB.')
      return
    }
    setLoading(true)
    try {
      const processed = await processFile(file)
      setResult(processed.questionnaire)
      setUnmatchedStatements(processed.unmatchedStatements)
      setLanguageDisagreement(processed.languageDisagreement)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ocurrió un error inesperado.')
      setRequestId(err instanceof ApiError ? err.requestId : null)
    } finally {
      setLoading(false)
    }
  }

  function download() {
    if (!result) return
    const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' }))
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'cuestionario.json'
    anchor.click()
    setTimeout(() => URL.revokeObjectURL(url), 0)
  }

  return (
    <main className="container">
      <header>
        <p className="eyebrow">GIUNTI · PRUEBA TÉCNICA</p>
        <h1>Extractor de cuestionarios</h1>
        <p>Convierte un documento en ítems y alternativas estructurados en JSON.</p>
      </header>
      <section className="card" aria-labelledby="upload-title">
        <h2 id="upload-title">Sube tu documento</h2>
        <p className="notice"><strong>Privacidad:</strong> el texto se envía a un proveedor externo de IA. Usa solo material inventado o de dominio público, sin datos personales ni pruebas comerciales.</p>
        <form onSubmit={submit}>
          <label htmlFor="file">Archivo PDF, DOCX o XLSX <span>(máximo 10 MB)</span></label>
          <input id="file" type="file" accept=".pdf,.docx,.xlsx" disabled={loading} onChange={event => { setFile(event.target.files?.[0] ?? null); setResult(null); setError(''); setRequestId(null) }} />
          <p className="hint">Los PDF deben contener texto seleccionable; no se incluye OCR.</p>
          <button type="submit" disabled={!file || loading}>{loading ? 'Procesando…' : 'Procesar documento'}</button>
        </form>
        {loading && <p role="status">Analizando el documento. Esto puede tardar unos segundos.</p>}
        {error && <p className="error" role="alert">{error}{requestId && <><br />Referencia: {requestId}</>}</p>}
      </section>
      {result && <section className="card" aria-labelledby="result-title">
        <div className="result-header"><div><h2 id="result-title">Resultado</h2><p>{result.total_items} ítems · idioma: {result.idioma}</p></div><button type="button" onClick={download}>Descargar JSON</button></div>
        <p className="hint">Revisa el resultado antes de usarlo: la extracción automática puede cometer errores.</p>
        {languageDisagreement && <p className="notice" role="status">El idioma detectado por la IA no coincide con la pista lingüística automática. Revisa el documento: ambas detecciones pueden equivocarse.</p>}
        {unmatchedStatements > 0 && <p className="notice" role="status">No se pudieron localizar literalmente {unmatchedStatements} enunciados en el texto extraído. Comprueba el documento original; los cambios de formato pueden afectar esta verificación.</p>}
        <pre><code>{JSON.stringify(result, null, 2)}</code></pre>
      </section>}
    </main>
  )
}
