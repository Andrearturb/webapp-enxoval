import { Link, useParams } from 'react-router-dom'
import type { EnxovalSaida } from '../../api/enxovais'

interface Props {
  enxoval: EnxovalSaida
  abaAtiva: 'planilha' | 'roteiro' | 'guia' | 'seguranca' | 'ajustes'
}

const ABAS = [
  { rotulo: 'Planilha', sufixo: 'planilha' },
  { rotulo: 'Roteiro', sufixo: 'roteiro' },
  { rotulo: 'Guia', sufixo: 'guia' },
  { rotulo: 'Segurança', sufixo: 'seguranca' },
  { rotulo: 'Ajustes', sufixo: 'ajustes' },
] as const

export function CabecalhoEnxoval({ enxoval, abaAtiva }: Props) {
  const { id } = useParams<{ id: string }>()
  const { municipio, data_prevista } = enxoval.respostas

  const data = new Date(data_prevista + 'T12:00:00')
  const dataFormatada = data.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })

  return (
    <header className="bg-superficie shadow-sm">
      <div className="mx-auto max-w-2xl px-4 py-3">
        <p className="text-sm text-texto-suave">
          {municipio.nome} - {municipio.uf} · Previsão: {dataFormatada}
        </p>
        <nav className="mt-2 flex gap-1 overflow-x-auto" aria-label="Seções do enxoval">
          {ABAS.map((aba) => {
            const ativa = aba.sufixo === abaAtiva
            return (
              <Link
                key={aba.sufixo}
                to={`/enxoval/${id}/${aba.sufixo}`}
                className={`shrink-0 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                  ativa
                    ? 'bg-principal text-white'
                    : 'bg-principal-suave text-texto-suave hover:bg-principal hover:text-white'
                }`}
                aria-current={ativa ? 'page' : undefined}
              >
                {aba.rotulo}
              </Link>
            )
          })}
        </nav>
      </div>
    </header>
  )
}
