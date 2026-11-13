import { useEffect, useState, type DragEvent, type FormEvent } from 'react'
import { ApiError, previewFile, processFile } from './api'
import PdfPreview from './PdfPreview'
import type { Questionnaire } from './types'

const TYPE_LABELS: Record<Questionnaire['items'][number]['tipo'], string> = {
  escala_likert: 'Escala Likert',
  seleccion_multiple: 'Selección múltiple',
  verdadero_falso: 'Verdadero / Falso',
  desarrollo: 'Respuesta abierta',
  emparejamiento: 'Emparejamiento',
}

function fileSize(bytes: number) {
  return bytes < 1024 * 1024 ? `${Math.max(1, Math.ceil(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export default function App() {
  const [file, setFile] = useState<File | null>(null)
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<Questionnaire | null>(null)
  const [error, setError] = useState('')
  const [requestId, setRequestId] = useState<string | null>(null)
  const [unmatchedStatements, setUnmatchedStatements] = useState(0)
  const [languageDisagreement, setLanguageDisagreement] = useState(false)
  const [preview, setPreview] = useState<{ text: string; truncated: boolean } | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewError, setPreviewError] = useState('')
  const [view, setView] = useState<'items' | 'json'>('items')
  const [copyStatus, setCopyStatus] = useState('')
  const isPdf = !!file && /\.pdf$/i.test(file.name)

  useEffect(() => {
    setPreview(null)
    setPreviewError('')
    if (!file || /\.pdf$/i.test(file.name)) {
      setPreviewLoading(false)
      return
    }
    const controller = new AbortController()
    let active = true
    setPreviewLoading(true)
    previewFile(file, controller.signal)
      .then(data => { if (active) setPreview(data) })
      .catch(err => { if (active) setPreviewError(err instanceof Error ? err.message : 'No se pudo cargar la vista previa.') })
      .finally(() => { if (active) setPreviewLoading(false) })
    return () => { active = false; controller.abort() }
  }, [file])

  function chooseFile(candidate: File | null) {
    if (loading) return
    setError('')
    setRequestId(null)
    setResult(null)
    setUnmatchedStatements(0)
    setLanguageDisagreement(false)
    setCopyStatus('')
    if (candidate && !/\.(pdf|docx|xlsx)$/i.test(candidate.name)) {
      setFile(null)
      setError('Usa un archivo PDF, DOCX o XLSX.')
    } else if (candidate && candidate.size > 10 * 1024 * 1024) {
      setFile(null)
      setError('El archivo supera el límite de 10 MB.')
    } else {
      setFile(candidate)
    }
  }

  function drop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault()
    setDragging(false)
    if (event.dataTransfer.files.length > 1) {
      chooseFile(null)
      setError('Selecciona un solo archivo a la vez.')
      return
    }
    chooseFile(event.dataTransfer.files[0] ?? null)
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!file || loading) return
    setError('')
    setRequestId(null)
    setResult(null)
    setUnmatchedStatements(0)
    setLanguageDisagreement(false)
    setCopyStatus('')
    setView('items')
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

  async function copy() {
    if (!result) return
    try {
      await navigator.clipboard.writeText(JSON.stringify(result, null, 2))
      setCopyStatus('JSON copiado')
    } catch {
      setCopyStatus('No se pudo copiar. Puedes descargar el JSON.')
    }
  }

  return <div className="app-shell">
    <header className="topbar">
      <a className="brand" href="/" aria-label="Inicio: extractor de cuestionarios"><span className="brand-mark">g<span>.</span></span><span>giunti <b>tools</b></span></a>
      <span className="topbar-note"><span className="status-dot" /> EXTRACTOR DE CUESTIONARIOS</span>
    </header>
    <main className="workspace">
      <div className="page-heading"><div><div className="eyebrow"><span /> HERRAMIENTAS / EXTRACCIÓN</div><h1>Del documento <em>al dato.</em></h1><p>Transforma cuestionarios en papel en información lista para trabajar.</p></div><div className="heading-badge">✦ &nbsp; ASISTIDO POR IA</div></div>

      <div className="workflow">
        <section className="panel upload-panel" aria-labelledby="upload-title">
          <div className="section-heading"><div><span className="step">01</span><h2 id="upload-title">Tu documento</h2></div><span className="section-label">CARGA DE ARCHIVO</span></div>
          <p className="section-description">Selecciona un cuestionario para comenzar.</p>
          <form onSubmit={submit}>
            <label htmlFor="file" className={`dropzone${dragging ? ' dragging' : ''}${loading ? ' disabled' : ''}`} onDragOver={event => { event.preventDefault(); if (!loading) setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={drop}>
              <span className="upload-icon" aria-hidden="true">↑</span>
              <strong>Arrastra tu archivo aquí</strong>
              <span>o <span className="upload-link">explora tus archivos</span></span>
              <small>PDF, DOCX o XLSX · máximo 10 MB</small>
            </label>
            <input className="file-input" id="file" aria-label="Archivo PDF, DOCX o XLSX" type="file" accept=".pdf,.docx,.xlsx" disabled={loading} onChange={event => { chooseFile(event.target.files?.[0] ?? null); event.target.value = '' }} />
            {file && <div className="selected-file"><span className="file-icon" aria-hidden="true">▤</span><div className="file-details"><strong>{file.name}</strong><span>{fileSize(file.size)} · listo para procesar</span></div><button type="button" className="remove-button" disabled={loading} aria-label="Quitar archivo" onClick={() => chooseFile(null)}>×</button></div>}
            <div className="privacy-note"><span aria-hidden="true">◈</span><p><strong>Uso responsable.</strong> La vista previa de DOCX y XLSX se envía al servidor; al procesar, el texto se envía a un proveedor externo de IA. Usa solo material inventado o público, sin datos personales ni pruebas comerciales.</p></div>
            <button className="process-button" type="submit" disabled={!file || loading}>{loading ? <><span className="spinner" /> Procesando documento…</> : <>Procesar documento <span aria-hidden="true">↗</span></>}</button>
          </form>
          {loading && <p className="process-status" role="status">Analizando el documento. Esto puede tardar unos segundos.</p>}
          {error && <p className="error" role="alert">{error}{requestId && <><br />Referencia: {requestId}</>}</p>}
        </section>

        <section className="panel preview-panel" aria-labelledby="preview-title">
          <div className="section-heading"><div><span className="step">02</span><h2 id="preview-title">Vista previa</h2></div><span className="section-label">DOCUMENTO ORIGINAL</span></div>
          {!file ? <div className="preview-empty"><div className="empty-document" aria-hidden="true"><span /><span /><span /></div><strong>Aún no hay documento</strong><p>Tu vista previa aparecerá aquí cuando selecciones un archivo.</p><div className="format-list"><span>PDF</span><span>DOCX</span><span>XLSX</span></div></div> : <div className="preview-content">
            <div className="preview-filebar"><span className="file-icon small" aria-hidden="true">▤</span><div><strong>{file.name}</strong><span>{isPdf ? 'Vista visual en tu navegador' : 'Texto extraído del documento'}</span></div></div>
            {isPdf ? <PdfPreview file={file} /> : <>
              {previewLoading && <p className="preview-loading" role="status">Extrayendo vista previa…</p>}
              {previewError && <p className="preview-error" role="status">{previewError} Puedes intentar procesar el documento.</p>}
              {preview && <><pre className="document-text">{preview.text}</pre><p className="hint preview-caption">Vista de texto; el formato y las tablas pueden diferir del original.{preview.truncated && ' Vista previa limitada a los primeros 40.000 caracteres.'}</p></>}
            </>}
          </div>}
        </section>
      </div>

      <section className="panel result-panel" aria-labelledby="result-title">
        <div className="section-heading result-heading"><div><span className="step">03</span><h2 id="result-title">Resultado</h2>{result && <span className="result-count">{result.total_items} ítems · {result.idioma.toUpperCase()}</span>}</div>{result && <div className="result-actions"><button className="secondary-button" type="button" onClick={copy}>Copiar JSON</button><button className="download-button" type="button" onClick={download}>Descargar JSON <span aria-hidden="true">↓</span></button></div>}</div>
        {!result ? <div className="result-empty"><span className="result-empty-icon" aria-hidden="true">{loading ? '◌' : '{ }'}</span><div><strong>{loading ? 'Estamos procesando tu documento' : 'Aquí empieza la estructura'}</strong><p>{loading ? 'La vista previa seguirá disponible mientras esperas.' : 'Cuando el procesamiento termine, encontrarás aquí los ítems y su JSON.'}</p></div></div> : <div className="result-body">
          <div className="result-topline"><div><p className="result-title-label">CUESTIONARIO DETECTADO</p><h3>{result.titulo}</h3></div><div className="view-switch" aria-label="Vista del resultado"><button type="button" aria-pressed={view === 'items'} onClick={() => setView('items')}>Ítems</button><button type="button" aria-pressed={view === 'json'} onClick={() => setView('json')}>JSON</button></div></div>
          <p className="hint">Revisa el resultado antes de usarlo: la extracción automática puede cometer errores.</p>
          {copyStatus && <p className="copy-status" role="status">{copyStatus}</p>}
          {languageDisagreement && <p className="notice" role="status">El idioma detectado por la IA no coincide con la pista lingüística automática. Revisa el documento: ambas detecciones pueden equivocarse.</p>}
          {unmatchedStatements > 0 && <p className="notice" role="status">No se pudieron localizar literalmente {unmatchedStatements} enunciados en el texto extraído. Comprueba el documento original; los cambios de formato pueden afectar esta verificación.</p>}
          {view === 'json' ? <pre className="json-output"><code>{JSON.stringify(result, null, 2)}</code></pre> : <div className="item-list">{result.items.map(item => <article className="question-card" key={item.numero}>
            <div className="question-meta"><span>ÍTEM {String(item.numero).padStart(2, '0')}</span><span className="type-badge">{TYPE_LABELS[item.tipo]}</span></div>
            <h4>{item.enunciado}</h4>
            {item.alternativas.length > 0 && <ul className="alternatives">{item.alternativas.map((alternative, index) => <li key={`${String(alternative.valor)}-${index}`}><span>{alternative.valor}</span>{alternative.texto}</li>)}</ul>}
            {item.respuesta_correcta !== null && <p className="correct-answer">Respuesta indicada: {String(item.respuesta_correcta)}</p>}
          </article>)}</div>}
        </div>}
      </section>
      <footer><span>GIUNTI <b>TOOLS</b> · EXTRACTOR DE CUESTIONARIOS</span><span>Construido para transformar información en posibilidades.</span></footer>
    </main>
  </div>
}
