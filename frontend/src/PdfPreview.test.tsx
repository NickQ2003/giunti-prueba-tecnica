import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import PdfPreview from './PdfPreview'

const mocks = vi.hoisted(() => {
  const render = vi.fn(() => ({ promise: Promise.resolve(), cancel: vi.fn() }))
  const getPage = vi.fn(async () => ({ getViewport: ({ scale }: { scale: number }) => ({ width: 600 * scale, height: 800 * scale }), render }))
  const destroy = vi.fn(async () => {})
  return { render, getPage, destroy }
})

vi.mock('pdfjs-dist', () => ({
  GlobalWorkerOptions: {},
  getDocument: () => ({ promise: Promise.resolve({ numPages: 2, getPage: mocks.getPage }), destroy: mocks.destroy }),
}))

describe('vista previa PDF', () => {
  it('renderiza y navega páginas y libera recursos', async () => {
    const file = new File(['pdf'], 'ejemplo.pdf')
    Object.defineProperty(file, 'arrayBuffer', { value: async () => new ArrayBuffer(1) })
    const { unmount } = render(<PdfPreview file={file} />)
    expect(await screen.findByText('Página 1 de 2')).toBeInTheDocument()
    await waitFor(() => expect(mocks.getPage).toHaveBeenCalledWith(1))
    fireEvent.click(screen.getByRole('button', { name: 'Página siguiente' }))
    expect(screen.getByText('Página 2 de 2')).toBeInTheDocument()
    await waitFor(() => expect(mocks.getPage).toHaveBeenCalledWith(2))
    expect(screen.getByRole('button', { name: 'Página siguiente' })).toBeDisabled()
    unmount()
    expect(mocks.destroy).toHaveBeenCalled()
  })
})
