import { useState } from 'react'
import { Check, ChevronDown, ShieldCheck } from 'lucide-react'
import type { LinhaSaida, MarcacaoEntrada } from '../../api/enxovais'
import { ContadorMarcacao } from './ContadorMarcacao'

interface Props {
  linha: LinhaSaida
  destacarJaTinha: boolean
  onMarcar: (chave: string, marcacao: MarcacaoEntrada) => void
  onCompletar: (
    chave: string,
    origem: 'comprada' | 'ganhada' | 'ja_tinha',
  ) => void
}

const SELO_PRIORIDADE = {
  essencial: { texto: 'Essencial', classes: 'bg-[#F5DDD2] text-[#874129]' },
  util: { texto: 'Útil', classes: 'bg-[#E1EAE2] text-[#36513D]' },
  pode_esperar: {
    texto: 'Pode esperar',
    classes: 'bg-[#EDE4D3] text-[#5E4B2A]',
  },
}

export function LinhaItem({
  linha,
  destacarJaTinha,
  onMarcar,
  onCompletar,
}: Props) {
  const [expandido, setExpandido] = useState(false)
  const selo = SELO_PRIORIDADE[linha.prioridade]
  const atendido =
    linha.faltam === 0 && linha.comprada + linha.ganhada + linha.ja_tinha > 0

  return (
    <li
      data-testid="linha-item"
      className={`border-b border-borda last:border-0 ${atendido ? 'bg-principal-suave/20' : ''}`}
    >
      <button
        type="button"
        className="flex min-h-20 w-full items-start justify-between gap-3 px-4 py-4 text-left hover:bg-principal-suave/20"
        onClick={() => setExpandido((v) => !v)}
        aria-expanded={expandido}
      >
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium text-texto">
              {linha.nome}
              {linha.rotulo_variante ? ` (${linha.rotulo_variante})` : ''}
              {linha.tamanho ? ` ${linha.tamanho}` : ''}
            </span>
            <span
              className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${selo.classes}`}
            >
              {selo.texto}
            </span>
            {linha.e_seguranca && (
              <span className="inline-flex items-center gap-1 rounded-full bg-alerta-fundo px-2 py-0.5 text-[11px] text-alerta-texto">
                <ShieldCheck size={12} aria-hidden="true" />
                Segurança
              </span>
            )}
          </div>
          <p className="mt-0.5 text-sm text-texto-suave">
            {linha.quantidade} {linha.unidade_texto ?? 'unidades'} · faltam{' '}
            {linha.faltam}
          </p>
          {atendido && (
            <span className="mt-1 inline-flex items-center gap-1 text-xs text-principal">
              <Check size={13} aria-hidden="true" /> Já organizado
            </span>
          )}
        </div>
        <ChevronDown
          size={17}
          className={`mt-1 shrink-0 text-texto-suave transition-transform ${expandido ? 'rotate-180' : ''}`}
          aria-hidden="true"
        />
      </button>

      {expandido && (
        <div className="mx-4 mb-4 rounded-2xl bg-fundo px-4 py-3">
          <ContadorMarcacao
            linha={linha}
            destacarJaTinha={destacarJaTinha}
            onMarcar={(marcacao) => onMarcar(linha.chave, marcacao)}
            onCompletar={(origem) => onCompletar(linha.chave, origem)}
          />
        </div>
      )}
    </li>
  )
}
