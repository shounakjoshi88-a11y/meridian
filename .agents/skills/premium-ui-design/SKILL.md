---
name: premium-ui-design
description: Use when designing or restyling any UI (mobile app, web app, dashboard, landing page, component library) and the result must look premium, intentional and hand-designed rather than like generic AI output. Covers what separates premium from AI-slop, plus color, typography, spacing, layout, elevation, iconography, motion, copywriting, states, component patterns, empty-state animations, and a build-and-critique process. Framework-agnostic.
license: MIT
metadata:
  version: "1.0"
---

# Premium UI design

This skill teaches you to produce interfaces that look designed by a person with taste, not assembled from defaults. It is framework-agnostic: the principles apply to HTML/CSS, Tailwind, React, React Native, Flutter, SwiftUI, Jetpack Compose, or anything else.

## The core idea

Premium is not more decoration. Premium is:

1. Fewer things, each with a reason.
2. A clear hierarchy, so the eye knows where to go in under a second.
3. Consistency from a small system (few colors, few sizes, few radii, one spacing scale).
4. Craft in the details nobody names but everybody feels: alignment, spacing rhythm, contrast, state handling, copy.
5. Choices made for this specific product and audience, not the defaults you would produce for any product.

AI slop is the opposite: many things, all the same weight, from a template, with decoration standing in for decisions.

