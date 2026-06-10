import { useCallback, useEffect, useLayoutEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { ArrowLeft, ArrowRight, MousePointer2, X } from "lucide-react";
import { ClaroMascot } from "./ClaroMascot";
import {
  CLARO_NAME,
  CLARO_PERSONA,
  CLARO_STORAGE_KEY,
  formatClaroStepProgress,
  getAvailableClaroSteps,
  getClaroRouteConfig,
  getStepIndexByDirection,
  markClaroPromptDismissed,
  markClaroTourCompleted,
  normalizeClaroState,
  shouldShowClaroPrompt,
} from "../../lib/claroTourContent";
import { useClaroFooterOffset } from "../../hooks/useClaroFooterOffset";
import { useReducedMotion } from "../../lib/useReducedMotion";

const OVERLAY_Z = 300;
const TARGET_PADDING = 10;
const CARD_GAP = 16;

function readClaroState() {
  try {
    return normalizeClaroState(JSON.parse(window.localStorage.getItem(CLARO_STORAGE_KEY)));
  } catch {
    return normalizeClaroState(null);
  }
}

function writeClaroState(nextState) {
  window.localStorage.setItem(CLARO_STORAGE_KEY, JSON.stringify(normalizeClaroState(nextState)));
}

function getTargetElement(target) {
  if (!target) return null;
  return document.querySelector(`[data-claro-target="${target}"]`);
}

function rectWithPadding(rect) {
  return {
    top: Math.max(8, rect.top - TARGET_PADDING),
    left: Math.max(8, rect.left - TARGET_PADDING),
    width: Math.min(window.innerWidth - 16, rect.width + TARGET_PADDING * 2),
    height: rect.height + TARGET_PADDING * 2,
  };
}

function getCardPosition(targetRect, placement) {
  const maxWidth = Math.min(390, window.innerWidth - 24);
  const fallbackTop = Math.max(12, (window.innerHeight - 260) / 2);
  const centerLeft = (window.innerWidth - maxWidth) / 2;

  if (!targetRect || placement === "center") {
    return { top: fallbackTop, left: centerLeft, width: maxWidth };
  }

  const rightLeft = targetRect.left + targetRect.width + CARD_GAP;
  const leftLeft = targetRect.left - maxWidth - CARD_GAP;
  const topTop = targetRect.top - CARD_GAP - 260;
  const bottomTop = targetRect.top + targetRect.height + CARD_GAP;
  const alignedTop = Math.min(Math.max(12, targetRect.top), window.innerHeight - 280);

  if (placement === "right" && rightLeft + maxWidth <= window.innerWidth - 12) {
    return { top: alignedTop, left: rightLeft, width: maxWidth };
  }
  if (placement === "left" && leftLeft >= 12) {
    return { top: alignedTop, left: leftLeft, width: maxWidth };
  }
  if (placement === "top" && topTop >= 12) {
    return { top: topTop, left: Math.min(Math.max(12, targetRect.left), window.innerWidth - maxWidth - 12), width: maxWidth };
  }
  if (placement === "bottom" && bottomTop + 260 <= window.innerHeight - 12) {
    return { top: bottomTop, left: Math.min(Math.max(12, targetRect.left), window.innerWidth - maxWidth - 12), width: maxWidth };
  }

  if (targetRect.top > window.innerHeight / 2) {
    return { top: 12, left: centerLeft, width: maxWidth };
  }
  return { top: window.innerHeight - 292, left: centerLeft, width: maxWidth };
}

function ClaroCursorHint({ rect, hint, reducedMotion }) {
  if (!rect || !hint) return null;
  return (
    <div
      className={`claro-cursor-hint ${reducedMotion ? "" : "claro-cursor-hint-motion"}`}
      style={{
        top: rect.top + Math.min(rect.height - 8, Math.max(20, rect.height * 0.48)),
        left: rect.left + Math.min(rect.width - 8, Math.max(24, rect.width * 0.62)),
      }}
      aria-hidden
    >
      <MousePointer2 className="h-6 w-6" />
      <span>{hint}</span>
    </div>
  );
}

function ClaroOverlay({ steps, stepIndex, onPrevious, onNext, onEnd }) {
  const reducedMotion = useReducedMotion();
  const [targetRect, setTargetRect] = useState(null);
  const activeStep = steps[stepIndex];
  const isFirst = stepIndex <= 0;
  const isLast = stepIndex >= steps.length - 1;

  const updatePosition = useCallback(() => {
    if (!activeStep?.target) {
      setTargetRect(null);
      return;
    }
    const element = getTargetElement(activeStep.target);
    if (!element) {
      setTargetRect(null);
      return;
    }
    setTargetRect(rectWithPadding(element.getBoundingClientRect()));
  }, [activeStep]);

  useLayoutEffect(() => {
    updatePosition();
    window.addEventListener("scroll", updatePosition, true);
    window.addEventListener("resize", updatePosition);
    return () => {
      window.removeEventListener("scroll", updatePosition, true);
      window.removeEventListener("resize", updatePosition);
    };
  }, [updatePosition]);

  useEffect(() => {
    if (!activeStep?.target) return;
    const element = getTargetElement(activeStep.target);
    element?.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "center", inline: "nearest" });
    const timer = window.setTimeout(updatePosition, reducedMotion ? 20 : 320);
    return () => window.clearTimeout(timer);
  }, [activeStep, reducedMotion, updatePosition]);

  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.key === "Escape") onEnd();
      if (event.key === "ArrowRight") onNext();
      if (event.key === "ArrowLeft") onPrevious();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onEnd, onNext, onPrevious]);

  if (!activeStep) return null;

  const cardPosition = getCardPosition(targetRect, activeStep.placement);
  const stepLabel = formatClaroStepProgress(stepIndex, steps.length);

  return createPortal(
    <div className="claro-tour-layer" style={{ zIndex: OVERLAY_Z }} role="dialog" aria-modal="true" aria-label={`${CLARO_NAME} guided tour`}>
      <div className="claro-tour-scrim" aria-hidden />
      {targetRect && (
        <div
          className="claro-spotlight"
          style={{
            top: targetRect.top,
            left: targetRect.left,
            width: targetRect.width,
            height: targetRect.height,
          }}
          aria-hidden
        />
      )}
      <ClaroCursorHint rect={targetRect} hint={activeStep.cursorHint} reducedMotion={reducedMotion} />
      <section
        className="claro-tour-card"
        style={{
          top: cardPosition.top,
          left: cardPosition.left,
          width: cardPosition.width,
        }}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="claro-kicker">
              <ClaroMascot className="h-4 w-4" />
              {CLARO_PERSONA.name} · {CLARO_PERSONA.tagline}
            </p>
            <h2 className="mt-2 text-xl font-semibold leading-snug text-slate-950">{activeStep.title}</h2>
          </div>
          <button type="button" className="claro-icon-button" onClick={onEnd} aria-label="End Claro tour">
            <X className="h-5 w-5" aria-hidden />
          </button>
        </div>
        <p className="mt-3 text-base leading-relaxed text-slate-700">{activeStep.body}</p>
        <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <span className="text-base font-medium text-slate-600">{stepLabel}</span>
          <div className="flex flex-wrap gap-2">
            <button type="button" className="action-button h-11 px-3" onClick={onPrevious} disabled={isFirst}>
              <ArrowLeft className="h-4 w-4" aria-hidden />
              Back
            </button>
            <button type="button" className="claro-button px-3" onClick={onNext}>
              {isLast ? "Finish" : "Next"}
              {!isLast && <ArrowRight className="h-4 w-4" aria-hidden />}
            </button>
          </div>
        </div>
      </section>
    </div>,
    document.body
  );
}

