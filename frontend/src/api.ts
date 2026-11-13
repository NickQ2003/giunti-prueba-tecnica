import type { Questionnaire } from './types'

export class ApiError extends Error {
  constructor(message: string, readonly requestId: string | null) {
    super(message)
  }
}

export async function processFile(file: File): Promise<{ questionnaire: Questionnaire; unmatchedStatements: number; languageDisagreement: boolean }> {
  const body = new FormData()
  body.append('file', file)
  const response = await fetch('/api/process', { method: 'POST', body })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const requestId = data?.error?.request_id || response.headers?.get('X-Request-ID') || null
    throw new ApiError(data?.error?.mensaje || 'No fue posible procesar el archivo.', requestId)
  }
  const unmatched = Number(response.headers?.get('X-Unmatched-Statements') ?? 0)
  return { questionnaire: data as Questionnaire, unmatchedStatements: Number.isSafeInteger(unmatched) && unmatched > 0 ? unmatched : 0, languageDisagreement: response.headers?.get('X-Language-Disagreement') === 'true' }
}
