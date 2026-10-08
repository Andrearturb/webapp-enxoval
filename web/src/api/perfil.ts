import { apiFetch } from './cliente'
import type { AvatarCodigo } from '../componentes/avatares'

export interface PerfilUsuario {
  avatar: AvatarCodigo
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
