import {
  ArrowRight,
  Check,
  Heart,
  ListChecks,
  MapPin,
  Sparkles,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { Marca } from '../componentes/Marca'
import { IlustracaoEnxoval } from '../componentes/IlustracaoEnxoval'

const PASSOS = [
  {
    numero: '01',
    titulo: 'Responda 6 perguntas',
    descricao:
      'Conte sobre sua cidade, a chegada do bebê e a rotina da sua família.',
    icone: MapPin,
  },
  {
    numero: '02',
    titulo: 'Receba sua planilha',
    descricao:
      'Uma lista com quantidades pensadas para o seu clima, sua rotina e cada fase.',
    icone: ListChecks,
  },
  {
    numero: '03',
    titulo: 'Marque conforme compra',
    descricao:
      'Organize o que comprou, ganhou ou já tinha. Um pequeno passo de cada vez.',
    icone: Heart,
  },
]

export default function Inicio() {
  return (
    <div className="min-h-screen bg-fundo">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5 sm:px-8">
        <Marca />
        <a
          href="#como-funciona"
          className="text-sm font-medium text-texto-suave hover:text-principal"
        >
          Como funciona
        </a>
      </header>
      <main>
        <section className="mx-auto grid max-w-6xl items-center gap-5 px-5 pb-12 pt-8 sm:px-8 sm:pb-20 lg:grid-cols-2 lg:gap-16 lg:pt-14">
          <div>
            <p className="mb-5 inline-flex items-center gap-2 rounded-full border border-borda bg-superficie/70 px-3.5 py-2 text-xs font-medium text-principal">
              <Sparkles size={14} aria-hidden="true" /> Cada família tem seu
              jeito
            </p>
            <h1 className="max-w-xl font-titulo text-4xl font-semibold leading-[1.15] tracking-tight sm:text-5xl lg:text-6xl">
              O enxoval certo
              <br />
              para o seu bebê
            </h1>
            <p className="mt-5 max-w-md text-base leading-relaxed text-texto-suave sm:text-lg">
              Menos dúvidas, mais tranquilidade. Descubra o que comprar, quanto
              e quando — com uma lista feita para a sua família.
            </p>
            <Link
              to="/questionario/1"
              className="mt-7 inline-flex min-h-12 items-center gap-4 rounded-2xl bg-principal px-6 py-4 font-medium text-white transition-colors hover:bg-principal/90"
            >
              Começar meu enxoval <ArrowRight size={18} aria-hidden="true" />
            </Link>
            <div className="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-xs text-texto-suave">
              {[
                '6 perguntas simples',
                'Personalizado para você',
                'Gratuito',
              ].map((texto) => (
                <span key={texto} className="inline-flex items-center gap-1.5">
                  <Check
                    size={14}
                    className="text-principal"
                    aria-hidden="true"
                  />
                  {texto}
                </span>
              ))}
            </div>
          </div>
          <div className="relative mx-auto w-full max-w-md lg:max-w-none">
            <IlustracaoEnxoval className="mx-auto w-full max-w-[420px]" />
            <div className="relative mx-4 -mt-10 rounded-2xl border border-borda bg-superficie p-4 shadow-sm sm:mx-10">
              <div className="flex items-center gap-3">
                <span className="flex size-9 items-center justify-center rounded-xl bg-principal-suave text-principal">
                  <Heart size={18} aria-hidden="true" />
                </span>
                <div>
                  <p className="font-titulo font-semibold">Tudo no seu tempo</p>
                  <p className="mt-0.5 text-xs text-texto-suave">
                    Do primeiro body aos primeiros passos.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>
        <section
          id="como-funciona"
          className="border-y border-borda bg-superficie/60"
        >
          <div className="mx-auto max-w-6xl px-5 py-12 sm:px-8 sm:py-16">
            <p className="text-xs font-semibold uppercase tracking-[.18em] text-principal">
              Um começo mais leve
            </p>
            <h2 className="mt-3 text-3xl font-semibold">Como funciona</h2>
            <ol className="mt-8 grid gap-6 md:grid-cols-3">
              {PASSOS.map(({ numero, titulo, descricao, icone: Icone }) => (
                <li
                  key={numero}
                  className="rounded-3xl border border-borda bg-superficie p-6"
                >
                  <div className="mb-6 flex items-center justify-between">
                    <span className="flex size-11 items-center justify-center rounded-2xl bg-principal-suave text-principal">
                      <Icone size={21} aria-hidden="true" />
                    </span>
                    <span className="font-titulo text-2xl text-texto-suave">
                      {numero}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold">{titulo}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-texto-suave">
                    {descricao}
                  </p>
                </li>
              ))}
            </ol>
          </div>
        </section>
        <section className="mx-auto max-w-2xl px-5 py-14 text-center sm:py-20">
          <h2 className="text-3xl font-semibold">
            Um cuidado a menos na sua lista.
          </h2>
          <p className="mt-3 leading-relaxed text-texto-suave">
            Prepare a chegada do bebê com clareza e sem precisar comprar tudo de
            uma vez.
          </p>
          <Link
            to="/questionario/1"
            className="mt-6 inline-flex min-h-12 items-center gap-3 rounded-2xl bg-principal px-6 py-3 font-medium text-white hover:bg-principal/90"
          >
            Começar meu enxoval <ArrowRight size={18} aria-hidden="true" />
          </Link>
        </section>
      </main>
      <footer className="border-t border-borda px-5 py-6 text-center">
        <p className="text-xs leading-relaxed text-texto-suave">
          Marcas e regras de segurança em processo de validação. Confirme com
          seu pediatra.
        </p>
      </footer>
    </div>
  )
}
