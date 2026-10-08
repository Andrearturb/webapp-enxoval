import {
  BookOpen,
  CalendarDays,
  ClipboardList,
  Settings2,
  ShieldCheck,
} from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import type { EnxovalSaida } from '../../api/enxovais'
import { Marca } from '../../componentes/Marca'

interface Props {
  enxoval: EnxovalSaida
  abaAtiva: 'planilha' | 'roteiro' | 'guia' | 'seguranca' | 'ajustes'
}
const ABAS = [
  { rotulo: 'Planilha', sufixo: 'planilha', icone: ClipboardList },
  { rotulo: 'Roteiro', sufixo: 'roteiro', icone: CalendarDays },
  { rotulo: 'Guia', sufixo: 'guia', icone: BookOpen },
  { rotulo: 'Segurança', sufixo: 'seguranca', icone: ShieldCheck },
  { rotulo: 'Ajustes', sufixo: 'ajustes', icone: Settings2 },
] as const

export function CabecalhoEnxoval({ enxoval, abaAtiva }: Props) {
  const { id } = useParams<{ id: string }>()
  const { municipio, data_prevista } = enxoval.respostas
  const dataFormatada = new Date(
    data_prevista + 'T12:00:00',
  ).toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })
  return (
    <header className="border-b border-borda bg-superficie">
      <div className="mx-auto max-w-5xl px-4 pt-4 sm:px-6">
        <div className="flex items-center justify-between gap-3 pb-4">
          <Marca destino="/meus-enxovais" />
          <Link
            to="/meus-enxovais"
            className="inline-flex min-h-11 items-center rounded-xl border border-borda px-3 text-xs font-medium text-principal sm:text-sm"
          >
            Meus enxovais
          </Link>
        </div>
        <p className="pb-3 text-xs text-texto-suave sm:text-sm">
          {municipio.nome} - {municipio.uf} · Previsão: {dataFormatada}
        </p>
        <nav
          className="grid grid-cols-5 gap-1 pb-3 sm:flex sm:gap-2"
          aria-label="Seções do enxoval"
        >
          {ABAS.map(({ rotulo, sufixo, icone: Icone }) => (
            <Link
              key={sufixo}
              to={`/enxoval/${id}/${sufixo}`}
              aria-current={sufixo === abaAtiva ? 'page' : undefined}
              className={`flex min-h-14 min-w-0 flex-col items-center justify-center gap-1 rounded-xl px-1 py-2 text-[11px] font-medium transition-colors sm:min-h-11 sm:flex-row sm:gap-2 sm:px-4 sm:text-sm ${sufixo === abaAtiva ? 'bg-principal text-white' : 'text-texto-suave hover:bg-principal-suave'}`}
            >
              <Icone size={17} aria-hidden="true" />
              {rotulo}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  )
}
