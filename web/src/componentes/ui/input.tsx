import { type InputHTMLAttributes, forwardRef } from 'react'
import { cn } from '../../lib/utils'

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        'min-h-11 w-full rounded-xl border border-principal-suave bg-superficie px-4 py-3 text-texto placeholder:text-texto-suave focus:outline focus:outline-2 focus:outline-principal',
        className,
      )}
      {...props}
    />
  ),
)
Input.displayName = 'Input'
