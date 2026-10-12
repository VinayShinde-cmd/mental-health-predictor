import { useEffect, useRef } from "react";
import { describeError } from "../api/client.ts";
import type { Range } from "../api/types.ts";
import type { PredictState } from "../hooks/usePredict.ts";
import { formatScore } from "../lib/format.ts";
import { EmptyState, ErrorState, Skeleton } from "./ui/Feedback.tsx";
import { ScoreScale } from "./ScoreScale.tsx";

/** Shown before any result, so the ruler is visible from the first moment. Matches the backend constants. */
const DEFAULT_SCALE: Range = { min: 3.6, max: 9.4 };
const DEFAULT_TYPICAL: Range = { min: 5.1, max: 7.1 };

interface ResultPanelProps {
  state: PredictState;
  onRetry: () => void;
}

const BAND_SENTENCE = {
  below_typical: "That is below where most survey respondents scored.",
  typical: "That is where most survey respondents scored.",
  above_typical: "That is above where most survey respondents scored.",
} as const;

export function ResultPanel({ state, onRetry }: ResultPanelProps) {
  const panelRef = useRef<HTMLElement>(null);
  const settled = state.status === "success" || state.status === "error";

  // On narrow screens the panel sits below the form, so bring the outcome into view.
  useEffect(() => {
    if (!settled || !window.matchMedia("(max-width: 59.99rem)").matches) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    panelRef.current?.scrollIntoView?.({ behavior: reduce ? "auto" : "smooth", block: "start" });
  }, [settled]);

  return (
    <section className="result" ref={panelRef} aria-labelledby="result-heading" aria-live="polite">
      <h2 className="result__heading" id="result-heading">
        Your estimate
      </h2>

      {state.status === "idle" && (
        <>
          <EmptyState title="Nothing to show yet">
            Answer the questions and choose Estimate my score. Your result will appear on this ruler.
          </EmptyState>
          <ScoreScale scale={DEFAULT_SCALE} typical={DEFAULT_TYPICAL} />
        </>
      )}

      {state.status === "pending" && (
        <div aria-busy="true">
          <p className="result__status">Estimating…</p>
          <Skeleton height="4.5rem" width="45%" />
          <div className="result__gap" />
          <Skeleton height="3.5rem" />
        </div>
      )}

      {state.status === "error" && (
        <ErrorState title="Couldn't get an estimate" message={describeError(state.error)} onRetry={onRetry} />
      )}

      {state.status === "success" && (
        <>
          <p className="result__score">{formatScore(state.prediction.score)}</p>
          <p className="result__band">{state.prediction.band_label}</p>
          <p className="result__sentence">{BAND_SENTENCE[state.prediction.band]}</p>
          <ScoreScale
            scale={state.prediction.scale}
            typical={state.prediction.typical_range}
            score={state.prediction.score}
          />
          {state.prediction.warnings.length > 0 && (
            <ul className="result__warnings">
              {state.prediction.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          )}
          <p className="result__disclaimer">{state.prediction.disclaimer}</p>
          <p className="result__meta">Model {state.prediction.model_id}</p>
        </>
      )}
    </section>
  );
}
