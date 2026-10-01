"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

function GitHubIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
      className={className}
    >
      <path d="M12 .5C5.73.5.5 5.73.5 12a11.5 11.5 0 0 0 7.86 10.92c.58.1.79-.25.79-.56v-2.1c-3.2.7-3.88-1.37-3.88-1.37-.53-1.34-1.29-1.7-1.29-1.7-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.56-.29-5.25-1.28-5.25-5.7 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11 11 0 0 1 5.79 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.12 3.05.74.81 1.18 1.84 1.18 3.1 0 4.43-2.69 5.4-5.26 5.69.41.36.78 1.06.78 2.14v3.18c0 .31.21.67.8.56A11.5 11.5 0 0 0 23.5 12C23.5 5.73 18.27.5 12 .5Z" />
    </svg>
  );
}

function LinkedInIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
      className={className}
    >
      <path d="M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.86 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.47-.9 1.63-1.85 3.36-1.85 3.6 0 4.27 2.37 4.27 5.45v6.29ZM5.34 7.43a2.07 2.07 0 1 1 0-4.13 2.07 2.07 0 0 1 0 4.13ZM7.12 20.45H3.56V9h3.56v11.45Z" />
    </svg>
  );
}

export function Footer() {
  const pathname = usePathname();

  // The landing page ships its own richer footer (product links, links column),
  // which already carries the same links and attribution. Rendering the shared
  // bar underneath it would stack two footers on the same route.
  if (pathname === "/") return null;

  return (
    <footer className="border-t bg-background px-4 py-5 md:px-6 lg:px-8">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 sm:flex-row">
        <div className="flex items-center gap-2">
          <a
            href="https://github.com/HassaanDeveloper/ResolveAI"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="ResolveAI on GitHub"
            title="GitHub"
            className="flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            <GitHubIcon className="h-4 w-4" />
          </a>
          <a
            href="https://www.linkedin.com/in/muhammad-hassaan-a22693269"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Muhammad Hassaan on LinkedIn"
            title="LinkedIn"
            className="flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            <LinkedInIcon className="h-4 w-4" />
          </a>
        </div>
        <p className="text-label text-muted-foreground">
          Made by{" "}
          <Link
            href="/"
            className="font-medium text-foreground transition-colors hover:text-primary"
          >
            Muhammad Hassaan
          </Link>
        </p>
      </div>
    </footer>
  );
}