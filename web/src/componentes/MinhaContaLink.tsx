import { Link } from 'react-router-dom'
import { keycloakHabilitado } from '../auth/keycloak'
import { useAuth } from '../auth/AuthProvider'
import { usePerfil } from '../hooks/usePerfil'
import { imagemAvatar, type AvatarCodigo } from './avatares'

export function AvatarUsuario({
  foto,
  avatar,
  nome,
  grande = false,
}: {
  foto?: string | null
  avatar?: AvatarCodigo | null
  nome: string
  grande?: boolean
}) {
  const iniciais =
    nome
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((p) => p[0])
      .join('')
      .toUpperCase() || 'EU'
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-principal-suave font-semibold text-principal ${grande ? 'size-24 text-2xl' : 'size-9 text-xs'}`}
    >
      {avatar || foto ? (
        <img src={avatar ? imagemAvatar(avatar) : foto!} alt="" className="size-full object-cover" />
      ) : (
        <span aria-hidden="true">{iniciais}</span>
      )}
    </span>
  )
}

export function MinhaContaLink() {
  const { nomeUsuario } = useAuth()
  const { data } = usePerfil()
  if (!keycloakHabilitado) return null
  return (
    <Link
      to="/minha-conta"
      aria-label="Minha conta"
      className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-borda px-2 py-1 text-sm text-principal hover:bg-principal-suave"
    >
      <AvatarUsuario avatar={data?.avatar} foto={data?.foto} nome={nomeUsuario ?? 'Minha conta'} />
      <span className="hidden sm:inline">Minha conta</span>
    </Link>
  )
}
