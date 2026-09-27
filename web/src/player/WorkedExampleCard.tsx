import type { WorkedExample } from "../api";
import { Markdown } from "../markdown";
import FrameStepper from "../visuals/FrameStepper";
import { workedExampleParts } from "./workedExample";

/**
 * Renders a worked-example card from whatever the server actually sent.
 *
 * The card has historically arrived as `{md}`, as `{steps_md}`, or as a payload
 * with neither field (the server strips `solution_md`, issue #126). Every shape
 * renders something useful and none of them throw.
 */
export default function WorkedExampleCard({ example }: { example: WorkedExample | null | undefined }) {
  const { md, steps, frames } = workedExampleParts(example);
  const empty = !md && steps.length === 0 && frames.length === 0;

  return (
    <div className="worked-example" data-testid="worked-example">
      {md && <Markdown text={md} />}
      {!md && steps.length > 0 && (
        <ol>
          {steps.map((step, i) => (
            <li key={i}>
              <Markdown text={step} />
            </li>
          ))}
        </ol>
      )}
      {frames.length > 0 && <FrameStepper frames={frames} label="Worked example frames" />}
      {empty && (
        <p className="muted" data-testid="worked-example-empty">
          No worked example is available for this step yet.
        </p>
      )}
    </div>
  );
}