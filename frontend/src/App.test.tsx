import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

vi.mock('./PdfPreview', () => ({ default: ({ file }: { file: File }) => <div>Vista PDF: {file.name}</div> }))

afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals() })

describe('procesamiento', () => {
  it('sube un archivo y muestra el resultado', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({ titulo: 'Ejemplo', idioma: 'es', total_items: 1, items: [] }),
    } as Response)
    render(<App />)
    const button = screen.getByRole('button', { name: 'Procesar documento' })
    expect(button).toBeDisabled()
    fireEvent.change(screen.getByLabelText(/Archivo PDF/), { target: { files: [new File(['test'], 'ejemplo.docx')] } })
    fireEvent.click(button)
    expect(await screen.findByRole('button', { name: 'Descargar JSON' })).toBeInTheDocument()
    expect(screen.getByText(/1 ítems/)).toBeInTheDocument()
  })

  it('muestra errores de la API', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      json: async () => ({ error: { mensaje: 'No se encontraron ítems.', request_id: 'abc123' } }),
    } as Response)
    render(<App />)
    fireEvent.change(screen.getByLabelText(/Archivo PDF/), { target: { files: [new File(['test'], 'ejemplo.pdf')] } })
    fireEvent.click(screen.getByRole('button', { name: 'Procesar documento' }))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('No se encontraron ítems.'))
    expect(screen.getByRole('alert')).toHaveTextContent('Referencia: abc123')
  })

  it('descarga el JSON generado', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({ titulo: 'Ejemplo', idioma: 'es', total_items: 0, items: [] }),
    } as Response)
    const createUrl = vi.fn(() => 'blob:test')
    const revokeUrl = vi.fn()
    vi.stubGlobal('URL', { createObjectURL: createUrl, revokeObjectURL: revokeUrl })
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
    render(<App />)
    fireEvent.change(screen.getByLabelText(/Archivo PDF/), { target: { files: [new File(['test'], 'ejemplo.docx')] } })
    fireEvent.click(screen.getByRole('button', { name: 'Procesar documento' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Descargar JSON' }))
    expect(createUrl).toHaveBeenCalledWith(expect.any(Blob))
    expect(click).toHaveBeenCalledOnce()
    await waitFor(() => expect(revokeUrl).toHaveBeenCalledWith('blob:test'))
    vi.unstubAllGlobals()
  })

  it('advierte cuando no se localizan enunciados', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      headers: new Headers({ 'X-Unmatched-Statements': '2' }),
      json: async () => ({ titulo: 'Ejemplo', idioma: 'es', total_items: 2, items: [] }),
    } as Response)
    render(<App />)
    fireEvent.change(screen.getByLabelText(/Archivo PDF/), { target: { files: [new File(['test'], 'ejemplo.docx')] } })
    fireEvent.click(screen.getByRole('button', { name: 'Procesar documento' }))
    expect(await screen.findByText(/No se pudieron localizar literalmente 2 enunciados/)).toBeInTheDocument()
  })

  it('advierte cuando difieren las señales de idioma', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      headers: new Headers({ 'X-Language-Disagreement': 'true' }),
      json: async () => ({ titulo: 'Ejemplo', idioma: 'en', total_items: 1, items: [] }),
    } as Response)
    render(<App />)
    fireEvent.change(screen.getByLabelText(/Archivo PDF/), { target: { files: [new File(['test'], 'ejemplo.docx')] } })
    fireEvent.click(screen.getByRole('button', { name: 'Procesar documento' }))
    expect(await screen.findByText(/idioma detectado por la IA no coincide/)).toBeInTheDocument()
  })

  it('muestra la vista de texto de DOCX sin llamar al procesamiento', async () => {
    const fetcher = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({ text: '1. Pregunta inventada <script>texto</script>', truncated: false }),
    } as Response)
    render(<App />)
    fireEvent.change(screen.getByLabelText(/Archivo PDF/), { target: { files: [new File(['test'], 'ejemplo.docx')] } })
    expect(await screen.findByText('1. Pregunta inventada <script>texto</script>')).toBeInTheDocument()
    expect(fetcher).toHaveBeenCalledTimes(1)
    expect(fetcher.mock.calls[0][0]).toBe('/api/preview')
    fireEvent.click(screen.getByRole('button', { name: 'Quitar archivo' }))
    expect(screen.queryByText('1. Pregunta inventada <script>texto</script>')).not.toBeInTheDocument()
  })

  it('permite cambiar entre ítems y JSON', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async input => ({
      ok: true,
      json: async () => input === '/api/preview'
        ? { text: 'Pregunta de muestra', truncated: false }
        : { titulo: 'Ejemplo', idioma: 'es', total_items: 1, items: [{ numero: 1, enunciado: 'Pregunta de muestra', tipo: 'desarrollo', alternativas: [], respuesta_correcta: null }] },
    }) as Response)
    render(<App />)
    fireEvent.change(screen.getByLabelText(/Archivo PDF/), { target: { files: [new File(['test'], 'ejemplo.docx')] } })
    fireEvent.click(screen.getByRole('button', { name: 'Procesar documento' }))
    expect(await screen.findByText('Respuesta abierta')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'JSON' }))
    expect(screen.getByText(/"enunciado": "Pregunta de muestra"/)).toBeInTheDocument()
  })

  it('acepta un PDF arrastrado y no solicita vista de texto', () => {
    const fetcher = vi.spyOn(globalThis, 'fetch')
    render(<App />)
    fireEvent.drop(screen.getByText('Arrastra tu archivo aquí').closest('label')!, { dataTransfer: { files: [new File(['test'], 'prueba.pdf')] } })
    expect(screen.getByText('Vista PDF: prueba.pdf')).toBeInTheDocument()
    expect(fetcher).not.toHaveBeenCalled()
  })
})
