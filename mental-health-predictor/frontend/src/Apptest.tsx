import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App.tsx";

const limit = (min: number, max: number) => ({ min, max });
const OPTIONS = {
  genders: ["Female", "Male"],
  academic_levels: ["Graduate", "High School", "Undergraduate"],
  platforms: ["Instagram", "TikTok"],
  purposes: ["Education", "Entertainment"],
  countries: ["Australia", "India", "Other"],
  stress_levels: ["Low", "Medium", "High", "Very High"],
  limits: {
    age: limit(13, 100),
    avg_daily_usage_hours: limit(0, 24),
    daily_unlocks: limit(0, 2000),
    study_hours: limit(0, 24),
    physical_activity_hours: limit(0, 24),
    sleep_hours_per_night: limit(0, 24),
  },
  training_ranges: {
    age: limit(18, 24),
    avg_daily_usage_hours: limit(1, 8.8),
    daily_unlocks: limit(62, 273),
    study_hours: limit(0.3, 8.3),
    physical_activity_hours: limit(0, 4.1),
    sleep_hours_per_night: limit(3.6, 9.9),
  },
};

const PREDICTION = {
  score: 6.4,
  band: "typical",
  band_label: "Within the typical range",
  typical_range: limit(5.1, 7.1),
  scale: limit(3.6, 9.4),
  warnings: [],
  disclaimer: "This is a statistical estimate. It is not a diagnosis or medical advice.",
  model_id: "abc123def456",
};

function json(body: unknown, status = 200, headers: Record<string, string> = {}) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...headers } });
}

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
  window.location.hash = "";
});
afterEach(() => vi.unstubAllGlobals());

/** Routes by URL so each test only describes what differs. */
function serve(handlers: { options?: () => Response | Promise<Response>; predict?: () => Response | Promise<Response> }) {
  fetchMock.mockImplementation((url: string) => {
    if (url.endsWith("/api/options")) return Promise.resolve((handlers.options ?? (() => json(OPTIONS)))());
    if (url.endsWith("/api/predict")) return Promise.resolve((handlers.predict ?? (() => json(PREDICTION)))());
    return Promise.reject(new Error(`unexpected request to ${url}`));
  });
}

async function fillValidForm(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText("Age"), "21");
  await user.selectOptions(screen.getByLabelText("Gender"), "Female");
  await user.selectOptions(screen.getByLabelText("Academic level"), "Undergraduate");
  await user.selectOptions(screen.getByLabelText("Country"), "India");
  await user.selectOptions(screen.getByLabelText("Most-used platform"), "Instagram");
  await user.selectOptions(screen.getByLabelText("Main reason you use it"), "Education");
  await user.type(screen.getByLabelText("Daily phone use"), "4.5");
  await user.type(screen.getByLabelText("Phone unlocks per day"), "150");
  await user.type(screen.getByLabelText("Study time"), "3");
  await user.type(screen.getByLabelText("Physical activity"), "1.5");
  await user.type(screen.getByLabelText("Sleep"), "7");
  await user.selectOptions(screen.getByLabelText("Stress level"), "Medium");
}

async function expectNoAccessibilityViolations(container: HTMLElement) {
  // Colour contrast needs real layout, which jsdom lacks; contrast was checked numerically (docs/testing.md).
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  expect(results.violations.map((v) => `${v.id}: ${v.help}`)).toEqual([]);
}

describe("loading the form", () => {
  it("shows a loading state, then the form", async () => {
    serve({});
    render(<App />);
    expect(screen.getByText("Loading the form…")).toBeInTheDocument();
    expect(await screen.findByLabelText("Age")).toBeInTheDocument();
    expect(screen.queryByText("Loading the form…")).not.toBeInTheDocument();
  });

  it("shows what went wrong with a retry, and recovers when retried", async () => {
    const user = userEvent.setup();
    let calls = 0;
    serve({ options: () => (++calls === 1 ? json({ error: { code: "internal_error", message: "x" } }, 500) : json(OPTIONS)) });
    render(<App />);
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Couldn't load the form");
    expect(alert).toHaveTextContent("Something went wrong on our side");
    await user.click(within(alert).getByRole("button", { name: "Try again" }));
    expect(await screen.findByLabelText("Age")).toBeInTheDocument();
  });

  it("explains a network failure in plain words", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Can't reach the server");
  });
});

describe("empty state", () => {
  it("invites the first action and shows the empty ruler", async () => {
    serve({});
    render(<App />);
    await screen.findByLabelText("Age");
    expect(screen.getByText("Nothing to show yet")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /Scale from 3\.6 to 9\.4/ })).toBeInTheDocument();
  });
});

