"use client";

import { MagnifyingGlass } from "@phosphor-icons/react";
import { useMemo, useState } from "react";

import { glossary } from "@/data/research";

export function GlossarySearch() {
  const [query, setQuery] = useState("");
  const results = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return needle
      ? glossary.filter(([term, definition]) => `${term} ${definition}`.toLowerCase().includes(needle))
      : glossary;
  }, [query]);

  return (
    <div className="glossary-tool">
      <label className="search-box">
        <MagnifyingGlass aria-hidden="true" />
        <span className="sr-only">Search the glossary</span>
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search a term or idea…" />
      </label>
      <div className="glossary-grid" aria-live="polite">
        {results.map(([term, definition]) => (
          <article key={term}>
            <h3>{term}</h3>
            <p>{definition}</p>
          </article>
        ))}
        {results.length === 0 && <p className="empty-state">No matching term. Try “scaffold,” “calibration,” or “frozen.”</p>}
      </div>
    </div>
  );
}

