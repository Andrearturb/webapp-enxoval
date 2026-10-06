import { useState } from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'
import { buscarMunicipios } from '../../api/municipios'
import { ErroApi } from '../../api/cliente'
import type { RespostasParciais } from './tipos'
import PassoCidade from './PassoCidade'

vi.mock('../../api/municipios')

function renderPasso(respostasIniciais: RespostasParciais) {
  const onChange = vi.fn()

  function Harness() {
    const [respostas, setRespostas] = useState(respostasIniciais)
    function aoMudar(parcial: Partial<RespostasParciais>) {
      onChange(parcial)
      setRespostas((atual) => ({ ...atual, ...parcial }))
    }
    return <PassoCidade respostas={respostas} onChange={aoMudar} />
  }

  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  render(
    <QueryClientProvider client={queryClient}>
      <Harness />
    </QueryClientProvider>,
  )
  return { onChange }
}

describe('PassoCidade', () => {
  it('busca e lista cidades depois de digitar', async () => {
    vi.mocked(buscarMunicipios).mockResolvedValue([
      { codigo_ibge: 4106902, nome: 'Curitiba', uf: 'PR', perfil_sugerido: 'frio' },
    ])
    renderPasso({})

    fireEvent.change(screen.getByLabelText('Cidade'), { target: { value: 'curitiba' } })

    await waitFor(() => expect(screen.getByText('Curitiba - PR')).toBeInTheDocument())
  })

  it('escolhe a cidade e mostra o perfil sugerido', async () => {
    vi.mocked(buscarMunicipios).mockResolvedValue([
      { codigo_ibge: 4106902, nome: 'Curitiba', uf: 'PR', perfil_sugerido: 'frio' },
    ])
    const { onChange } = renderPasso({})

    fireEvent.change(screen.getByLabelText('Cidade'), { target: { value: 'curitiba' } })
    await waitFor(() => screen.getByText('Curitiba - PR'))
    fireEvent.click(screen.getByText('Curitiba - PR'))

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ municipio_codigo: 4106902, perfil_sugerido: 'frio' }),
    )
    expect(screen.getByText('Perfil de clima sugerido: Inverno frio')).toBeInTheDocument()
  })

  it('permite corrigir o perfil sugerido', () => {
    const { onChange } = renderPasso({
      municipio_codigo: 4106902,
      municipio_nome: 'Curitiba',
      municipio_uf: 'PR',
      perfil_sugerido: 'frio',
    })

    fireEvent.click(screen.getByText('Quente o ano todo'))

    expect(onChange).toHaveBeenCalledWith({ correcao_perfil: 'quente' })
  })

  it('trocar o texto de busca depois de escolher uma cidade limpa a escolha e o perfil', () => {
    const { onChange } = renderPasso({
      municipio_codigo: 4106902,
      municipio_nome: 'Curitiba',
      municipio_uf: 'PR',
      perfil_sugerido: 'frio',
    })

    fireEvent.change(screen.getByLabelText('Cidade'), { target: { value: 'outra cidade' } })

    expect(onChange).toHaveBeenCalledWith({
      municipio_codigo: undefined,
      municipio_nome: undefined,
      municipio_uf: undefined,
      perfil_sugerido: undefined,
      correcao_perfil: undefined,
    })
  })

  it('mostra "Buscando..." enquanto a query está carregando', async () => {
    // Promise que nunca resolve para simular loading contínuo
    vi.mocked(buscarMunicipios).mockReturnValue(new Promise(() => {}))
    renderPasso({})

    fireEvent.change(screen.getByLabelText('Cidade'), { target: { value: 'cur' } })

    await waitFor(() => expect(screen.getByText('Buscando...')).toBeInTheDocument())
  })

  it('mostra "Nenhuma cidade encontrada" quando a busca retorna lista vazia', async () => {
    vi.mocked(buscarMunicipios).mockResolvedValue([])
    renderPasso({})

    fireEvent.change(screen.getByLabelText('Cidade'), { target: { value: 'xyzabc' } })

    await waitFor(() => expect(screen.getByText('Nenhuma cidade encontrada')).toBeInTheDocument())
  })

  it('mostra mensagem de erro quando a busca falha', async () => {
    // retry: 1 no componente → mock rejeita 2 vezes (tentativa inicial + 1 retry)
    const erro = new ErroApi('erro_busca', 'Falha ao buscar cidades.', 500)
    vi.mocked(buscarMunicipios).mockRejectedValue(erro)
    renderPasso({})

    fireEvent.change(screen.getByLabelText('Cidade'), { target: { value: 'cur' } })

    await waitFor(
      () => expect(screen.getByRole('alert')).toBeInTheDocument(),
      { timeout: 5000 },
    )
    expect(screen.getByRole('alert')).toHaveTextContent('Falha ao buscar cidades.')
  })
})
