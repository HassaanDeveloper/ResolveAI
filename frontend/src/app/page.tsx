"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { ArrowRight, ArrowUpRight } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { DecisionBadge } from "@/components/ui/decision-badge";
import { Reveal } from "@/components/landing/motion";
import { ResolutionPipeline } from "@/components/landing/pipeline";
import { cn } from "@/lib/utils";

/**
 * TODO(owner): replace every entry with a real URL before publishing.
 * Left blank on purpose — a placeholder link that points nowhere is better than
 * an invented repository, profile, or company that does not exist.
 */
const EXTERNAL_LINKS: Record<string, string> = {
  architecture: "",
  github: "https://github.com/HassaanDeveloper/ResolveAI",
  linkedin: "https://www.linkedin.com/in/muhammad-hassaan-a22693269",
};

const CORE_LOOP = [
  "Evidence",
  "Policy",
  "Controlled action",
  "Verification",
  "Audit",
] as const;

type Decision = "ALLOW" | "DENY" | "REQUIRES_APPROVAL";

/**
 * The real rule ladder from `backend/app/policies/engine.py`. Rules are sorted
 * by priority descending and the first match wins; `refund_eligibility_denied`
 * sits at priority 100 so an ineligible request is denied before any amount
 * band is considered.
 */
const DECISION_LADDER: { rule: string; condition: string; decision: Decision }[] = [
  { rule: "refund_eligibility_denied", condition: "Request violates eligibility", decision: "DENY" },
  { rule: "refund_high_value_customer_escalation", condition: "High-value customer or prior escalation", decision: "REQUIRES_APPROVAL" },
  { rule: "refund_carrier_loss_requires_approval", condition: "Carrier loss or damage", decision: "REQUIRES_APPROVAL" },
  { rule: "refund_auto_approve", condition: "Eligible and amount at or below $100.00", decision: "ALLOW" },
  { rule: "refund_manager_approval", condition: "Above $100.00 up to $500.00", decision: "REQUIRES_APPROVAL" },
  { rule: "refund_director_approval", condition: "Above $500.00 up to $1,000.00", decision: "REQUIRES_APPROVAL" },
  { rule: "refund_legal_review", condition: "Above $1,000.00", decision: "REQUIRES_APPROVAL" },
  { rule: "cancellation_after_shipment", condition: "Cancellation after the order shipped", decision: "REQUIRES_APPROVAL" },
  { rule: "unknown_action_requires_approval", condition: "Unknown or high-risk action", decision: "REQUIRES_APPROVAL" },
];

const STACK = [
  {
    layer: "Frontend",
    detail: "Next.js 16 App Router, React 19, TypeScript, Tailwind CSS v4, shadcn/ui",
  },
  {
    layer: "API",
    detail: "FastAPI with Uvicorn, REST over typed Pydantic models",
  },
  {
    layer: "Orchestration",
    detail: "Custom Python controller. No LangChain, LangGraph, CrewAI or AutoGen",
  },
  {
    layer: "Data",
    detail: "Supabase PostgreSQL, with pgvector for embedding storage and similarity search",
  },
  {
    layer: "Models",
    detail: "Google Gemini for reasoning, gemini-embedding-001 for retrieval",
  },
  {
    layer: "Runtime",
    detail: "No Docker, Kubernetes, Redis, Kafka or Celery. The stack runs as-is",
  },
];

const ENGINEERING_NOTES = [
  "Deny-first, priority-ordered rule evaluation. The first matching rule decides the outcome, and an ineligible request is denied before any amount band is read.",
  "The policy engine is plain Python and sits outside the model. The same request produces the same decision every time.",
  "Business tools are deterministic functions. The model chooses which tool to call; the tool computes the answer.",
  "An idempotency ledger is keyed by operation, so a retried refund resolves to the original result instead of executing twice.",
  "Reads and external calls are wrapped in retry with backoff and circuit breakers.",
  "High-risk actions stop at an approval gate. A human decision is recorded before anything is executed.",
  "Execution is verified against the system of record, then written to an audit log and a workflow trace.",
];

