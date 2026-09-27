import type { CuratedDiagramFrame } from "../api";

export function describeCuratedDiagram(frame: CuratedDiagramFrame): string {
  return frame.alt || frame.caption || `Curated diagram ${frame.asset_id}`;
}

/** Renders a provenance-backed OSS/public-domain diagram from the teach-visual pack. */
export default function CuratedDiagram({ frame }: { frame: CuratedDiagramFrame }) {
  return (
    <div
      className="curated-diagram"
      data-testid="curated-diagram"
      data-asset-id={frame.asset_id}
      role="img"
      aria-label={describeCuratedDiagram(frame)}
    >
      <img
        src={frame.src}
        alt={frame.alt || frame.caption || frame.asset_id}
        loading="lazy"
        decoding="async"
        style={{ display: "block", maxWidth: "100%", height: "auto" }}
      />
    </div>
  );
}
