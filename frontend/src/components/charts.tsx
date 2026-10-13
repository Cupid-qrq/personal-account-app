import { useState } from 'react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { categoryColor, dayLabel, money } from '@/lib/format'
import type { Summary } from '@/lib/types'

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tooltip">
      <strong>{String(label || payload[0]?.name || '')}</strong>
      {payload.map((item: any, i: number) => (
        <div key={i}>
          <span>
            <i style={{ background: item.color || item.payload?.fill || '#ad563d' }} />
            {item.name}
          </span>
          <b>{money(Number(item.value))}</b>
        </div>
      ))}
    </div>
  )
}
const axis = { fill: '#706e65', fontSize: 12 }
export function CashChart({ data }: { data: Summary }) {
  const [mode, setMode] = useState('daily')
  const [table, setTable] = useState(false)
  const daily = data.daily.map((row) => ({ ...row, label: `${Number(row.date.slice(-2))}日` }))
  const annual = data.trend
    .filter((row) => row.month.startsWith(data.month?.slice(0, 4) || ''))
    .map((row) => ({ ...row, label: `${Number(row.month.slice(-2))}月` }))
  return (
    <section className="chart-panel">
      <div className="panel-heading">
        <div>
          <h2>{mode === 'daily' ? '消费的日常节奏' : '这一年的收与支'}</h2>
          <p>{mode === 'daily' ? '每日支出 · 人民币 / 元' : '月度汇总 · 人民币 / 元'}</p>
        </div>
        <Tabs value={mode} onValueChange={setMode}>
          <TabsList aria-label="图表时间范围">
            <TabsTrigger id="cash-tab-daily" aria-controls="cash-chart-content" value="daily">
              本月
            </TabsTrigger>
            <TabsTrigger id="cash-tab-annual" aria-controls="cash-chart-content" value="annual">
              年度
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>
      <div className="chart-summary">
        <strong>
          {money(
            mode === 'daily' ? data.metrics.expense : annual.reduce((v, row) => v + row.expense, 0),
          )}
        </strong>
        <span>
          {mode === 'daily'
            ? `已记录 ${data.coverage?.observed_days || 0} 天`
            : `${annual.length} 个月的支出`}
        </span>
      </div>
      <div
        id="cash-chart-content"
        className="chart-canvas"
        role="tabpanel"
        aria-labelledby={mode === 'daily' ? 'cash-tab-daily' : 'cash-tab-annual'}
        aria-label={
          mode === 'daily'
            ? '本月每日支出趋势；可通过下方按钮查看数据表'
            : '年度收入与支出对比；可通过下方按钮查看数据表'
        }
      >
        <ResponsiveContainer width="100%" height={222} minWidth={0}>
          {mode === 'daily' ? (
            <AreaChart
              data={daily}
              margin={{ top: 18, right: 16, bottom: 4, left: -13 }}
              accessibilityLayer
            >
              <defs>
                <linearGradient id="expense-fill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ad563d" stopOpacity={0.15} />
                  <stop offset="100%" stopColor="#ad563d" stopOpacity={0.01} />
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} stroke="#e7e4dd" strokeDasharray="3 5" />
              <XAxis
                dataKey="label"
                tick={axis}
                axisLine={false}
                tickLine={false}
                minTickGap={20}
                dy={8}
              />
              <YAxis tick={axis} axisLine={false} tickLine={false} width={52} tickCount={4} />
              <Tooltip content={<ChartTooltip />} />
              <Area
                name="支出"
                dataKey="amount"
                type="monotone"
                stroke="#ad563d"
                strokeWidth={2.5}
                fill="url(#expense-fill)"
                isAnimationActive={false}
                activeDot={{ r: 5, stroke: '#fff', strokeWidth: 2 }}
              />
            </AreaChart>
          ) : (
            <BarChart
              data={annual}
              margin={{ top: 18, right: 6, bottom: 4, left: -13 }}
              accessibilityLayer
            >
              <CartesianGrid vertical={false} stroke="#e7e4dd" strokeDasharray="3 5" />
              <XAxis dataKey="label" tick={axis} axisLine={false} tickLine={false} />
              <YAxis
                tick={axis}
                axisLine={false}
                tickLine={false}
                width={52}
                tickFormatter={(value) => (value >= 1000 ? `${value / 1000}k` : value)}
              />
              <Tooltip content={<ChartTooltip />} />
              <Bar
                dataKey="income"
                name="收入"
                fill="#496f68"
                radius={[3, 3, 0, 0]}
                maxBarSize={18}
                isAnimationActive={false}
              />
              <Bar
                dataKey="expense"
                name="支出"
                fill="#ad563d"
                radius={[3, 3, 0, 0]}
                maxBarSize={18}
                isAnimationActive={false}
              />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
      <div className="chart-foot">
        <span className="chart-legend">
          <i className="expense-dot" />
          支出
          {mode === 'annual' && (
            <>
              <i className="income-dot" />
              收入
            </>
          )}
        </span>
        <Button variant="ghost" size="sm" onClick={() => setTable(!table)} aria-expanded={table}>
          {table ? '收起数据' : '查看数据表'}
        </Button>
      </div>
      {table && (
        <div className="chart-data-table">
          <table>
            <caption className="sr-only">{mode === 'daily' ? '每日支出' : '每月收支'}</caption>
            <thead>
              <tr>
                <th scope="col">日期</th>
                {mode === 'annual' && <th scope="col">收入</th>}
                <th scope="col">支出</th>
              </tr>
            </thead>
            <tbody>
              {mode === 'daily'
                ? daily.map((row) => (
                    <tr key={row.date}>
                      <td>{dayLabel(row.date)}</td>
                      <td>{money(row.amount)}</td>
                    </tr>
                  ))
                : annual.map((row) => (
                    <tr key={row.month}>
                      <td>{row.month}</td>
                      <td>{money(row.income)}</td>
                      <td>{money(row.expense)}</td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
export function CategoryChart({
  data,
  onCategory,
}: {
  data: Summary
  onCategory: (name: string) => void
}) {
  return (
    <section className="category-panel">
      <div className="panel-heading">
        <div>
          <h2>钱花在了哪里</h2>
          <p>支出构成 · 点击分类查看明细</p>
        </div>
        <span className="quiet-count">{data.categories.length} 类</span>
      </div>
      {data.categories.length ? (
        <>
          <div className="donut-chart" aria-label="支出分类比例图">
            <ResponsiveContainer width="100%" height={182} minWidth={0}>
              <PieChart>
                <Pie
                  data={data.categories}
                  nameKey="name"
                  dataKey="amount"
                  innerRadius={60}
                  outerRadius={78}
                  paddingAngle={4}
                  stroke="none"
                  isAnimationActive={false}
                >
                  {data.categories.map((c) => (
                    <Cell key={c.name} fill={categoryColor(c.name)} />
                  ))}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="donut-label">
              <span>支出分类</span>
              <strong>
                {data.categories.length}
                <small> 类</small>
              </strong>
            </div>
          </div>
          <div className="category-legend">
            {data.categories.map((c) => (
              <button
                key={c.name}
                onClick={() => onCategory(c.name)}
                aria-label={`查看${c.name}明细`}
              >
                <span className="category-name">
                  <i style={{ background: categoryColor(c.name) }} />
                  {c.name}
                </span>
                <span className="category-share">{c.share.toFixed(1)}%</span>
                <strong>{money(c.amount)}</strong>
              </button>
            ))}
          </div>
        </>
      ) : (
        <div className="empty-chart">当月暂无支出记录</div>
      )}
    </section>
  )
}
export function WeekdayChart({ data }: { data: Summary }) {
  return (
    <div className="weekday-canvas">
      <ResponsiveContainer width="100%" height={235} minWidth={0}>
        <BarChart
          data={data.weekday}
          accessibilityLayer
          margin={{ top: 15, right: 8, bottom: 0, left: -16 }}
        >
          <CartesianGrid vertical={false} stroke="#e7e4dd" strokeDasharray="3 5" />
          <XAxis dataKey="name" tick={axis} axisLine={false} tickLine={false} />
          <YAxis tick={axis} axisLine={false} tickLine={false} />
          <Tooltip content={<ChartTooltip />} />
          <Bar
            dataKey="amount"
            name="支出"
            fill="#496f68"
            radius={[4, 4, 0, 0]}
            maxBarSize={32}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
