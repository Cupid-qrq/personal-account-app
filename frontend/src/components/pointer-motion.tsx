import { useEffect, useRef, type ComponentProps, type RefObject } from 'react'
import { Button } from './ui/button'
import { useMotionPreference } from './motion'

/** Stable hit area, separate moving surface, and a damped spring that sleeps at rest. */
export function usePointerSpring(
  surfaceRef: RefObject<HTMLElement | null>,
  targetRef: RefObject<HTMLElement | null>,
  identity?: string | null,
) {
  const { reduced } = useMotionPreference()
  useEffect(() => {
    const surface = surfaceRef.current,
      target = targetRef.current
    if (!surface || !target) return
    const fine = matchMedia('(hover: hover) and (pointer: fine)')
    let frame = 0,
      last = 0,
      point: { x: number; y: number } | null = null
    const value = { x: 0, y: 0, lift: 0 },
      velocity = { x: 0, y: 0, lift: 0 },
      goal = { x: 0, y: 0, lift: 0 }
    const keys = ['x', 'y', 'lift'] as const
    function write() {
      target!.style.setProperty('--pointer-x', value.x.toFixed(4))
      target!.style.setProperty('--pointer-y', value.y.toFixed(4))
      target!.style.setProperty('--pointer-active', Math.max(0, Math.min(1, value.lift)).toFixed(4))
    }
    function stop() {
      cancelAnimationFrame(frame)
      frame = last = 0
      point = null
      keys.forEach((key) => {
        value[key] = velocity[key] = goal[key] = 0
      })
      write()
      target!.dataset.pointerMotion = 'idle'
    }
    stop()
    if (reduced) return stop
    function paint(time: number) {
      const dt = last ? Math.min((time - last) / 1000, 0.032) : 1 / 60
      last = time
      // One geometry read per pointer frame, before writing any visual styles.
      if (point) {
        const bounds = surface!.getBoundingClientRect()
        goal.x = Math.max(-1, Math.min(1, ((point.x - bounds.left) / bounds.width) * 2 - 1))
        goal.y = Math.max(-1, Math.min(1, ((point.y - bounds.top) / bounds.height) * 2 - 1))
        point = null
      }
      let moving = false
      for (const key of keys) {
        velocity[key] += ((goal[key] - value[key]) * 190 - velocity[key] * 20) * dt
        value[key] += velocity[key] * dt
        if (Math.abs(goal[key] - value[key]) > 0.001 || Math.abs(velocity[key]) > 0.008)
          moving = true
      }
      if (!moving)
        keys.forEach((key) => {
          value[key] = goal[key]
          velocity[key] = 0
        })
      write()
      target!.dataset.pointerMotion = moving ? 'moving' : 'idle'
      frame = moving ? requestAnimationFrame(paint) : 0
      if (!moving) last = 0
    }
    function schedule() {
      if (!frame) frame = requestAnimationFrame(paint)
    }
    function move(event: PointerEvent) {
      if (!fine.matches || event.pointerType !== 'mouse') return
      point = { x: event.clientX, y: event.clientY }
      goal.lift = 1
      schedule()
    }
    function leave() {
      point = null
      goal.x = goal.y = goal.lift = 0
      schedule()
    }
    surface.addEventListener('pointerenter', move)
    surface.addEventListener('pointermove', move, { passive: true })
    surface.addEventListener('pointerleave', leave)
    surface.addEventListener('pointercancel', leave)
    surface.addEventListener('focusout', leave)
    window.addEventListener('blur', stop)
    document.addEventListener('visibilitychange', stop)
    fine.addEventListener('change', stop)
    return () => {
      stop()
      surface.removeEventListener('pointerenter', move)
      surface.removeEventListener('pointermove', move)
      surface.removeEventListener('pointerleave', leave)
      surface.removeEventListener('pointercancel', leave)
      surface.removeEventListener('focusout', leave)
      window.removeEventListener('blur', stop)
      document.removeEventListener('visibilitychange', stop)
      fine.removeEventListener('change', stop)
    }
  }, [reduced, identity, surfaceRef, targetRef])
}

export function MagneticButton({
  children,
  className = '',
  ...props
}: ComponentProps<typeof Button>) {
  const surface = useRef<HTMLSpanElement>(null),
    button = useRef<HTMLButtonElement>(null)
  usePointerSpring(surface, button)
  return (
    <span ref={surface} className="magnetic-zone">
      <Button {...props} ref={button} className={`magnetic-button ${className}`}>
        <span className="magnetic-content">{children}</span>
      </Button>
    </span>
  )
}
