# ADR 010 — Wide-card scenic side rails replace the top band

Builds on ADR 005 (illustrated scenic band) and ADR 006 (photo-derived band).
This ADR changes only the **wide desktop** presentation; phones and narrow
reviewer panes keep ADR 005/006 exactly as shipped.

## Context

The top scenic band is the back card's first visual block on every card. It
paints 44–58px but its net flow cost is real vertical space, while the same
card sits on a full-window backdrop. On a widescreen desktop reviewer that
vertical strip is the most expensive decoration in the card and reads as a
second, smaller landscape pasted above the content.

Phones are a different constraint: AnkiDroid gives the card only 6px of side
padding at 412px wide, so there is no gutter for a side treatment; the compact
top band is the correct mobile answer. The treatment is therefore
desktop-only.

Two further constraints shaped the implementation:

1. ADR 006 required exactly one `{{Picture}}` reference. A naive two-rail
   design would reference the field twice, which this ADR accepts **only**
   because both crops stay inside the single lightbox trigger — one focus
   stop, one lightbox target.
2. Anki's reviewer pane width is not the monitor width. A 27-inch display can
   host a 700px reviewer pane, so the gate must be the card's container
   width, not a viewport media query.

## Decision

- **Gate:** `@container anki-card (min-width: 1000px)`. The query container is
  the existing `.card-wrapper` (`container-type: inline-size`). Below 1000px
  the §17 top band is untouched; this includes narrow desktop panes.
- **Geometry:** on wide cards `.scenic-band` becomes `position: absolute;
  inset: 0; height: auto; margin: 0; z-index: 0`. It leaves the flow
  entirely, and `.card-container` sets `padding-top: 0`, so the content
  begins at the card's inner top edge.
- **Rails:** one inline `<clipPath id="scenic-side-clip">` per band branch,
  with rects `0 → 0.06` and `0.94 → 1` (`objectBoundingBox`). The 6% token is
  `--scenic-rail-w`; at a 1360px card that is ~82px per side. `::before` /
  `::after` gradients fade each rail's inner edge into the card surface.
- **Picture treatment:** on wide cards the photo is mounted into two
  independent rail elements (`.rail-photo-left`, `.rail-photo-right`),
  sampling horizontal positions 25% and 75% with `object-fit: cover`. All
  color-altering overlays (`.tint`, `.wash`, `.grain`, `.fade`) are disabled
  on the rails and `filter: blur(16px)` is applied to the image directly, so
  the photo keeps its authentic scene colors with no tint or sky bleed.
  Fallback cards without a photo render the illustrated scene with
  `background: var(--scenic-sky)` in the rails. Both rails sit inside the
  single `.scenic-photo` lightbox trigger.
- **Content layer:** everything after the band is wrapped in `.card-content`
  (`position: relative; z-index: 1`) so content paints above the absolute
  band; the card's horizontal padding is widened by `--scenic-rail-w` so no
  text renders on top of the rails.
- **No JS, no new fields, no new assets.** `openLightbox` is untouched.
- **Deviation from the Japanese original:** the dark back card keeps its
  **warm** accent (`--accent-color`). The Japanese ADR 008 switched the dark
  theme to a cool blue/purple accent to match the rails; the Chinese palette
  (Ink Night / Rice Paper) keeps the warm accent for consistency. Frequency
  stars keep their semantic tier colours in both repos.

## Consequences

- Wide desktop cards reclaim the band's flow cost and the container's top
  padding; content starts at the card's inner top edge with padded clearance
  from the rails.
- The blurred picture (or the pagoda fallback) remains visible on wide
  cards, now as two quiet full-height rails with authentic colors.
- Mobile and narrow reviewer panes keep the ADR 005/006 top band, photo
  pipeline, and full-width lightbox target.
- `tests/test_yukei.py` gains wide-card contracts (absolute zero-flow band,
  two-rect clip, `.card-content` wrapper, disabled overlays, blur-only rail
  images at 25%/75%, reclaimed top padding, 6% falloff gradients, inset focus
  ring) and keeps the existing top-band browser probes.
- The single-`Picture` rule from ADR 006 is amended: two references are
  allowed **only** inside one trigger. `QUALITY.md` and the tests state this.
- The breakpoint is a judgement call: 1000px is wide enough for two rails
  plus a readable centre column, and low enough for common maximized desktop
  reviewer panes.
