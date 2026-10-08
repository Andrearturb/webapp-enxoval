import { Check, Heart, ShoppingBag } from 'lucide-react'
import type { EnxovalSaida } from '../../api/enxovais'

export function ResumoPlanilha({ enxoval }: { enxoval: EnxovalSaida }) {
  const { progresso, resumo } = enxoval
  return (
    <section
      className="rounded-3xl border border-borda bg-superficie p-5 sm:p-6"
      aria-label="Resumo do enxoval"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[.14em] text-principal">
            Um passo de cada vez
          </p>
          <h2 className="mt-2 text-xl font-semibold sm:text-2xl">
            Seu enxoval está tomando forma
          </h2>
        </div>
        <span className="rounded-2xl bg-principal-suave px-3 py-2 font-titulo text-2xl font-semibold text-principal">
          {progresso.percentual}%
        </span>
      </div>
      <p className="mt-3 text-sm text-texto-suave">
        {progresso.atendidas} de {progresso.total_unidades} unidades já
        organizadas
      </p>
      <div
        className="mt-3 h-2 overflow-hidden rounded-full bg-principal-suave"
        role="progressbar"
        aria-valuenow={progresso.percentual}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Progresso do enxoval"
      >
        <div
          className="h-full rounded-full bg-principal transition-all duration-300"
          style={{ width: `${progresso.percentual}%` }}
        />
      </div>
      <div className="mt-5 grid grid-cols-3 divide-x divide-borda">
        <div className="pr-3">
          <Check size={16} className="mb-1 text-principal" aria-hidden="true" />
          <p className="text-xl font-semibold tabular-nums">
            {progresso.atendidas}
          </p>
          <p className="mt-0.5 text-xs text-texto-suave">Já tenho</p>
        </div>
        <div className="px-4">
          <ShoppingBag
            size={16}
            className="mb-1 text-principal"
            aria-hidden="true"
          />
          <p className="text-xl font-semibold tabular-nums">
            {progresso.faltam}
          </p>
          <p className="mt-0.5 text-xs text-texto-suave">Ainda faltam</p>
        </div>
        <div className="pl-4">
          <Heart size={16} className="mb-1 text-principal" aria-hidden="true" />
          <p className="text-xl font-semibold tabular-nums">
            {progresso.total_unidades}
          </p>
          <p className="mt-0.5 text-xs text-texto-suave">Na sua lista</p>
        </div>
      </div>
      <p className="mt-5 border-t border-borda pt-3 text-xs text-texto-suave">
        Pensado para lavar a cada {resumo.dias_sem_lavar} dia
        {resumo.dias_sem_lavar > 1 ? 's' : ''}.
      </p>
      {resumo.aviso_volume_alto && (
        <p className="mt-2 rounded-xl bg-areia/50 px-3 py-2 text-xs text-texto-suave">
          Volume alto — considere comprar mais aos poucos
        </p>
      )}
    </section>
  )
}