When in doubt, remove. Before finishing, take one accessory off (Chanel's rule).

---

## Part 1: What makes UI look like AI slop

Recognize these so you can avoid them. Each one is a default, not a decision.

### Structure and layout tells

- Everything is a card. Content chopped into identical rounded rectangles with a border or shadow, each with the same padding. Cards are a tool for grouping, not a default container. If items are a list, make it a list (rows separated by space or a hairline).
- One border radius on everything (say 16px on cards, buttons, inputs, chips, images alike). Real systems vary radius by element size and role.
- Uniform weight. Every element the same size and contrast, so there is no focal point. Slop has no hierarchy; it has a grid of equal siblings.
- Icon tiles: a small colored rounded square with an icon inside, in front of every row or feature. It is the single most common tell.
- Pills and chips everywhere: tags, filters, badges and status all rendered as colored capsules.
- Hero pattern by rote: big headline, one word in an accent color or italic, subtitle, two buttons, three feature cards below.
- Three-up feature grids with icon, bold title, two-line description, repeated.
- The dashboard kit: four stat cards on top (big number, tiny label, green up-arrow percent), a line chart, a table.
- Center-aligning everything. Long text, lists and forms are almost always better left-aligned.
- Stat blocks with a big number, a small label and a gradient accent, used because they look "data-y", not because a number is the point.

### Color tells

- Purple-to-blue or indigo-to-violet gradients. Gradient washes as decoration, gradient text, gradient buttons.
- The "AI dark mode": near-black background, one neon accent (electric purple, acid green, cyan), glowing borders.
- The "AI warm mode": cream background (#F4F1EA-ish) with a terracotta/clay accent and a high-contrast serif. Just as much a default as neon-on-black.
- Pure black (#000) with pure white (#fff) text, which is harsh and vibrates. Or, the reverse lazy fix: generic #111 / #0B0B0B chosen without thinking.
- Rainbow category colors: every tag, folder or chart series a different saturated hue.
- Tailwind default palette used raw (indigo-500, slate-800, emerald-400) with no adjustment.
- Semantic colors used decoratively: green, red, amber and blue appearing where nothing is succeeding, failing, warning or informational.
- Low-contrast gray text on gray backgrounds "for elegance". Fails accessibility and reads as unfinished.

### Typography tells

- System or Inter/Roboto at default weights everywhere, with no typographic decision.
- Bold (700) on everything to create hierarchy, instead of size, contrast and spacing.
- ALL-CAPS tracked-out eyebrow labels above every heading.
- Monospace font used for small labels or metadata just to feel technical.
- One word in a headline set in a different color or italic.
- Titles in Title Case Everywhere.
- Emoji used as icons or bullets.

### Chrome and decoration tells

- Soft grey drop shadows (rgba(0,0,0,.1)) under every card. Glassmorphism/blur on things that sit over nothing. Glows.
- Hairline borders on every element so the screen looks like a wireframe.
- Meta strings joined by middle dots (A · B · C) everywhere. "WORD — fragment" labels with a spaced em dash. Arrows (→) appended to every link.
- Numbered markers (01, 02, 03) on content that is not a sequence.
- Fade-and-slide-up on every section, hover lift on every card, pulsing dots, shimmer everywhere.
- Decorative blobs, grids, noise, sparkles.
- Stock, emoji or gradient placeholders for imagery.

### Content tells

- Placeholder copy such as "Lorem ipsum", "Feature title", "John Doe", "Acme Inc", "Seamlessly unlock your workflow".
- Marketing words in product UI: seamless, powerful, unlock, elevate, supercharge, effortless, delightful, next-generation.
- Vague or clever labels instead of plain ones.
- "Successfully", "Please", exclamation marks in system messages.
- Perfect round data (1,000 users, 50%, $10,000) and identical-length list items.

### State and craft tells

- Only the happy path is designed. No empty, loading, error, offline, long-text or one-item states.
- Destructive actions (delete) sitting permanently on every row as small red icons.
- Tap targets under 44pt / 48dp.
- Inconsistent spacing (13px here, 17px there), misaligned baselines, icons that do not optically center with text.
- Focus rings removed, contrast not checked, dark mode is just inverted colors.

None of these are forbidden. They are defaults. Use one only when the product genuinely calls for it, and then commit to it fully.

---

## Part 2: What makes UI feel premium

### 1. Hierarchy first

Decide the single most important thing on every screen and make it visibly dominant. Then a second tier, then everything else quiet.

- Use at most 3 levels of emphasis on a screen: primary (what to look at), secondary (what to read), tertiary (metadata).
- Build hierarchy from size, contrast and space, in that order. Use weight sparingly. Color last.
- Squint test: blur your eyes (or view a small screenshot). You should still see the structure and the focal point.
- One primary action per screen, visually unmistakable. Everything else is secondary or tertiary.
- Let one element be memorable and keep everything around it disciplined.

### 2. Restraint

- Fewer colors, fewer fonts, fewer sizes, fewer radii, fewer borders, fewer shadows.
- Prefer removing a container over styling it. Whitespace, alignment and type contrast should do the grouping before borders or fills do.
- A screen with 2 to 3 well-chosen contrasts beats one with 10 mediocre ones.
- Decoration must encode information. A border, divider, badge or number should mean something.

### 3. Space is the material

Generous, consistent, rhythmic spacing is the biggest single quality signal.

- Use one base unit (4px) with a scale: 4, 8, 12, 16, 24, 32, 48, 64, 96. Never invent values off the scale.
- Group by proximity: related items closer than unrelated ones. The gap between groups should be at least 2x the gap inside groups.
- Screen edge padding: 16 to 24px on mobile, consistent across all screens. Do not shrink it to fit more.
- Vertical rhythm: sections separated by 32 to 48px, not 16.
- If a layout feels cramped, add space before you shrink text. If it feels empty, check hierarchy before adding elements.
- Optical alignment beats mathematical alignment: icons, play buttons and rounded shapes often need a 1 to 2px nudge.

### 4. Typography carries the personality

- Use one family, or two that are clearly different in role (e.g. a serif for display plus a sans for UI, or a grotesk plus a mono for data). Never two similar sans-serifs.
- Choose typefaces deliberately for the product's character. Do not default to Inter/Roboto/system just because they are safe. If you use them, do it as a conscious neutral choice and put the personality somewhere else.
- Font pairing patterns that work: (a) one versatile sans with strong weight range, used well; (b) editorial serif display plus neutral sans body; (c) geometric or grotesque display plus humanist sans body. Check license and availability, and always give a fallback stack.
- Type scale: pick a ratio (1.2 for dense apps, 1.25 for balanced, 1.333 for expressive) and stick to it. Mobile app example: 12 / 14 / 16 / 20 / 24 / 32 / 40.
- Body text 15 to 17px on mobile. Never below 11 to 12px for anything, and only for true metadata.
- Line height: body 1.4 to 1.6 (serif slightly more), headings 1.1 to 1.25, tight display text 1.0 to 1.1.
- Letter spacing: large display text slightly negative (-0.01 to -0.03em). Small text neutral or slightly positive. Never track-out lowercase body text.
- Line length: 45 to 75 characters. On mobile this happens naturally; on wide screens cap it (max-width around 65ch).
- Use two weights in most interfaces (400 and 500/600). A third only with reason. Avoid 700+ for UI text unless the typeface is designed for it.
- Use tabular (monospaced) numerals for anything that aligns or changes: prices, timers, tables, stats (`font-variant-numeric: tabular-nums`).
- Hierarchy via size and color contrast, not by making everything bold.
- Sentence case for all UI text. All caps only for very short, tightly spaced labels and only when it earns its place.
- Align text to the left (or start). Center only short, single, standalone lines (a title on an empty state, a splash).
- Numbers and dates: format consistently and for locale (26 Sep, not 26/09/2026 raw, unless space or context needs it).

### 5. Color is a system, not a mood

Build the palette from roles, not from a list of favorite hues.

**Structure of a palette (aim for 5 to 7 named values total):**

- Background (canvas)
- Surface (one or two elevations above canvas)
- Text primary
- Text secondary (and muted for hints)
- Border/divider (very low contrast)
- Accent (one hue, used for the primary action and key state only)
- Semantic: success / warning / danger, used only for their meaning

**Rules:**

- 60 / 30 / 10: about 60% neutral canvas, 30% surfaces and text, 10% or less accent.
- One accent. A second accent only if it has a distinct job. Never assign a random color per item.
- Tint your neutrals toward the brand hue very slightly (2 to 6% saturation) so grays feel intentional, but keep them neutral enough to read as gray. This is what separates a crafted palette from raw slate/zinc.
- Avoid pure #000 and pure #FFF as large surfaces or text pairs. Use off-black and off-white (for example a dark of roughly L 8 to 12% and text of roughly L 92 to 96%).
- Do not default to the AI clusters: indigo/violet gradient, neon-on-black, cream-plus-terracotta. Pick an accent from the product's world (its materials, subject matter, audience). A tea app, a trading tool, a kids' app and a security tool should not share a palette.
- Prefer building the palette in a perceptual space (OKLCH/OKLab, or HSL as a fallback) so steps have even lightness. Generate a 9 to 11 step ramp for neutral and accent; use only a few steps.
- Contrast: body text at least 4.5:1, large text and UI components at least 3:1. Check secondary and muted text too, because that is where designs fail.
- Muted text still has to be readable. If it is under 4.5:1 on its background, darken it or make it larger.
- Use color to state meaning, not to decorate. If you remove the color, the hierarchy should still work.
- Status colors: tint backgrounds lightly (10 to 15% alpha) and use a strong hue for text/icons instead of solid saturated blocks.
- Gradients: avoid by default. If used, keep hues close (analogous), low contrast between stops, and subtle. Never on text, never as the main brand device unless the brand is built on it.

**Light mode vs dark mode:**

- Design both intentionally. Dark mode is not inverted light mode.
- Dark canvas: dark neutral (not pure black), surfaces get lighter as they rise. Elevation is shown by lightness, not shadow.
- Desaturate and slightly lighten accents in dark mode so they do not vibrate.
- Reduce text contrast a touch in dark mode (off-white, not white) to avoid halation.
- Borders in dark mode are white at 6 to 12% alpha; in light mode black at 6 to 10% alpha.
- Test images, charts, and semantic colors in both modes.

**Example neutral+accent structure (illustrative only, always choose your own):**

```
canvas        oklch(0.16 0.008 80)   /* dark warm neutral */
surface       oklch(0.20 0.008 80)
text          oklch(0.95 0.01 85)
text-2        oklch(0.72 0.01 85)
text-muted    oklch(0.55 0.01 85)
border        oklch(1 0 0 / 0.08)
accent        one hue from the product's world, chroma moderate, not neon
```

### 6. Surfaces, borders, radius and elevation

- Establish 2 to 3 elevation levels at most: canvas, surface, overlay (sheets, menus, dialogs).
- Separate with, in order of preference: space, then subtle tonal difference (a slightly lighter or darker surface), then a hairline divider, then a border, then a shadow.
- Cards are justified when an item is a discrete object the user acts on as a unit (a product, a document, a person). Lists of homogeneous rows are usually better as rows with dividers.
- Borders: 1px (or 0.5px on high-DPI) at very low contrast. Do not outline every element.
- Radius system by role, for example: small controls 8, inputs/buttons 10 to 12, cards 14 to 20, sheets 24 to 28, avatars full, pills only for true pills. Nested radius: inner radius = outer radius minus padding.
- Or commit to a different overall attitude on purpose (sharp 0 to 4px for editorial/technical, fully round for playful). Just stay consistent with the choice.
- Shadows: rarely. When used, layered, low opacity, colored slightly toward the background hue, larger blur with small offset. Never the same gray shadow on everything. Never on flat list items.
- Blur/glass only for elements that truly overlay content (nav bars over scrolling content, sheets), with sufficient tint for legibility.

### 7. Layout patterns

- Start from a grid. Mobile: 4 columns with 16 to 24px margins. Desktop: 12 columns, max content width 1100 to 1280px.
- Align to a small number of vertical lines. Everything on a screen should share edges. Ragged alignments read as amateur.
- Use asymmetry and scale contrast for interest instead of ornament: a large title and a small meta, a full-bleed image and a narrow text column.
- Left-align text blocks. Make one dominant column and let supporting content sit beside or below.
- Order content by user importance, not by data model.
- Lists: rows of 56 to 72px with a clear primary line, one secondary line, and trailing meta. Dividers inset from the leading edge, or spacing only.
- Progressive disclosure: show the most common 80% and tuck the rest behind a tap (detail screens, sheets, menus).
- Group with headings only when the group needs a name. Do not add section labels for the sake of structure.
- Pin the most-used action within thumb reach on mobile (bottom third). Avoid top-right reliance for primary actions on large phones.

### 8. Navigation and chrome

- Keep navigation quiet: labels or icons in a low-contrast color, with the active item clearly different in both color and one more cue (weight, indicator dot, underline). Do not rely on color alone.
- Bottom tab bars: 3 to 5 items, consistent icon style, 44pt+ targets, safe-area padding respected.
- Headers: a large title that collapses on scroll is more elegant than a fixed bar plus a subtitle plus an icon row.
- Filters/categories: text tabs with an underline or a segmented control often look more refined than a row of chips. Use chips when multi-select or removable.
- A single floating action button is acceptable when creation is the core action. Make it modest, one color, and make sure it never covers content (add bottom padding to the list).
- Avoid duplicated navigation (a tagline of section names under a title that also appears in the tab bar).
- Destructive actions live behind swipe, long-press, a menu or a detail screen, with confirm or undo. Do not show a delete icon on every row.

### 9. Iconography and imagery

- One icon set, one stroke width, one corner style, one size grid (20 or 24px). Never mix filled and outlined randomly.
- Icons support text; they do not replace it unless universally understood. Do not put an icon in front of every item.
- Do not wrap icons in colored tiles unless the tile is a real avatar/app icon.
- Optical size: stroke around 1.5px for 20 to 24px icons.
- Imagery: real, cropped with intention, consistent treatment (same aspect ratios, same tone). If no imagery exists, use type, color fields, or simple geometry instead of stock-style placeholders.
- Avatars and thumbnails: consistent shape, with a designed fallback (initials on a neutral tone).
- Illustrations: skip unless they are bespoke and consistent. Generic blobs and gradient orbs signal template.

### 10. Motion

- Motion answers user action and shows what changed: opening, expanding, reordering, confirming, navigating.
- Durations: 120 to 200ms for small feedback, 200 to 320ms for transitions, up to 400ms for large moves. Ease-out for entering, ease-in for exiting, ease-in-out for moves. Springs should be tight, with little overshoot.
- Animate transform and opacity only. Never animate layout properties on long lists.
- One orchestrated entrance at most (e.g. a staggered list on first load). Do not fade-slide-up every section. Do not add hover lifts to every card.
- Respect reduced motion (`prefers-reduced-motion`, platform accessibility setting).
- Provide tactile feedback where the platform supports it (pressed states, subtle haptics on mobile).
- Skeletons should match the final layout. Prefer a quiet fade to shimmering gradients.

### 11. Copy is design

- Every word must help someone understand or act. Cut the rest.
- Plain verbs, sentence case, no punctuation on labels and headings. Buttons are verb-first: Save changes, Create note, Delete folder.
- Name things by what users understand, not how the system works.
- Keep names consistent across the flow: the button says Publish, the toast says Published.
- Errors say what happened and how to fix it, in one sentence, no blame and no apology: "That name is already taken. Try another."
- Empty states are invitations: a headline naming the space, one line on what goes here, one action.
- Use realistic content in every mockup: real-sounding names, uneven lengths, plausible dates, imperfect numbers. Never lorem ipsum.
- Avoid: seamless, unlock, elevate, supercharge, leverage, effortless, "Please", "successfully", and exclamation marks in system copy.
- Do not add taglines under the app title that just list the tabs.

### 12. States and edge cases (this is where premium is won)

Design and implement each of these, not just the default view:

- Empty (first use, and empty after filter/search)
- Loading (skeleton or inline progress, no layout jump)
- Error (recoverable, with a retry)
- Offline / degraded
- One item, many items, very long titles (truncate or wrap deliberately), very short titles
- Pressed, focused (visible keyboard/D-pad focus ring), selected, disabled (with reason where possible), hover on pointer devices
- Destructive confirmation with undo
- Success feedback that is proportionate (a subtle toast or inline change, not a modal)
- Dark and light, large text (dynamic type up to 200%), small screens (320 to 360px wide)

### 13. Data-dense and utility apps

Study tools, dashboards and admin panels should still feel premium.

- Lead with the one number or item the user came for. Do not open with four equal stat cards.
- Reduce chrome: rows and dividers instead of boxes; align numbers right with tabular figures.
- Charts: minimal gridlines, direct labels instead of legends, one highlight color against neutral series, no 3D, no gradients under lines unless subtle.
- Density controls: comfortable by default, compact optional. Do not shrink text below 13px to fit data.
- Use progressive disclosure for detail, filters and settings.
- Emphasize what needs action (due soon, low attendance, unread) with a single restrained signal, not with badges on everything.

### 14. Components: quick premium recipes

- Buttons: three tiers only (primary filled, secondary tonal or outlined, tertiary text). One primary per view. Height 44 to 52px on mobile. Label 15 to 16px, weight 500. Avoid trailing arrows unless it means navigation.
- Inputs: 48 to 52px height, clear label (not placeholder-only), visible focus, inline validation text beneath, no heavy borders. Prefer filled-tonal or underline styles for a refined look.
- Lists: covered above. Swipe actions for secondary operations.
- Tabs/segmented controls: text with an indicator or a subtle sliding thumb; equal spacing; 44px height.
- Sheets and dialogs: bottom sheets on mobile with a grabber, large radius on top corners, clear primary action, dismiss by drag or tap outside.
- Toasts: short, above the nav, auto-dismiss, undo when relevant.
- Search: integrated at the top of the list, collapsing on scroll or behind an icon when secondary. Not a giant bordered field competing with content.
- Badges: only when they carry information a user must act on. Prefer plain colored text or a dot.
- Progress: thin bars or rings, one color, with a label users can read. Do not decorate every item with a progress bar.
- Avatars, tags, chips: small, quiet, consistent.

---

## Part 3: Process (follow this every time)

### Step 0. Ground it

Identify the product, the audience, and the primary job of the screen. If the brief is thin, propose a one-line answer to each and proceed (ask only if the answer changes the design substantially). Check the repo for existing tokens, fonts, components and brand assets, and extend them instead of replacing them, unless the user asked for a redesign.

Ask: what is in this product's world (materials, vocabulary, tools, culture) that can inform color, type and shape? Distinctive choices come from there.

### Step 1. Write a compact design plan before coding

Keep it under one screen:

- Attitude: 3 adjectives (for example: calm, precise, warm).
- Color: 5 to 7 named values with hex (or OKLCH), including the single accent and where it is used.
- Type: families, roles, the scale, and weights.
- Spacing and radius: base unit, scale, radius by role.
- Layout concept: one sentence plus a rough ASCII wireframe. State alignment rules.
- The one memorable element and what stays quiet around it.

### Step 2. Review the plan against the slop list

Ask honestly: would I produce this same palette, type and layout for any similar product? If yes, change the parts that are defaults. Say what you changed and why. Check specifically for: indigo/violet, neon-on-black, cream-plus-terracotta, identical cards, icon tiles, chip rows, ALL-CAPS eyebrows, mono labels, gradient accents.

### Step 3. Define tokens first, then build

Create the tokens as variables before any component. Components must use only tokens. Do not hardcode hex, px or ms in components.

```css
:root {
  /* color roles */
  --bg: ;          --surface: ;     --surface-raised: ;
  --text: ;        --text-2: ;      --text-muted: ;
  --border: ;      --accent: ;      --on-accent: ;
  --success: ;     --warning: ;     --danger: ;

  /* type */
  --font-display: ; --font-body: ;
  --fs-xs: 12px; --fs-sm: 14px; --fs-md: 16px; --fs-lg: 20px; --fs-xl: 28px; --fs-2xl: 40px;
  --lh-tight: 1.15; --lh-body: 1.5;

  /* space (4px base) */
  --s-1: 4px; --s-2: 8px; --s-3: 12px; --s-4: 16px; --s-5: 24px; --s-6: 32px; --s-7: 48px; --s-8: 64px;

  /* shape and motion */
  --r-sm: 8px; --r-md: 12px; --r-lg: 20px;
  --dur-fast: 140ms; --dur-base: 240ms;
  --ease-out: cubic-bezier(.2,.7,.2,1);
}
@media (prefers-color-scheme: dark) { :root { /* redefine color roles, do not invert */ } }
```

Map the same tokens to the target stack: Tailwind theme extension, React Native theme object, Flutter ThemeData/ThemeExtension, SwiftUI Color/Font extensions, Compose MaterialTheme with custom scheme. Never scatter raw values through the screens.

### Step 4. Build the focal point first, then the quiet surroundings

Build the most important element, get it right, then lay out everything else at lower emphasis. Use real content from the start.

### Step 5. Critique loop

If you can run the app or take screenshots, do it, at 360px wide and at desktop width, in light and dark. Then check:

1. Squint test: is there one clear focal point?
2. Can I remove any border, container, color, icon or label without losing meaning? Remove it.
3. Do spacing values all come from the scale? Are edges aligned?
4. Are there more than 2 to 3 emphasis levels, more than one accent, more than 2 weights?
5. Contrast: body 4.5:1, UI and large text 3:1, including muted text and disabled controls.
6. Tap targets 44pt/48dp minimum, with adequate spacing between them.
7. All states exist: empty, loading, error, long text, focus, pressed.
8. Copy: sentence case, verb-first buttons, no filler, no lorem.
9. Is anything on the slop list still in there by default, not by decision?
10. Would this still look right with different content lengths and text at 130% size?

Fix, then repeat once. Do not announce the checklist in the output; just deliver the result.

---

## Part 4: Accessibility and quality floor

These are non-negotiable and invisible when done well:

- Semantic structure (real buttons, headings, labels, lists). Screen-reader labels on icon-only controls.
- Visible focus for keyboard and switch users; logical focus order.
- Do not use color as the only carrier of state (add text, icon, weight or shape).
- Support dynamic type / browser zoom without truncating essential content.
- Respect reduced motion and, where relevant, reduced transparency.
- Safe areas (notch, home indicator, system bars) handled on mobile.
- Performance is part of premium: no jank on scroll, no layout shift, images sized, fonts loaded with fallbacks and `font-display: swap` (or equivalent).

---

## Part 5: Direction library (choose on purpose, do not copy)

These are starting attitudes, each with typical, non-default expressions. Pick or invent one per product, then commit fully.

- Quiet editorial: text-led, large type, hairline dividers, very few colors, generous margins. Risk: becomes the "AI serif" default; use a distinctive typeface pairing and a specific accent, and vary structure so it does not read as a template.
- Soft utility (Apple/Things-like): light surfaces, one clear accent, large titles, gentle radii, clear tap targets, minimal borders. Premium through polish and rhythm.
- Dense pro tool (Linear/Raycast-like): tight spacing on a strict grid, small but legible type, keyboard-first, muted neutral canvas, one precise accent, very fast motion.
- Tactile/material: real-feeling surfaces, subtle texture or depth used consistently, warm palette. Needs restraint to avoid kitsch.
- Bold graphic: large flat color fields, oversized type, strong grid, few elements. Works for consumer, culture and event products; needs strict spacing to avoid chaos.
- Technical/instrument: monospace or grotesk data type, thin lines, numeric emphasis, restrained color for state. Use mono only where data actually lives.
- Playful: rounded shapes, saturated color, expressive motion, but with a disciplined palette and consistent radius.

If the user gives their own brand, references or screenshots, they override everything here. Match their direction exactly and apply this skill's craft rules (hierarchy, spacing, contrast, states, copy) inside it.

---

## Part 6: Redesign playbook (when improving an existing screen)

1. List what the screen is for and what users do most.
2. Identify the focal item and demote everything else.
3. Delete: extra borders, containers, icons, labels, badges, taglines, shadows.
4. Replace repeated cards with rows or a single featured item plus a list.
5. Move destructive and rare actions out of the main view.
6. Re-space using the scale; increase edge padding and section gaps.
7. Rework type: pick the pairing, set the scale, fix line heights and weights.
8. Re-derive the palette from roles; reduce to one accent; fix contrast.
9. Add missing states; rewrite copy.
10. Re-run the critique loop.

---

## Part 7: Empty state animations

An empty state is the first thing a new user sees and the screen they return to when they finish everything. A good one teaches what the space is for, gives one clear action, and adds a moment of craft. Animation is optional; when used it must serve that job.

### When to animate, and when not to

- Animate when it clarifies what will live here (a page drawing itself, a list assembling) or gives calm feedback (a check drawing on inbox zero).
- Do not animate when the state is an error the user must act on, when the screen is seen many times a day (use a static or near-static version), or when it delays the call to action.
- The call to action must be visible and tappable immediately. Never gate it behind the animation.
- Decide the emotional tone first: first-use (inviting), finished (calm reward), no results (helpful, neutral), offline or error (clear, unpanicked). Motion character follows tone.

### Motion principles for empty states

- Small and slow. One subject, moving with restraint. Total entrance 600 to 1200ms; ambient loops with long periods (4 to 8s) and tiny amplitude.
- One-shot entrance, then near stillness. Endless bouncing or spinning becomes annoying on a screen people stare at.
- Sequence with a clear order: illustration, then headline, then supporting line, then action. Stagger 60 to 120ms. Fade plus a few pixels of movement, not large slides.
- Ease-out for entering, gentle springs with almost no overshoot. Avoid elastic or bouncy easing except in deliberately playful products.
- Animate transform and opacity (and SVG stroke-dashoffset). Never animate layout properties.
- The final frame is the design. The static end state must look complete and good on its own (it is also your reduced-motion version and your screenshot).
- Make the illustration part of the system: same stroke width, corner style and palette as the icons and UI. Use 1 to 2 palette colors plus neutrals.
- Keep it proportionate: illustration around 96 to 160px on mobile, not a full-screen hero, so text and action stay above the fold.

### Techniques that look premium (pick one per state)

1. Line draw: a simple outline (page, folder, search glass, envelope) draws itself with stroke-dashoffset, then a small detail appears. Clean, cheap, scalable, no dependencies.
2. Assemble: three or four simple shapes (list rows, cards) fade and settle into place with a stagger. Communicates "things will appear here".
3. Idle breathing: after the entrance, the main object drifts 2 to 4px or scales 1.00 to 1.02 over 5 to 7s. Barely noticeable.
4. Scan / sweep: a soft highlight or thin line passes across skeleton rows once, then they resolve into the empty message. Good for no-results and search.
5. Morph: one icon morphs into another to show a state change (loading to check, cloud to slashed cloud for offline). Use SVG path morphing with matching point counts, or Rive/Lottie.
6. Reactive: the illustration responds to touch or pointer (tap makes it nod, drag tilts it) or to device tilt with a very small parallax. Use sparingly and never required.
7. Typographic: no illustration, just large type whose words or a single glyph animate in (a cursor blink, a line writing itself). Suits editorial and technical products and is the least "AI stock illustration" option.
8. Progress-linked: the empty state shows real state (7 of 7 tasks done, streak count) and the number counts up once with tabular figures. Meaningful rather than decorative.

### Ideas by context (adapt to the product's world, do not copy literally)

- No items yet (notes, tasks, files): the object outline draws in, a blinking caret or a dashed placeholder row appears where the first item will go, and the action pulses once.
- Nothing left (all done): a single check or mark draws in, the headline fades in. No confetti unless the product is playful and the moment is rare.
- No search results: a magnifier drifts slowly over faint rows and settles; text suggests a broader query or shows recent searches.
- Filtered to zero: the applied filter chip gently nudges and offers "Clear filter".
- Offline: signal bars fill down to one and hold; a quiet "Retry" action. No sad faces.
- Permission needed (camera, notifications): the relevant device element (viewfinder corners, bell) animates gently, followed by a single explanation and one button.
- First launch / onboarding-like: a small assembly of the product's own UI pieces, drawn with the real tokens, rather than a generic stock illustration.

### Implementation options

- CSS or SVG (default choice): zero dependencies, tiny, crisp at any density, easy to theme with CSS variables. Use for line draw, fades, staggers and breathing.
- Lottie / dotLottie: good when a designer delivers After Effects work. Keep files under about 50 KB, avoid raster layers and heavy effects, recolor with theme tokens, and render a static fallback.
- Rive: best for interactive or state-machine animations (reacts to input, loops, transitions between states) at small size with good runtime performance.
- Canvas / WebGL / Skia: only for special hero moments. Check battery and frame-rate cost.
- Native frameworks: Reanimated (React Native), Flutter implicit and explicit animations, SwiftUI `withAnimation` and `PhaseAnimator`, Compose `animate*AsState`. Prefer these for simple fades, staggers and springs instead of adding a runtime.
- Never ship GIFs or video for empty states: heavy, unthemeable, no dark mode, no reduced motion.
- Lazy-load and pause when off-screen or when the app is backgrounded.

### Example: line-draw plus staggered reveal (CSS/SVG)

```html
<div class="empty" role="status">
  <svg class="empty-art" viewBox="0 0 96 96" width="112" height="112" aria-hidden="true" fill="none"
       stroke="var(--text-2)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <path class="draw" pathLength="1" d="M28 16h30l14 14v50H28z" />
    <path class="draw d2" pathLength="1" d="M58 16v14h14" />
    <path class="draw d3" pathLength="1" d="M38 48h24M38 60h16" stroke="var(--accent)" />
  </svg>
  <h2 class="empty-title">Start your first note</h2>
  <p class="empty-body">Notes you write or import will show up here.</p>
  <button class="empty-cta">Create note</button>
</div>
```

```css
.draw { stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw 700ms var(--ease-out) forwards; }
.d2 { animation-delay: 180ms; }
.d3 { animation-delay: 360ms; }
@keyframes draw { to { stroke-dashoffset: 0; } }

.empty-title, .empty-body, .empty-cta {
  opacity: 0; transform: translateY(6px);
  animation: rise 420ms var(--ease-out) forwards;
}
.empty-title { animation-delay: 500ms; }
.empty-body  { animation-delay: 580ms; }
.empty-cta   { animation-delay: 660ms; }
@keyframes rise { to { opacity: 1; transform: none; } }

.empty-art { animation: breathe 6s ease-in-out 1.6s infinite; }
@keyframes breathe { 50% { transform: translateY(-3px); } }

@media (prefers-reduced-motion: reduce) {
  .draw, .empty-title, .empty-body, .empty-cta, .empty-art {
    animation: none; opacity: 1; transform: none; stroke-dashoffset: 0;
  }
}
```

Note that `pathLength="1"` normalizes every path so one dash value works for all shapes.

### Craft rules for the artwork

- Draw with the product's icon style: same stroke width, caps and joins. One accent detail, everything else neutral.
- Start from geometric primitives on a grid (rectangles, circles, lines). Avoid gradient blobs, sparkles and generic characters.
- Avoid mascots and faces unless the brand already has them. Never use sad faces for errors or empty results.
- Test on light and dark; colors come from tokens, never hardcoded.
- Provide an equivalent static version (same composition) for reduced motion, screenshots, and slow devices.

### Copy for empty states

- Headline names the space or the outcome ("Start your first note", "You're all caught up", "No matches"). No terminal punctuation. No "Oops".
- One supporting line explaining what goes here or what to try. Ends with a period.
- One verb-first action ("Create note", "Clear filters", "Retry"). A secondary text link only if truly needed ("Import files").
- Do not blame the user, apologize, or joke during errors.

### Accessibility and performance

- Respect `prefers-reduced-motion` and the platform's reduce-motion setting: show the final frame with no movement (opacity fades of 100 to 150ms are acceptable).
- Mark decorative art `aria-hidden="true"`; put the message in real text. Use `role="status"` (or `aria-live="polite"`) when the empty state appears after a user action such as a search.
- No flashing above 3 times per second. Provide a pause option for any loop longer than 5 seconds if the animation is continuous.
- Keep the animation off the main thread: transforms and opacity, hardware-accelerated properties; avoid `filter` and `box-shadow` animation.
- Budget: aim for under 30 KB for an inline SVG/CSS animation, under 50 KB for Lottie/Rive assets, and no layout shift when the state appears.
- Do not replay the entrance on every re-render or tab switch. Play once per mount, and skip it when returning quickly.

### Empty state checklist

1. Is the call to action visible immediately and reachable without waiting?
2. Does the motion communicate something (what belongs here, that a task is complete), or is it decoration?
3. Is there one moving subject, ending in stillness or a very subtle loop?
4. Does the static end frame look finished by itself?
5. Do art, color and stroke come from the design tokens and work in light and dark?
6. Is reduced motion handled, and is the art hidden from screen readers while the text is exposed?
7. Is the copy plain, verb-first for the action, without "Oops" or apologies?
8. Does it stay small enough that text and button sit above the fold on a 360px-wide screen?

---

## Output expectations

- Deliver working, token-driven code that fits the project's stack and conventions.
- Prefer editing existing components and theme files over adding parallel ones.
- Keep the explanation short: state the design decisions that matter (palette roles, type pairing, key layout choice) in a few lines; do not lecture.
- If asked for a mockup only, produce it at real content fidelity and mention the tokens used so it can be implemented faithfully.