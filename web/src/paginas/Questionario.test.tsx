import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes, useParams } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { buscarMunicipios } from '../api/municipios'
import { criarEnxoval } from '../api/enxovais'
import { ErroApi } from '../api/cliente'
import Questionario from './Questionario'

vi.mock('../api/municipios')
vi.mock('../api/enxovais')

function DestinoPlanilha() {
  const { id } = useParams()
  return <p>destino: {id}</p>
}

function renderEm(caminho: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[caminho]}>
        <Routes>
          <Route path="/questionario/:passo" element={<Questionario />} />
          <Route path="/enxoval/:id/planilha" element={<DestinoPlanilha />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/** Data válida para o passo 2: hoje + 5 meses (dentro do intervalo aceito pelo backend) */
function dataValida(): string {
  const d = new Date()
  d.setMonth(d.getMonth() + 5)
  return d.toISOString().slice(0, 10)
}

describe('Questionario', () => {
  it('mostra o passo 1 por padrão e desabilita Voltar', () => {
    renderEm('/questionario/1')
    expect(screen.getByText('Passo 1 de 6')).toBeInTheDocument()
    expect(screen.getByText('Voltar')).toBeDisabled()
  })

  it.each(['/questionario/0', '/questionario/99', '/questionario/abc'])(
    '%s cai no passo 1 em vez de tela branca',
    (caminho) => {
      renderEm(caminho)
      expect(screen.getByText('Passo 1 de 6')).toBeInTheDocument()
    },
  )

  it('Avançar fica desabilitado até escolher uma cidade, e habilita depois', async () => {
    vi.mocked(buscarMunicipios).mockResolvedValue([
      { codigo_ibge: 4106902, nome: 'Curitiba', uf: 'PR', perfil_sugerido: 'frio' },
    ])
    renderEm('/questionario/1')
    expect(screen.getByText('Avançar')).toBeDisabled()

    fireEvent.change(screen.getByLabelText('Cidade'), { target: { value: 'curitiba' } })
    await waitFor(() => screen.getByText('Curitiba - PR'))
    fireEvent.click(screen.getByText('Curitiba - PR'))

    expect(screen.getByText('Avançar')).toBeEnabled()
  })

  it('preserva a cidade escolhida ao avançar e voltar', async () => {
    vi.mocked(buscarMunicipios).mockResolvedValue([
      { codigo_ibge: 4106902, nome: 'Curitiba', uf: 'PR', perfil_sugerido: 'frio' },
    ])
    renderEm('/questionario/1')

    fireEvent.change(screen.getByLabelText('Cidade'), { target: { value: 'curitiba' } })
    await waitFor(() => screen.getByText('Curitiba - PR'))
    fireEvent.click(screen.getByText('Curitiba - PR'))
    fireEvent.click(screen.getByText('Avançar'))

    expect(screen.getByText('Passo 2 de 6')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Voltar'))

    expect(screen.getByDisplayValue('Curitiba - PR')).toBeInTheDocument()
  })

  it('completa as 6 perguntas e cria o enxoval', async () => {
    vi.mocked(buscarMunicipios).mockResolvedValue([
      { codigo_ibge: 4106902, nome: 'Curitiba', uf: 'PR', perfil_sugerido: 'frio' },
    ])
    vi.mocked(criarEnxoval).mockResolvedValue({ id: 'id-teste' })
    renderEm('/questionario/1')

    fireEvent.change(screen.getByLabelText('Cidade'), { target: { value: 'curitiba' } })
    await waitFor(() => screen.getByText('Curitiba - PR'))
    fireEvent.click(screen.getByText('Curitiba - PR'))
    fireEvent.click(screen.getByText('Avançar'))

    const data = dataValida()
    fireEvent.change(screen.getByLabelText('Data prevista'), { target: { value: data } })
    fireEvent.click(screen.getByText('Avançar'))

    fireEvent.click(screen.getByText('Lavo a cada 2 dias'))
    fireEvent.click(screen.getByText('Avançar'))

    fireEvent.click(screen.getByText('Apartamento'))
    fireEvent.click(screen.getByText('Sim'))
    fireEvent.click(screen.getByText('Avançar'))

    fireEvent.click(screen.getByText('Intermediário'))
    fireEvent.click(screen.getByText('Avançar'))

    fireEvent.click(screen.getByText('Sim'))
    fireEvent.click(screen.getByText('Concluir'))

    await waitFor(() =>
      expect(criarEnxoval).toHaveBeenCalledWith(
        {
          municipio_codigo: 4106902,
          data_prevista: data,
          dias_entre_lavagens: 2,
          moradia: 'apartamento',
          tem_carro: true,
          orcamento: 'intermediario',
          primeiro_filho: true,
          correcao_perfil: null,
        },
        expect.anything(),
      ),
    )
    await waitFor(() => expect(screen.getByText('destino: id-teste')).toBeInTheDocument())
  })

  it('mostra o erro da API e mantém as respostas quando falha ao concluir', async () => {
    vi.mocked(buscarMunicipios).mockResolvedValue([
      { codigo_ibge: 4106902, nome: 'Curitiba', uf: 'PR', perfil_sugerido: 'frio' },
    ])
    vi.mocked(criarEnxoval).mockRejectedValue(
      new ErroApi('dados_invalidos', 'Confira os dados enviados.', 422),
    )
    renderEm('/questionario/1')

    fireEvent.change(screen.getByLabelText('Cidade'), { target: { value: 'curitiba' } })
    await waitFor(() => screen.getByText('Curitiba - PR'))
    fireEvent.click(screen.getByText('Curitiba - PR'))
    fireEvent.click(screen.getByText('Avançar'))
    fireEvent.change(screen.getByLabelText('Data prevista'), { target: { value: dataValida() } })
    fireEvent.click(screen.getByText('Avançar'))
    fireEvent.click(screen.getByText('Lavo a cada 2 dias'))
    fireEvent.click(screen.getByText('Avançar'))
    fireEvent.click(screen.getByText('Apartamento'))
    fireEvent.click(screen.getByText('Sim'))
    fireEvent.click(screen.getByText('Avançar'))
    fireEvent.click(screen.getByText('Intermediário'))
    fireEvent.click(screen.getByText('Avançar'))
    fireEvent.click(screen.getByText('Sim'))
    fireEvent.click(screen.getByText('Concluir'))

    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent('Confira os dados enviados.'),
    )
    expect(screen.getByText('Concluir')).toBeEnabled()
    expect(screen.getByText('Passo 6 de 6')).toBeInTheDocument()
  })

  it('entrar direto no passo 2 sem completar o passo 1 redireciona para o passo 1', () => {
    renderEm('/questionario/2')
    expect(screen.getByText('Passo 1 de 6')).toBeInTheDocument()
  })

  it('entrar direto no passo 6 sem completar os passos anteriores redireciona para o passo 1', () => {
    renderEm('/questionario/6')
    expect(screen.getByText('Passo 1 de 6')).toBeInTheDocument()
  })
})
