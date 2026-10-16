import { useEffect, useRef, type PointerEvent } from 'react'
import { ArrowUpRight, NotebookPen, Check, ArrowDown } from 'lucide-react'
import { useMotionPreference } from './motion'
import type { Summary } from '@/lib/types'
import { dayLabel } from '@/lib/format'

export const reviewLabel = (data: Summary) =>
  data.review?.status === 'closed'
    ? '已完成月结'
    : data.review?.status === 'in_progress'
      ? '仍在记录'
      : '自动判断'
export function ChapterCard({ data, onEdit }: { data: Summary; onEdit: () => void }) {
  const card = useRef<HTMLButtonElement>(null),
    frame = useRef(0),
    bounds = useRef<DOMRect | null>(null)
  const { reduced } = useMotionPreference()
  function reset() {
    cancelAnimationFrame(frame.current)
    card.current?.style.setProperty('--tilt-x', '0deg')
    card.current?.style.setProperty('--tilt-y', '0deg')
  }
  useEffect(() => {
    reset()
    return () => cancelAnimationFrame(frame.current)
  }, [reduced, data.month])
  function tilt(event: PointerEvent) {
    if (reduced || event.pointerType !== 'mouse' || !bounds.current) return
    const x = (event.clientX - bounds.current.left) / bounds.current.width - 0.5
    const y = (event.clientY - bounds.current.top) / bounds.current.height - 0.5
    cancelAnimationFrame(frame.current)
    frame.current = requestAnimationFrame(() => {
      card.current?.style.setProperty('--tilt-x', `${-y * 5}deg`)
      card.current?.style.setProperty('--tilt-y', `${x * 5}deg`)
    })
  }
  return (
    <div className="chapter-art" key={data.month}>
      <div className="chapter-paper-back" aria-hidden="true" />
      <button
        ref={card}
        className="chapter-card"
        onClick={onEdit}
        aria-label="编辑月度手记与月结状态"
        onPointerEnter={() => {
          bounds.current = card.current?.getBoundingClientRect() || null
        }}
        onPointerMove={tilt}
        onPointerLeave={reset}
        onBlur={reset}
      >
        <span className="chapter-topline">
          <span>{data.month?.slice(0, 4)} / MONTHLY JOURNAL</span>
          <ArrowUpRight size={15} aria-hidden="true" />
        </span>
        <span className="chapter-number" aria-hidden="true">
          {data.month?.slice(-2)}
          <span className="chapter-flower">✳</span>
        </span>
        <span className="chapter-rule" aria-hidden="true" />
        <span className="chapter-caption">
          <NotebookPen size={14} aria-hidden="true" />
          {data.review?.note ? '这个月，有话想记下' : '给这个月，留一句话'}
        </span>
        <span className={`chapter-stamp ${data.review?.status === 'closed' ? 'closed' : ''}`}>
          {data.review?.status === 'closed' ? (
            <Check size={12} aria-hidden="true" />
          ) : (
            <span className="stamp-dot" />
          )}
          {data.review?.status === 'closed' ? '已月结' : '生活记录中'}
        </span>
      </button>
    </div>
  )
}
export function ChapterMeta({ data }: { data: Summary }) {
  const { reduced } = useMotionPreference()
  return (
    <div className="chapter-meta">
      <span>
        <i />
        {data.metrics.records} 笔生活片段
      </span>
      <span>{data.coverage ? `收录至 ${dayLabel(data.coverage.last_date)}` : '等待新的记录'}</span>
      <a
        href="#monthly-details"
        onClick={(e) => {
          e.preventDefault()
          document
            .getElementById('monthly-details')
            ?.scrollIntoView({ behavior: reduced ? 'instant' : 'smooth', block: 'start' })
        }}
        aria-label="向下阅读本月收支"
      >
        <ArrowDown size={14} aria-hidden="true" />
        <span>继续阅读</span>
      </a>
    </div>
  )
}
export function MonthNote({ data, onEdit }: { data: Summary; onEdit: () => void }) {
  return (
    <section className="month-note-panel">
      <div>
        <span className="note-eyebrow">
          <NotebookPen size={14} aria-hidden="true" />
          本月手记
        </span>
        <span className="note-status">{reviewLabel(data)}</span>
      </div>
      <p className={data.review?.note ? '' : 'note-placeholder'}>
        {data.review?.note ||
          '数字记录花费，文字留下生活。记下这个月的小事，也让家人更了解你的日常。'}
      </p>
      <button className="text-link" onClick={onEdit}>
        {data.review?.note ? '编辑手记与月结' : '写下本月手记'}
        <ArrowUpRight size={14} aria-hidden="true" />
      </button>
    </section>
  )
}
