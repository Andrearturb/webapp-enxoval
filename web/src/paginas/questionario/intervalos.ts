/**
 * Intervalo de datas aceito pelo backend para data prevista do parto.
 * api/app/servicos/escrita.py: MESES_A_FRENTE=10, ANOS_ATRAS=1
 */
export function intervaloDataPrevista(hoje: Date = new Date()): { min: string; max: string } {
  const min = new Date(hoje)
  min.setFullYear(min.getFullYear() - 1)

  const max = new Date(hoje)
  max.setMonth(max.getMonth() + 10)

  return {
    min: min.toISOString().slice(0, 10),
    max: max.toISOString().slice(0, 10),
  }
}

export function dataNoIntervalo(dataStr: string, hoje: Date = new Date()): boolean {
  if (!dataStr) return false
  const { min, max } = intervaloDataPrevista(hoje)
  return dataStr >= min && dataStr <= max
}
