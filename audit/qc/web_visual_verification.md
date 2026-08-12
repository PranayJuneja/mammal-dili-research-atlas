# Web visual and interaction verification

Date: 2026-08-13

State under test: outcome execution pending; no result artifact loaded

Route: `/`

## Viewports and structure

| Check | Desktop 1440 px | Mobile 407 px |
| --- | --- | --- |
| Page-level horizontal overflow | Pass | Pass |
| One visible H1 and one `main` landmark | Pass | Pass |
| Internal hash links resolve | Pass | Pass |
| Empty accessible buttons | None | None |
| Pending-governance wording visible | Pass | Pass |
| Results dashboard hidden before `status: complete` | Pass | Pass |

The mobile research-phase rail is intentionally horizontally scrollable. No other
content crossed the viewport boundary. The primary benchmark labels remained inside
their card at the narrow viewport.

## Interaction checks

- The mobile menu opened, changed `aria-expanded` to `true`, and exposed the site navigation.
- Selecting research phase 2 changed the detailed phase heading and evidence panel.
- Selecting the inconclusive-outcome tab changed the scenario heading and interval illustration.
- Searching the glossary for `scaffold` reduced the list to the Scaffold entry.
- Keyboard Tab navigation focused the skip link first with a visible solid outline.
- Reduced-motion CSS disables smooth scrolling and collapses animation and transition durations.

## Scientific-state check

The page does not expose or imply model performance before the accepted pipeline has
created the hash-bound result packet. It states that technical design validation has
passed and that PA-01/PA-02 human amendment sign-off remains pending. The conditional
results component requires `status: complete`, a primary result, and an update-transport
result before it renders.

## Verification method

The production build was checked separately. Interaction and geometry checks used a
local Next.js development server and Chrome DevTools Protocol with desktop and exact
mobile device metrics. The browser-verification skill advertised in the session was
not present at its configured filesystem path, so this documented CDP fallback was
used.
