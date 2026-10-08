import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import type { LinhaSaida, MarcacaoEntrada } from '../../api/enxovais'
import { LinhaItem } from './LinhaItem'

interface Props {
  nome: string
  linhas: LinhaSaida[]
  destacarJaTinha: boolean
  onMarcar: (chave: string, marcacao: MarcacaoEntrada) => void
  onCompletar: (
    chave: string,
    origem: 'comprada' | 'ganhada' | 'ja_tinha',
  ) => void
}

export function CategoriaPlanilha({
  nome,
  linhas,
  destacarJaTinha,
  onMarcar,
  onCompletar,
}: Props) {
  const [aberta, setAberta] = useState(true)
  const atendidas = linhas.filter(
    (l) => l.faltam === 0 && l.comprada + l.ganhada + l.ja_tinha > 0,
  ).length

  if (linhas.length === 0) return null

  return (
    <section className="overflow-hidden rounded-2xl border border-borda bg-superficie">
      <button
        type="button"
        className="flex min-h-14 w-full items-center justify-between gap-3 bg-principal-suave/30 px-4 py-3"
        onClick={() => setAberta((v) => !v)}
        aria-expanded={aberta}
      >
        <h3 className="font-titulo font-semibold text-texto">{nome}</h3>
        <span className="flex items-center gap-2 text-xs text-texto-suave">
          {atendidas}/{linhas.length}{' '}
          <ChevronDown
            size={16}
            className={aberta ? 'rotate-180' : ''}
            aria-hidden="true"
          />
        </span>
      </button>

      {aberta && (
        <ul>
          {linhas.map((linha) => (
            <LinhaItem
              key={linha.chave}
              linha={linha}
              destacarJaTinha={destacarJaTinha}
              onMarcar={onMarcar}
              onCompletar={onCompletar}
            />
          ))}
        </ul>
      )}
    </section>
  )
}
