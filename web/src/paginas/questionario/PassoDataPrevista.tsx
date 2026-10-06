import { Input } from '../../componentes/ui/input'
import { Label } from '../../componentes/ui/label'
import { intervaloDataPrevista, dataNoIntervalo } from './intervalos'
import type { PassoProps } from './tipos'

export default function PassoDataPrevista({ respostas, onChange }: PassoProps) {
  const { min, max } = intervaloDataPrevista()
  const dataPreenchida = !!respostas.data_prevista
  const dataInvalida = dataPreenchida && !dataNoIntervalo(respostas.data_prevista ?? '')

  return (
    <div className="space-y-4">
      <h2 className="text-xl">Qual é a data prevista do parto?</h2>
      <Label htmlFor="data-prevista">Data prevista</Label>
      <Input
        id="data-prevista"
        type="date"
        min={min}
        max={max}
        value={respostas.data_prevista ?? ''}
        onChange={(e) => onChange({ data_prevista: e.target.value || undefined })}
      />
      {dataInvalida && (
        <p role="alert" className="text-sm text-alerta-texto">
          A data prevista deve estar entre um ano atrás e 10 meses à frente de hoje.
        </p>
      )}
    </div>
  )
}
