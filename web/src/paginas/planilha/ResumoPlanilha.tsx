import type { EnxovalSaida } from '../../api/enxovais'

interface Props {
  enxoval: EnxovalSaida
}

export function ResumoPlanilha({ enxoval }: Props) {
  const { progresso, resumo } = enxoval
  const pct = progresso.percentual

  return (
    <div className="rounded-2xl bg-superficie p-4 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm text-texto-suave">
          {progresso.atendidas} de {progresso.total_unidades} unidades
        </span>
        <span className="font-medium text-principal">{pct}%</span>
      </div>

      {/* Barra de progresso */}
      <div
        className="h-2 w-full overflow-hidden rounded-full bg-principal-suave"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Progresso do enxoval"
      >
        <div
          className="h-full rounded-full bg-principal transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="mt-3 flex flex-wrap gap-3 text-sm text-texto-suave">
        <span>Lavar a cada {resumo.dias_sem_lavar} dia{resumo.dias_sem_lavar > 1 ? 's' : ''}</span>
        {resumo.aviso_volume_alto && (
          <span className="rounded-md bg-alerta-fundo px-2 py-0.5 text-alerta-texto">
            Volume alto — considere comprar mais aos poucos
          </span>
        )}
      </div>
    </div>
  )
}
