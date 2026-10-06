import { Input } from '../../componentes/ui/input'
import { Label } from '../../componentes/ui/label'
import type { PassoProps } from './tipos'

export default function PassoDataPrevista({ respostas, onChange }: PassoProps) {
  return (
    <div className="space-y-4">
      <h2 className="text-xl">Qual é a data prevista do parto?</h2>
      <Label htmlFor="data-prevista">Data prevista</Label>
      <Input
        id="data-prevista"
        type="date"
        value={respostas.data_prevista ?? ''}
        onChange={(e) => onChange({ data_prevista: e.target.value || undefined })}
      />
    </div>
  )
}
