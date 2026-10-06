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

export async function apiFetch<T>(caminho: string, opcoes?: RequestInit): Promise<T> {
  let resposta: Response
  try {
    resposta = await fetch(`${BASE}${caminho}`, {
      headers: { 'Content-Type': 'application/json', ...opcoes?.headers },
      ...opcoes,
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
  if (resposta.status === 204) return undefined as T
  return resposta.json() as Promise<T>
}
