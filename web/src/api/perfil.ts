import { apiFetch } from './cliente'
import type { AvatarCodigo } from '../componentes/avatares'

export interface PerfilUsuario {
  avatar: AvatarCodigo | null
}

export function getPerfil(): Promise<PerfilUsuario> {
  return apiFetch('/perfil')
}

export function salvarAvatar(avatar: AvatarCodigo | null): Promise<PerfilUsuario> {
  return apiFetch('/perfil/avatar', {
    method: 'PUT',
    body: JSON.stringify({ avatar }),
  })
}
