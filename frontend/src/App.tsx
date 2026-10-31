import { useEffect } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import { ChatWidget } from "./components/chat/ChatWidget";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Footer } from "./components/Footer";
import { Navbar } from "./components/Navbar";
import About from "./pages/About";
import Contact from "./pages/Contact";
import Experience from "./pages/Experience";
import Home from "./pages/Home";
import NotFound from "./pages/NotFound";
import ProjectDetail from "./pages/ProjectDetail";
import Projects from "./pages/Projects";
import Resume from "./pages/Resume";
import Skills from "./pages/Skills";

function ScrollToTop() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    if (!hash) {
      window.scrollTo(0, 0);
      return;
    }
    // The target may render a tick after navigation, so wait a frame before looking it up.
    const frame = requestAnimationFrame(() => document.getElementById(hash.slice(1))?.scrollIntoView());
    return () => cancelAnimationFrame(frame);
  }, [pathname, hash]);
  return null;
}

export default function App() {
  return (
    <>
      <a href="#main" className="skip-link">Skip to content</a>
      <Navbar />
      <ScrollToTop />
      <main id="main" tabIndex={-1} className="outline-none">
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/experience" element={<Experience />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/projects/:projectId" element={<ProjectDetail />} />
            <Route path="/skills" element={<Skills />} />
            <Route path="/resume" element={<Resume />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </ErrorBoundary>
      </main>
      <Footer />
      <ChatWidget />
    </>
  );
}
