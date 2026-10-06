import { type ButtonHTMLAttributes, forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '../../lib/utils'

const buttonVariants = cva(
  'inline-flex min-h-11 items-center justify-center rounded-xl px-5 py-3 text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        principal: 'bg-principal text-white hover:bg-principal/90',
        secundario: 'bg-principal-suave text-principal hover:bg-principal-suave/80',
      },
    },
    defaultVariants: { variant: 'principal' },
  },
)

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, ...props }, ref) => (
    <button ref={ref} className={cn(buttonVariants({ variant }), className)} {...props} />
  ),
)
Button.displayName = 'Button'
