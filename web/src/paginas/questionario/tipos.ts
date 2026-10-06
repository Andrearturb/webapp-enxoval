import type { components } from '../../api/tipos'

export const TOTAL_PASSOS = 6

export interface RespostasParciais {
  municipio_codigo?: number
  municipio_nome?: string
  municipio_uf?: string
  perfil_sugerido?: components['schemas']['PerfilCodigo']
  correcao_perfil?: components['schemas']['PerfilCodigo']
  data_prevista?: string
  dias_entre_lavagens?: number
  moradia?: components['schemas']['Moradia']
  tem_carro?: boolean
  orcamento?: components['schemas']['Faixa']
  primeiro_filho?: boolean
}

export interface PassoProps {
  respostas: RespostasParciais
  onChange: (parcial: Partial<RespostasParciais>) => void
}
