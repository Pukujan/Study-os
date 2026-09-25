export interface VisitContext {
  idleSeconds: number;
  lastVisitSeconds: number | null;
  probeOpen: boolean;
  typing: boolean;
  speaking: boolean;
  petTalking: boolean;
  petThinking: boolean;
  reducedMotion: boolean;
  petHidden: boolean;
}

export function shouldVisit(ctx: VisitContext): boolean {
  if (ctx.reducedMotion) return false;
  if (ctx.petHidden) return false;
  if (ctx.probeOpen) return false;
  if (ctx.typing || ctx.speaking || ctx.petTalking || ctx.petThinking) return false;
  if (ctx.idleSeconds < 90) return false;
  if (ctx.lastVisitSeconds !== null && ctx.lastVisitSeconds < 600) return false;
  return true;
}
