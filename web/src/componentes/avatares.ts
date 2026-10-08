export const AVATARES = [
  { codigo: 'ursinho', nome: 'Ursinho' },
  { codigo: 'coelhinho', nome: 'Coelhinho' },
  { codigo: 'elefantinho', nome: 'Elefantinho' },
  { codigo: 'patinho', nome: 'Patinho' },
  { codigo: 'nuvem', nome: 'Nuvem' },
  { codigo: 'lua', nome: 'Lua' },
] as const

export type AvatarCodigo = (typeof AVATARES)[number]['codigo']

export function imagemAvatar(codigo: AvatarCodigo): string {
  return `/avatares/${codigo}.webp`
}
