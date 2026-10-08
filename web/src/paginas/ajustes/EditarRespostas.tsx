import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  editarEnxoval,
  preverEnxoval,
  type EnxovalSaida,
  type RespostasEntrada,
} from '../../api/enxovais'
import { ErroApi } from '../../api/cliente'
import { Button } from '../../componentes/ui/button'
import PassoCidade from '../questionario/PassoCidade'
import PassoDataPrevista from '../questionario/PassoDataPrevista'
import PassoFrequenciaLavagem from '../questionario/PassoFrequenciaLavagem'
import PassoMoradia from '../questionario/PassoMoradia'
import PassoOrcamento from '../questionario/PassoOrcamento'
import PassoPrimeiroFilho from '../questionario/PassoPrimeiroFilho'
import { todosPassosValidos } from '../questionario/validacao'
import type { RespostasParciais } from '../questionario/tipos'

const CAMPOS = [
  PassoCidade,
  PassoDataPrevista,
  PassoFrequenciaLavagem,
  PassoMoradia,
  PassoOrcamento,
  PassoPrimeiroFilho,
]

function resumoRespostas(enxoval: EnxovalSaida): Record<string, string> {
  const r = enxoval.respostas
  return {
    Cidade: `${r.municipio.nome} - ${r.municipio.uf}`,
    'Data prevista': r.data_prevista.split('-').reverse().join('/'),
    Lavagem: `A cada ${r.dias_entre_lavagens} dia(s)`,
    Moradia: {
      apartamento: 'Apartamento',
      casa_sem_escada: 'Casa sem escada',
      casa_com_escada: 'Casa com escada',
    }[r.moradia],
    'Tem carro': r.tem_carro ? 'Sim' : 'Não',
    Orçamento: {
      economico: 'Econômico',
      intermediario: 'Intermediário',
      investir: 'Investir mais',
    }[r.orcamento],
    'Primeiro filho': r.primeiro_filho ? 'Sim' : 'Não',
    Clima: {
      quente: 'Quente o ano todo',
      moderado: 'Inverno moderado',
      frio: 'Inverno frio',
    }[r.perfil_clima],
  }
}