const ROUTES = [
  {
    href: "/console",
    name: "Resolution Console",
    description:
      "Submit a real order and watch the nine stages run end to end, with the retrieved evidence, the policy decision, every tool call, and the verification result.",
  },
  {
    href: "/approvals",
    name: "Approval Queue",
    description:
      "Review what the engine refused to decide alone. High-value refunds and post-shipment cancellations arrive here with the policy reason, risk level, and the exact action payload.",
  },
  {
    href: "/knowledge",
    name: "Knowledge Base",
    description:
      "Ingest policy documents, watch them chunk and embed into pgvector, and run semantic search against the same index the engine queries while resolving.",
  },
  {
    href: "/evaluation",
    name: "Evaluation",
    description:
      "Read the latest real integration run: scenario count, pass rate, results by category, and per-scenario duration with the reason for any failure.",
  },
];

/* -------------------------------------------------------------------------- */

function SectionLabel({ children }: { children: ReactNode }) {
  return <p className="text-label text-muted-foreground">{children}</p>;
}

function SectionIntro({
  id,
  label,
  title,
  lede,
}: {
  id: string;
  label: string;
  title: ReactNode;
  lede: ReactNode;
}) {
  return (
    <Reveal className="max-w-2xl">
      <SectionLabel>{label}</SectionLabel>
      <h2
        id={id}
        className="mt-4 text-[1.75rem] font-semibold leading-[1.15] tracking-[-0.02em] text-foreground md:text-[2.125rem]"
      >
        {title}
      </h2>
      <p className="mt-4 text-h2 font-normal leading-[1.6] text-muted-foreground">
        {lede}
      </p>
    </Reveal>
  );
}

function Divider() {
  return <div aria-hidden="true" className="h-px w-full bg-border-default" />;
}

/* -------------------------------------------------------------------------- */

