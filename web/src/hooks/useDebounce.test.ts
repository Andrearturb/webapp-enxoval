import { act, renderHook } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { useDebounce } from './useDebounce'

describe('useDebounce', () => {
  it('só atualiza depois do atraso', () => {
    vi.useFakeTimers()
    const { result, rerender } = renderHook(({ valor }) => useDebounce(valor, 300), {
      initialProps: { valor: 'a' },
    })
    expect(result.current).toBe('a')

    rerender({ valor: 'ab' })
    expect(result.current).toBe('a')

    act(() => vi.advanceTimersByTime(300))
    expect(result.current).toBe('ab')

    vi.useRealTimers()
  })
})
