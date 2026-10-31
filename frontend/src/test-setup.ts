import "@testing-library/jest-dom/vitest";

// jsdom does not implement layout APIs used by the chat widget.
Element.prototype.scrollIntoView = () => {};
window.matchMedia =
  window.matchMedia ??
  ((query: string) =>
    ({ matches: false, media: query, addEventListener() {}, removeEventListener() {} }) as unknown as MediaQueryList);
