import { Link } from 'react-router-dom'
import { keycloakHabilitado } from '../auth/keycloak'
import { usePerfil } from '../hooks/usePerfil'
import { imagemAvatar, type AvatarCodigo } from './avatares'

export function AvatarUsuario({
  avatar = 'ursinho',
  grande = false,
}: {
  avatar?: AvatarCodigo
  grande?: boolean
}) {
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-principal-suave font-semibold text-principal ${grande ? 'size-24 text-2xl' : 'size-9 text-xs'}`}
    >
      <img src={imagemAvatar(avatar)} alt="" className="size-full object-cover" />
    </span>
  )
}

export function MinhaContaLink() {
  const { data } = usePerfil()
  if (!keycloakHabilitado) return null
  return (
    <Link
      to="/minha-conta"
      aria-label="Minha conta"
      className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-borda px-2 py-1 text-sm text-principal hover:bg-principal-suave"
    >
      <AvatarUsuario avatar={data?.avatar} />
      <span className="hidden sm:inline">Minha conta</span>
    </Link>
  )
}
