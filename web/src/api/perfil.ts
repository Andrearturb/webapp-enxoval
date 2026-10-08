import { apiFetch } from './cliente'

export interface PerfilUsuario {
  foto: string | null
}

export function getPerfil(): Promise<PerfilUsuario> {
  return apiFetch('/perfil')
}

export function salvarFoto(foto: File): Promise<PerfilUsuario> {
  return apiFetch('/perfil/foto', {
    method: 'PUT',
    headers: { 'Content-Type': foto.type || 'application/octet-stream' },
    body: foto,
  })
}

export function removerFoto(): Promise<void> {
  return apiFetch('/perfil/foto', { method: 'DELETE' })
}
