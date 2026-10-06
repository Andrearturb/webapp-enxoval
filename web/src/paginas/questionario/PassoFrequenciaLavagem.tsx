import { GrupoOpcoes } from './GrupoOpcoes'
import type { PassoProps } from './tipos'

const OPCOES = [
  { valor: '1', rotulo: 'Lavo todo dia' },
  { valor: '2', rotulo: 'Lavo a cada 2 dias' },
  { valor: '3', rotulo: 'Lavo a cada 3 dias' },
  { valor: '4', rotulo: 'Lavo cerca de 2 vezes por semana' },
] as const

export default function PassoFrequenciaLavagem({ respostas, onChange }: PassoProps) {
  return (
    <div className="space-y-4">
      <h2 className="text-xl">Com que frequência você lava roupa?</h2>
      <GrupoOpcoes
        nome="Frequência de lavar roupa"
        opcoes={OPCOES}
        valor={
          respostas.dias_entre_lavagens !== undefined
            ? String(respostas.dias_entre_lavagens)
            : undefined
        }
        onEscolher={(v) => onChange({ dias_entre_lavagens: Number(v) })}
      />
    </div>
  )
}
