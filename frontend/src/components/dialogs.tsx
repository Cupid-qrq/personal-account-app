import { useState, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import {
  Upload,
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ArrowRight,
} from 'lucide-react'
import { toast } from 'sonner'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet'
import { request } from '@/lib/api'
import { money, monthLabel } from '@/lib/format'
import { CategoryIcon } from './shared'
import type { ImportPreview, Summary, Transaction } from '@/lib/types'

export function TransactionDetail({
  row,
  onClose,
}: {
  row: Transaction | null
  onClose: () => void
}) {
  return (
    <Sheet open={!!row} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="detail-sheet">
        <SheetHeader>
          <SheetTitle>账单详情</SheetTitle>
          <SheetDescription>查看这笔记录的来源与分类</SheetDescription>
        </SheetHeader>
        {row && (
          <div className="detail-body">
            <CategoryIcon name={row.category} income={row.type === '收入'} />
            <h2>{row.note !== '无备注' ? row.note : row.category}</h2>
            <div className={`detail-amount ${row.type === '收入' ? 'good' : ''}`}>
              {row.type === '收入' ? '+' : '−'}
              {money(row.amount)}
            </div>
            <span className="category-tag">{row.type}</span>
            <dl>
              {[
                ['记账时间', row.date],
                ['一级分类', row.category],
                ['二级分类', row.subcategory],
                ['备注', row.note],
                ['账户', row.account || '未提供'],
                ['账本', row.book || '未提供'],
                ['币种', row.currency || 'CNY'],
                ['标签', row.tags || '未提供'],
                ['原始 ID', row.id],
              ].map(([label, value]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
            <p className="quiet-note">
              金额与分类来自已导入账单。需要修改时，可更新来源文件后重新导入。
            </p>
          </div>
        )}
      </SheetContent>
    </Sheet>
  )
}
export function BudgetDialog({
  data,
  authRequired,
  onClose,
}: {
  data: Summary
  authRequired: boolean
  onClose: () => void
}) {
  const [amount, setAmount] = useState(data.budget?.toString() || ''),
    [token, setToken] = useState(''),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false)
  const qc = useQueryClient()
  async function save(clear = false) {
    if (
      !clear &&
      (!amount ||
        !Number.isFinite(Number(amount)) ||
        Number(amount) <= 0 ||
        Number(amount) > 10000000)
    ) {
      setError('请输入大于 0、且不超过 1000 万元的预算。')
      document.getElementById('budget-amount')?.focus()
      return
    }
    setBusy(true)
    setError('')
    try {
      await request(`/budgets/${data.month}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-Admin-Token': token },
        body: JSON.stringify({ amount: clear ? null : Number(amount) }),
      })
      await qc.invalidateQueries({ queryKey: ['summary'] })
      toast.success(clear ? '已取消本月预算' : '本月预算已保存')
      onClose()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }
  return (
    <Dialog open onOpenChange={(open) => !open && !busy && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>为这个月留一点余量</DialogTitle>
          <DialogDescription>
            {monthLabel(data.month || '')} · 预算会保存到账本，所有浏览器共享。
          </DialogDescription>
        </DialogHeader>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            save()
          }}
        >
          <label className="field-label" htmlFor="budget-amount">
            月度支出预算（元）
          </label>
          <Input
            id="budget-amount"
            name="budget"
            type="number"
            inputMode="decimal"
            min="0.01"
            max="10000000"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            autoComplete="off"
            placeholder="例如 3000…"
            aria-invalid={!!error}
            aria-describedby={error ? 'budget-error' : undefined}
          />
          <p className="field-hint">
            本月已支出 {money(data.metrics.expense)}。预算是你的计划，不是系统推荐。
          </p>
          {authRequired && <TokenField value={token} setValue={setToken} />}{' '}
          {error && (
            <p id="budget-error" className="form-error" role="alert">
              {error}
            </p>
          )}
          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={data.budget ? () => save(true) : onClose}
              disabled={busy}
            >
              {data.budget ? '取消预算' : '暂不设置'}
            </Button>
            <Button type="submit" disabled={busy}>
              {busy && <Loader2 className="animate-spin" size={14} />}保存预算
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
function TokenField({ value, setValue }: { value: string; setValue: (value: string) => void }) {
  return (
    <div className="token-field">
      <label className="field-label" htmlFor="admin-token">
        管理令牌
      </label>
      <Input
        id="admin-token"
        name="admin-token"
        type="password"
        autoComplete="off"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        spellCheck={false}
        placeholder="输入服务器配置的管理令牌…"
      />
      <p className="field-hint">仅用于本次操作，不保存在浏览器。</p>
    </div>
  )
}
export function ImportDialog({
  authRequired,
  onClose,
}: {
  authRequired: boolean
  onClose: () => void
}) {
  const [file, setFile] = useState<File | null>(null),
    [preview, setPreview] = useState<ImportPreview | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(''),
    [token, setToken] = useState(''),
    [done, setDone] = useState<number | null>(null)
  const [dragging, setDragging] = useState(false)
  const input = useRef<HTMLInputElement>(null),
    qc = useQueryClient()
  function selectFile(next: File | undefined) {
    setError('')
    setPreview(null)
    if (!next) return
    if (!/\.(csv|xlsx|xls)$/i.test(next.name)) {
      setFile(null)
      setError('请选择 CSV、XLSX 或 XLS 格式的账单。')
      return
    }
    if (next.size > 10 * 1024 * 1024) {
      setFile(null)
      setError('文件超过 10 MB，请分批导入。')
      return
    }
    setFile(next)
  }
  async function submit(commit = false) {
    if (!file) return
    setBusy(true)
    setError('')
    const body = new FormData()
    body.append('file', file)
    try {
      if (commit) {
        const result = await request<{ new_rows: number }>('/import', {
          method: 'POST',
          headers: { 'X-Admin-Token': token },
          body,
        })
        await qc.invalidateQueries()
        setDone(result.new_rows)
        toast.success('账单导入成功')
      } else
        setPreview(
          await request<ImportPreview>('/import/preview', {
            method: 'POST',
            headers: { 'X-Admin-Token': token },
            body,
          }),
        )
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }
  return (
    <Dialog open onOpenChange={(open) => !open && !busy && onClose()}>
      <DialogContent className="import-dialog">
        <DialogHeader>
          <DialogTitle>{done !== null ? '账本已更新' : '导入生活账单'}</DialogTitle>
          <DialogDescription>
            {done !== null
              ? '分析页面已刷新，可以继续查看最新数据。'
              : '先预览，确认后写入。支持 CSV、XLSX 和 XLS，最大 10 MB。'}
          </DialogDescription>
        </DialogHeader>
        {done !== null ? (
          <>
            <div className="import-success">
              <CheckCircle2 size={42} />
              <strong>新增 {done} 笔记录</strong>
              <p>已存在的 ID 按本次内容更新，原始文件已保留。</p>
            </div>
            <Button onClick={onClose}>
              回到账本 <ArrowRight size={15} />
            </Button>
          </>
        ) : (
          <>
            <div className="import-steps" aria-label="导入步骤">
              <span className="active">1 选择文件</span>
              <i />
              <span className={preview ? 'active' : ''}>2 预览校验</span>
              <i />
              <span>3 确认导入</span>
            </div>
            <input
              ref={input}
              name="ledger-file"
              type="file"
              accept=".csv,.xlsx,.xls"
              className="sr-only"
              tabIndex={-1}
              aria-label="账单文件"
              onChange={(e) => selectFile(e.target.files?.[0])}
            />
            <button
              type="button"
              className={`dropzone ${dragging ? 'dragging' : ''}`}
              disabled={busy}
              onClick={() => input.current?.click()}
              onDragOver={(e) => {
                e.preventDefault()
                setDragging(true)
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => {
                e.preventDefault()
                setDragging(false)
                selectFile(e.dataTransfer.files[0])
              }}
            >
              {file ? <FileSpreadsheet size={28} /> : <Upload size={28} />}
              <strong>{file ? file.name : '选择文件，或拖到这里'}</strong>
              <span>
                {file
                  ? `${(file.size / 1024).toFixed(1)} KB · 点击更换文件`
                  : '从记账软件导出的原始账单'}
              </span>
            </button>
            {authRequired && <TokenField value={token} setValue={setToken} />}{' '}
            {preview && (
              <div className="import-preview" aria-live="polite">
                <div className={`validation-result ${preview.valid ? 'good' : 'warm'}`}>
                  {preview.valid ? <CheckCircle2 size={17} /> : <AlertCircle size={17} />}
                  <strong>
                    {preview.valid
                      ? '校验通过，可以导入'
                      : `发现 ${preview.issue_count} 行问题，请修正文件`}
                  </strong>
                </div>
                <div className="preview-counts">
                  <div>
                    <b>{preview.new_rows}</b>
                    <span>新增记录</span>
                  </div>
                  <div>
                    <b>{preview.updated_rows}</b>
                    <span>内容变更</span>
                  </div>
                  <div>
                    <b>{preview.unchanged_rows}</b>
                    <span>保持不变</span>
                  </div>
                </div>
                {preview.valid ? (
                  <>
                    <p>覆盖月份：{preview.months.join('、')}</p>
                    <p className="field-hint">已有 ID 会更新为本次内容；预览阶段尚未修改账本。</p>
                    {preview.duplicate_rows > 0 && (
                      <p className="field-hint">
                        文件内 {preview.duplicate_rows} 条重复 ID 已合并，取最后一行。
                      </p>
                    )}
                    {preview.changes.length > 0 && (
                      <details className="import-diff">
                        <summary>查看 {preview.updated_rows} 笔变更的前后差异</summary>
                        <div>
                          {preview.changes.map((change) => (
                            <section className="diff-record" key={change.id}>
                              <p>
                                记录 <code>{change.id}</code>
                              </p>
                              <dl>
                                {change.fields.map((field) => (
                                  <div key={field.field}>
                                    <dt>{field.field}</dt>
                                    <dd>
                                      <span className="diff-before">
                                        <span className="sr-only">原值：</span>
                                        {field.before || '空'}
                                      </span>
                                      <ArrowRight size={12} aria-hidden="true" />
                                      <span className="diff-after">
                                        <span className="sr-only">新值：</span>
                                        {field.after || '空'}
                                      </span>
                                    </dd>
                                  </div>
                                ))}
                              </dl>
                            </section>
                          ))}
                        </div>
                        {preview.changes_truncated && (
                          <p className="field-hint">
                            为便于阅读，显示前 20 笔变更。其余变更也会应用。
                          </p>
                        )}
                      </details>
                    )}
                  </>
                ) : (
                  <ul className="import-issues">
                    {preview.issues.map((issue) => (
                      <li key={issue.row}>
                        第 {issue.row} 行：{issue.reason}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}
            <DialogFooter>
              <Button variant="ghost" onClick={onClose} disabled={busy}>
                取消
              </Button>
              <Button
                disabled={
                  !file || busy || (authRequired && !token) || (preview !== null && !preview.valid)
                }
                onClick={() => submit(!!preview)}
              >
                {busy ? (
                  <>
                    <Loader2 size={15} className="animate-spin" />
                    正在{preview ? '导入' : '校验'}…
                  </>
                ) : preview ? (
                  '确认导入账单'
                ) : (
                  '预览并校验'
                )}
                {!busy && <ArrowRight size={15} />}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
