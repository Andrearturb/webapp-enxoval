import { useState } from 'react'
import type { LinhaSaida, MarcacaoEntrada, MomentoCompra } from '../../api/enxovais'
import { CategoriaPlanilha } from './CategoriaPlanilha'

interface GrupoConfig {
  rotulo: string
  icone: string
  classeSecao: string
  classeH2: string
  colapsadoPorPadrao: boolean
}

const CONFIG: Record<MomentoCompra, GrupoConfig> = {
  atrasado: {
    rotulo: 'Comprar agora',
    icone: '⚠',
    classeSecao: 'rounded-2xl bg-alerta-fundo shadow-sm overflow-hidden',
    classeH2: 'text-alerta-texto',
    colapsadoPorPadrao: false,
  },
  agora: {
    rotulo: 'Nesta fase',
    icone: '📋',
    classeSecao: 'rounded-2xl bg-principal-suave shadow-sm overflow-hidden',
    classeH2: 'text-principal',
    colapsadoPorPadrao: false,
  },
  proxima_fase: {
    rotulo: 'Próxima fase',
    icone: '🗓',
    classeSecao: 'rounded-2xl bg-superficie shadow-sm overflow-hidden',
    classeH2: 'text-texto',
    colapsadoPorPadrao: false,
  },
  futuro: {
    rotulo: 'Mais para frente',
    icone: '🗓',
    classeSecao: 'rounded-2xl bg-superficie shadow-sm overflow-hidden',
    classeH2: 'text-texto-suave',
    colapsadoPorPadrao: true,
  },
}

interface CategoriaComLinhas {
  slug: string
  nome: string
  ordem: number
  linhas: LinhaSaida[]
}

interface Props {
  momento: MomentoCompra
  categorias: CategoriaComLinhas[]
  destacarJaTinha: boolean
  onMarcar: (chave: string, marcacao: MarcacaoEntrada) => void
  onCompletar: (chave: string, origem: 'comprada' | 'ganhada' | 'ja_tinha') => void
}

export function GrupoPlanilha({ momento, categorias, destacarJaTinha, onMarcar, onCompletar }: Props) {
  const cfg = CONFIG[momento]
  const [aberto, setAberto] = useState(!cfg.colapsadoPorPadrao)
  const totalItens = categorias.reduce((acc, c) => acc + c.linhas.length, 0)

  if (totalItens === 0) return null

  return (
    <section className={cfg.classeSecao} data-momento={momento}>
      <button
        type="button"
        className="flex w-full items-center justify-between px-4 py-3"
        onClick={() => setAberto((v) => !v)}
        aria-expanded={aberto}
      >
        <h2 className={`font-titulo font-semibold ${cfg.classeH2}`}>
          {cfg.icone} {cfg.rotulo}
        </h2>
        <span className="text-sm text-texto-suave">
          {totalItens} {totalItens === 1 ? 'item' : 'itens'} · {aberto ? '▲' : '▼'}
        </span>
      </button>

      {aberto && (
        <div className="space-y-2 px-2 pb-2">
          {categorias.map((cat) => (
            <CategoriaPlanilha
              key={cat.slug}
              nome={cat.nome}
              linhas={cat.linhas}
              destacarJaTinha={destacarJaTinha}
              onMarcar={onMarcar}
              onCompletar={onCompletar}
            />
          ))}
        </div>
      )}
    </section>
  )
}
