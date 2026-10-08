import { type ComponentType, useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { Button } from '../componentes/ui/button'
import { ErroApi } from '../api/cliente'
import {
  criarEnxoval,
  type EnxovalCriado,
  type RespostasEntrada,
} from '../api/enxovais'
import { BarraProgresso } from './questionario/BarraProgresso'
import { todosPassosValidos, passoValido } from './questionario/validacao'
import {
  TOTAL_PASSOS,
  type PassoProps,
  type RespostasParciais,
} from './questionario/tipos'
import PassoCidade from './questionario/PassoCidade'
import PassoDataPrevista from './questionario/PassoDataPrevista'
import PassoFrequenciaLavagem from './questionario/PassoFrequenciaLavagem'
import PassoMoradia from './questionario/PassoMoradia'
import PassoOrcamento from './questionario/PassoOrcamento'
import PassoPrimeiroFilho from './questionario/PassoPrimeiroFilho'
import { Marca } from '../componentes/Marca'
import { IlustracaoEnxoval } from '../componentes/IlustracaoEnxoval'
import { ArrowRight, Heart } from 'lucide-react'
import { Link } from 'react-router-dom'

const CONTEXTO = [
  'O clima da sua cidade ajuda a escolher os tecidos e as quantidades de roupa.',
  'A previsão de chegada organiza as compras por estação e por fase do bebê.',
  'Sua rotina de lavagem define quantas peças precisam estar disponíveis entre uma lavagem e outra.',
  'O espaço da sua casa e os deslocamentos ajudam a montar uma lista mais prática.',
  'O orçamento orienta as sugestões. Você pode preparar tudo aos poucos.',
  'O que sua família já tem também conta. Aproveitar faz parte de um enxoval bem pensado.',
]

const PASSOS: ComponentType<PassoProps>[] = [
  PassoCidade,
  PassoDataPrevista,
  PassoFrequenciaLavagem,
  PassoMoradia,
  PassoOrcamento,
  PassoPrimeiroFilho,
]

function passoDaUrl(valor: string | undefined): number {
  const n = Number(valor)
  if (!Number.isInteger(n) || n < 1 || n > TOTAL_PASSOS) return 1
  return n
}

/** Retorna o número do primeiro passo inválido antes de `ate`, ou null se todos válidos. */
function primeiroPassoIncompletoAntes(
  respostas: RespostasParciais,
  ate: number,
): number | null {
  for (let p = 1; p < ate; p++) {
    if (!passoValido(p, respostas)) return p
  }
  return null
}

export default function Questionario() {
  const { passo: passoParam } = useParams()
  const passo = passoDaUrl(passoParam)
  const navigate = useNavigate()
  const [respostas, setRespostas] = useState<RespostasParciais>({})
  const [erro, setErro] = useState<string | null>(null)

  // Redirecionar para o primeiro passo incompleto se o usuário chegou num passo
  // avançado sem ter completado os anteriores (reload, URL colada, botão Voltar do browser)
  useEffect(() => {
    const incompleto = primeiroPassoIncompletoAntes(respostas, passo)
    if (incompleto !== null) {
      navigate(`/questionario/${incompleto}`, { replace: true })
    }
  }, [passo, respostas, navigate])

  const mutacao = useMutation<EnxovalCriado, ErroApi, RespostasEntrada>({
    mutationFn: criarEnxoval,
    onSuccess: (criado) =>
      navigate(`/enxoval/${criado.id}/planilha`, { replace: true }),
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
    setErro(null)
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
    <div className="min-h-screen bg-fundo">
      <header className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-5 py-5 sm:px-6">
        <Marca />
        <Link to="/" className="text-sm text-texto-suave hover:text-principal">
          Voltar ao início
        </Link>
      </header>
      <main className="mx-auto grid max-w-5xl gap-8 px-5 pb-12 pt-4 sm:px-6 lg:grid-cols-[.9fr_1.1fr] lg:gap-16 lg:pt-12">
        <aside className="hidden lg:block">
          <p className="text-xs font-semibold uppercase tracking-[.16em] text-principal">
            Preparar também é cuidar
          </p>
          <h2 className="mt-4 text-4xl font-semibold leading-tight">
            Uma lista com
            <br />o jeito da sua família.
          </h2>
          <p className="mt-4 max-w-sm leading-relaxed text-texto-suave">
            Cada resposta ajuda a escolher o que faz sentido para você. Sem
            pressa, sem excessos.
          </p>
          <IlustracaoEnxoval className="mt-3 w-full max-w-xs" />
        </aside>
        <section className="rounded-3xl border border-borda bg-superficie p-5 sm:p-8">
          <p className="mb-2 text-xs font-semibold uppercase tracking-[.14em] text-principal">
            Seu enxoval começa aqui
          </p>
          <h1 className="mb-6 text-2xl font-semibold">Questionário</h1>
          <div className="space-y-6">
            <BarraProgresso passo={passo} total={TOTAL_PASSOS} />
            <PassoAtual respostas={respostas} onChange={atualizar} />
            <p className="flex items-start gap-2 rounded-2xl bg-fundo p-4 text-xs leading-relaxed text-texto-suave">
              <Heart
                size={16}
                className="mt-0.5 shrink-0 text-principal"
                aria-hidden="true"
              />
              {CONTEXTO[passo - 1]}
            </p>
            {erro && (
              <p
                role="alert"
                className="rounded-xl bg-alerta-fundo p-3 text-alerta-texto"
              >
                {erro}
              </p>
            )}
            <div className="flex justify-between gap-3 border-t border-borda pt-5">
              <Button
                type="button"
                variant="secundario"
                onClick={voltar}
                disabled={passo === 1}
              >
                Voltar
              </Button>
              {passo < TOTAL_PASSOS ? (
                <Button
                  type="button"
                  onClick={avancar}
                  disabled={!passoAtualValido}
                >
                  Avançar
                  <ArrowRight size={16} className="ml-2" aria-hidden="true" />
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
        </section>
      </main>
    </div>
  )
}
