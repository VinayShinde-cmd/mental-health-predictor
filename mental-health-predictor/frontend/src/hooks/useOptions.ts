import { useCallback, useEffect, useState } from "react";
import { ApiError, fetchOptions } from "../api/client.ts";
import type { Options } from "../api/types.ts";

export type OptionsState =
  | { status: "loading" }
  | { status: "error"; error: ApiError }
  | { status: "ready"; options: Options };

/** Loads the dropdown values and limits. `reload` retries after a failure. */
export function useOptions(): { state: OptionsState; reload: () => void } {
  const [state, setState] = useState<OptionsState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    fetchOptions(controller.signal)
      .then((options) => setState({ status: "ready", options }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          status: "error",
          error:
            error instanceof ApiError
              ? error
              : new ApiError({ status: 0, code: "network_error", message: "Could not load the form." }),
        });
      });
    return () => controller.abort();
  }, [attempt]);

  const reload = useCallback(() => setAttempt((n) => n + 1), []);
  return { state, reload };
}
