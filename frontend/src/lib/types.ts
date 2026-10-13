export type View = 'overview' | 'analysis' | 'ledger' | 'data'
export type Transaction = {
  id: string
  date: string
  category: string
  subcategory: string
  type: string
  amount: number
  note: string
  account?: string
  book?: string
  currency?: string
  tags?: string
}
export type Category = { name: string; amount: number; share: number; records: number }
export type Daily = { date: string; amount: number; cumulative: number }
export type Summary = {
  month: string | null
  months: string[]
  budget: number | null
  metrics: {
    income: number
    expense: number
    balance: number
    saving_rate: number
    records: number
    expense_change: number | null
    daily_average: number
  }
  coverage: {
    last_date: string
    is_partial: boolean
    observed_days: number
    month_days: number
  } | null
  comparison: { month: string; expense: number; partial: boolean; available: boolean } | null
  categories: Category[]
  daily: Daily[]
  recent: Transaction[]
  trend: {
    month: string
    income: number
    expense: number
    balance: number
    running_balance: number
  }[]
  weekday: { name: string; amount: number; records: number }[]
  insights: { tone: string; title: string; body: string }[]
}
export type Patterns = {
  subcategories: { category: string; subcategory: string; amount: number; records: number }[]
}
export type DataRoom = {
  duplicate_ids: number
  columns: string[]
  null_counts: Record<string, number>
  manifest: {
    rows?: number
    raw_rows?: number
    generated_at?: string
    date_min?: string
    date_max?: string
    master_sha256?: string
    months?: string[]
    source_files?: { name: string; bytes: number; sha256: string }[]
    month_counts?: Record<string, number>
  }
}
export type ImportPreview = {
  valid: boolean
  raw_rows: number
  unique_rows: number
  new_rows: number
  existing_rows: number
  duplicate_rows: number
  issue_count: number
  issues: { row: number; reason: string }[]
  months: string[]
  sample: { date: string; category: string; type: string; amount: number }[]
}
