import { cn } from '../../lib/utils'

interface Opcao<T extends string> {
  valor: T
  rotulo: string
}

interface Props<T extends string> {
  nome: string
  opcoes: readonly Opcao<T>[]
  valor?: T
  onEscolher: (valor: T) => void
}

export function GrupoOpcoes<T extends string>({ nome, opcoes, valor, onEscolher }: Props<T>) {
  return (
    <div role="radiogroup" aria-label={nome} className="flex flex-col gap-2">
      {opcoes.map((opcao) => (
        <button
          key={opcao.valor}
          type="button"
          role="radio"
          aria-checked={valor === opcao.valor}
          onClick={() => onEscolher(opcao.valor)}
          className={cn(
            'min-h-11 rounded-xl border px-4 py-3 text-left',
            valor === opcao.valor
              ? 'border-principal bg-principal-suave text-principal'
              : 'border-principal-suave bg-superficie text-texto',
          )}
        >
          {opcao.rotulo}
        </button>
      ))}
    </div>
  )
}
