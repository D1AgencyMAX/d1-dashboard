"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/numbers", label: "Numbers" },
  { href: "/characters", label: "Characters" },
  { href: "/conversations", label: "Conversations" },
  { href: "/releases", label: "Releases" },
];

export function ComedianNav() {
  const pathname = usePathname();
  return (
    <nav className="sticky top-0 z-40 border-b border-white/10 bg-slate-950/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-2 px-4 py-3 sm:px-6 lg:px-8">
        <Link href="/" className="mr-3 text-sm font-semibold uppercase tracking-[0.28em] text-cyan-300/80">
          D1 · Comedian
        </Link>
        {links.map((l) => {
          const active = l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
          return (
            <Link
              key={l.href}
              href={l.href}
              className={`rounded-full px-3 py-1.5 text-sm transition ${
                active
                  ? "bg-cyan-500/15 text-cyan-200 ring-1 ring-cyan-400/40"
                  : "text-slate-300 hover:bg-white/5 hover:text-white"
              }`}
            >
              {l.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
