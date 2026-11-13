import { useEffect, useRef, useState } from 'react'
import type { PDFDocumentLoadingTask, PDFDocumentProxy, RenderTask } from 'pdfjs-dist'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

export default function PdfPreview({ file }: { file: File }) {
  const canvas = useRef<HTMLCanvasElement>(null)
  const [document, setDocument] = useState<PDFDocumentProxy | null>(null)
  const [page, setPage] = useState(1)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    let task: PDFDocumentLoadingTask | undefined
    setDocument(null)
    setPage(1)
    setError('')

    async function load() {
      try {
        const pdfjs = await import('pdfjs-dist')
        const bytes = await file.arrayBuffer()
        if (cancelled) return
        pdfjs.GlobalWorkerOptions.workerSrc = workerUrl
        task = pdfjs.getDocument({ data: bytes, disableAutoFetch: true })
        const loaded = await task.promise
        if (loaded.numPages > 200) throw new Error('page limit')
        if (!cancelled) setDocument(loaded)
      } catch {
        if (!cancelled) setError('No se pudo mostrar el PDF. Verifica que no esté protegido o dañado.')
      }
    }

    void load()
    return () => {
      cancelled = true
      if (task) void task.destroy().catch(() => {})
    }
  }, [file])

  useEffect(() => {
    if (!document || !canvas.current) return
    let cancelled = false
    let renderTask: RenderTask | undefined
    const target = canvas.current

    async function renderPage() {
      try {
        const pdfPage = await document!.getPage(page)
        if (cancelled) return
        const base = pdfPage.getViewport({ scale: 1 })
        const scale = Math.min(1.5, 760 / base.width, Math.sqrt(2_000_000 / (base.width * base.height)))
        const viewport = pdfPage.getViewport({ scale })
        target.width = Math.ceil(viewport.width)
        target.height = Math.ceil(viewport.height)
        renderTask = pdfPage.render({ canvas: target, viewport })
        await renderTask.promise
      } catch {
        if (!cancelled) setError('No se pudo mostrar esta página del PDF.')
      }
    }

    void renderPage()
    return () => { cancelled = true; renderTask?.cancel() }
  }, [document, page])

  if (error) return <p className="preview-error" role="status">{error}</p>
  if (!document) return <p className="preview-loading" role="status">Preparando vista previa del PDF…</p>

  return <>
    <div className="pdf-toolbar">
      <button type="button" className="icon-button" disabled={page <= 1} onClick={() => setPage(page - 1)} aria-label="Página anterior">←</button>
      <span aria-live="polite">Página {page} de {document.numPages}</span>
      <button type="button" className="icon-button" disabled={page >= document.numPages} onClick={() => setPage(page + 1)} aria-label="Página siguiente">→</button>
    </div>
    <div className="pdf-canvas-wrap"><canvas ref={canvas} aria-label={`Vista previa de página ${page}`} /></div>
    <p className="hint preview-caption">Vista visual local. El procesamiento requiere que el PDF tenga texto seleccionable.</p>
  </>
}
