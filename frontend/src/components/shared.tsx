import {
  Utensils,
  ShoppingBag,
  Shapes,
  BookOpen,
  ArrowDownLeft,
  AlertCircle,
  Inbox,
  Loader2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { categoryColor } from '@/lib/format'
export function CategoryIcon({ name, income = false }: { name: string; income?: boolean }) {
  const Icon = income
    ? ArrowDownLeft
    : name === '餐饮'
      ? Utensils
      : name === '购物'
        ? ShoppingBag
        : name === '日常'
          ? BookOpen
          : Shapes
  return (
    <span
      className="category-icon"
      style={{ color: categoryColor(name), backgroundColor: `${categoryColor(name)}12` }}
    >
      <Icon aria-hidden="true" size={17} />
    </span>
  )
}
export function Choice({
  value,
  onChange,
  label,
  items,
  id,
  disabled,
}: {
  value: string
  onChange: (v: string) => void
  label: string
  items: { value: string; label: string }[]
  id?: string
  disabled?: boolean
}) {
  return (
    <Select value={value} onValueChange={onChange} disabled={disabled}>
      <SelectTrigger id={id} aria-label={label}>
        <SelectValue placeholder={label} />
      </SelectTrigger>
      <SelectContent>
        {items.map((item) => (
          <SelectItem key={item.value} value={item.value}>
            {item.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
export function Loading() {
  return (
    <div className="loading-state" role="status">
      <Loader2 className="animate-spin" size={20} />
      正在整理账本…
      <div className="skeleton-line" />
      <div className="skeleton-line short" />
    </div>
  )
}
export function ErrorState({ error, retry }: { error: Error; retry: () => void }) {
  return (
    <div className="empty-state" role="alert">
      <AlertCircle size={28} />
      <h2>暂时无法读取账本</h2>
      <p>{error.message}</p>
      <Button variant="outline" onClick={retry}>
        重新加载
      </Button>
    </div>
  )
}
export function Empty({
  title,
  body,
  action,
}: {
  title: string
  body: string
  action?: React.ReactNode
}) {
  return (
    <div className="empty-state">
      <Inbox size={28} />
      <h2>{title}</h2>
      <p>{body}</p>
      {action}
    </div>
  )
}
