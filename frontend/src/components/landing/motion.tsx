"use client";

import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ElementType,
  type ReactNode,
} from "react";
import { cn } from "@/lib/utils";

/**
 * Scroll/entrance motion primitives for the marketing landing page.
 *
 * Design constraints (deliberate):
 * - Zero animation dependencies. The only effects needed are scroll reveals and a
 *   one-shot staged sequence, both of which are a small IntersectionObserver plus
 *   CSS transitions. A library would ship tens of KB for unused capabilities.
 * - No layout-affecting animation: only `opacity` and `transform` transition, so
 *   reveals cannot cause cumulative layout shift.
 * - Nothing loops forever. Every animation runs once and settles.
 * - Reduced motion: content is visible in the server HTML, so it is never hidden
 *   behind JS. Under `prefers-reduced-motion: reduce` the observer is never
 *   installed and the final state renders immediately with no transform/delay.
 */

const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";

const TRANSITION =
  "transition-[opacity,transform] duration-[380ms] ease-[cubic-bezier(0.16,1,0.3,1)] motion-reduce:transition-none";

/** Tracks the user's motion preference, staying in sync with live changes. */
export function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia(REDUCED_MOTION_QUERY);
    const sync = () => setReduced(mq.matches);
    sync();
    mq.addEventListener("change", sync);
    return () => mq.removeEventListener("change", sync);
  }, []);

  return reduced;
}

/* -------------------------------------------------------------------------- */
/*  Shared one-shot reveal primitive                                          */
/* -------------------------------------------------------------------------- */

/**
 * Arms an element only if it starts below the fold, then reveals it exactly
 * once when it scrolls into view.
 *
 * An instant jump (scrollbar drag, End key, hash link, `scrollTo`) can move past
 * an element without it ever intersecting the viewport, which would leave it
 * permanently hidden. A passive scroll check treats "scrolled above the
 * viewport" as revealed, so the page can never be stranded with invisible
 * content. Reduced motion is handled by the caller: the final state is already
 * the default, so no observer or listener is installed at all.
 */
function useArmedReveal<T extends HTMLElement>(
  ref: React.RefObject<T | null>,
  { threshold, bottomInset }: { threshold: number; bottomInset: string }
) {
  const [armed, setArmed] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia(REDUCED_MOTION_QUERY).matches) return;
    // Already within (or past) the trigger line: nothing to animate.
    if (el.getBoundingClientRect().top < window.innerHeight * 0.92) return;

    setArmed(true);

    let observer: IntersectionObserver | null = null;

    const settle = () => {
      setArmed(false);
      observer?.disconnect();
      window.removeEventListener("scroll", onScroll);
    };

    const onScroll = () => {
      if (el.getBoundingClientRect().top < 0) settle();
    };

    observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) settle();
      },
      { threshold, rootMargin: `0px 0px ${bottomInset} 0px` }
    );

    observer.observe(el);
    window.addEventListener("scroll", onScroll, { passive: true });

    return () => {
      observer?.disconnect();
      window.removeEventListener("scroll", onScroll);
    };
  }, [threshold, bottomInset]);

  return armed;
}

/* -------------------------------------------------------------------------- */
/*  Scroll reveal                                                             */
/* -------------------------------------------------------------------------- */

interface RevealProps {
  children: ReactNode;
  className?: string;
  /** Stagger offset in ms. Applied only when motion is allowed. */
  delay?: number;
  as?: ElementType;
  /** Fraction of the element that must be visible before it reveals. */
  threshold?: number;
}

export function Reveal({
  children,
  className,
  delay = 0,
  as: Tag = "div",
  threshold = 0.15,
}: RevealProps) {
  const ref = useRef<HTMLElement | null>(null);

  // Visible by default so server HTML and no-JS are usable. Elements below the
  // fold are armed (hidden) only after mount, so in-view content never flashes.
  const armed = useArmedReveal(ref, { threshold, bottomInset: "-8%" });

  return (
    <Tag
      ref={ref}
      style={
        armed
          ? { opacity: 0, transform: "translateY(14px)", transitionDelay: `${delay}ms` }
          : undefined
      }
      className={cn(TRANSITION, className)}
    >
      {children}
    </Tag>
  );
}

/* -------------------------------------------------------------------------- */
/*  One-shot staged sequence (used by the pipeline diagram)                    */
/* -------------------------------------------------------------------------- */

interface StagedContextValue {
  settled: boolean;
  step: number;
}

const StagedContext = createContext<StagedContextValue>({
  settled: true,
  step: 0,
});

interface StagedGroupProps {
  children: ReactNode;
  /** Milliseconds between consecutive stages. */
  step?: number;
  threshold?: number;
  className?: string;
}

export function StagedGroup({
  children,
  step = 55,
  threshold = 0.2,
  className,
}: StagedGroupProps) {
  const ref = useRef<HTMLDivElement | null>(null);
  const armed = useArmedReveal(ref, { threshold, bottomInset: "-10%" });

  // `settled` means "no motion": everything renders in its final state.
  const settled = !armed;

  return (
    <StagedContext.Provider value={{ settled, step }}>
      <div ref={ref} className={className}>
        {children}
      </div>
    </StagedContext.Provider>
  );
}

interface StagedItemProps {
  index: number;
  children: ReactNode;
  className?: string;
  as?: ElementType;
}

/**
 * A single stage of a `StagedGroup`. Receives the group's motion state through
 * context and applies its own stagger offset.
 */
export function StagedItem({
  index,
  children,
  className,
  as: Tag = "div",
}: StagedItemProps) {
  const { settled, step } = useContext(StagedContext);

  return (
    <Tag
      style={
        settled
          ? undefined
          : {
              opacity: 0,
              transform: "translateY(10px)",
              transitionDelay: `${index * step}ms`,
            }
      }
      className={cn(TRANSITION, className)}
    >
      {children}
    </Tag>
  );
}
