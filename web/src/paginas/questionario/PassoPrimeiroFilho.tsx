import { GrupoOpcoes } from './GrupoOpcoes'
import type { PassoProps } from './tipos'

const OPCOES = [
  { valor: 'sim', rotulo: 'Sim' },
  { valor: 'nao', rotulo: 'Não' },
] as const

export default function PassoPrimeiroFilho({ respostas, onChange }: PassoProps) {
  return (
    <div className="space-y-4">
      <h2 className="text-xl">Este é o primeiro filho?</h2>
      <GrupoOpcoes
        nome="Primeiro filho"
        opcoes={OPCOES}
        valor={
          respostas.primeiro_filho === undefined
            ? undefined
            : respostas.primeiro_filho
              ? 'sim'
              : 'nao'
        }
        onEscolher={(v) => onChange({ primeiro_filho: v === 'sim' })}
      />
    </div>
  )
}
