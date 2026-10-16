import {
  createContext,
  useContext,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { Sparkles, Leaf } from 'lucide-react'
import { Button } from './ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip'

const MotionContext = createContext({ reduced: false, systemReduced: false, toggle: () => {} })
const storageKey = 'ledger-atlas:motion:v1'
export function MotionProvider({ children }: { children: ReactNode }) {
  const [systemReduced, setSystemReduced] = useState(
    () => matchMedia('(prefers-reduced-motion: reduce)').matches,
  )
  const [quiet, setQuiet] = useState(() => {
    try {
      return localStorage.getItem(storageKey) === 'reduce'
    } catch {
      return false
    }
  })
  const reduced = quiet || systemReduced
  useEffect(() => {
    const query = matchMedia('(prefers-reduced-motion: reduce)')
    const change = () => setSystemReduced(query.matches)
    query.addEventListener('change', change)
    return () => query.removeEventListener('change', change)
  }, [])
  useLayoutEffect(() => {
    document.documentElement.dataset.motion = reduced ? 'reduce' : 'full'
    if (reduced)
      document
        .getAnimations()
        .filter((a) => a.id.startsWith('atlas-'))
        .forEach((a) => a.cancel())
  }, [reduced])
  function toggle() {
    if (systemReduced) return
    setQuiet((value) => {
      try {
        localStorage.setItem(storageKey, !value ? 'reduce' : 'full')
      } catch {
        /* Preference is still kept for this session. */
      }
      return !value
    })
  }
  return (
    <MotionContext.Provider value={{ reduced, systemReduced, toggle }}>
      {children}
    </MotionContext.Provider>
  )
}
export const useMotionPreference = () => useContext(MotionContext)

export function MotionToggle() {
  const { reduced, systemReduced, toggle } = useMotionPreference()
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label={
            systemReduced ? '已遵循系统减少动态效果设置' : reduced ? '开启动效' : '减少动态效果'
          }
          aria-pressed={!reduced}
          aria-disabled={systemReduced}
          onClick={toggle}
        >
          {reduced ? <Leaf size={16} /> : <Sparkles size={16} />}
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        {systemReduced
          ? '已遵循系统的减少动态效果设置'
          : reduced
            ? '已减少动态效果 · 点击恢复'
            : '减少动态效果'}
      </TooltipContent>
    </Tooltip>
  )
}

/** One passive listener; transforms update without rerendering React or the charts. */
export function useReadingMotion(sceneKey: string) {
  const { reduced } = useMotionPreference()
  useEffect(() => {
    let frame = 0
    const nativeScroll = CSS.supports('animation-timeline', 'scroll(root block)')
    document.documentElement.dataset.scrollEngine = nativeScroll ? 'native' : 'fallback'
    function paint() {
      frame = 0
      const top = window.scrollY
      const length = Math.max(1, document.documentElement.scrollHeight - innerHeight)
      const root = document.documentElement
      root.style.setProperty('--reading-progress', String(Math.min(1, top / length)))
      root.style.setProperty(
        '--hero-progress',
        reduced ? '0' : String(Math.max(0, Math.min(1, top / 260))),
      )
      root.dataset.scrolled = top > 40 ? 'true' : 'false'
    }
    function schedule() {
      if (!frame) frame = requestAnimationFrame(paint)
    }
    const observer = new ResizeObserver(schedule)
    observer.observe(document.body)
    window.addEventListener('scroll', schedule, { passive: true })
    window.addEventListener('resize', schedule)
    schedule()
    return () => {
      cancelAnimationFrame(frame)
      observer.disconnect()
      window.removeEventListener('scroll', schedule)
      window.removeEventListener('resize', schedule)
    }
  }, [sceneKey, reduced])
}

export function MotionScene({ children, sceneKey }: { children: ReactNode; sceneKey: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const { reduced } = useMotionPreference()
  useEffect(() => {
    const root = ref.current
    if (!root || reduced) return
    const registered = new WeakSet<Element>(),
      animations = new Set<Animation>()
    const observer = new IntersectionObserver(
      (entries) => {
        let stagger = 0
        for (const entry of entries) {
          if (!entry.isIntersecting) continue
          observer.unobserve(entry.target)
          // Content is visible by default. Never depend on animation completion for correctness.
          entry.target.setAttribute('data-revealed', 'true')
          const animation = entry.target.animate([{ translate: '0 14px' }, { translate: '0 0' }], {
            id: 'atlas-reveal',
            duration: 480,
            delay: Math.min(stagger++ * 40, 160),
            easing: 'cubic-bezier(.22,1,.36,1)',
          })
          animations.add(animation)
          animation.finished.catch(() => {}).finally(() => animations.delete(animation))
        }
      },
      { threshold: 0.08, rootMargin: '0px 0px -24px 0px' },
    )
    function register() {
      root!
        .querySelectorAll(
          '.money-summary,.overview-charts,.budget-strip,.overview-bottom>section,.paper-panel,.import-callout,.ledger-content,.month-note-panel,.recent-transactions>button',
        )
        .forEach((element) => {
          if (!registered.has(element)) {
            registered.add(element)
            observer.observe(element)
          }
        })
    }
    register()
    const mutation = new MutationObserver(register)
    mutation.observe(root, { subtree: true, childList: true })
    return () => {
      observer.disconnect()
      mutation.disconnect()
      animations.forEach((a) => a.cancel())
    }
  }, [sceneKey, reduced])
  return (
    <div ref={ref} className="motion-scene" data-scene={sceneKey}>
      {children}
    </div>
  )
}
