import { useQuery } from '@tanstack/react-query'
import {
  Search,
  Download,
  ArrowDownUp,
  ChevronLeft,
  ChevronRight,
  X,
  ArrowUpRight,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Choice, CategoryIcon, Empty, Loading, ErrorState } from '@/components/shared'
import { request, monthQuery } from '@/lib/api'
import { money, dayLabel, exportCsv } from '@/lib/format'
import type { Summary, Transaction } from '@/lib/types'
type Props = {
  data: Summary
  params: URLSearchParams
  update: (p: Record<string, string | null>, replace?: boolean) => void
  onDetail: (row: Transaction) => void
}
export default function Ledger({ data, params, update, onDetail }: Props) {
  const query = useQuery({
    queryKey: ['transactions', data.month],
    queryFn: ({ signal }) =>
      request<{ rows: Transaction[] }>(`/transactions${monthQuery(data.month || '')}`, { signal }),
  })
  const subcategory = params.get('subcategory') || ''
  const search = params.get('q') || '',
    category = params.get('category') || 'all',
    type = params.get('type') || 'all',
    date = params.get('date') || '',
    sort = params.get('sort') || 'date-desc'
  const setFilter = (key: string, value: string) =>
    update(
      {
        [key]: value === 'all' ? null : value,
        ...(key === 'category' ? { subcategory: null } : {}),
        page: null,
      },
      key === 'q',
    )
  if (query.isPending) return <Loading />
  if (query.isError) return <ErrorState error={query.error} retry={() => query.refetch()} />
  const rows = query.data.rows
  const categories = [...new Set(rows.map((row) => row.category))]
  const filtered = rows
    .filter(
      (row) =>
        (category === 'all' || row.category === category) &&
        (!subcategory || row.subcategory === subcategory) &&
        (type === 'all' || row.type === type) &&
        (!date || row.date.startsWith(date)) &&
        [row.note, row.category, row.subcategory, row.date, row.amount]
          .join(' ')
          .toLowerCase()
          .includes(search.toLowerCase()),
    )
    .sort((a, b) =>
      sort === 'amount-desc'
        ? b.amount - a.amount
        : sort === 'amount-asc'
          ? a.amount - b.amount
          : sort === 'date-asc'
            ? a.date.localeCompare(b.date)
            : b.date.localeCompare(a.date),
    )
  const pages = Math.max(1, Math.ceil(filtered.length / 15)),
    page = Math.min(pages, Math.max(1, Number(params.get('page')) || 1))
  const shown = filtered.slice((page - 1) * 15, page * 15)
  const hasFilter = !!(search || date || subcategory || category !== 'all' || type !== 'all')
  return (
    <section className="ledger-content">
      <div className="ledger-toolbar">
        <div className="search-field">
          <Search size={17} />
          <Input
            aria-label="搜索账单"
            name="search"
            autoComplete="off"
            value={search}
            onChange={(e) => setFilter('q', e.target.value)}
            placeholder="搜索备注、分类或金额…"
          />
          {search && (
            <button aria-label="清除搜索" onClick={() => setFilter('q', '')}>
              <X size={15} />
            </button>
          )}
        </div>
        <div className="ledger-filters">
          <Choice
            label="筛选分类"
            value={category}
            onChange={(v) => setFilter('category', v)}
            items={[
              { value: 'all', label: '全部分类' },
              ...categories.map((v) => ({ value: v, label: v })),
            ]}
          />
          <Choice
            label="筛选收支"
            value={type}
            onChange={(v) => setFilter('type', v)}
            items={[
              { value: 'all', label: '全部收支' },
              { value: '支出', label: '仅支出' },
              { value: '收入', label: '仅收入' },
            ]}
          />
          <Button
            variant="outline"
            disabled={!filtered.length}
            onClick={() =>
              exportCsv(
                filtered.map((row) => ({
                  ID: row.id,
                  时间: row.date,
                  分类: row.category,
                  二级分类: row.subcategory,
                  类型: row.type,
                  金额: row.amount,
                  备注: row.note,
                })),
                `Ledger-Atlas-${data.month}.csv`,
              )
            }
          >
            <Download size={15} />
            导出
          </Button>
        </div>
      </div>
      <div className="ledger-summary">
        <span>
          找到 <strong>{filtered.length}</strong> 笔记录
          {subcategory && (
            <span className="filter-tag">
              {subcategory}
              <button aria-label="清除二级分类筛选" onClick={() => setFilter('subcategory', '')}>
                <X size={12} />
              </button>
            </span>
          )}
          {date && (
            <span className="filter-tag">
              {dayLabel(date)}
              <button aria-label="清除日期筛选" onClick={() => setFilter('date', '')}>
                <X size={12} />
              </button>
            </span>
          )}
          {hasFilter && (
            <button
              className="text-link"
              onClick={() =>
                update({
                  q: null,
                  type: null,
                  category: null,
                  subcategory: null,
                  date: null,
                  page: null,
                })
              }
            >
              重置筛选
            </button>
          )}
        </span>
        <span>
          支出{' '}
          <b>
            {money(filtered.filter((r) => r.type === '支出').reduce((s, r) => s + r.amount, 0))}
          </b>
        </span>
      </div>
      {filtered.length ? (
        <>
          <div className="ledger-sort-mobile">
            <Choice
              value={sort}
              label="排序方式"
              onChange={(v) => setFilter('sort', v)}
              items={[
                { value: 'date-desc', label: '时间：最新在前' },
                { value: 'date-asc', label: '时间：最早在前' },
                { value: 'amount-desc', label: '金额：从高到低' },
                { value: 'amount-asc', label: '金额：从低到高' },
              ]}
            />
          </div>
          <div className="ledger-table-wrap">
            <table className="ledger-table">
              <caption className="sr-only">当前月份筛选后的账单，每页 15 条</caption>
              <thead>
                <tr>
                  <th scope="col">消费记录</th>
                  <th
                    scope="col"
                    aria-sort={
                      sort === 'date-asc'
                        ? 'ascending'
                        : sort === 'date-desc'
                          ? 'descending'
                          : 'none'
                    }
                  >
                    <button
                      onClick={() =>
                        setFilter('sort', sort === 'date-desc' ? 'date-asc' : 'date-desc')
                      }
                    >
                      日期 <ArrowDownUp size={13} />
                    </button>
                  </th>
                  <th scope="col">分类</th>
                  <th scope="col">收支</th>
                  <th
                    scope="col"
                    className="amount-cell"
                    aria-sort={
                      sort === 'amount-asc'
                        ? 'ascending'
                        : sort === 'amount-desc'
                          ? 'descending'
                          : 'none'
                    }
                  >
                    <button
                      onClick={() =>
                        setFilter('sort', sort === 'amount-desc' ? 'amount-asc' : 'amount-desc')
                      }
                    >
                      金额 <ArrowDownUp size={13} />
                    </button>
                  </th>
                  <th scope="col">
                    <span className="sr-only">操作</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {shown.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <button className="record-name" onClick={() => onDetail(row)}>
                        <CategoryIcon name={row.category} income={row.type === '收入'} />
                        <span>
                          <strong>
                            {row.note !== '无备注'
                              ? row.note
                              : row.subcategory !== '未分类'
                                ? row.subcategory
                                : row.category}
                          </strong>
                          <small className="mobile-record-meta">
                            {dayLabel(row.date)} · {row.category}
                          </small>
                        </span>
                      </button>
                    </td>
                    <td className="date-cell">
                      <span>{row.date.slice(5, 10).replace('-', ' / ')}</span>
                      <small>{row.date.slice(11)}</small>
                    </td>
                    <td className="category-cell">
                      <span className="category-tag">{row.category}</span>
                      {row.subcategory !== '未分类' && <small>{row.subcategory}</small>}
                    </td>
                    <td className="type-cell">
                      <span className={row.type === '收入' ? 'good' : ''}>{row.type}</span>
                    </td>
                    <td className={`amount-cell ${row.type === '收入' ? 'good' : ''}`}>
                      {row.type === '收入' ? '+' : '−'}
                      {money(row.amount)}
                    </td>
                    <td className="detail-cell">
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`查看${row.note !== '无备注' ? row.note : row.category}账单详情`}
                        onClick={() => onDetail(row)}
                      >
                        <ArrowUpRight size={15} />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination">
            <span>
              第 {(page - 1) * 15 + 1}–{Math.min(page * 15, filtered.length)} 条，共{' '}
              {filtered.length} 条
            </span>
            <div>
              <Button
                variant="outline"
                size="icon"
                disabled={page === 1}
                onClick={() => update({ page: String(page - 1) })}
                aria-label="上一页"
              >
                <ChevronLeft size={16} />
              </Button>
              <span>
                {page} / {pages}
              </span>
              <Button
                variant="outline"
                size="icon"
                disabled={page === pages}
                onClick={() => update({ page: String(page + 1) })}
                aria-label="下一页"
              >
                <ChevronRight size={16} />
              </Button>
            </div>
          </div>
        </>
      ) : (
        <Empty
          title="没有找到匹配的账单"
          body="试试其他关键词，或清除筛选后查看整月。"
          action={
            <Button
              variant="outline"
              onClick={() =>
                update({ q: null, type: null, category: null, subcategory: null, date: null })
              }
            >
              清除筛选
            </Button>
          }
        />
      )}
    </section>
  )
}
