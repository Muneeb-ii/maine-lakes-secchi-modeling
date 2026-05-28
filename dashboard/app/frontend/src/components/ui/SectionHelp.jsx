import { useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { HelpCircle } from "lucide-react";

const TOOLTIP_Z = 200;

function getTooltipPosition(rect, placement) {
  const centerX = rect.left + rect.width / 2;
  if (placement === "top") {
    return {
      top: rect.top - 8,
      left: centerX,
      transform: "translate(-50%, -100%)",
    };
  }
  return {
    top: rect.bottom + 8,
    left: centerX,
    transform: "translateX(-50%)",
  };
}

export function SectionHelp({ content, placement = "bottom" }) {
  const tooltipId = useId();
  const buttonRef = useRef(null);
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState(null);

  const updatePosition = () => {
    if (!buttonRef.current) return;
    const rect = buttonRef.current.getBoundingClientRect();
    setPosition(getTooltipPosition(rect, placement));
  };

  useLayoutEffect(() => {
    if (!open) {
      setPosition(null);
      return;
    }
    updatePosition();
    window.addEventListener("scroll", updatePosition, true);
    window.addEventListener("resize", updatePosition);
    return () => {
      window.removeEventListener("scroll", updatePosition, true);
      window.removeEventListener("resize", updatePosition);
    };
  }, [open, placement]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event) => {
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open]);

  if (!content?.title) return null;

  const show = () => {
    setOpen(true);
  };

  const hide = () => {
    setOpen(false);
  };

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        className="inline-flex p-1 ml-1.5 rounded-full text-slate-500 hover:text-lake-accent hover:bg-slate-800/60 transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-lake-accent align-middle"
        aria-describedby={open ? tooltipId : undefined}
        aria-label={`Help: ${content.title}`}
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={hide}
      >
        <HelpCircle className="w-4 h-4" aria-hidden />
      </button>
      {open &&
        position &&
        createPortal(
          <div
            id={tooltipId}
            role="tooltip"
            style={{
              position: "fixed",
              top: position.top,
              left: position.left,
              transform: position.transform,
              zIndex: TOOLTIP_Z,
            }}
            className="help-tooltip w-64 max-w-[calc(100vw-2rem)] p-4 rounded-lg text-left"
          >
            <p className="text-sm font-semibold text-slate-50">{content.title}</p>
            <p className="text-sm text-slate-300 mt-2 leading-relaxed">{content.body}</p>
          </div>,
          document.body
        )}
    </>
  );
}
