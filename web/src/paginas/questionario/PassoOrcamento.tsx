import { GrupoOpcoes } from './GrupoOpcoes'
import type { PassoProps } from './tipos'

const OPCOES = [
  { valor: 'economico', rotulo: 'Econômico' },
  { valor: 'intermediario', rotulo: 'Intermediário' },
  { valor: 'investir', rotulo: 'Investir mais' },
] as const

export default function PassoOrcamento({ respostas, onChange }: PassoProps) {
  return (
    <div className="space-y-4">
      <h2 className="text-xl">Qual orçamento vocês têm em mente?</h2>
      <GrupoOpcoes
        nome="Orçamento"
        opcoes={OPCOES}
        valor={respostas.orcamento}
        onEscolher={(v) => onChange({ orcamento: v })}
      />
    </div>
  )
}
