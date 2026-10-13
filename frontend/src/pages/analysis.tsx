import { useQuery } from '@tanstack/react-query'
import { ArrowUpRight } from 'lucide-react'
import { WeekdayChart } from '@/components/charts'
import { Loading, ErrorState } from '@/components/shared'
import { categoryColor, dayLabel, money } from '@/lib/format'
import { request, monthQuery } from '@/lib/api'
import type { Patterns, Summary } from '@/lib/types'
export default function Analysis({
  data,
  onLedger,
}: {
  data: Summary
  onLedger: (category?: string, date?: string, subcategory?: string) => void
}) {
  const pattern = useQuery({
    queryKey: ['patterns', data.month],
    queryFn: ({ signal }) =>
      request<Patterns>(`/patterns${monthQuery(data.month || '')}`, { signal }),
  })
  const peak = [...data.daily].sort((a, b) => b.amount - a.amount)[0]
  const firstWeekday = data.month ? (new Date(`${data.month}-01T12:00:00`).getDay() + 6) % 7 : 0
  return (
    <div className="analysis-content">
      <div className="analysis-top">
        <section className="paper-panel">
          <div className="panel-heading">
            <div>
              <h2>分类支出</h2>
              <p>按支出金额排序 · 点击查看账单</p>
            </div>
          </div>
          <div className="category-ranking">
            {data.categories.map((c, i) => (
              <button key={c.name} onClick={() => onLedger(c.name)}>
                <span className="rank-index">0{i + 1}</span>
                <div>
                  <div className="rank-label">
                    <strong>{c.name}</strong>
                    <span>
                      {money(c.amount)} <small>{c.share.toFixed(1)}%</small>
                    </span>
                  </div>
                  <div className="progress-track">
                    <i style={{ width: `${c.share}%`, background: categoryColor(c.name) }} />
                  </div>
                  <small>{c.records} 笔记录</small>
                </div>
                <ArrowUpRight size={16} />
              </button>
            ))}
          </div>
        </section>
        <section className="paper-panel">
          <div className="panel-heading">
            <div>
              <h2>一周的消费偏好</h2>
              <p>按星期累计支出 · 人民币 / 元</p>
            </div>
          </div>
          <WeekdayChart data={data} />
          <div className="weekday-accessible">
            {data.weekday.map((d) => (
              <span key={d.name}>
                {d.name} <b>{money(d.amount)}</b>
              </span>
            ))}
          </div>
        </section>
      </div>
      <div className="analysis-bottom">
        <section className="paper-panel">
          <div className="panel-heading">
            <div>
              <h2>消费日历</h2>
              <p>
                {peak?.amount
                  ? `最高支出日 ${dayLabel(peak.date)} · ${money(peak.amount)}`
                  : '当月暂无支出'}
              </p>
            </div>
            <span className="quiet-count">点击日期</span>
          </div>
          <div className="calendar-grid">
            {['一', '二', '三', '四', '五', '六', '日'].map((d) => (
              <span className="calendar-weekday" key={d}>
                {d}
              </span>
            ))}
            {Array.from({ length: firstWeekday }, (_, i) => (
              <span key={`blank-${i}`} />
            ))}
            {Array.from({ length: data.coverage?.month_days || 0 }, (_, i) => {
              const row = data.daily[i]
              return (
                <button
                  key={i}
                  disabled={!row}
                  onClick={() => onLedger(undefined, row.date)}
                  aria-label={`${i + 1}日，${row ? money(row.amount) : '未收录'}，查看账单`}
                  style={{
                    background: row?.amount
                      ? `rgba(173,86,61,${0.06 + (row.amount / (peak?.amount || 1)) * 0.15})`
                      : undefined,
                  }}
                >
                  <b>{i + 1}</b>
                  <span>{row ? (row.amount ? money(row.amount) : '—') : ''}</span>
                </button>
              )
            })}
          </div>
          <p className="quiet-note">「—」表示没有支出记录；灰色日期尚未收录。</p>
        </section>
        <section className="paper-panel">
          <div className="panel-heading">
            <div>
              <h2>再看细一点</h2>
              <p>二级分类 · 支出前 12 项</p>
            </div>
          </div>
          {pattern.isPending ? (
            <Loading />
          ) : pattern.isError ? (
            <ErrorState error={pattern.error} retry={() => pattern.refetch()} />
          ) : (
            <div className="subcategories">
              {pattern.data.subcategories.map((row, i) => (
                <button
                  key={`${row.category}-${row.subcategory}`}
                  onClick={() => onLedger(row.category, undefined, row.subcategory)}
                >
                  <span className="rank-index">{String(i + 1).padStart(2, '0')}</span>
                  <span>
                    <strong>{row.subcategory}</strong>
                    <small>
                      {row.category} · {row.records} 笔
                    </small>
                  </span>
                  <b>{money(row.amount)}</b>
                </button>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
