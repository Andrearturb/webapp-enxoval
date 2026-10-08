import type { EnxovalSaida } from '../../api/enxovais'

export function ItensForaDaLista({
  linhas,
}: {
  linhas: EnxovalSaida['linhas_fora_da_lista']
}) {
  if (!linhas.length) return null
  return (
    <section
      aria-labelledby="fora-recomendacao"
      className="rounded-3xl border border-borda bg-superficie p-5 sm:p-6"
    >
      <h2 id="fora-recomendacao" className="font-titulo text-xl font-semibold">
        Fora da recomendação atual
      </h2>
      <p className="mt-2 text-sm text-texto-suave">
        Estes itens continuam guardados. Eles não entram no progresso atual e
        serão reaproveitados se voltarem à sua lista.
      </p>
      <ul className="mt-4 divide-y divide-borda">
        {linhas.map((l) => (
          <li key={l.chave} className="py-3">
            <p className="font-medium">
              {l.nome ?? l.chave.split(':')[0].replaceAll('-', ' ')}
              {l.tamanho ? ` · ${l.tamanho}` : ''}
              {l.rotulo_variante ? ` · ${l.rotulo_variante}` : ''}
            </p>
            <p className="mt-1 text-sm text-texto-suave">
              Comprei: {l.comprada} · Ganhei: {l.ganhada} · Já tinha:{' '}
              {l.ja_tinha}
            </p>
          </li>
        ))}
      </ul>
    </section>
  )
}
