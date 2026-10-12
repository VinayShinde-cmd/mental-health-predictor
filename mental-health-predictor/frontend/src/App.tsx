import { useEffect, useState } from "react";
import { DesignPage } from "./pages/DesignPage.tsx";
import { EstimatorPage } from "./pages/EstimatorPage.tsx";

function useHash(): string {
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const onChange = () => setHash(window.location.hash);
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return hash;
}

export default function App() {
  const onDesignPage = useHash() === "#/design";
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="site-header">
        <div className="page">
          <a className="site-header__brand" href="#/">
            Habit gauge
          </a>
        </div>
      </header>
      <main className="page" id="main" tabIndex={-1}>
        {onDesignPage ? <DesignPage /> : <EstimatorPage />}
      </main>
      <footer className="site-footer">
        <div className="page">
          <p>
            Built on a student survey dataset. Not medical advice.{" "}
            <a href={onDesignPage ? "#/" : "#/design"}>{onDesignPage ? "Back to the estimator" : "Design system"}</a>
          </p>
        </div>
      </footer>
    </>
  );
}
