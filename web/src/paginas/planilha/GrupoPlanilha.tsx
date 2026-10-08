import { useState } from 'react'
import { CalendarDays, ChevronDown, Clock3, ClipboardList } from 'lucide-react'
import type {
  LinhaSaida,
  MarcacaoEntrada,
  MomentoCompra,
} from '../../api/enxovais'
import { CategoriaPlanilha } from './CategoriaPlanilha'

interface GrupoConfig {
  rotulo: string
  classeSecao: string
  classeH2: string
  colapsadoPorPadrao: boolean
}

const CONFIG: Record<MomentoCompra, GrupoConfig> = {
  atrasado: {
    rotulo: 'Comprar agora',
    classeSecao: 'space-y-3 rounded-2xl border-l-2 border-alerta-texto/40 pl-3',
    classeH2: 'text-alerta-texto',
    colapsadoPorPadrao: false,
  },
  agora: {
    rotulo: 'Nesta fase',
    classeSecao: 'space-y-3',
    classeH2: 'text-principal',
    colapsadoPorPadrao: false,
  },
  proxima_fase: {
    rotulo: 'Próxima fase',
    classeSecao: 'space-y-3',
    classeH2: 'text-texto',
    colapsadoPorPadrao: false,
  },
  futuro: {
    rotulo: 'Mais para frente',
    classeSecao: 'space-y-3',
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
  onCompletar: (
    chave: string,
    origem: 'comprada' | 'ganhada' | 'ja_tinha',
  ) => void
}

export function GrupoPlanilha({
  momento,
  categorias,
  destacarJaTinha,
  onMarcar,
  onCompletar,
}: Props) {
  const cfg = CONFIG[momento]
  const [aberto, setAberto] = useState(!cfg.colapsadoPorPadrao)
  const totalItens = categorias.reduce((acc, c) => acc + c.linhas.length, 0)
  const Icone =
    momento === 'atrasado'
      ? Clock3
      : momento === 'agora'
        ? ClipboardList
        : CalendarDays

  if (totalItens === 0) return null

  return (
    <section className={cfg.classeSecao} data-momento={momento}>
      <button
        type="button"
        className="flex min-h-12 w-full items-center justify-between gap-3 py-2 text-left"
        onClick={() => setAberto((v) => !v)}
        aria-expanded={aberto}
      >
        <h2
          className={`flex items-center gap-2 font-titulo text-lg font-semibold ${cfg.classeH2}`}
        >
          <Icone size={18} aria-hidden="true" /> {cfg.rotulo}
        </h2>
        <span className="flex shrink-0 items-center gap-2 text-xs text-texto-suave">
          {totalItens} {totalItens === 1 ? 'item' : 'itens'}{' '}
          <ChevronDown
            size={16}
            className={aberto ? 'rotate-180' : ''}
            aria-hidden="true"
          />
        </span>
      </button>

      {aberto && (
        <div className="space-y-3">
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
