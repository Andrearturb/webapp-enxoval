import { type ComponentType, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { Button } from '../componentes/ui/button'
import { ErroApi } from '../api/cliente'
import { criarEnxoval, type EnxovalCriado, type RespostasEntrada } from '../api/enxovais'
import { BarraProgresso } from './questionario/BarraProgresso'
import { todosPassosValidos, passoValido } from './questionario/validacao'
import { TOTAL_PASSOS, type PassoProps, type RespostasParciais } from './questionario/tipos'
import PassoCidade from './questionario/PassoCidade'
import PassoDataPrevista from './questionario/PassoDataPrevista'
import PassoFrequenciaLavagem from './questionario/PassoFrequenciaLavagem'
import PassoMoradia from './questionario/PassoMoradia'
import PassoOrcamento from './questionario/PassoOrcamento'

function PassoEmConstrucao() {
  return <p className="text-texto-suave">Em construção.</p>
}

const PASSOS: ComponentType<PassoProps>[] = [
  PassoCidade,
  PassoDataPrevista,
  PassoFrequenciaLavagem,
  PassoMoradia,
  PassoOrcamento,
  PassoEmConstrucao,
]

function passoDaUrl(valor: string | undefined): number {
  const n = Number(valor)
  if (!Number.isInteger(n) || n < 1 || n > TOTAL_PASSOS) return 1
  return n
}

export default function Questionario() {
  const { passo: passoParam } = useParams()
  const passo = passoDaUrl(passoParam)
  const navigate = useNavigate()
  const [respostas, setRespostas] = useState<RespostasParciais>({})
  const [erro, setErro] = useState<string | null>(null)

  const mutacao = useMutation<EnxovalCriado, ErroApi, RespostasEntrada>({
    mutationFn: criarEnxoval,
    onSuccess: (criado) => navigate(`/enxoval/${criado.id}/planilha`),
    onError: (e) => setErro(e.message),
  })

  function atualizar(parcial: Partial<RespostasParciais>) {
    setErro(null)
    setRespostas((atual) => ({ ...atual, ...parcial }))
  }

  function avancar() {
    if (passo < TOTAL_PASSOS) navigate(`/questionario/${passo + 1}`)
  }

  function voltar() {
    if (passo > 1) navigate(`/questionario/${passo - 1}`)
  }

  function concluir() {
    if (!todosPassosValidos(respostas)) return
    mutacao.mutate({
      municipio_codigo: respostas.municipio_codigo!,
      data_prevista: respostas.data_prevista!,
      dias_entre_lavagens: respostas.dias_entre_lavagens!,
      moradia: respostas.moradia!,
      tem_carro: respostas.tem_carro!,
      orcamento: respostas.orcamento!,
      primeiro_filho: respostas.primeiro_filho!,
      correcao_perfil: respostas.correcao_perfil ?? null,
    })
  }

  const PassoAtual = PASSOS[passo - 1]
  const passoAtualValido = passoValido(passo, respostas)

  return (
    <div className="mx-auto max-w-md space-y-6 p-4">
      <h1 className="text-2xl">Questionário</h1>
      <BarraProgresso passo={passo} total={TOTAL_PASSOS} />
      <PassoAtual respostas={respostas} onChange={atualizar} />
      {erro && (
        <p role="alert" className="rounded-xl bg-alerta-fundo p-3 text-alerta-texto">
          {erro}
        </p>
      )}
      <div className="flex justify-between gap-3">
        <Button type="button" variant="secundario" onClick={voltar} disabled={passo === 1}>
          Voltar
        </Button>
        {passo < TOTAL_PASSOS ? (
          <Button type="button" onClick={avancar} disabled={!passoAtualValido}>
            Avançar
          </Button>
        ) : (
          <Button
            type="button"
            onClick={concluir}
            disabled={!todosPassosValidos(respostas) || mutacao.isPending}
          >
            {mutacao.isPending ? 'Enviando...' : 'Concluir'}
          </Button>
        )}
      </div>
    </div>
  )
}