export default function LandingPage() {
  return (
    <div id="main-content" className="pb-24">
      {/* ============================ Hero ============================ */}
      <section aria-labelledby="hero-heading" className="pt-10 md:pt-16 lg:pt-20">
        <div className="mx-auto max-w-6xl px-4 md:px-0">
          <Reveal>
            <span className="inline-flex items-center gap-2.5 border border-border-default bg-surface-card px-3 py-1.5">
              <span
                aria-hidden="true"
                className="h-1.5 w-1.5 rounded-full bg-status-evidence"
              />
              <span className="text-label text-foreground">
                Controlled AI resolution engine
              </span>
            </span>
          </Reveal>

          <Reveal delay={60}>
            <h1
              id="hero-heading"
              className="mt-8 max-w-4xl text-[2.125rem] font-semibold leading-[1.08] tracking-[-0.03em] text-foreground sm:text-[2.75rem] lg:text-[3.5rem]"
            >
              Operational exceptions, resolved under policy control.
            </h1>
          </Reveal>

          <Reveal delay={120}>
            <p className="mt-6 max-w-2xl text-h2 font-normal leading-[1.65] text-muted-foreground">
              ResolveAI is not a chatbot. It is an engine for the requests that
              normally stall in an operations queue: a refund that may or may not
              be owed, a cancellation that has already shipped, a charge that
              looks wrong. It gathers the evidence, applies a deterministic
              policy engine outside the model, and only then acts.
            </p>
          </Reveal>

          {/* Core loop */}
          <Reveal delay={180}>
            <div className="mt-10">
              <SectionLabel>Core loop</SectionLabel>
              <ol className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-2 text-mono text-foreground">
                {CORE_LOOP.map((step, i) => (
                  <li key={step} className="flex items-center gap-2">
                    <span
                      className={cn(
                        "rounded border px-2 py-1 text-foreground",
                        i === 0 && "border-status-evidence/50",
                        i === 1 && "border-status-policy/50"
                      )}
                    >
                      {step}
                    </span>
                    {i < CORE_LOOP.length - 1 && (
                      <ArrowRight
                        aria-hidden="true"
                        className="h-3 w-3 text-muted-foreground/50"
                      />
                    )}
                  </li>
                ))}
              </ol>
            </div>
          </Reveal>

          <Reveal delay={220}>
            <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:items-center">
                <Link
                  href="/console"
                  className={cn(
                    buttonVariants({ variant: "outline", size: "lg" }),
                    "group inline-flex items-center justify-center gap-2 border-transparent bg-foreground px-5 py-2.5 text-body-sm font-medium text-background hover:bg-foreground/90 hover:text-background"
                  )}
                >
                  Open the Resolution Console
                  <ArrowRight
                    aria-hidden="true"
                    className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5 motion-reduce:transform-none motion-reduce:transition-none"
                  />
                </Link>

              {EXTERNAL_LINKS.architecture ? (
                <a
                  href={EXTERNAL_LINKS.architecture}
                  target="_blank"
                  rel="noreferrer noopener"
                  className={cn(
                    buttonVariants({ variant: "outline", size: "lg" }),
                    "inline-flex items-center justify-center gap-2 px-5 py-2.5 text-body-sm font-medium"
                  )}
                >
                  Read the architecture
                  <ArrowUpRight aria-hidden="true" className="h-3.5 w-3.5" />
                </a>
              ) : (
                <span
                  className="inline-flex cursor-not-allowed items-center gap-2 border border-dashed border-border-muted px-5 py-2.5 text-body-sm text-muted-foreground"
                  title="TODO: set EXTERNAL_LINKS.architecture to your published architecture document"
                >
                  Read the architecture
                  <span className="text-label text-muted-foreground">
                    TODO link
                  </span>
                </span>
              )}
            </div>
          </Reveal>
        </div>
      </section>

      <div className="mx-auto mt-20 max-w-6xl px-4 md:mt-28 md:px-0">
        <Divider />
      </div>

      {/* ======================= Positioning ========================== */}
      <section aria-labelledby="positioning-heading" className="py-20 md:py-28">
        <div className="mx-auto max-w-6xl px-4 md:px-0">
          <SectionIntro
            id="positioning-heading"
            label="Positioning"
            title={
              <>
                An answer ends the conversation.
                <br />
                A resolution has to survive review.
              </>
            }
            lede="A plausible paragraph is cheap and unauditable. ResolveAI is built for the part where someone has to be accountable for what actually happened to a customer."
          />

          <div className="mt-14 grid gap-10 md:grid-cols-2 md:gap-16">
            <Reveal>
              <SectionLabel>AI that answers</SectionLabel>
              <ul className="mt-5 space-y-4">
                {[
                  "Produces text. There is no state change to verify against anything.",
                  "Policy is whatever the prompt happened to produce on this run.",
                  "Nothing records which rule applied, so a decision cannot be explained later.",
                  "Fails silently: a confident wrong answer is indistinguishable from a correct one.",
                ].map((item) => (
                  <li key={item} className="flex gap-3 text-body leading-[1.65] text-muted-foreground">
                    <span
                      aria-hidden="true"
                      className="mt-[0.6rem] h-1 w-1 flex-shrink-0 rounded-full bg-muted-foreground/40"
                    />
                    {item}
                  </li>
                ))}
              </ul>
            </Reveal>

            <Reveal delay={80}>
              <SectionLabel>AI that resolves</SectionLabel>
              <ul className="mt-5 space-y-4">
                {[
                  "Every outcome comes from an ordered rule set evaluated outside the model.",
                  "The engine returns exactly one of three states: ALLOW, DENY or REQUIRES_APPROVAL.",
                  "Actions run through deterministic tools and are confirmed against the system of record.",
                  "Each stage is written to an audit log and a queryable workflow trace.",
                ].map((item) => (
                  <li key={item} className="flex gap-3 text-body leading-[1.65] text-foreground">
                    <span
                      aria-hidden="true"
                      className="mt-[0.6rem] h-1 w-1 flex-shrink-0 rounded-full bg-status-complete"
                    />
                    {item}
                  </li>
                ))}
              </ul>
            </Reveal>
          </div>

          {/* Real rule ladder */}
          <Reveal delay={60}>
            <div className="mt-16 border border-border-default bg-surface-card">
              <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-border-default px-5 py-4">
                <p className="text-mono text-foreground">
                  app/policies/engine.py
                </p>
                <p className="text-body-sm text-muted-foreground">
                  Rules sorted by priority, descending. First match decides.
                </p>
              </div>
              <ul className="divide-y divide-[var(--border-default)]">
                {DECISION_LADDER.map((entry) => (
                  <li
                    key={entry.rule}
                    className="flex flex-col gap-2 px-5 py-3.5 transition-colors duration-200 hover:bg-surface-base motion-reduce:transition-none sm:flex-row sm:items-center sm:gap-6"
                  >
                    <code className="w-full shrink-0 text-mono text-foreground sm:w-[19rem]">
                      {entry.rule}
                    </code>
                    <span className="flex-1 text-body-sm text-muted-foreground">
                      {entry.condition}
                    </span>
                    <DecisionBadge decision={entry.decision} size="sm" />
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
        </div>
      </section>

      <div className="mx-auto max-w-6xl px-4 md:px-0">
        <Divider />
      </div>

      {/* ======================== How it works ======================== */}
      <section aria-labelledby="pipeline-heading" className="py-20 md:py-28">
        <div className="mx-auto max-w-6xl px-4 md:px-0">
          <SectionIntro
            id="pipeline-heading"
            label="How it works"
            title="Nine stages, in a fixed order."
            lede="This is the same stage list the Resolution Console renders while a resolution is running, read from the same source. Nothing is skipped silently: if a stage does not run, it is recorded as skipped."
          />

          <Reveal className="mt-14">
            <ResolutionPipeline />
          </Reveal>

          <Reveal delay={60}>
            <p className="mt-10 max-w-3xl text-body leading-[1.7] text-muted-foreground">
              The model is used where judgement is genuinely required: reading the
              request, deciding which tool to call, and summarising the result. It
              is not used to decide whether money moves. That question is answered
              by the rule engine, and the answer is written down.
            </p>
          </Reveal>
        </div>
      </section>

      <div className="mx-auto max-w-6xl px-4 md:px-0">
        <Divider />
      </div>

      {/* ====================== Tech honesty ========================== */}
      <section aria-labelledby="stack-heading" className="py-20 md:py-28">
        <div className="mx-auto max-w-6xl px-4 md:px-0">
          <SectionIntro
            id="stack-heading"
            label="Under the hood"
            title="The stack, and why it is this size."
            lede="No orchestration framework, no message broker, no container platform. The whole system is a FastAPI process and a Next.js app, which keeps the resolution path short enough to reason about."
          />

          <div className="mt-14 grid gap-x-16 gap-y-10 md:grid-cols-2">
            <Reveal>
              <SectionLabel>Stack</SectionLabel>
              <dl className="mt-5 divide-y divide-[var(--border-default)] border-t border-[var(--border-default)]">
                {STACK.map((item) => (
                  <div
                    key={item.layer}
                    className="flex flex-col gap-1 py-4 transition-colors duration-200 hover:bg-surface-base motion-reduce:transition-none sm:flex-row sm:gap-8"
                  >
                    <dt className="w-32 flex-shrink-0 text-mono text-foreground">
                      {item.layer}
                    </dt>
                    <dd className="text-body-sm leading-[1.6] text-muted-foreground">
                      {item.detail}
                    </dd>
                  </div>
                ))}
              </dl>
            </Reveal>

            <Reveal delay={80}>
              <SectionLabel>Engineering decisions</SectionLabel>
              <ul className="mt-5 space-y-4">
                {ENGINEERING_NOTES.map((item) => (
                  <li key={item} className="flex gap-3 text-body-sm leading-[1.65] text-muted-foreground">
                    <span
                      aria-hidden="true"
                      className="mt-[0.55rem] h-1 w-1 flex-shrink-0 rounded-full bg-status-evidence/60"
                    />
                    {item}
                  </li>
                ))}
              </ul>
            </Reveal>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-6xl px-4 md:px-0">
        <Divider />
      </div>

      {/* ====================== See it in action ===================== */}
      <section aria-labelledby="routes-heading" className="py-20 md:py-28">
        <div className="mx-auto max-w-6xl px-4 md:px-0">
          <SectionIntro
            id="routes-heading"
            label="See it in action"
            title="Four surfaces, one system."
            lede="The demo runs against a live backend. The orders and policy documents are synthetic, but the workflow, the policy engine and the audit trail are the real thing."
          />

          <ul className="mt-14 grid gap-px overflow-hidden border border-border-default bg-[var(--border-default)] sm:grid-cols-2">
            {ROUTES.map((route, i) => (
              <li key={route.href} className="bg-background">
                <Reveal delay={i * 70} as="div" className="h-full">
                  <Link
                    href={route.href}
                    className="group flex h-full flex-col justify-between gap-6 p-6 transition-colors duration-200 hover:bg-surface-card focus-visible:bg-surface-card motion-reduce:transition-none md:p-8"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-4">
                        <h3 className="text-h2 font-semibold text-foreground">
                          {route.name}
                        </h3>
                        <ArrowUpRight
                          aria-hidden="true"
                          className="h-4 w-4 flex-shrink-0 text-muted-foreground transition-transform duration-200 group-hover:-translate-y-0.5 group-hover:translate-x-0.5 motion-reduce:transform-none motion-reduce:transition-none"
                        />
                      </div>
                      <p className="mt-3 text-body-sm leading-[1.65] text-muted-foreground">
                        {route.description}
                      </p>
                    </div>
                    <code className="text-mono text-muted-foreground">
                      {route.href}
                    </code>
                  </Link>
                </Reveal>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* ========================== Closing =========================== */}
      <section aria-labelledby="close-heading" className="py-20 md:py-28">
        <div className="mx-auto max-w-6xl px-4 md:px-0">
          <Reveal>
            <h2
              id="close-heading"
              className="max-w-3xl text-[1.75rem] font-semibold leading-[1.15] tracking-[-0.02em] text-foreground md:text-[2.125rem]"
            >
              Put a real request in front of it.
            </h2>
            <p className="mt-4 max-w-2xl text-h2 font-normal leading-[1.6] text-muted-foreground">
              Pick an order in the Console and follow it through evidence, policy,
              approval, execution and verification. Every stage is inspectable
              afterwards.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
                <Link
                  href="/console"
                  className={cn(
                    buttonVariants({ variant: "outline", size: "lg" }),
                    "group inline-flex items-center justify-center gap-2 border-transparent bg-foreground px-5 py-2.5 text-body-sm font-medium text-background hover:bg-foreground/90 hover:text-background"
                  )}
                >
                  Open the Resolution Console
                  <ArrowRight
                    aria-hidden="true"
                    className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5 motion-reduce:transform-none motion-reduce:transition-none"
                  />
                </Link>
              <Link
                href="/dashboard"
                className={cn(
                  buttonVariants({ variant: "outline", size: "lg" }),
                  "inline-flex items-center justify-center px-5 py-2.5 text-body-sm font-medium"
                )}
              >
                View operations dashboard
              </Link>
            </div>
          </Reveal>
        </div>
      </section>

      {/* =========================== Footer =========================== */}
      <footer role="contentinfo" className="border-t border-border-default">
        <div className="mx-auto max-w-6xl px-4 py-12 md:px-0">
          <div className="flex flex-col gap-10 md:flex-row md:justify-between">
            <div className="max-w-sm">
              <p className="text-body-sm font-semibold text-foreground">
                ResolveAI
              </p>
              <p className="mt-2 text-body-sm leading-[1.65] text-muted-foreground">
                A controlled AI resolution engine. All demo data is synthetic; the
                workflow, policy engine and audit trail are real.
              </p>
            </div>

            <nav aria-label="Footer" className="flex flex-col gap-8 sm:flex-row sm:gap-16">
              <div>
                <SectionLabel>Product</SectionLabel>
                <ul className="mt-4 space-y-2.5">
                  {ROUTES.map((route) => (
                    <li key={route.href}>
                      <Link
                        href={route.href}
                        className="text-body-sm text-muted-foreground transition-colors duration-200 hover:text-foreground focus-visible:text-foreground motion-reduce:transition-none"
                      >
                        {route.name}
                      </Link>
                    </li>
                  ))}
                  <li>
                    <Link
                      href="/dashboard"
                      className="text-body-sm text-muted-foreground transition-colors duration-200 hover:text-foreground focus-visible:text-foreground motion-reduce:transition-none"
                    >
                      Dashboard
                    </Link>
                  </li>
                </ul>
              </div>

              <div>
                <SectionLabel>Elsewhere</SectionLabel>
                <ul className="mt-4 space-y-2.5">
                  {[
                    { key: "github", label: "GitHub" },
                    { key: "linkedin", label: "LinkedIn" },
                  ].map(({ key, label }) =>
                    EXTERNAL_LINKS[key] ? (
                      <li key={key}>
                        <a
                          href={EXTERNAL_LINKS[key]}
                          target="_blank"
                          rel="noreferrer noopener"
                          className="inline-flex items-center gap-1.5 text-body-sm text-muted-foreground transition-colors duration-200 hover:text-foreground focus-visible:text-foreground motion-reduce:transition-none"
                        >
                          {label}
                          <ArrowUpRight aria-hidden="true" className="h-3 w-3" />
                        </a>
                      </li>
                    ) : null
                  )}
                </ul>
              </div>
            </nav>
          </div>

          <Divider />

          <div className="flex flex-col gap-2 pt-6 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-label text-muted-foreground">
              Evidence, policy, controlled action, verification, audit
            </p>
            <p className="text-label text-muted-foreground">
              Made by{" "}
              <span className="font-medium text-foreground">
                Muhammad Hassaan
              </span>
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
