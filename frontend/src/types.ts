export type Value = string | number
export interface Questionnaire {
  titulo: string
  idioma: string
  total_items: number
  items: {
    numero: number
    enunciado: string
    tipo: 'escala_likert' | 'seleccion_multiple' | 'verdadero_falso' | 'desarrollo' | 'emparejamiento'
    alternativas: { valor: Value; texto: string }[]
    respuesta_correcta: Value | null
  }[]
}
