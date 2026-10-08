import { useEffect, useRef } from 'react'
import { Check, X } from 'lucide-react'
import { AVATARES, imagemAvatar, type AvatarCodigo } from './avatares'
import { AvatarUsuario } from './MinhaContaLink'

interface Props {
  aberto: boolean
  atual: AvatarCodigo | null
  nome: string
  salvando: boolean
  erro: string | null
  onEscolher: (avatar: AvatarCodigo | null) => void
  onFechar: () => void
}

export function ModalAvatar({ aberto, atual, nome, salvando, erro, onEscolher, onFechar }: Props) {
  const dialog = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const elemento = dialog.current
    if (!elemento) return
    if (aberto && !elemento.open) elemento.showModal()
    if (!aberto && elemento.open) elemento.close()
    if (aberto) {
      const anterior = document.body.style.overflow
      document.body.style.overflow = 'hidden'
      return () => { document.body.style.overflow = anterior }
    }
  }, [aberto])

  return (
    <dialog
      ref={dialog}
      aria-labelledby="titulo-avatar"
      aria-describedby="descricao-avatar"
      onCancel={(event) => {
        event.preventDefault()
        onFechar()
      }}
      onKeyDown={(event) => {
        if (event.key !== 'Tab') return
        const botoes = Array.from(event.currentTarget.querySelectorAll<HTMLButtonElement>('button:not(:disabled)'))
        const primeiro = botoes[0]
        const ultimo = botoes[botoes.length - 1]
        if (!primeiro || !ultimo) return
        if (event.shiftKey && document.activeElement === primeiro) {
          event.preventDefault()
          ultimo.focus()
        } else if (!event.shiftKey && document.activeElement === ultimo) {
          event.preventDefault()
          primeiro.focus()
        }
      }}
      onClick={(event) => {
        if (event.target !== event.currentTarget) return
        const r = event.currentTarget.getBoundingClientRect()
        if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) onFechar()
      }}
      className="m-auto max-h-[90dvh] w-[calc(100%_-_2rem)] max-w-lg overflow-y-auto rounded-3xl border border-borda bg-superficie p-0 text-texto shadow-xl backdrop:bg-texto/40"
    >
      <div className="p-5 sm:p-6">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 id="titulo-avatar" className="font-titulo text-2xl font-semibold">Escolha seu avatar</h2>
            <p id="descricao-avatar" className="mt-2 text-sm text-texto-suave">Escolha uma ilustração ou use as iniciais do seu nome.</p>
          </div>
          <button type="button" aria-label="Fechar seleção de avatar" onClick={onFechar} className="inline-flex size-11 shrink-0 items-center justify-center rounded-xl text-texto-suave hover:bg-principal-suave focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-principal">
            <X size={20} aria-hidden="true" />
          </button>
        </div>
        {erro && <p role="alert" className="mt-4 rounded-xl bg-alerta-fundo p-3 text-sm text-alerta-texto">{erro}</p>}
        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3" role="group" aria-label="Avatares disponíveis" aria-busy={salvando}>
          {AVATARES.map(({ codigo, nome }) => (
            <button
              key={codigo}
              type="button"
              aria-label={`Escolher ${nome}`}
              aria-pressed={atual === codigo}
              disabled={salvando}
              onClick={() => onEscolher(codigo)}
              className={`relative flex flex-col items-center gap-2 rounded-2xl border-2 px-2 py-3 transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-principal disabled:cursor-wait disabled:opacity-60 ${atual === codigo ? 'border-principal bg-principal-suave' : 'border-borda bg-fundo hover:border-principal/50'}`}
            >
              <img src={imagemAvatar(codigo)} alt="" width={80} height={80} className="size-16 rounded-full object-cover sm:size-20" />
              <span className="text-sm font-medium">{nome}</span>
              {atual === codigo && <Check size={16} aria-hidden="true" className="absolute right-2 top-2 text-principal" />}
            </button>
          ))}
        </div>
        <button
          type="button"
          aria-pressed={atual === null}
          disabled={salvando}
          onClick={() => onEscolher(null)}
          className={`mt-4 flex min-h-11 w-full items-center gap-3 rounded-xl border px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-principal disabled:opacity-60 ${atual === null ? 'border-principal bg-principal-suave text-principal' : 'border-borda hover:bg-principal-suave'}`}
        >
          <AvatarUsuario avatar={null} nome={nome} />
          <span>Usar minhas iniciais</span>
          {atual === null && <Check size={16} aria-hidden="true" className="ml-auto" />}
        </button>
        {salvando && <p role="status" className="mt-4 text-sm text-texto-suave">Atualizando seu avatar...</p>}
      </div>
    </dialog>
  )
}
