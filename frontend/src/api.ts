import type { Questionnaire } from './types'

export async function processFile(file: File): Promise<Questionnaire> {
  const body = new FormData()
  body.append('file', file)
  const response = await fetch('/api/process', { method: 'POST', body })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(data?.error?.mensaje || 'No fue posible procesar el archivo.')
  }
  return data as Questionnaire
}
