import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="error-boundary">
          <h2 className="error-boundary-title">
            오류가 발생했습니다
          </h2>
          <p className="error-boundary-msg">
            페이지를 표시하는 중 문제가 발생했습니다. 다시 시도해 주세요.
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="error-boundary-btn"
          >
            다시 시도
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
