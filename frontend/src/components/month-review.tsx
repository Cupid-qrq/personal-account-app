import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Check, Loader2, NotebookPen } from 'lucide-react'
import { toast } from 'sonner'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from './ui/dialog'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Textarea } from './ui/textarea'
import { Choice } from './shared'
import { monthLabel } from '@/lib/format'
import { request } from '@/lib/api'
import type { MonthReview, Summary } from '@/lib/types'

export function MonthReviewDialog({
  data,
  authRequired,
  onClose,
}: {
  data: Summary
  authRequired: boolean
  onClose: () => void
}) {
  const initial = data.review || { note: '', status: 'auto' }
  const [note, setNote] = useState(initial.note),
    [status, setStatus] = useState<MonthReview['status']>(initial.status)
  const [token, setToken] = useState(''),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false),
    [discard, setDiscard] = useState(false)
  const qc = useQueryClient(),
    dirty = note !== initial.note || status !== initial.status
  const title = useRef<HTMLHeadingElement>(null),
    textarea = useRef<HTMLTextAreaElement>(null),
    errorMessage = useRef<HTMLParagraphElement>(null),
    wasDiscard = useRef(false)
  useEffect(() => {
    if (discard) title.current?.focus()
    else if (wasDiscard.current) textarea.current?.focus()
    wasDiscard.current = discard
  }, [discard])
  useEffect(() => {
    if (error) errorMessage.current?.focus()
  }, [error])
  useEffect(() => {
    if (!dirty) return
    const guard = (e: BeforeUnloadEvent) => {
      e.preventDefault()
      e.returnValue = ''
    }
    window.addEventListener('beforeunload', guard)
    return () => window.removeEventListener('beforeunload', guard)
  }, [dirty])
  function close() {
    if (busy) return
    if (dirty) setDiscard(true)
    else onClose()
  }
  async function save() {
    setBusy(true)
    setError('')
    try {
      await request(`/reviews/${data.month}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-Admin-Token': token },
        body: JSON.stringify({ note, status }),
      })
      await qc.invalidateQueries({ queryKey: ['summary'] })
      await qc.invalidateQueries({ queryKey: ['patterns'] })
      toast.success('月度手记已保存')
      onClose()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }
  return (
    <Dialog open onOpenChange={(open) => !open && close()}>
      <DialogContent
        className="review-dialog"
        showCloseButton={!busy}
        onOpenAutoFocus={(event) => {
          if (matchMedia('(pointer: coarse)').matches) {
            event.preventDefault()
            title.current?.focus()
          }
        }}
      >
        <DialogHeader>
          <DialogTitle ref={title} tabIndex={-1}>
            {discard ? '还有未保存的手记' : '为这个月，留一页手记'}
          </DialogTitle>
          <DialogDescription>
            {discard
              ? '继续编辑保留草稿，或放弃这次修改。'
              : `${monthLabel(data.month || '')} · 手记与月结状态会保存到共享账本。`}
          </DialogDescription>
        </DialogHeader>
        {discard ? (
          <DialogFooter>
            <Button variant="outline" onClick={() => setDiscard(false)}>
              继续编辑
            </Button>
            <Button onClick={onClose}>放弃修改</Button>
          </DialogFooter>
        ) : (
          <form
            aria-busy={busy}
            onSubmit={(e) => {
              e.preventDefault()
              save()
            }}
          >
            <label className="field-label" htmlFor="month-note">
              <NotebookPen size={14} aria-hidden="true" />
              本月手记
            </label>
            <Textarea
              ref={textarea}
              id="month-note"
              name="month-note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              maxLength={800}
              disabled={busy}
              rows={5}
              autoComplete="off"
              placeholder="例如：这个月添置了学习用品，和朋友一起参加了运动会…"
              aria-describedby="note-hint"
            />
            <div className="note-field-footer" id="note-hint">
              <span>会显示在总览和打印月报中</span>
              <span>{note.length} / 800</span>
            </div>
            <label className="field-label" htmlFor="review-status">
              月结状态
            </label>
            <Choice
              id="review-status"
              disabled={busy}
              label="月结状态"
              value={status}
              onChange={(v) => setStatus(v as MonthReview['status'])}
              items={[
                { value: 'auto', label: '自动判断' },
                { value: 'in_progress', label: '仍在记录' },
                { value: 'closed', label: '已完成月结' },
              ]}
            />
            <p className="field-hint status-explanation">
              {status === 'closed'
                ? '表示你已核对该月账单。日均按整月自然日计算，环比使用上月整月；之后仍可改回。'
                : status === 'in_progress'
                  ? '按月初至最后记账日计算日均，与上月同日区间比较。适用于尚未补齐的历史月份。'
                  : '最新月份按最后记账日判断覆盖范围，历史月份默认按整月。'}
            </p>
            {authRequired && (
              <>
                <label className="field-label" htmlFor="review-token">
                  管理令牌
                </label>
                <Input
                  id="review-token"
                  name="review-token"
                  type="password"
                  disabled={busy}
                  autoComplete="off"
                  spellCheck={false}
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="输入本次操作的管理令牌…"
                />
              </>
            )}
            {error && (
              <p ref={errorMessage} tabIndex={-1} className="form-error" role="alert">
                {error}
              </p>
            )}
            <DialogFooter>
              <Button type="button" variant="ghost" disabled={busy} onClick={close}>
                取消
              </Button>
              <Button type="submit" disabled={busy}>
                {busy ? <Loader2 size={15} className="animate-spin" /> : <Check size={15} />}
                {busy ? '保存中…' : '保存月度手记'}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  )
}
