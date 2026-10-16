import { useRef } from 'react'
import { ArrowUpRight, NotebookPen, ArrowDown } from 'lucide-react'
import { useMotionPreference } from './motion'
import { usePointerSpring } from './pointer-motion'
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
    surface = useRef<HTMLDivElement>(null)
  usePointerSpring(surface, card, data.month)
  return (
    <div className="chapter-art" ref={surface}>
      <div className="chapter-scroll-layer">
        <div className="chapter-enter" key={data.month}>
          <div className="chapter-paper chapter-paper-back" aria-hidden="true" />
          <div className="chapter-paper chapter-paper-middle" aria-hidden="true" />
          <button
            ref={card}
            className="chapter-card"
            onClick={onEdit}
            aria-label="编辑月度手记与月结状态"
          >
            <span className="chapter-spotlight" aria-hidden="true" />
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
              {data.review?.note ? '编辑月度手记' : '添加月度手记'}
            </span>
          </button>
        </div>
      </div>
    </div>
  )
}
export function ChapterMeta({ data }: { data: Summary }) {
  const { reduced } = useMotionPreference()
  return (
    <div className="chapter-meta">
      <span>
        <i />
        {data.metrics.records} 笔账单
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
        {data.review?.note || '暂无手记，可补充本月支出说明。'}
      </p>
      <button className="text-link" onClick={onEdit}>
        {data.review?.note ? '编辑手记与月结' : '写下本月手记'}
        <ArrowUpRight size={14} aria-hidden="true" />
      </button>
    </section>
  )
}