export function EditarRespostas({
  enxoval,
  onFechar,
}: {
  enxoval: EnxovalSaida
  onFechar: (salvou: boolean) => void
}) {
  const qc = useQueryClient()
  const r = enxoval.respostas
  const [respostas, setRespostas] = useState<RespostasParciais>({
    municipio_codigo: r.municipio.codigo_ibge,
    municipio_nome: r.municipio.nome,
    municipio_uf: r.municipio.uf,
    perfil_sugerido: r.perfil_clima,
    correcao_perfil: r.perfil_corrigido ? r.perfil_clima : undefined,
    data_prevista: r.data_prevista,
    dias_entre_lavagens: r.dias_entre_lavagens,
    moradia: r.moradia,
    tem_carro: r.tem_carro,
    orcamento: r.orcamento,
    primeiro_filho: r.primeiro_filho,
  })
  const [revisao, setRevisao] = useState<{
    dados: RespostasEntrada
    enxoval: EnxovalSaida
  } | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const previa = useMutation({
    mutationFn: (dados: RespostasEntrada) => preverEnxoval(enxoval.id, dados),
    onSuccess: (novo, dados) => setRevisao({ dados, enxoval: novo }),
    onError: (e) =>
      setErro(
        e instanceof ErroApi
          ? e.message
          : 'Não foi possível calcular a prévia. Tente novamente.',
      ),
  })
  const salvar = useMutation({
    mutationFn: (dados: RespostasEntrada) => editarEnxoval(enxoval.id, dados),
    onSuccess: (novo) => {
      qc.setQueryData(['enxoval', enxoval.id], novo)
      void qc.invalidateQueries({ queryKey: ['meus-enxovais'] })
      onFechar(true)
    },
    onError: (e) =>
      setErro(
        e instanceof ErroApi
          ? e.message
          : 'Não foi possível salvar. Suas respostas continuam aqui para tentar novamente.',
      ),
  })
  const ocupado = previa.isPending || salvar.isPending
  const dados: RespostasEntrada = {
    municipio_codigo: respostas.municipio_codigo!,
    data_prevista: respostas.data_prevista!,
    dias_entre_lavagens: respostas.dias_entre_lavagens!,
    moradia: respostas.moradia!,
    tem_carro: respostas.tem_carro!,
    orcamento: respostas.orcamento!,
    primeiro_filho: respostas.primeiro_filho!,
    correcao_perfil: respostas.correcao_perfil ?? null,
  }
  const alterou =
    JSON.stringify(dados) !==
    JSON.stringify({
      municipio_codigo: r.municipio.codigo_ibge,
      data_prevista: r.data_prevista,
      dias_entre_lavagens: r.dias_entre_lavagens,
      moradia: r.moradia,
      tem_carro: r.tem_carro,
      orcamento: r.orcamento,
      primeiro_filho: r.primeiro_filho,
      correcao_perfil: r.perfil_corrigido ? r.perfil_clima : null,
    })
  const antigas = new Map(enxoval.linhas.map((l) => [l.chave, l]))
  const novas = new Map(revisao?.enxoval.linhas.map((l) => [l.chave, l]) ?? [])
  const adicionadas = [...novas.values()].filter((l) => !antigas.has(l.chave))
  const removidas = enxoval.linhas.filter((l) => !novas.has(l.chave))
  const ajustadas = [...novas.values()].filter((l) => {
    const antiga = antigas.get(l.chave)
    return (
      antiga &&
      (antiga.quantidade !== l.quantidade || antiga.prioridade !== l.prioridade)
    )
  })
  const respostasAnteriores = resumoRespostas(enxoval)
  const respostasNovas = revisao ? resumoRespostas(revisao.enxoval) : {}

  return (
    <form
      className="mt-5 space-y-5"
      onSubmit={(e) => {
        e.preventDefault()
        if (ocupado) return
        setErro(null)
        if (revisao) salvar.mutate(revisao.dados)
        else if (todosPassosValidos(respostas) && alterou) previa.mutate(dados)
      }}
    >
      {!revisao ? (
        <fieldset disabled={ocupado} className="space-y-6">
          <legend className="sr-only">Editar respostas do questionário</legend>
          {CAMPOS.map((Campo, i) => (
            <div key={i} className="border-t border-borda pt-5">
              <Campo
                respostas={respostas}
                onChange={(parcial) => {
                  setErro(null)
                  setRespostas((atual) => ({ ...atual, ...parcial }))
                }}
              />
            </div>
          ))}
        </fieldset>
      ) : (
        <section
          aria-label="Prévia das alterações"
          className="space-y-4 rounded-2xl bg-fundo p-4 sm:p-5"
        >
          <h3 className="font-titulo text-xl font-semibold">
            Confira seu enxoval atualizado
          </h3>
          <p className="text-sm text-texto-suave">
            Nada foi salvo ainda. As compras, os presentes e os itens que você
            já tinha serão preservados.
          </p>
          <ul className="space-y-2 text-sm">
            {Object.entries(respostasNovas)
              .filter(([campo, valor]) => respostasAnteriores[campo] !== valor)
              .map(([campo, valor]) => (
                <li key={campo}>
                  <span className="font-medium">{campo}:</span>{' '}
                  {respostasAnteriores[campo]} → {valor}
                </li>
              ))}
          </ul>
          <dl className="grid grid-cols-1 gap-3 text-center min-[360px]:grid-cols-3">
            {[
              ['Novos itens', adicionadas.length],
              ['Ajustados', ajustadas.length],
              ['Saem da lista', removidas.length],
            ].map(([nome, numero]) => (
              <div
                key={nome}
                className="min-w-0 rounded-xl border border-borda bg-superficie p-2 sm:p-3"
              >
                <dt className="break-words text-xs text-texto-suave">{nome}</dt>
                <dd className="mt-1 text-2xl font-semibold text-principal">
                  {numero}
                </dd>
              </div>
            ))}
          </dl>
          <p className="text-sm">
            Lista recomendada: {enxoval.progresso.total_unidades} →{' '}
            {revisao.enxoval.progresso.total_unidades} unidades. Faltam{' '}
            {revisao.enxoval.progresso.faltam} na nova lista.
          </p>
          {revisao.enxoval.linhas_fora_da_lista.length > 0 && (
            <p className="text-sm text-texto-suave">
              {revisao.enxoval.linhas_fora_da_lista.length} registro(s) ficarão
              em “Fora da recomendação atual”, sem entrar no progresso da lista.
            </p>
          )}
          {adicionadas.length + ajustadas.length + removidas.length > 0 && (
            <details className="rounded-xl border border-borda bg-superficie p-3">
              <summary className="min-h-11 cursor-pointer py-2 text-sm font-medium text-principal">
                Ver itens que mudam
              </summary>
              <ul className="max-h-72 space-y-2 overflow-auto pt-3 text-sm">
                {adicionadas.map((l) => (
                  <li key={`a-${l.chave}`}>
                    Acrescentar: {l.nome} {l.tamanho} — {l.quantidade}{' '}
                    unidade(s)
                  </li>
                ))}
                {ajustadas.map((l) => (
                  <li key={`q-${l.chave}`}>
                    Ajustar: {l.nome} {l.tamanho} —{' '}
                    {antigas.get(l.chave)!.quantidade} → {l.quantidade}{' '}
                    unidade(s)
                    {antigas.get(l.chave)!.prioridade !== l.prioridade
                      ? ' (prioridade atualizada)'
                      : ''}
                  </li>
                ))}
                {removidas.map((l) => (
                  <li key={`r-${l.chave}`}>
                    Sai da recomendação: {l.nome} {l.tamanho}
                    {l.comprada + l.ganhada + l.ja_tinha > 0
                      ? ' — registros preservados'
                      : ''}
                  </li>
                ))}
              </ul>
            </details>
          )}
          <p className="text-xs text-texto-suave">
            As sugestões de marcas, o roteiro e as exportações também
            acompanharão suas novas respostas.
          </p>
        </section>
      )}
      {erro && (
        <p
          role="alert"
          className="rounded-xl bg-alerta-fundo p-3 text-sm text-alerta-texto"
        >
          {erro}
        </p>
      )}
      <div className="flex flex-wrap gap-3">
        <Button
          type="submit"
          disabled={
            ocupado ||
            (!revisao && (!todosPassosValidos(respostas) || !alterou))
          }
        >
          {salvar.isPending
            ? 'Salvando...'
            : previa.isPending
              ? 'Calculando...'
              : revisao
                ? 'Confirmar e atualizar enxoval'
                : 'Revisar alterações'}
        </Button>
        {revisao && (
          <Button
            type="button"
            variant="secundario"
            disabled={ocupado}
            onClick={() => {
              setRevisao(null)
              setErro(null)
            }}
          >
            Voltar à edição
          </Button>
        )}
        <Button
          type="button"
          variant="secundario"
          disabled={ocupado}
          onClick={() => onFechar(false)}
        >
          Cancelar
        </Button>
      </div>
    </form>
  )
}
