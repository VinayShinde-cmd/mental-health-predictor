import type { Range } from "../api/types.ts";
import { formatScore, percentAlong, wholeTicks } from "../lib/format.ts";

interface ScoreScaleProps {
  scale: Range;
  typical: Range;
  /** Leave out to show the empty ruler. */
  score?: number;
}

/**
 * The one distinctive element: a ruler across the range seen in the survey. The shaded stretch is where the
 * middle half of respondents fall; the marker is the estimate. The text alternative carries the same facts.
 */
export function ScoreScale({ scale, typical, score }: ScoreScaleProps) {
  const bandStart = percentAlong(typical.min, scale);
  const bandWidth = percentAlong(typical.max, scale) - bandStart;
  const label =
    `Scale from ${formatScore(scale.min)} to ${formatScore(scale.max)}. ` +
    `The middle half of survey respondents scored ${formatScore(typical.min)} to ${formatScore(typical.max)}.` +
    (score === undefined ? "" : ` Your estimate is ${formatScore(score)}.`);

  return (
    <div className="scale" role="img" aria-label={label}>
      <div className="scale__track">
        <div className="scale__band" style={{ left: `${bandStart}%`, width: `${bandWidth}%` }} />
        {wholeTicks(scale).map((tick) => (
          <span key={tick} className="scale__tick" style={{ left: `${percentAlong(tick, scale)}%` }}>
            <span className="scale__tick-label">{tick}</span>
          </span>
        ))}
        {score !== undefined ? (
          <span className="scale__marker" style={{ left: `${percentAlong(score, scale)}%` }}>
            <span className="scale__marker-value">{formatScore(score)}</span>
          </span>
        ) : null}
      </div>
      <p className="scale__caption" aria-hidden="true">
        Shaded: where the middle half of survey respondents scored
      </p>
    </div>
  );
}
