export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api${path}`, options)
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new Error('无法连接账本服务，请检查网络或确认服务已启动，然后重试。')
  }
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail =
      typeof data?.detail === 'string'
        ? data.detail
        : response.status === 401
          ? '管理令牌不正确，请重新输入。'
          : `请求失败（${response.status}），请稍后重试。`
    throw new Error(detail)
  }
  return data as T
}
export const monthQuery = (month: string) => (month ? `?month=${encodeURIComponent(month)}` : '')
