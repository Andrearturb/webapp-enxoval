import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { buscarMunicipios, type Municipio } from '../../api/municipios'
import { useDebounce } from '../../hooks/useDebounce'
import { Button } from '../../componentes/ui/button'
import { Input } from '../../componentes/ui/input'
import { Label } from '../../componentes/ui/label'
import type { PassoProps } from './tipos'

const PERFIS = [
  { codigo: 'quente', nome: 'Quente o ano todo' },
  { codigo: 'moderado', nome: 'Inverno moderado' },
  { codigo: 'frio', nome: 'Inverno frio' },
] as const

export default function PassoCidade({ respostas, onChange }: PassoProps) {
  const cidadeEscolhida = respostas.municipio_codigo !== undefined
  const [busca, setBusca] = useState(
    respostas.municipio_nome ? `${respostas.municipio_nome} - ${respostas.municipio_uf}` : '',
  )
  const buscaDebounced = useDebounce(busca, 300)

  const { data: resultados = [] } = useQuery({
    queryKey: ['municipios', buscaDebounced],
    queryFn: () => buscarMunicipios(buscaDebounced),
    enabled: buscaDebounced.trim().length >= 2 && !cidadeEscolhida,
  })

  function escolher(m: Municipio) {
    setBusca(`${m.nome} - ${m.uf}`)
    onChange({
      municipio_codigo: m.codigo_ibge,
      municipio_nome: m.nome,
      municipio_uf: m.uf,
      perfil_sugerido: m.perfil_sugerido,
      correcao_perfil: undefined,
    })
  }

  function aoDigitar(valor: string) {
    setBusca(valor)
    if (cidadeEscolhida) {
      onChange({
        municipio_codigo: undefined,
        municipio_nome: undefined,
        municipio_uf: undefined,
        perfil_sugerido: undefined,
        correcao_perfil: undefined,
      })
    }
  }

  const perfilAtual = respostas.correcao_perfil ?? respostas.perfil_sugerido

  return (
    <div className="space-y-4">
      <h2 className="text-xl">Qual é a sua cidade?</h2>
      <Label htmlFor="cidade">Cidade</Label>
      <Input
        id="cidade"
        value={busca}
        onChange={(e) => aoDigitar(e.target.value)}
        placeholder="Digite o nome da cidade"
        autoComplete="off"
      />
      {!cidadeEscolhida && resultados.length > 0 && (
        <ul className="rounded-xl border border-principal-suave bg-superficie">
          {resultados.map((m) => (
            <li key={m.codigo_ibge}>
              <button
                type="button"
                className="min-h-11 w-full px-4 py-3 text-left hover:bg-principal-suave"
                onClick={() => escolher(m)}
              >
                {m.nome} - {m.uf}
              </button>
            </li>
          ))}
        </ul>
      )}
      {cidadeEscolhida && perfilAtual && (
        <div className="rounded-xl bg-principal-suave p-4">
          <p>Perfil de clima sugerido: {PERFIS.find((p) => p.codigo === perfilAtual)?.nome}</p>
          <p className="text-sm text-texto-suave">Não é isso? Escolha outro perfil:</p>
          <div className="flex flex-wrap gap-2">
            {PERFIS.map((p) => (
              <Button
                key={p.codigo}
                type="button"
                variant={perfilAtual === p.codigo ? 'principal' : 'secundario'}
                onClick={() => onChange({ correcao_perfil: p.codigo })}
              >
                {p.nome}
              </Button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
