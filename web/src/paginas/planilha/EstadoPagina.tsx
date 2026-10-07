import { ErroApi } from '../../api/cliente'

interface Props {
  isLoading?: boolean
  isError?: boolean
  error?: Error | null
}

export function EstadoPagina({ isLoading, isError, error }: Props) {
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-fundo">
        <p className="text-texto-suave">Carregando...</p>
      </div>
    )
  }

  if (isError) {
    const status = error instanceof ErroApi ? error.status : 0
    const mensagem =
      status === 404
        ? 'Enxoval não encontrado. Verifique o link ou crie um novo enxoval.'
        : error instanceof Error
          ? error.message
          : 'Não foi possível carregar o enxoval.'

    return (
      <div className="flex min-h-screen items-center justify-center bg-fundo p-4">
        <div className="max-w-sm rounded-2xl bg-superficie p-6 text-center shadow-sm">
          <p className="text-texto">{mensagem}</p>
        </div>
      </div>
    )
  }

  return null
}
