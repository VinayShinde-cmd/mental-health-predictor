import { useRef } from "react";
import { describeError } from "../api/client.ts";
import type { FieldIssue, PredictRequest } from "../api/types.ts";
import { PredictionForm } from "../components/PredictionForm.tsx";
import { ResultPanel } from "../components/ResultPanel.tsx";
import { ErrorState, Skeleton } from "../components/ui/Feedback.tsx";
import { useOptions } from "../hooks/useOptions.ts";
import type { PredictState } from "../hooks/usePredict.ts";
import { usePredict } from "../hooks/usePredict.ts";

/** Stable reference so the form's effect does not re-run on every render. */
const NO_ISSUES: FieldIssue[] = [];

function FormSkeleton() {
  return (
    <div aria-busy="true">
      <p className="visually-hidden" role="status">
        Loading the form…
      </p>
      <div className="fields fields--skeleton">
        {Array.from({ length: 8 }, (_, index) => (
          <Skeleton key={index} height="4.25rem" />
        ))}
      </div>
    </div>
  );
}

export function EstimatorPage() {
  const { state: optionsState, reload } = useOptions();
  const { state: predictState, submit, reset } = usePredict();
  const lastRequest = useRef<PredictRequest | null>(null);

  function handleSubmit(payload: PredictRequest) {
    lastRequest.current = payload;
    submit(payload);
  }

  function retry() {
    if (lastRequest.current) submit(lastRequest.current);
  }

  const fieldProblem = predictState.status === "error" && predictState.error.issues.length > 0;
  const serverIssues = predictState.status === "error" && fieldProblem ? predictState.error.issues : NO_ISSUES;
  const formMessage = predictState.status === "error" && fieldProblem ? describeError(predictState.error) : undefined;
  // Field-level problems are shown on the form; the result panel stays quiet for those.
  const panelState: PredictState = fieldProblem ? { status: "idle" } : predictState;

  return (
    <>
      <div className="intro">
        <h1 className="intro__title">Estimate a wellbeing score from your daily habits</h1>
        <p className="intro__lede">
          Answer 12 questions. A model trained on a student survey places you on a scale. It is an estimate, not a
          diagnosis.
        </p>
      </div>

      <div className="layout">
        <div className="layout__form">
          {optionsState.status === "loading" && <FormSkeleton />}
          {optionsState.status === "error" && (
            <ErrorState
              title="Couldn't load the form"
              message={describeError(optionsState.error)}
              onRetry={reload}
            />
          )}
          {optionsState.status === "ready" && (
            <PredictionForm
              options={optionsState.options}
              pending={predictState.status === "pending"}
              serverIssues={serverIssues}
              formMessage={formMessage}
              onSubmit={handleSubmit}
              onClear={reset}
            />
          )}
        </div>
        <div className="layout__result">
          <ResultPanel state={panelState} onRetry={retry} />
        </div>
      </div>
    </>
  );
}
