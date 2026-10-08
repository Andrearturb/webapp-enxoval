import { Link } from 'react-router-dom'

export function Marca({ destino = '/' }: { destino?: string }) {
  return (
    <Link
      to={destino}
      className="inline-flex items-center gap-2.5 text-texto"
      aria-label="Enxoval Inteligente — início"
    >
      <span className="flex size-10 shrink-0 items-center justify-center rounded-2xl bg-principal text-white">
        <svg
          viewBox="0 0 32 32"
          className="size-7"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M7 22c2 6 16 6 18 0M16 22V11M16 16C8 16 7 11 8 7c6 0 9 3 8 9ZM16 13c0-6 4-8 9-8 1 5-3 9-9 8Z"
            stroke="currentColor"
            strokeWidth="1.7"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      <span className="font-titulo text-base font-semibold leading-tight sm:text-lg">
        Enxoval
        <br className="sm:hidden" /> Inteligente
      </span>
    </Link>
  )
}
