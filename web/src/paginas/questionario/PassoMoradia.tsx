import { GrupoOpcoes } from './GrupoOpcoes'
import type { PassoProps } from './tipos'

const OPCOES_MORADIA = [
  { valor: 'apartamento', rotulo: 'Apartamento' },
  { valor: 'casa_sem_escada', rotulo: 'Casa sem escada' },
  { valor: 'casa_com_escada', rotulo: 'Casa com escada' },
] as const

const OPCOES_CARRO = [
  { valor: 'sim', rotulo: 'Sim' },
  { valor: 'nao', rotulo: 'Não' },
] as const

export default function PassoMoradia({ respostas, onChange }: PassoProps) {
  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <h2 className="text-xl">Onde vocês moram?</h2>
        <GrupoOpcoes
          nome="Moradia"
          opcoes={OPCOES_MORADIA}
          valor={respostas.moradia}
          onEscolher={(v) => onChange({ moradia: v })}
        />
      </div>
      <div className="space-y-4">
        <h2 className="text-xl">Vocês têm carro?</h2>
        <GrupoOpcoes
          nome="Tem carro"
          opcoes={OPCOES_CARRO}
          valor={respostas.tem_carro === undefined ? undefined : respostas.tem_carro ? 'sim' : 'nao'}
          onEscolher={(v) => onChange({ tem_carro: v === 'sim' })}
        />
      </div>
    </div>
  )
}