const LAUNCHER_HEIGHT_MOBILE = 48;
const LAUNCHER_HEIGHT_DESKTOP = 56;
const PROMPT_GAP_ABOVE_LAUNCHER = 12;

export function ClaroGuide({ routeId }) {
  const routeConfig = getClaroRouteConfig(routeId);
  const [state, setState] = useState(() => readClaroState());
  const [tourOpen, setTourOpen] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [targetVersion, setTargetVersion] = useState(0);
  const footerBottomOffset = useClaroFooterOffset();
  const [launcherTier, setLauncherTier] = useState("mobile");

  useEffect(() => {
    const media = window.matchMedia("(min-width: 1024px)");
    const sync = () => setLauncherTier(media.matches ? "desktop" : "mobile");
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, []);

  const launcherHeight =
    launcherTier === "desktop" ? LAUNCHER_HEIGHT_DESKTOP : LAUNCHER_HEIGHT_MOBILE;
  const dockStyle = { bottom: `${footerBottomOffset}px` };
  const promptStyle = {
    bottom: `${footerBottomOffset + launcherHeight + PROMPT_GAP_ABOVE_LAUNCHER}px`,
  };

  const steps = useMemo(() => {
    if (!routeConfig) return [];
    return getAvailableClaroSteps(routeConfig.steps, (target) => Boolean(getTargetElement(target)));
  }, [routeConfig, targetVersion]);

  const promptVisible = routeConfig && shouldShowClaroPrompt(state, routeId) && !tourOpen;

  useEffect(() => {
    setTourOpen(false);
    setStepIndex(0);
    setState(readClaroState());
  }, [routeId]);

  useEffect(() => {
    const timer = window.setTimeout(() => setTargetVersion((previous) => previous + 1), 0);
    return () => window.clearTimeout(timer);
  }, [routeId]);

  if (!routeConfig) return null;

  const persistState = (nextState) => {
    setState(nextState);
    writeClaroState(nextState);
  };

  const openTour = () => {
    setTargetVersion((previous) => previous + 1);
    setStepIndex(0);
    setTourOpen(true);
  };

  const closePrompt = () => {
    persistState(markClaroPromptDismissed(state, routeId));
  };

  const completeTour = () => {
    setTourOpen(false);
    setStepIndex(0);
    persistState(markClaroTourCompleted(state, routeId));
  };

  const previousStep = () => {
    setStepIndex((previous) => getStepIndexByDirection(previous, -1, steps));
  };

  const nextStep = () => {
    if (stepIndex >= steps.length - 1) {
      completeTour();
      return;
    }
    setStepIndex((previous) => getStepIndexByDirection(previous, 1, steps));
  };

  return (
    <>
      {promptVisible && (
        <aside
          className="claro-prompt"
          style={promptStyle}
          aria-label="Claro guided tour invitation"
        >
          <p className="claro-kicker">
            <ClaroMascot className="h-4 w-4" />
            {CLARO_PERSONA.name}
          </p>
          <h2 className="mt-2 text-lg font-semibold leading-snug text-slate-950">{routeConfig.promptTitle}</h2>
          <p className="mt-2 text-base leading-relaxed text-slate-700">{routeConfig.promptBody}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            <button type="button" className="claro-button px-3" onClick={openTour}>
              Start tour
            </button>
            <button type="button" className="action-button h-11 px-3" onClick={closePrompt}>
              Dismiss
            </button>
          </div>
        </aside>
      )}
      <button
        type="button"
        className="claro-launcher"
        style={dockStyle}
        onClick={openTour}
        aria-label="Start Claro guided tour"
      >
        <span className="claro-launcher-mark">
          <ClaroMascot className="h-7 w-7 lg:h-8 lg:w-8" />
        </span>
        <span>{CLARO_NAME}</span>
      </button>
      {tourOpen && steps.length > 0 && (
        <ClaroOverlay
          steps={steps}
          stepIndex={stepIndex}
          onPrevious={previousStep}
          onNext={nextStep}
          onEnd={completeTour}
        />
      )}
    </>
  );
}
