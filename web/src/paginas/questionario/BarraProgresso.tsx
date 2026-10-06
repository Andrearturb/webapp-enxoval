interface Props {
  passo: number
  total: number
}

export function BarraProgresso({ passo, total }: Props) {
  const percentual = Math.round((passo / total) * 100)
  return (
    <div role="progressbar" aria-valuenow={passo} aria-valuemin={1} aria-valuemax={total}>
      <p className="text-sm text-texto-suave">
        Passo {passo} de {total}
      </p>
      <div className="h-2 w-full rounded-full bg-principal-suave">
        <div className="h-2 rounded-full bg-principal" style={{ width: `${percentual}%` }} />
      </div>
    </div>
  )
}
