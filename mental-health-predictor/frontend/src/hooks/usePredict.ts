import { useCallback, useRef, useState } from "react";
import { ApiError, postPrediction } from "../api/client.ts";
import type { PredictRequest, Prediction } from "../api/types.ts";

export type PredictState =
  | { status: "idle" }
  | { status: "pending" }
  | { status: "success"; prediction: Prediction }
  | { status: "error"; error: ApiError };

export function usePredict(): {
  state: PredictState;
  submit: (payload: PredictRequest) => void;
  reset: () => void;
} {
  const [state, setState] = useState<PredictState>({ status: "idle" });
  const latest = useRef(0);

  const submit = useCallback((payload: PredictRequest) => {
    const id = ++latest.current;
    setState({ status: "pending" });
    postPrediction(payload)
      .then((prediction) => {
        if (id === latest.current) setState({ status: "success", prediction });
      })
      .catch((error: unknown) => {
        if (id !== latest.current) return; // a newer request replaced this one
        setState({
          status: "error",
          error:
            error instanceof ApiError
              ? error
              : new ApiError({ status: 0, code: "network_error", message: "Could not reach the server." }),
        });
      });
  }, []);

  const reset = useCallback(() => {
    latest.current += 1; // ignore any answer still on its way
    setState({ status: "idle" });
  }, []);

  return { state, submit, reset };
}
