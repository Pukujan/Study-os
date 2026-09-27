import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = {
  children: ReactNode;
  /** Changing this value clears a caught error, e.g. when the route changes. */
  resetKey?: string;
  /** Called after a caught error is cleared so the caller can remount children. */
  onReset?: () => void;
  /** Recovery action for the Retry button; defaults to reloading the page. */
  onRetry?: () => void;
};

type State = { error: Error | null };

/**
 * Recoverable render-error boundary.
 *
 * A thrown render used to unmount the whole React root and leave the learner on
 * an empty page with no way back (issue #126). This keeps the failure on screen
 * as a card with Retry / Go home instead of a blank shell.
 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("study-os render error", error, info.componentStack);
  }

  componentDidUpdate(prev: Props): void {
    if (this.state.error && prev.resetKey !== this.props.resetKey) this.clear();
  }

  clear = (): void => {
    this.setState({ error: null });
    this.props.onReset?.();
  };

  retry = (): void => {
    if (this.props.onRetry) {
      this.clear();
      this.props.onRetry();
      return;
    }
    if (typeof window !== "undefined") window.location.reload();
  };

  goHome = (): void => {
    if (typeof window !== "undefined") window.location.assign("/");
  };

  render(): ReactNode {
    if (!this.state.error) return this.props.children;
    return (
      <section className="card render-error" role="alert" data-testid="render-error">
        <h2>Something broke on this screen</h2>
        <p className="muted">Your progress is saved. Retry this view, or head back home.</p>
        <p className="fine">{this.state.error.message}</p>
        <div className="render-error-actions">
          <button className="btn primary" onClick={this.retry} data-testid="render-error-retry">
            Retry
          </button>
          <button className="btn" onClick={this.goHome} data-testid="render-error-home">
            Go home
          </button>
        </div>
      </section>
    );
  }
}