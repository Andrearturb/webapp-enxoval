import { useState } from 'react'
import type { LinhaSaida, MarcacaoEntrada } from '../../api/enxovais'
import { ContadorMarcacao } from './ContadorMarcacao'

interface Props {
  linha: LinhaSaida
  destacarJaTinha: boolean
  onMarcar: (chave: string, marcacao: MarcacaoEntrada) => void
  onCompletar: (chave: string, origem: 'comprada' | 'ganhada' | 'ja_tinha') => void
}

const SELO_PRIORIDADE = {
  essencial: { texto: 'Essencial', classes: 'bg-[#F5DDD2] text-[#874129]' },
  util: { texto: 'Útil', classes: 'bg-[#E1EAE2] text-[#36513D]' },
  pode_esperar: { texto: 'Pode esperar', classes: 'bg-[#EDE4D3] text-[#5E4B2A]' },
}

export function LinhaItem({ linha, destacarJaTinha, onMarcar, onCompletar }: Props) {
  const [expandido, setExpandido] = useState(false)
  const selo = SELO_PRIORIDADE[linha.prioridade]
  const atendido = linha.faltam === 0 && (linha.comprada + linha.ganhada + linha.ja_tinha) > 0

  return (
    <li
      data-testid="linha-item"
      className={`border-b border-principal-suave last:border-0 ${atendido ? 'opacity-60' : ''}`}
    >
      <button
        type="button"
        className="flex w-full items-start justify-between gap-2 px-4 py-3 text-left"
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
            <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${selo.classes}`}>
              {selo.texto}
            </span>
            {linha.e_seguranca && (
              <span className="rounded bg-alerta-fundo px-1.5 py-0.5 text-xs text-alerta-texto">
                Segurança
              </span>
            )}
          </div>
          <p className="mt-0.5 text-sm text-texto-suave">
            {linha.quantidade} {linha.unidade_texto ?? 'unidades'} · faltam {linha.faltam}
          </p>
        </div>
        <span className="mt-1 text-xs text-texto-suave" aria-hidden>
          {expandido ? '▲' : '▼'}
        </span>
      </button>

      {expandido && (
        <div className="px-4 pb-4">
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
