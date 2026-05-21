import { ErrorBoundary } from "./components/common/ErrorBoundary";
import { AppShell } from "./components/layout/AppShell";

export default function App() {
  return (
    <ErrorBoundary>
      <AppShell />
    </ErrorBoundary>
  );
}
