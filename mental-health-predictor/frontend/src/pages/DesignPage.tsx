import { Button } from "../components/ui/Button.tsx";
import { Alert, EmptyState, ErrorState, Skeleton } from "../components/ui/Feedback.tsx";
import { SelectField } from "../components/ui/SelectField.tsx";
import { TextField } from "../components/ui/TextField.tsx";
import { ScoreScale } from "../components/ScoreScale.tsx";

const SCALE = { min: 3.6, max: 9.4 };
const TYPICAL = { min: 5.1, max: 7.1 };
const noop = () => undefined;

const COLOURS = [
  ["--paper", "Page"],
  ["--surface", "Panel and inputs"],
  ["--ink", "Text"],
  ["--ink-soft", "Secondary text"],
  ["--line-strong", "Input borders"],
  ["--accent", "Actions"],
  ["--band", "Typical range"],
  ["--marker", "Estimate marker"],
  ["--danger", "Errors"],
  ["--warn-bg", "Notices"],
] as const;

/** Every component in every state, so changes can be reviewed in one place. Reached at #/design. */
export function DesignPage() {
  return (
    <div className="design">
      <h1 className="intro__title">Design system</h1>
      <p className="intro__lede">Every component in every state. Light and dark follow the device setting.</p>

      <section className="design__section">
        <h2>Colour</h2>
        <ul className="swatches">
          {COLOURS.map(([token, role]) => (
            <li key={token} className="swatch">
              <span className="swatch__chip" style={{ background: `var(${token})` }} />
              <span className="swatch__name">{token}</span>
              <span className="swatch__role">{role}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="design__section">
        <h2>Type</h2>
        <p className="intro__title">Display: Bricolage Grotesque</p>
        <p>Body: Instrument Sans. Sentence case everywhere, 16 px minimum, lines under 70 characters.</p>
        <p className="field__hint">Hint text: 14 px, secondary colour.</p>
      </section>

      <section className="design__section">
        <h2>Buttons</h2>
        <div className="design__row">
          <Button>Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="quiet">Quiet</Button>
          <Button disabled>Disabled</Button>
          <Button loading>Estimating…</Button>
        </div>
      </section>

      <section className="design__section">
        <h2>Fields</h2>
        <div className="fields">
          <TextField id="d-default" label="Default" value="" onChange={noop} unit="hours a day" hint="Survey range 1 to 8.8" />
          <TextField id="d-filled" label="Filled" value="6.5" onChange={noop} unit="hours a night" />
          <TextField id="d-error" label="With error" value="30" onChange={noop} error="Enter a value between 0 and 24." />
          <TextField id="d-disabled" label="Disabled" value="21" onChange={noop} disabled />
          <SelectField id="d-select" label="Select" value="" options={[{ value: "a", label: "Option A" }]} onChange={noop} />
          <SelectField
            id="d-select-error"
            label="Select with error"
            value=""
            options={[{ value: "a", label: "Option A" }]}
            onChange={noop}
            error="Choose an option."
          />
        </div>
      </section>

      <section className="design__section">
        <h2>Feedback</h2>
        <div className="design__stack">
          <Skeleton height="2.75rem" />
          <EmptyState title="Nothing to show yet" action={{ label: "Start", onClick: noop }}>
            Say why it is empty and what to do next.
          </EmptyState>
          <ErrorState title="Couldn't load the form" message="Can't reach the server. Check your connection and try again." onRetry={noop} />
          <Alert tone="error">Some answers need a look. Fix the highlighted fields and try again.</Alert>
          <Alert tone="warning">Age (40) is outside the 18 to 24 range the model was trained on.</Alert>
        </div>
      </section>

      <section className="design__section">
        <h2>Score ruler</h2>
        <div className="design__stack">
          <ScoreScale scale={SCALE} typical={TYPICAL} />
          <ScoreScale scale={SCALE} typical={TYPICAL} score={4.2} />
          <ScoreScale scale={SCALE} typical={TYPICAL} score={6.4} />
          <ScoreScale scale={SCALE} typical={TYPICAL} score={8.9} />
        </div>
      </section>
    </div>
  );
}