describe("submitting", () => {
  it("shows inline errors, focuses the first one and sends nothing when the form is empty", async () => {
    const user = userEvent.setup();
    serve({});
    render(<App />);
    await screen.findByLabelText("Age");
    await user.click(screen.getByRole("button", { name: "Estimate my score" }));
    expect(screen.getByLabelText("Age")).toHaveFocus();
    expect(screen.getByLabelText("Age")).toHaveAttribute("aria-invalid", "true");
    expect(screen.getAllByText("Choose an option.").length).toBeGreaterThan(0);
    expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith("/api/predict"))).toBe(false);
  });

  it("sends the answers and shows the estimate on the ruler", async () => {
    const user = userEvent.setup();
    serve({});
    render(<App />);
    await screen.findByLabelText("Age");
    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: "Estimate my score" }));

    expect(await screen.findByText("6.4", { selector: ".result__score" })).toBeInTheDocument();
    expect(screen.getByText("Within the typical range")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /Your estimate is 6\.4/ })).toBeInTheDocument();
    expect(screen.getByText(/not a diagnosis/)).toBeInTheDocument();

    const predictCall = fetchMock.mock.calls.find(([url]) => String(url).endsWith("/api/predict"));
    expect(JSON.parse(String(predictCall?.[1]?.body))).toMatchObject({ age: 21, country: "India", stress_level: "Medium" });
  });

  it("disables the form while the request is pending", async () => {
    const user = userEvent.setup();
    let release: (response: Response) => void = () => undefined;
    serve({ predict: () => new Promise<Response>((resolve) => (release = resolve)) as unknown as Response });
    render(<App />);
    await screen.findByLabelText("Age");
    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: "Estimate my score" }));

    const busy = await screen.findByRole("button", { name: "Estimating…" });
    expect(busy).toBeDisabled();
    expect(screen.getByLabelText("Age")).toBeDisabled();
    release(json(PREDICTION));
    expect(await screen.findByText("6.4", { selector: ".result__score" })).toBeInTheDocument();
  });

  it("shows server field errors next to the field", async () => {
    const user = userEvent.setup();
    serve({
      predict: () =>
        json(
          { error: { code: "invalid_request", message: "Some fields are invalid.", request_id: "r", details: [{ field: "age", message: "Input should be greater than or equal to 13" }] } },
          400,
        ),
    });
    render(<App />);
    await screen.findByLabelText("Age");
    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: "Estimate my score" }));

    expect(await screen.findByText("Input should be greater than or equal to 13")).toBeInTheDocument();
    expect(screen.getByLabelText("Age")).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByRole("alert")).toHaveTextContent("Some answers need a look");
  });

  it("tells the user when to retry after being rate limited, and retries with the same answers", async () => {
    const user = userEvent.setup();
    let calls = 0;
    serve({
      predict: () =>
        ++calls === 1
          ? json({ error: { code: "rate_limited", message: "Too many requests." } }, 429, { "Retry-After": "42" })
          : json(PREDICTION),
    });
    render(<App />);
    await screen.findByLabelText("Age");
    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: "Estimate my score" }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Try again in 42 seconds");
    await user.click(within(alert).getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(screen.getByText("6.4", { selector: ".result__score" })).toBeInTheDocument());
  });

  it("shows out-of-range warnings from the server", async () => {
    const user = userEvent.setup();
    serve({ predict: () => json({ ...PREDICTION, warnings: ["Age (40) is outside the 18 to 24 range the model was trained on."] }) });
    render(<App />);
    await screen.findByLabelText("Age");
    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: "Estimate my score" }));
    expect(await screen.findByText(/Age \(40\) is outside/)).toBeInTheDocument();
  });

  it("never renders server text as HTML", async () => {
    const user = userEvent.setup();
    serve({ predict: () => json({ ...PREDICTION, warnings: ["<img src=x onerror=alert(1)>"] }) });
    const { container } = render(<App />);
    await screen.findByLabelText("Age");
    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: "Estimate my score" }));
    await screen.findByText("<img src=x onerror=alert(1)>");
    expect(container.querySelector("img")).toBeNull();
  });
});

describe("accessibility (axe)", () => {
  it("the loaded form has no violations", async () => {
    serve({});
    const { container } = render(<App />);
    await screen.findByLabelText("Age");
    await expectNoAccessibilityViolations(container);
  });

  it("the form with errors has no violations", async () => {
    const user = userEvent.setup();
    serve({});
    const { container } = render(<App />);
    await screen.findByLabelText("Age");
    await user.click(screen.getByRole("button", { name: "Estimate my score" }));
    await expectNoAccessibilityViolations(container);
  });

  it("the result has no violations", async () => {
    const user = userEvent.setup();
    serve({});
    const { container } = render(<App />);
    await screen.findByLabelText("Age");
    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: "Estimate my score" }));
    await screen.findByText("6.4", { selector: ".result__score" });
    await expectNoAccessibilityViolations(container);
  });

  it("the design system page has no violations", async () => {
    window.location.hash = "#/design";
    serve({});
    const { container } = render(<App />);
    expect(await screen.findByRole("heading", { name: "Design system", level: 1 })).toBeInTheDocument();
    await expectNoAccessibilityViolations(container);
  });
});
