import { useQuery } from '@tanstack/react-query'
import {
  FileSpreadsheet,
  ShieldCheck,
  Upload,
  Copy,
  Check,
  Database,
  CalendarRange,
  Files,
} from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { ErrorState, Loading } from '@/components/shared'
import { request } from '@/lib/api'
import { dayLabel } from '@/lib/format'
import type { DataRoom } from '@/lib/types'
export default function DataPage({ onImport }: { onImport: () => void }) {
  const query = useQuery({
    queryKey: ['data-room'],
    queryFn: ({ signal }) => request<DataRoom>('/data-room', { signal }),
  })
  const [copied, setCopied] = useState(false)
  if (query.isPending) return <Loading />
  if (query.isError) return <ErrorState error={query.error} retry={() => query.refetch()} />
  const data = query.data,
    m = data.manifest
  return (
    <div className="data-content">
      <section className="import-callout">
        <div className="file-illustration" aria-hidden="true">
          <FileSpreadsheet size={30} strokeWidth={1.3} />
          <span>CSV / XLSX</span>
        </div>
        <div>
          <span className="eyebrow">YOUR DATA, YOUR STORY</span>
          <h2>让账单，继续更新。</h2>
          <p>上传原始导出文件，预览校验结果后再导入。相同 ID 自动合并。</p>
        </div>
        <Button onClick={onImport}>
          <Upload size={16} />
          导入新账单
        </Button>
      </section>
      <div className="data-metrics">
        {[
          [Database, '唯一账单', m.rows || 0],
          [Files, '来源文件', m.source_files?.length || 0],
          [CalendarRange, '覆盖月份', m.months?.length || 0],
          [ShieldCheck, '重复 ID', data.duplicate_ids],
        ].map(([Icon, label, value]) => {
          const I = Icon as typeof Database
          return (
            <div key={String(label)}>
              <I size={17} />
              <span>{String(label)}</span>
              <strong>{String(value)}</strong>
            </div>
          )
        })}
      </div>
      <section className="paper-panel source-panel">
        <div className="panel-heading">
          <div>
            <h2>账本的来源</h2>
            <p>
              {m.date_min && m.date_max
                ? `${m.date_min.slice(0, 4)} 年 ${dayLabel(m.date_min)} — ${dayLabel(m.date_max)}`
                : '尚未导入账单'}
            </p>
          </div>
          <span className="status-tag">
            <ShieldCheck size={13} />
            {data.duplicate_ids === 0 ? '主表无重复 ID' : '存在重复 ID'}
          </span>
        </div>
        <div className="source-list">
          {m.source_files?.map((file) => (
            <div className="source-file" key={file.name}>
              <span className="source-file-icon">
                <FileSpreadsheet size={21} />
              </span>
              <div>
                <strong>{file.name}</strong>
                <small>
                  {(file.bytes / 1024).toFixed(1)} KB · {file.name.split('.').pop()?.toUpperCase()}
                </small>
              </div>
              <details>
                <summary>查看校验值</summary>
                <code>{file.sha256}</code>
              </details>
            </div>
          ))}
        </div>
      </section>
      <div className="data-bottom">
        <section className="paper-panel">
          <div className="panel-heading">
            <div>
              <h2>完整性校验</h2>
              <p>用于核对当前主表快照</p>
            </div>
          </div>
          <dl className="integrity-list">
            <div>
              <dt>输入记录总数</dt>
              <dd>{m.raw_rows || 0} 条</dd>
            </div>
            <div>
              <dt>合并后记录</dt>
              <dd>{m.rows || 0} 条</dd>
            </div>
            <div>
              <dt>最近重建</dt>
              <dd>
                {m.generated_at
                  ? new Intl.DateTimeFormat('zh-CN', {
                      dateStyle: 'medium',
                      timeStyle: 'short',
                      timeZone: 'Asia/Shanghai',
                    }).format(new Date(m.generated_at))
                  : '—'}
              </dd>
            </div>
          </dl>
          <div className="hash-box">
            <span>SHA-256</span>
            <code>{m.master_sha256 || '无快照'}</code>
            <Button
              variant="ghost"
              size="icon"
              aria-label="复制主表校验值"
              disabled={!m.master_sha256}
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(m.master_sha256 || '')
                  setCopied(true)
                  toast.success('校验值已复制')
                  setTimeout(() => setCopied(false), 2000)
                } catch {
                  setCopied(false)
                  toast.error('浏览器未允许复制，请手动选中校验值复制。')
                }
              }}
            >
              {copied ? <Check size={15} /> : <Copy size={15} />}
            </Button>
          </div>
        </section>
        <section className="paper-panel data-explainer">
          <h2>数据如何成为账本</h2>
          <ol>
            <li>
              <span>01</span>
              <div>
                <strong>读取与校验</strong>
                <p>识别 CSV / Excel，检查 ID、日期、收支类型与金额。</p>
              </div>
            </li>
            <li>
              <span>02</span>
              <div>
                <strong>合并与整理</strong>
                <p>按 ID 合并累计导出，统一分类；原始来源文件保留。</p>
              </div>
            </li>
            <li>
              <span>03</span>
              <div>
                <strong>保存与分析</strong>
                <p>生成 SQLite、CSV 和月度归档，页面读取真实汇总。</p>
              </div>
            </li>
          </ol>
        </section>
      </div>
    </div>
  )
}
