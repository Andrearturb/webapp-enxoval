import { useState } from 'react'
import type { LinhaSaida, MarcacaoEntrada } from '../../api/enxovais'
import { LinhaItem } from './LinhaItem'

interface Props {
  nome: string
  linhas: LinhaSaida[]
  destacarJaTinha: boolean
  onMarcar: (chave: string, marcacao: MarcacaoEntrada) => void
  onCompletar: (chave: string, origem: 'comprada' | 'ganhada' | 'ja_tinha') => void
}

export function CategoriaPlanilha({ nome, linhas, destacarJaTinha, onMarcar, onCompletar }: Props) {
  const [aberta, setAberta] = useState(true)
  const atendidas = linhas.filter((l) => l.faltam === 0 && (l.comprada + l.ganhada + l.ja_tinha) > 0).length

  if (linhas.length === 0) return null

  return (
    <section className="rounded-2xl bg-superficie shadow-sm overflow-hidden">
      <button
        type="button"
        className="flex w-full items-center justify-between px-4 py-3"
        onClick={() => setAberta((v) => !v)}
        aria-expanded={aberta}
      >
        <h2 className="font-titulo font-semibold text-texto">{nome}</h2>
        <span className="text-sm text-texto-suave">
          {atendidas}/{linhas.length} · {aberta ? '▲' : '▼'}
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
