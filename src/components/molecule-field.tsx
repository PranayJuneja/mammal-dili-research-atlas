export function MoleculeField() {
  return (
    <div className="molecule-field" aria-hidden="true">
      <svg viewBox="0 0 640 540" role="presentation">
        <defs>
          <linearGradient id="bond" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#76d5c5" />
            <stop offset="1" stopColor="#f0aa3c" />
          </linearGradient>
          <filter id="soft-glow">
            <feGaussianBlur stdDeviation="13" />
          </filter>
        </defs>
        <path className="molecule-glow" d="M142 172 277 91l144 78 3 159-140 82-142-80Z" />
        <g className="bonds" fill="none" stroke="url(#bond)" strokeWidth="3">
          <path d="M142 172 277 91l144 78 3 159-140 82-142-80Z" />
          <path d="m277 91 7 319M142 172l282 156M421 169 142 330" opacity=".34" />
          <path d="m421 169 89-52m-86 211 106 61M142 330l-92 65m92-223-70-61" />
        </g>
        <g className="atoms">
          <circle cx="277" cy="91" r="15" />
          <circle cx="421" cy="169" r="18" className="atom-accent" />
          <circle cx="424" cy="328" r="14" />
          <circle cx="284" cy="410" r="20" className="atom-warm" />
          <circle cx="142" cy="330" r="15" />
          <circle cx="142" cy="172" r="13" />
          <circle cx="510" cy="117" r="10" className="atom-warm" />
          <circle cx="530" cy="389" r="11" />
          <circle cx="50" cy="395" r="9" className="atom-accent" />
          <circle cx="72" cy="111" r="10" />
        </g>
        <g className="orbit" fill="none">
          <ellipse cx="286" cy="253" rx="238" ry="113" transform="rotate(-18 286 253)" />
          <ellipse cx="286" cy="253" rx="238" ry="113" transform="rotate(42 286 253)" />
        </g>
      </svg>
      <div className="vector-readout">
        <span>frozen vector</span>
        <b>[−0.08, 0.14, …]</b>
      </div>
    </div>
  );
}

