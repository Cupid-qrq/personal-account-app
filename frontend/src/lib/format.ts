const currency = new Intl.NumberFormat('zh-CN', {
  style: 'currency',
  currency: 'CNY',
  minimumFractionDigits: 2,
})
export const money = (value: number) => currency.format(value)
export const number = (value: number) =>
  new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 2 }).format(value)
export function monthLabel(value: string) {
  const [year, month] = value.split('-')
  return `${year} 年 ${Number(month)} 月`
}
export const dayLabel = (value: string) =>
  new Intl.DateTimeFormat('zh-CN', { month: 'long', day: 'numeric' }).format(
    new Date(`${value.slice(0, 10)}T12:00:00`),
  )
export const categoryColors: Record<string, string> = {
  日常: '#ad563d',
  餐饮: '#496f68',
  购物: '#8a7451',
  其它: '#85808f',
  生活费: '#496f68',
  红包: '#ad563d',
}
export const categoryColor = (name: string) => categoryColors[name] || '#74746c'
export function exportCsv(rows: Record<string, unknown>[], filename: string) {
  if (!rows.length) return
  const cell = (v: unknown) =>
    `"${String(v ?? '')
      .replace(/^[=+@\-\t\r]/, "'$&")
      .replace(/"/g, '""')}"`
  const data = [Object.keys(rows[0]), ...rows.map(Object.values)]
    .map((r) => r.map(cell).join(','))
    .join('\r\n')
  const url = URL.createObjectURL(new Blob(['\ufeff' + data], { type: 'text/csv;charset=utf-8' }))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
