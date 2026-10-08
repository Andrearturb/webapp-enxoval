/**
 * Cliente HTTP da aplicação.
 *
 * Injeta automaticamente o token Bearer do Keycloak em cada requisição
 * quando a autenticação está habilitada. Em modo dev sem Keycloak, o
 * header Authorization não é enviado.
 */
import { keycloak, keycloakHabilitado } from '../auth/keycloak'

export class ErroApi extends Error {
  codigo: string
  status: number

  constructor(codigo: string, mensagem: string, status: number) {
    super(mensagem)
    this.codigo = codigo
    this.status = status
  }
}

const BASE = '/api/v1'

/** Renova o token antes da requisição, inclusive após suspensão da aba. */
async function obterToken(): Promise<string | undefined> {
  if (!keycloakHabilitado) return undefined
  try {
    await keycloak.updateToken(30)
  } catch {
    throw new ErroApi('sessao_expirada', 'Sua sessão expirou. Entre novamente.', 401)
  }
  if (!keycloak.token) {
    throw new ErroApi('token_ausente', 'Entre na sua conta para continuar.', 401)
  }
  return keycloak.token
}

async function apiResponse(caminho: string, opcoes?: RequestInit): Promise<Response> {
  const token = await obterToken()
  const headers = new Headers(opcoes?.headers)
  if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)

  let resposta: Response
  try {
    resposta = await fetch(`${BASE}${caminho}`, {
      ...opcoes,
      headers,
    })
  } catch {
    throw new ErroApi(
      'sem_conexao',
      'Não foi possível conectar. Confira sua internet e tente de novo.',
      0,
    )
  }
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => null)
    throw new ErroApi(
      corpo?.erro ?? 'erro_desconhecido',
      corpo?.mensagem ?? 'Algo deu errado. Tente de novo.',
      resposta.status,
    )
  }
  return resposta
}

export async function apiFetch<T>(caminho: string, opcoes?: RequestInit): Promise<T> {
  const resposta = await apiResponse(caminho, opcoes)
  if (resposta.status === 204) return undefined as T
  return resposta.json() as Promise<T>
}

export async function apiDownload(caminho: string, nome: string): Promise<void> {
  const resposta = await apiResponse(caminho)
  const url = URL.createObjectURL(await resposta.blob())
  const link = document.createElement('a')
  link.href = url
  link.download = nome
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
