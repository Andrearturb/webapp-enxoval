import { TOTAL_PASSOS, type RespostasParciais } from './tipos'

export function passoValido(passo: number, r: RespostasParciais): boolean {
  switch (passo) {
    case 1:
      return r.municipio_codigo !== undefined
    case 2:
      return !!r.data_prevista
    case 3:
      return r.dias_entre_lavagens !== undefined
    case 4:
      return r.moradia !== undefined && r.tem_carro !== undefined
    case 5:
      return r.orcamento !== undefined
    case 6:
      return r.primeiro_filho !== undefined
    default:
      return false
  }
}

export function todosPassosValidos(r: RespostasParciais): boolean {
  for (let passo = 1; passo <= TOTAL_PASSOS; passo++) {
    if (!passoValido(passo, r)) return false
  }
  return true
}
