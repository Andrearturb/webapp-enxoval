import { apiFetch } from './cliente'
import type { AvatarCodigo } from '../componentes/avatares'

export interface PerfilUsuario {
  foto: string | null
  avatar: AvatarCodigo | null
}

export function getPerfil(): Promise<PerfilUsuario> {
  return apiFetch('/perfil')
}

export function salvarAvatar(avatar: AvatarCodigo): Promise<PerfilUsuario> {
  return apiFetch('/perfil/avatar', {
    method: 'PUT',
    body: JSON.stringify({ avatar }),
  })
}

export function removerAvatar(): Promise<void> {
  return apiFetch('/perfil/avatar', { method: 'DELETE' })
}
