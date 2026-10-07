import { Link } from 'react-router-dom'

const PASSOS = [
  {
    numero: '1',
    titulo: 'Responda 6 perguntas',
    descricao: 'Cidade, data prevista, rotina de lavagem, moradia, orçamento e se é o primeiro filho.',
  },
  {
    numero: '2',
    titulo: 'Receba sua planilha',
    descricao: 'Lista personalizada com quantidades calculadas para o seu clima, rotina e fase do bebê.',
  },
  {
    numero: '3',
    titulo: 'Marque conforme compra',
    descricao: 'Registre o que comprou, ganhou ou já tinha. Os dados ficam salvos e abrem em qualquer aparelho.',
  },
]

export default function Inicio() {
  return (
    <div className="min-h-screen bg-fundo">
      {/* Hero */}
      <main>
        <section className="mx-auto max-w-2xl px-4 py-16 text-center">
          <h1 className="font-titulo text-4xl font-semibold leading-tight text-texto">
            O enxoval certo para o seu bebê
          </h1>
          <p className="mx-auto mt-4 max-w-md text-lg text-texto-suave">
            Responda 6 perguntas e receba uma lista personalizada — quantidades certas
            para a sua cidade, data e rotina.
          </p>
          <Link
            to="/questionario/1"
            className="mt-8 inline-block rounded-2xl bg-principal px-8 py-4 font-medium text-white shadow-sm hover:opacity-90 transition-opacity"
          >
            Começar meu enxoval
          </Link>
        </section>

        {/* Como funciona */}
        <section className="border-t border-principal-suave bg-superficie">
          <div className="mx-auto max-w-2xl px-4 py-12">
            <h2 className="mb-8 text-center font-titulo text-2xl font-semibold text-texto">
              Como funciona
            </h2>
            <ol className="space-y-6">
              {PASSOS.map((passo) => (
                <li key={passo.numero} className="flex gap-4">
                  <span
                    className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-principal font-semibold text-white"
                    aria-hidden
                  >
                    {passo.numero}
                  </span>
                  <div>
                    <h3 className="font-semibold text-texto">{passo.titulo}</h3>
                    <p className="mt-1 text-sm text-texto-suave">{passo.descricao}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* CTA final */}
        <section className="mx-auto max-w-2xl px-4 py-12 text-center">
          <p className="text-texto-suave">
            Gratuito, sem cadastro e sem anúncios.
          </p>
          <Link
            to="/questionario/1"
            className="mt-4 inline-block rounded-2xl bg-principal px-8 py-4 font-medium text-white shadow-sm hover:opacity-90 transition-opacity"
          >
            Começar meu enxoval
          </Link>
        </section>
      </main>

      {/* Rodapé */}
      <footer className="border-t border-principal-suave px-4 py-6 text-center">
        <p className="text-xs text-texto-suave">
          Marcas e regras de segurança em processo de validação. Confirme com seu pediatra.
        </p>
      </footer>
    </div>
  )
}
