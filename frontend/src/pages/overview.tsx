import {
  ArrowDownRight,
  ArrowUpRight,
  ArrowRight,
  SlidersHorizontal,
  Info,
  CalendarDays,
  Target,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { CashChart, CategoryChart } from '@/components/charts'
import { CategoryIcon } from '@/components/shared'
import { dayLabel, money } from '@/lib/format'
import type { Summary, Transaction } from '@/lib/types'

export default function Overview({
  data,
  onLedger,
  onDetail,
  onBudget,
}: {
  data: Summary
  onLedger: (category?: string, date?: string) => void
  onDetail: (row: Transaction) => void
  onBudget: () => void
}) {
  const m = data.metrics
  const change = m.expense_change
  const rate = data.budget ? (m.expense / data.budget) * 100 : 0
  return (
    <>
      <section className="money-summary" aria-label="本月收支摘要">
        <div className="primary-amount">
          <div className="metric-label">
            <span className="small-mark expense-dot" />
            本月支出<span className="metric-unit">CNY</span>
          </div>
          <div className="hero-number">{money(m.expense)}</div>
          <div className="comparison">
            {change !== null ? (
              <>
                <span className={change <= 0 ? 'good change-pill' : 'warm change-pill'}>
                  {change <= 0 ? <ArrowDownRight size={13} /> : <ArrowUpRight size={13} />}{' '}
                  {Math.abs(change).toFixed(1)}%
                </span>
                <span>较上月{data.coverage?.is_partial ? '同期' : ''}</span>
              </>
            ) : (
              <span>暂无可比的上月记录</span>
            )}
          </div>
        </div>
        <div className="secondary-metrics">
          <div>
            <span className="metric-label">
              本月收入 <ArrowDownRight size={14} />
            </span>
            <strong>{money(m.income)}</strong>
            <small>{data.month ? `${Number(data.month.slice(-2))} 月到账合计` : '到账合计'}</small>
          </div>
          <div>
            <span className="metric-label">
              本月结余 <ArrowUpRight size={14} />
            </span>
            <strong className={m.balance >= 0 ? 'good' : 'warm'}>{money(m.balance)}</strong>
            <small>收入 − 支出</small>
          </div>
          <div>
            <span className="metric-label">
              日均支出 <CalendarDays size={14} />
            </span>
            <strong>{money(m.daily_average)}</strong>
            <small>按 {data.coverage?.observed_days || 0} 个自然日计算</small>
          </div>
        </div>
      </section>
      <div className="coverage-note">
        <Info size={14} />
        <span>
          {data.coverage?.is_partial
            ? `本月账单收录至 ${dayLabel(data.coverage.last_date)}，尚非整月；环比按上月同期比较。`
            : '按已导入账单汇总，未记账的消费不包含在统计中。'}
        </span>
      </div>
      <div className="overview-charts">
        <CashChart data={data} />
        <CategoryChart data={data} onCategory={(name) => onLedger(name)} />
      </div>
      <section className="budget-strip">
        <div className="budget-title">
          <Target size={18} />
          <div>
            <h2>给生活一点余量</h2>
            <p>
              {data.budget
                ? `本月预算 ${money(data.budget)}`
                : '设置月度预算，了解每一笔支出的空间。'}
            </p>
          </div>
        </div>
        <div className="budget-progress">
          {data.budget ? (
            <>
              <div>
                <span>
                  {rate > 100
                    ? `已超出 ${money(m.expense - data.budget)}`
                    : `剩余 ${money(data.budget - m.expense)}`}
                </span>
                <b>{rate.toFixed(1)}%</b>
              </div>
              <div
                className="progress-track"
                role="progressbar"
                aria-label="月度预算使用比例"
                aria-valuenow={Math.round(Math.min(rate, 100))}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuetext={`已使用 ${rate.toFixed(1)}%`}
              >
                <i
                  style={{
                    width: `${Math.min(rate, 100)}%`,
                    background: rate > 100 ? '#ad563d' : '#496f68',
                  }}
                />
              </div>
            </>
          ) : (
            <span className="budget-empty">尚未设置预算</span>
          )}
        </div>
        <Button variant="outline" onClick={onBudget}>
          <SlidersHorizontal size={14} />
          {data.budget ? '调整预算' : '设置预算'}
        </Button>
      </section>
      <div className="overview-bottom">
        <section>
          <div className="panel-heading">
            <div>
              <h2>最近的生活片段</h2>
              <p>每一笔，都有生活的注脚</p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => onLedger()}>
              全部账单 <ArrowRight size={14} />
            </Button>
          </div>
          <div className="recent-transactions">
            {data.recent.slice(0, 5).map((row) => (
              <button key={row.id} onClick={() => onDetail(row)} className="transaction-preview">
                <CategoryIcon name={row.category} income={row.type === '收入'} />
                <span className="transaction-description">
                  <strong>
                    {row.note && row.note !== '无备注'
                      ? row.note
                      : row.subcategory !== '未分类'
                        ? row.subcategory
                        : row.category}
                  </strong>
                  <small>
                    {dayLabel(row.date)} · {row.category}
                  </small>
                </span>
                <span
                  className={row.type === '收入' ? 'transaction-value good' : 'transaction-value'}
                >
                  {row.type === '收入' ? '+' : '−'}
                  {money(row.amount)}
                </span>
                <ArrowRight size={14} className="row-arrow" />
              </button>
            ))}
          </div>
        </section>
        <section className="observations">
          <div className="panel-heading">
            <div>
              <h2>账本里的小发现</h2>
              <p>基于当前月份的真实记录</p>
            </div>
            <span className="editorial-asterisk" aria-hidden="true">
              ✳
            </span>
          </div>
          {data.insights.map((item, i) => (
            <div className="observation" key={item.title}>
              <span className="observation-index">0{i + 1}</span>
              <div>
                <h3>{item.title}</h3>
                <p>{item.body}</p>
              </div>
            </div>
          ))}
          <p className="observation-footnote">记录是理解生活的起点，不是对生活的评分。</p>
        </section>
      </div>
    </>
  )
}
