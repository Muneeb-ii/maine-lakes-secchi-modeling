import { useEffect, useState } from "react";

const FOOTER_SELECTOR = "#app-footer";
const DEFAULT_GAP_PX = 16;
const DESKTOP_GAP_PX = 20;

function measureBottomOffset() {
  const footer = document.querySelector(FOOTER_SELECTOR);
  if (!footer) return window.innerWidth >= 1024 ? DESKTOP_GAP_PX : DEFAULT_GAP_PX;

  const gap = window.innerWidth >= 1024 ? DESKTOP_GAP_PX : DEFAULT_GAP_PX;
  const footerTop = footer.getBoundingClientRect().top;
  const viewportHeight = window.innerHeight;

  if (footerTop >= viewportHeight) {
    return gap;
  }

  return Math.max(gap, viewportHeight - footerTop + gap);
}

export function useClaroFooterOffset() {
  const [bottomOffset, setBottomOffset] = useState(DEFAULT_GAP_PX);

  useEffect(() => {
    const update = () => setBottomOffset(measureBottomOffset());

    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update, { passive: true });

    const footer = document.querySelector(FOOTER_SELECTOR);
    const observer =
      footer &&
      new ResizeObserver(() => {
        update();
      });

    if (footer && observer) {
      observer.observe(footer);
    }

    return () => {
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
      observer?.disconnect();
    };
  }, []);

  return bottomOffset;
}
