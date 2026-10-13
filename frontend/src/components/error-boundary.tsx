import { Component, type ReactNode } from 'react'
import { ErrorState } from './shared'

export class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  render() {
    if (this.state.failed) {
      return (
        <ErrorState
          error={new Error('页面加载异常，请重新加载。已保存的账本数据不会丢失。')}
          retry={() => window.location.reload()}
        />
      )
    }
    return this.props.children
  }
}
