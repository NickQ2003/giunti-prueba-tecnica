import { useState, type FormEvent } from 'react'
import { processFile } from './api'
import type { Questionnaire } from './types'

export default function App() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<Questionnaire | null>(null)
  const [error, setError] = useState('')

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!file || loading) return
    setError('')
    setResult(null)
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
      setResult(await processFile(file))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ocurrió un error inesperado.')
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
          <input id="file" type="file" accept=".pdf,.docx,.xlsx" disabled={loading} onChange={event => { setFile(event.target.files?.[0] ?? null); setResult(null); setError('') }} />
          <p className="hint">Los PDF deben contener texto seleccionable; no se incluye OCR.</p>
          <button type="submit" disabled={!file || loading}>{loading ? 'Procesando…' : 'Procesar documento'}</button>
        </form>
        {loading && <p role="status">Analizando el documento. Esto puede tardar unos segundos.</p>}
        {error && <p className="error" role="alert">{error}</p>}
      </section>
      {result && <section className="card" aria-labelledby="result-title">
        <div className="result-header"><div><h2 id="result-title">Resultado</h2><p>{result.total_items} ítems · idioma: {result.idioma}</p></div><button type="button" onClick={download}>Descargar JSON</button></div>
        <p className="hint">Revisa el resultado antes de usarlo: la extracción automática puede cometer errores.</p>
        <pre><code>{JSON.stringify(result, null, 2)}</code></pre>
      </section>}
    </main>
  )
}
