"use client";

import { List, X } from "@phosphor-icons/react";
import { useEffect, useState } from "react";

const links = [
  ["Question", "#question"],
  ["Design", "#design"],
  ["Phases", "#phases"],
  ["Outcomes", "#outcomes"],
  ["Evidence", "#evidence"],
];

export function SiteHeader() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const close = () => setOpen(false);
    window.addEventListener("hashchange", close);
    return () => window.removeEventListener("hashchange", close);
  }, []);

  return (
    <header className="site-header">
      <a className="brand" href="#top" aria-label="MAMMAL DILI research atlas home">
        <span className="brand-mark" aria-hidden="true">
          M×D
        </span>
        <span>
          <strong>MAMMAL × DILI</strong>
          <small>research atlas</small>
        </span>
      </a>
      <button
        className="menu-button"
        type="button"
        aria-expanded={open}
        aria-controls="site-navigation"
        aria-label={open ? "Close navigation" : "Open navigation"}
        onClick={() => setOpen((value) => !value)}
      >
        {open ? <X size={22} /> : <List size={22} />}
      </button>
      <nav id="site-navigation" className={open ? "site-nav is-open" : "site-nav"} aria-label="Primary navigation">
        {links.map(([label, href]) => (
          <a key={href} href={href} onClick={() => setOpen(false)}>
            {label}
          </a>
        ))}
        <a className="nav-cta" href="#status" onClick={() => setOpen(false)}>
          Study status
        </a>
      </nav>
    </header>
  );
}

