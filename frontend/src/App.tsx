import { lazy, Suspense, useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowUpRight,
  BookOpen,
  ChartNoAxesCombined,
  ChevronRight,
  Download,
  FileSpreadsheet,
  LayoutDashboard,
  NotebookPen,
  Plus,
  RefreshCw,
  Search,
  Printer,
  CircleHelp,
} from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { Toaster } from '@/components/ui/sonner'
import { Choice, Empty, ErrorState, Loading } from '@/components/shared'
import { BudgetDialog, ImportDialog, TransactionDetail } from '@/components/dialogs'
import { request, monthQuery } from '@/lib/api'
import { useLocationState } from '@/lib/location'
import { dayLabel, exportCsv, money, monthLabel } from '@/lib/format'
import type { Summary, Transaction, View } from '@/lib/types'
const Overview = lazy(() => import('@/pages/overview'))
const Analysis = lazy(() => import('@/pages/analysis'))
const Ledger = lazy(() => import('@/pages/ledger'))
const DataPage = lazy(() => import('@/pages/data'))
const navigation = [
  { id: 'overview', label: '月度总览', icon: LayoutDashboard },
  { id: 'analysis', label: '消费分析', icon: ChartNoAxesCombined },
  { id: 'ledger', label: '账单明细', icon: BookOpen },
  { id: 'data', label: '数据管理', icon: FileSpreadsheet },
] as const
const monthsCN = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二']
export function App() {
  const location = useLocationState(),
    qc = useQueryClient()
  const { view, month, params, update } = location
  const [importOpen, setImportOpen] = useState(false),
    [budgetOpen, setBudgetOpen] = useState(false),
    [detail, setDetail] = useState<Transaction | null>(null)
  const summary = useQuery({
    queryKey: ['summary', month],
    queryFn: ({ signal }) => request<Summary>(`/summary${monthQuery(month)}`, { signal }),
  })
  const health = useQuery({
    queryKey: ['health'],
    queryFn: () => request<{ rows: number; auth_required: boolean }>('/health'),
  })
  const data = summary.data,
    selectedMonth = data?.month || month
  const currentNav = navigation.find((item) => item.id === view)!
  const title =
    view === 'overview'
      ? `${selectedMonth ? monthsCN[Number(selectedMonth.slice(-2)) - 1] : '每个'}月的生活账本`
      : currentNav.label
  const subtitle = {
    overview: '收支之间，读懂生活的日常。',
    analysis: '从类别、频率与时间，看看生活的消费习惯。',
    ledger: '保留每一笔的细节，让所有数字都有来处。',
    data: '从一份原始文件，到一份清楚的生活记录。',
  }[view]
  useEffect(() => {
    document.title = `${currentNav.label} · Ledger Atlas`
  }, [currentNav.label])
  function navigate(next: View) {
    update({ view: next === 'overview' ? null : next })
    window.scrollTo({ top: 0, behavior: 'instant' })
    requestAnimationFrame(() => document.getElementById('page-title')?.focus())
  }
  function openLedger(category?: string, date?: string, subcategory?: string) {
    update({
      view: 'ledger',
      category: category || null,
      subcategory: subcategory || null,
      date: date || null,
      page: null,
      q: null,
      type: null,
    })
    window.scrollTo({ top: 0, behavior: 'instant' })
  }
  async function refresh() {
    await qc.invalidateQueries({ refetchType: 'none' })
    const result = await summary.refetch()
    await qc.refetchQueries({
      type: 'active',
      predicate: (query) => query.queryKey[0] !== 'summary',
    })
    if (result.isError) toast.error('连接失败，请检查服务后重试')
    else toast.success('已重新读取账本数据')
  }
  function downloadReport() {
    if (!data) return
    exportCsv(
      [
        {
          月份: data.month,
          收入: data.metrics.income,
          支出: data.metrics.expense,
          结余: data.metrics.balance,
          日均支出: data.metrics.daily_average,
          记录数: data.metrics.records,
          收录截至: data.coverage?.last_date,
          观察天数: data.coverage?.observed_days,
          预算: data.budget ?? '未设置',
        },
      ],
      `${data.month}-月度摘要.csv`,
    )
  }
  return (
    <TooltipProvider>
      <a className="skip-link" href="#main-content">
        跳到主要内容
      </a>
      <div className="app-shell">
        <aside className="sidebar">
          <a className="brand" href="/" aria-label="Ledger Atlas 首页">
            <span className="brand-symbol">
              <NotebookPen size={23} strokeWidth={1.45} />
            </span>
            <span translate="no">
              Ledger Atlas<small>个人生活账本</small>
            </span>
          </a>
          <Button className="sidebar-import" onClick={() => setImportOpen(true)} variant="outline">
            <Plus size={16} />
            导入账单<span>+</span>
          </Button>
          <div className="nav-caption">我的账本</div>
          <nav className="sidebar-nav" aria-label="主导航">
            {navigation.map(({ id, label, icon: Icon }) => (
              <a
                key={id}
                href={`?${new URLSearchParams({ ...(selectedMonth ? { month: selectedMonth } : {}), view: id })}`}
                aria-current={view === id ? 'page' : undefined}
                className={view === id ? 'active' : ''}
                onClick={(e) => {
                  if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return
                  e.preventDefault()
                  navigate(id)
                }}
              >
                <Icon size={18} strokeWidth={1.6} />
                <span>{label}</span>
                {id === 'ledger' && data && <small>{data.metrics.records}</small>}
              </a>
            ))}
          </nav>
          <div className="sidebar-collection">
            <span className="nav-caption">归档</span>
            <div>
              <span className="archive-icon">{selectedMonth?.slice(0, 4) || '—'}</span>
              <span>
                年度记录<small>{data?.months.length || 0} 个月的生活</small>
              </span>
            </div>
          </div>
          <div className="sidebar-bottom">
            <div className="sidebar-quote">
              <span className="tiny-asterisk" aria-hidden="true">
                ✳
              </span>
              <p>
                认真记录，
                <br />
                从容生活。
              </p>
              <span>MAKE ROOM FOR LIFE.</span>
            </div>
            <button className="sidebar-help" onClick={() => navigate('data')}>
              <CircleHelp size={16} />
              数据与导入说明
              <ArrowUpRight size={14} />
            </button>
            <div className="profile">
              <span className="avatar">我</span>
              <div>
                <strong>我的生活账本</strong>
                <small>本人 · 家庭共同阅读</small>
              </div>
            </div>
          </div>
        </aside>
        <div className="app-body">
          <header className="topbar">
            <div className="breadcrumb">
              <NotebookPen size={16} />
              <span>个人账本</span>
              <ChevronRight size={13} />
              <strong>{currentNav.label}</strong>
            </div>
            <div className="header-actions">
              <span className="sync-status">
                <i className={summary.isError ? 'offline' : ''} />
                {summary.isFetching ? '同步中…' : summary.isError ? '连接异常' : '账本已同步'}
              </span>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label="刷新账本"
                    onClick={refresh}
                    disabled={summary.isFetching}
                  >
                    <RefreshCw size={16} className={summary.isFetching ? 'animate-spin' : ''} />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>重新读取最新数据</TooltipContent>
              </Tooltip>
              <Button
                variant="ghost"
                size="icon"
                aria-label="搜索账单"
                onClick={() => openLedger()}
              >
                <Search size={17} />
              </Button>
              <span className="mini-avatar" aria-hidden="true">
                我
              </span>
            </div>
          </header>
          <main id="main-content" className="main-content">
            <div className="page-heading">
              <div>
                <div className="page-eyebrow">
                  <span>
                    {view === 'overview'
                      ? 'THE MONTHLY CHAPTER'
                      : view === 'analysis'
                        ? 'A CLOSER LOOK'
                        : view === 'ledger'
                          ? 'EVERY LITTLE DETAIL'
                          : 'THE SOURCE OF TRUTH'}
                  </span>
                  <i />
                  <span>{selectedMonth?.slice(0, 4) || 'LEDGER ATLAS'}</span>
                </div>
                <h1 id="page-title" tabIndex={-1}>
                  {title}
                  <span className="title-dot">.</span>
                </h1>
                <p>{subtitle}</p>
              </div>
              <div className="page-actions">
                {view !== 'data' && data?.months.length ? (
                  <Choice
                    label="选择月份"
                    value={data.month!}
                    onChange={(value) =>
                      update({
                        month: value,
                        category: null,
                        subcategory: null,
                        date: null,
                        page: null,
                        q: null,
                        type: null,
                      })
                    }
                    items={[...data.months]
                      .reverse()
                      .map((value) => ({ value, label: monthLabel(value) }))}
                  />
                ) : null}
                {view === 'data' ? null : (
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="outline" aria-label="导出月报" disabled={!data?.month}>
                        <Download size={15} />
                        <span>导出月报</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onSelect={downloadReport}>
                        <FileSpreadsheet size={15} />
                        下载月度摘要 CSV
                      </DropdownMenuItem>
                      <DropdownMenuItem onSelect={() => window.print()}>
                        <Printer size={15} />
                        打印 / 保存 PDF
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                )}
                {view === 'data' && (
                  <Button variant="outline" onClick={() => setImportOpen(true)}>
                    <Plus size={15} />
                    导入账单
                  </Button>
                )}
              </div>
            </div>
            {summary.isPending ? (
              <Loading />
            ) : summary.isError ? (
              <ErrorState error={summary.error} retry={() => summary.refetch()} />
            ) : !data?.month && view !== 'data' ? (
              <Empty
                title="从第一份账单开始"
                body="导入 CSV 或 Excel，收支、分类和日常节奏会在这里呈现。"
                action={
                  <Button onClick={() => setImportOpen(true)}>
                    <Plus size={16} />
                    导入第一份账单
                  </Button>
                }
              />
            ) : (
              <Suspense fallback={<Loading />}>
                {view === 'overview' && data && (
                  <Overview
                    data={data}
                    onLedger={openLedger}
                    onDetail={setDetail}
                    onBudget={() => setBudgetOpen(true)}
                  />
                )}{' '}
                {view === 'analysis' && data && <Analysis data={data} onLedger={openLedger} />}{' '}
                {view === 'ledger' && data && (
                  <Ledger data={data} params={params} update={update} onDetail={setDetail} />
                )}{' '}
                {view === 'data' && <DataPage onImport={() => setImportOpen(true)} />}
              </Suspense>
            )}
            <footer className="page-footer">
              <span>
                Ledger Atlas <i /> 每一笔，都有生活的注脚。
              </span>
              <span>
                {data?.coverage
                  ? `数据收录至 ${dayLabel(data.coverage.last_date)}`
                  : '从真实记录出发'}
                <span className="footer-currency">CNY · 人民币</span>
              </span>
            </footer>
            {data?.month && (
              <section className="print-report">
                <h1>{monthLabel(data.month)} · 生活账本</h1>
                <p>
                  统计截至 {data.coverage?.last_date} · {data.metrics.records} 笔记录
                </p>
                <dl>
                  {[
                    ['收入', data.metrics.income],
                    ['支出', data.metrics.expense],
                    ['结余', data.metrics.balance],
                  ].map(([label, value]) => (
                    <div key={String(label)}>
                      <dt>{label}</dt>
                      <dd>{money(Number(value))}</dd>
                    </div>
                  ))}
                </dl>
                <h2>支出结构</h2>
                {data.categories.map((c) => (
                  <p key={c.name}>
                    {c.name}：{money(c.amount)}（{c.share}%）
                  </p>
                ))}
                <h2>本月观察</h2>
                {data.insights.map((item) => (
                  <p key={item.title}>
                    {item.title}。{item.body}
                  </p>
                ))}
                <p>数据只来自已导入的账单；未记账消费不包含在统计中。</p>
              </section>
            )}
          </main>
        </div>
        <nav className="mobile-nav" aria-label="移动端导航">
          {navigation.map(({ id, label, icon: Icon }) => (
            <a
              key={id}
              href={`?${new URLSearchParams({ ...(selectedMonth ? { month: selectedMonth } : {}), view: id })}`}
              aria-current={view === id ? 'page' : undefined}
              className={view === id ? 'active' : ''}
              onClick={(e) => {
                if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return
                e.preventDefault()
                navigate(id)
              }}
            >
              <Icon size={20} strokeWidth={1.6} />
              <span>{label}</span>
            </a>
          ))}
        </nav>
      </div>
      {importOpen && (
        <ImportDialog
          authRequired={health.data?.auth_required ?? false}
          onClose={() => setImportOpen(false)}
        />
      )}{' '}
      {budgetOpen && data && (
        <BudgetDialog
          data={data}
          authRequired={health.data?.auth_required ?? false}
          onClose={() => setBudgetOpen(false)}
        />
      )}
      <TransactionDetail row={detail} onClose={() => setDetail(null)} />
      <Toaster theme="light" richColors position="top-center" />
    </TooltipProvider>
  )
}
