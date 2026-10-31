import { Component, type ReactNode } from "react";
import { Container, ErrorState } from "./ui";

export class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <Container className="py-24">
        <ErrorState message="This page failed to load. Please refresh, or go back to the home page." />
      </Container>
    );
  }
}
