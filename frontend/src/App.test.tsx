import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

afterEach(() => vi.restoreAllMocks())

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
})
