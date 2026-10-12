import type { FieldIssue, Options, PredictRequest, Prediction } from "./types.ts";

/** Empty means same origin (the dev proxy). Public by design: see .env.example. */
const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const TIMEOUT_MS = 10_000;

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly issues: FieldIssue[];
  readonly retryAfterSeconds: number | null;
  readonly requestId: string | null;

  constructor(init: {
    status: number;
    code: string;
    message: string;
    issues?: FieldIssue[];
    retryAfterSeconds?: number | null;
    requestId?: string | null;
  }) {
    super(init.message);
    this.name = "ApiError";
    this.status = init.status;
    this.code = init.code;
    this.issues = init.issues ?? [];
    this.retryAfterSeconds = init.retryAfterSeconds ?? null;
    this.requestId = init.requestId ?? null;
  }
}

interface ErrorBody {
  error?: { code?: unknown; message?: unknown; request_id?: unknown; details?: unknown };
}

function parseIssues(details: unknown): FieldIssue[] {
  if (!Array.isArray(details)) return [];
  return details.flatMap((item: unknown) => {
    if (typeof item !== "object" || item === null) return [];
    const { field, message } = item as Record<string, unknown>;
    return typeof field === "string" && typeof message === "string" ? [{ field, message }] : [];
  });
}

async function request<T>(path: string, init: RequestInit = {}, signal?: AbortSignal): Promise<T> {
  const timeout = new AbortController();
  const timer = setTimeout(() => timeout.abort(), TIMEOUT_MS);
  const onCallerAbort = () => timeout.abort();
  signal?.addEventListener("abort", onCallerAbort);

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: { Accept: "application/json", ...init.headers },
      signal: timeout.signal,
    });
  } catch (cause) {
    if (signal?.aborted) throw cause; // the caller cancelled; not an error to show
    const timedOut = timeout.signal.aborted;
    throw new ApiError({
      status: 0,
      code: timedOut ? "timeout" : "network_error",
      message: timedOut ? "The server took too long to answer." : "Could not reach the server.",
    });
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", onCallerAbort);
  }

  if (response.ok) return (await response.json()) as T;

  let body: ErrorBody = {};
  try {
    body = (await response.json()) as ErrorBody;
  } catch {
    // Not our error format (for example a proxy error page). Fall through to a generic error.
  }
  const retryHeader = Number(response.headers.get("Retry-After"));
  throw new ApiError({
    status: response.status,
    code: typeof body.error?.code === "string" ? body.error.code : "http_error",
    message: typeof body.error?.message === "string" ? body.error.message : "The request failed.",
    issues: parseIssues(body.error?.details),
    retryAfterSeconds: Number.isFinite(retryHeader) && retryHeader > 0 ? retryHeader : null,
    requestId: typeof body.error?.request_id === "string" ? body.error.request_id : null,
  });
}

export function fetchOptions(signal?: AbortSignal): Promise<Options> {
  return request<Options>("/api/options", {}, signal);
}

export function postPrediction(payload: PredictRequest, signal?: AbortSignal): Promise<Prediction> {
  return request<Prediction>(
    "/api/predict",
    { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) },
    signal,
  );
}

/** Plain-language text for an error, in the app's voice: what happened and what to do. */
export function describeError(error: ApiError): string {
  switch (error.code) {
    case "network_error":
      return "Can't reach the server. Check your connection and try again.";
    case "timeout":
      return "The server took too long to answer. Try again in a moment.";
    case "rate_limited":
      return error.retryAfterSeconds
        ? `That's a lot of estimates in a short time. Try again in ${error.retryAfterSeconds} seconds.`
        : "That's a lot of estimates in a short time. Wait a moment and try again.";
    case "invalid_request":
      return "Some answers need a look. Fix the highlighted fields and try again.";
    default:
      return error.status >= 500
        ? "Something went wrong on our side. Try again in a moment."
        : "The request didn't go through. Reload the page and try again.";
  }
}
