# 02 — Design System

> **This file is law.** Every color, every shadow, every radius in the product comes from
> this file. If a value isn't here, it doesn't go in the CSS. No exceptions, no "just this
> once for the error state."

---

## 1. Direction

**Name: `Carbon Copy`.**

The subject's world is paperwork. Manifests, rate cards, carbon copies, rubber stamps,
ledger books, the pink flimsy that goes to accounts. Andrei's entire professional life is
made of documents that are black ink on white paper, ruled with hairlines, stacked in trays,
and made official by being *stamped*.

So the product is not a "SaaS dashboard." It is **a clean desk**. White paper, black ink,
hairline rules, real shadows because paper has thickness, and one rubber stamp when the work
is approved. That's it. That's the whole language.

**Why monochrome is a decision and not a limitation:** the product's central promise is
*"there is nothing to figure out here."* Color is a signalling system that has to be
learned — what does the purple badge mean, is orange bad. Removing color removes a
vocabulary Andrei never asked for. The only things that carry emphasis are **weight,
size, rule thickness, and elevation** — all of which are physically intuitive because they
are how paper actually behaves. The one place ink turns into a mark of authority is the
Stamp, and because it is the only such moment in the entire product, it lands.

**The signature element: The Ledger.** The training loop is not a spinner and not a
progress bar. It is a stack of paper slips, one per attempt, each dropping onto the desk
with a shadow, each printed with its match percentage and what went wrong, the stack
physically growing as the intern learns. When it converges, a stamp comes down on the top
slip. This is the thing people will remember from the demo, and it is the thing that makes
the loop *legible* to a non-technical person — he can see the intern trying.

**The risk we are taking:** no color at all, and animation limited to a single physical
metaphor (paper landing, stamp landing). If it's badly executed it's a Word document. So
execution has to be precise — spacing, optical alignment, and shadow quality are the entire
budget. Spend it there.

---

## 2. Tokens

Implement as CSS custom properties on `:root` in `web/app/globals.css`, then map into
Tailwind v4 via `@theme`. **Never hard-code a hex in a component.**

### 2.1 Ink & paper

```css
:root {
  /* Paper — the surfaces. Warm-neutral, never pure #FFF (pure white glares and
     kills the shadow language; paper is never pure white). */
  --paper-0:  #FBFBFA;   /* app background — the desk */
  --paper-1:  #FFFFFF;   /* raised card — a sheet ON the desk */
  --paper-2:  #F4F4F2;   /* recessed well — inputs, code blocks, the tray */
  --paper-3:  #ECECEA;   /* deepest recess — disabled, table zebra */

  /* Ink — the marks. Near-black, never #000 (pure black on white vibrates). */
  --ink-900:  #0C0C0C;   /* headlines, primary text */
  --ink-700:  #2E2E2C;   /* body text */
  --ink-500:  #6B6B67;   /* secondary text, labels */
  --ink-300:  #A3A3A0;   /* placeholder, disabled text */
  --ink-100:  #D9D9D6;   /* the hairline rule */
  --ink-050:  #E9E9E7;   /* the faintest rule, table inner lines */

  /* Semantic — still monochrome. Meaning comes from WEIGHT and MARK, not hue. */
  --mark-good: var(--ink-900);   /* ✓ solid black */
  --mark-bad:  var(--ink-900);   /* ✗ solid black, but struck through */
  --mark-wait: var(--ink-300);   /* pending = faint, not colored */
}
```

**Rule:** there is exactly one non-monochrome value permitted in the entire product, and it
is the focus ring (see §2.5), because accessibility beats aesthetics.

### 2.2 Rules (lines)

The hairline is the primary structural device. Three weights, and they mean things:

```css
  --rule-hair:   1px solid var(--ink-050);  /* inside a component: table rows, list items */
  --rule-thin:   1px solid var(--ink-100);  /* component boundary: card edge, input edge */
  --rule-heavy:  2px solid var(--ink-900);  /* an assertion: active step, the Stamp, focus */
```

Use `1px` literally. Do not use `0.5px`, do not use `border-hairline` tricks. On a 2x
display a 1px CSS border is 2 device pixels and looks exactly right.

**A rule encodes hierarchy, never decorates.** If you catch yourself adding a divider to
"break up the page," delete it and add space instead.

### 2.3 Shadows — the most important token set

Paper has thickness. Elevation is our only substitute for color, so the shadows must be
*good* — layered, tight, low-opacity, and warm-neutral rather than blue-black. Four steps,
mapped to physical states:

```css
  /* On the desk, flat. */
  --lift-0: none;

  /* A sheet resting on the desk. */
  --lift-1:
    0 1px 1px rgba(12,12,12,0.04),
    0 2px 4px rgba(12,12,12,0.04);

  /* A sheet the user is touching / hovering, lifted a millimetre. */
  --lift-2:
    0 1px 1px rgba(12,12,12,0.03),
    0 3px 6px rgba(12,12,12,0.05),
    0 8px 16px rgba(12,12,12,0.04);

  /* A slip that just LANDED on the Ledger — the drama shadow. */
  --lift-3:
    0 2px 2px rgba(12,12,12,0.03),
    0 6px 12px rgba(12,12,12,0.06),
    0 16px 32px rgba(12,12,12,0.06),
    0 32px 64px rgba(12,12,12,0.04);

  /* Pressed INTO the desk — inputs, the code well. Not a shadow, a hollow. */
  --press-1: inset 0 1px 2px rgba(12,12,12,0.06);
```

Rules for shadows:
- **Always paired with `--rule-thin`.** Shadow alone reads as blurry; the crisp 1px edge is
  what makes it read as paper. Card = `background: var(--paper-1)` + `border: var(--rule-thin)`
  + `box-shadow: var(--lift-1)`.
- Never a shadow on a recessed surface. Recessed = `--paper-2` + `--press-1`, no lift.
- Never colored shadows. Never `rgba(0,0,0,0.25)` — too heavy, that's Material, not paper.

### 2.4 Radius

```css
  --r-0: 0px;    /* tables, rules, the code well, the drop zone */
  --r-1: 2px;    /* inputs, buttons, small chips — a paper corner is not sharp */
  --r-2: 4px;    /* cards, ledger slips — the maximum in the product */
  --r-stamp: 3px; /* the stamp's box */
  --r-full: 999px; /* ONLY the round attempt-number badge on a ledger slip */
```

`--r-2 = 4px` is the ceiling. If you write `rounded-xl` anywhere, you have broken the
system. Modern-SaaS 12–16px radii read as plastic; paper doesn't do that.

### 2.5 Focus

The one permitted deviation from monochrome, for WCAG:

```css
  --focus-ring: 0 0 0 2px var(--paper-0), 0 0 0 4px var(--ink-900);
```

Two-layer: a paper-colored gap then a heavy ink ring, so it's visible on any surface. Every
interactive element gets `:focus-visible { box-shadow: var(--focus-ring); outline: none; }`.
No exceptions, and test it with the keyboard before you call any screen done.

### 2.6 Space

8px base, but with a 4px half-step for optical work. Only these:

```
  --s-1: 4px    --s-2: 8px    --s-3: 12px   --s-4: 16px
  --s-5: 24px   --s-6: 32px   --s-7: 48px   --s-8: 64px   --s-9: 96px  --s-10: 128px
```

Vertical rhythm: sections are separated by `--s-9` (96px) on desktop, `--s-7` on mobile.
Generous space is doing the work color usually does — do not compress it to fit more in.

### 2.7 Motion

```css
  --ease-paper: cubic-bezier(0.2, 0.9, 0.25, 1);  /* fast out, settle — like paper landing */
  --ease-stamp: cubic-bezier(0.5, 1.6, 0.4, 1);   /* overshoot — like a stamp hitting */
  --t-fast: 120ms;   --t-base: 220ms;   --t-slow: 420ms;
```

Only three animations exist in this product:
1. **Slip lands** (Ledger): `translateY(-18px) scale(0.985) opacity(0)` → rest, `--t-slow`,
   `--ease-paper`, with the shadow interpolating `--lift-3` → `--lift-1` over the same
   duration. The shadow settling is what sells the weight. Stagger multiple by 60ms.
2. **Stamp lands** (convergence): `scale(2.4) rotate(-14deg) opacity(0)` → `scale(1)
   rotate(-4deg) opacity(1)`, `--t-base`, `--ease-stamp`, plus a 1-frame `translateY(1px)`
   recoil on the parent card. Once, ever, per training run.
3. **Hover lift**: `--lift-1` → `--lift-2` and `translateY(-1px)`, `--t-fast`.

Everything else is instant. Respect `prefers-reduced-motion: reduce` — drop 1 and 2 to a
plain opacity fade, keep the stamp's final state.

---

## 3. Typography

Three faces, three jobs. All from Google Fonts, self-hosted via `next/font` (no FOUT, no
CDN dependency in the demo).

```css
  --font-display: "Instrument Serif", Georgia, serif;
  --font-ui:      "Instrument Sans", system-ui, sans-serif;
  --font-data:    "IBM Plex Mono", ui-monospace, monospace;
```

**Why these:** Instrument Serif is a high-contrast, slightly editorial serif — used *only*
for the four or five sentences in the product that are addressed to Andrei as a person
("Your intern is ready."). Instrument Sans is the workhorse: a neutral grotesk with slightly
narrow proportions that stacks well in dense tables and doesn't look like Inter (which reads
as "another AI startup"). IBM Plex Mono is not a stylistic choice, it's a functional one —
every number in this product is a quantity Andrei will check, and tabular figures aligned in
a column is how a rate card has always been read.

### 3.1 Scale

| Token | Size / Line / Tracking | Face | Weight | Use |
|---|---|---|---|---|
| `display-1` | 56/60, -0.02em | display | 400 | The one sentence on the landing hero. Desktop only; 40/44 on mobile. |
| `display-2` | 34/40, -0.015em | display | 400 | Screen titles ("Your intern is ready.") |
| `title-1` | 22/28, -0.01em | ui | 600 | Card titles, section heads |
| `title-2` | 17/24, -0.005em | ui | 600 | Sub-heads, ledger slip title |
| `body` | 15/24, 0 | ui | 400 | All prose. **Never smaller than 15px for body.** Andrei is 38 and this is a work tool, not a portfolio. |
| `body-strong` | 15/24, 0 | ui | 600 | Emphasis inside prose. **Bold is our highlighter.** |
| `label` | 12/16, 0.08em, UPPERCASE | ui | 600 | Eyebrows, field labels, column heads |
| `data` | 14/20, 0 | data | 400 | Every number, filename, column name, cell value. `font-variant-numeric: tabular-nums;` **mandatory**. |
| `data-lg` | 28/32, -0.01em | data | 500 | The match percentage on a ledger slip |
| `code` | 13/21, 0 | data | 400 | The produced script |

### 3.2 Prose rules

- Measure: **62–68 characters**, hard-capped with `max-width: 62ch`. Long lines are the
  fastest way to make a plain-language product feel unreadable.
- Sentence case everywhere. Title Case is corporate; we are a desk.
- Numbers in prose are `data` inline: "Attempt 4 — <span class=data>97%</span> match".

---

## 4. Components

Build these in `web/components/`. No component library. No shadcn. They're twelve small
files and hand-rolling them is faster than fighting someone else's tokens.

### 4.1 `<Sheet>` — the base card

```
┌─────────────────────────────────────────┐  ← border: --rule-thin, radius --r-2
│                                         │     background: --paper-1
│   padding: --s-5 (24px), or --s-6 on    │     box-shadow: --lift-1
│   anything that is the focus of a screen│
│                                         │
└─────────────────────────────────────────┘
    ↑ subtle --lift-1 shadow, warm not blue
```
Props: `elevation: 0|1|2`, `padded: boolean`. That's it.

### 4.2 `<Button>`

Three variants only.

```
PRIMARY                    SECONDARY                  QUIET
┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│  Approve the brief │     │   Change something │     │  Download script   │
└────────────────────┘     └────────────────────┘     └────────────────────┘
bg: --ink-900              bg: --paper-1               bg: transparent
text: --paper-0            text: --ink-900             text: --ink-500
border: none               border: --rule-thin         border: none
shadow: --lift-1           shadow: --lift-0            underline on hover
h: 44px  px: --s-5         h: 44px  px: --s-5          h: 36px  px: --s-2
radius: --r-1              radius: --r-1
hover: --lift-2, -1px      hover: bg --paper-2         hover: text --ink-900
active: --lift-0, +1px     active: bg --paper-3
```

**44px min height on every button.** Not 36. This is a mouse-and-keyboard user in an office
with a cheap monitor, plus it's the WCAG touch target. Never a button below 44px except
`QUIET`.

One primary action per screen. If a screen looks like it needs two primaries, the screen is
wrong — go back to `03-SCREENS.md`.

### 4.3 `<Field>` — text input

```
   ORIGINAL FILE NAME                      ← label, --s-2 below
  ┌─────────────────────────────────────┐
  │ manifest_2026-07-17.csv             │  ← bg --paper-2, border --rule-thin,
  └─────────────────────────────────────┘     shadow --press-1, radius --r-1
   The name your file arrives with.        ← help, --ink-500, --s-2 above
```
- Height 44px, padding `--s-3`, font `body`.
- Help text is **always present, never a tooltip.** Andrei will not hover to discover.
  A tooltip is a secret. We don't keep secrets from Andrei.
- Error: border becomes `--rule-heavy`, help text becomes `--ink-900` `body-strong`, and
  prefixed with a `✗`. No red. The message says what to do, not what happened.

### 4.4 `<LedgerSlip>` — **the signature component**

One attempt of the loop. Renders on the training screen, newest at top.

```
 ┌──────────────────────────────────────────────────────────────────┐
 │  ╭───╮                                                           │
 │  │ 4 │  ATTEMPT 4 · 11:04:22                              97%    │   ← data-lg, right
 │  ╰───╯                                                    match  │      label under
 │                                                                  │
 │  ├──────────────────────────────────────────────────────────┤   │   ← hairline
 │                                                                  │
 │  Sorted the rows the way you asked. One cost is a dollar off.    │   ← body, plain language
 │                                                                  │
 │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░  47/48    │   ← the cell strip
 │                                                                  │
 │  Changed: rounding on the Cost column          [ see the diff ]  │   ← label + QUIET btn
 └──────────────────────────────────────────────────────────────────┘
   border --rule-thin · radius --r-2 · bg --paper-1 · shadow --lift-1
   ON LAND: shadow --lift-3 → --lift-1 over 420ms
```

- The round `4` badge: 28px, `--r-full`, `border: --rule-thin`, `data` 13px centered. It's
  the only circle in the product — it reads as a page number, which is exactly right.
- **The cell strip** is the soul of it: one tick per output cell, `▓` = matches ground truth,
  `░` = doesn't. Rendered as a flex row of 3px-wide, 14px-tall divs, 1px gap, `--ink-900`
  vs `--ink-100`. As attempts stack, Andrei literally *watches the strip fill in*. No
  explanation needed. This is the whole product in one graphic.
- The prose line is written by the repairer in plain language (see `05-LOOP-ENGINE.md §6.3`).
  Never "AssertionError on col 3". Always "One cost is a dollar off."
- The topmost (current) slip is `--lift-2`; older slips settle to `--lift-1` and their text
  drops to `--ink-500`. The stack recedes. Past attempts are history, not noise.

### 4.5 `<Stamp>` — the payoff

Appears once, on convergence, rotated over the top-right of the final slip.

```
            ╔═══════════════════════╗
            ║                       ║
            ║   M A T C H E D       ║      ← label style, letter-spacing 0.18em
            ║   ─────────────────   ║
            ║   100%   ·  5 TRIES   ║      ← data 12px
            ║                       ║
            ╚═══════════════════════╝
                  rotate(-4deg)
```
- `border: --rule-heavy` (2px `--ink-900`), `radius: --r-stamp`, background `transparent`.
- Inner content `--ink-900`, `opacity: 0.88` — a real stamp never prints solid.
- Optional 1-2% noise/roughen via an SVG `feTurbulence` displacement filter on the border.
  **Do this only if you have time after everything else works.** It's the accessory Chanel
  told you to take off if you're not sure.
- Animation: `--ease-stamp` overshoot, 220ms. Add a subtle `translateY(1px)` recoil on the
  parent slip in the same frame. Do not add sound.

### 4.6 `<DropZone>`

```
  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
                                                            
  │                     ↓                                  │
                Drop your two files here                    ← title-2
  │              or click to choose                        │  ← body, --ink-500
                                                            
  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
    border: 1px DASHED --ink-100 · radius --r-0 · bg --paper-2 · shadow --press-1
    min-height 180px · dragover: border --rule-heavy dashed, bg --paper-1
```
The **only** dashed border in the product. Dashed = "a space waiting to be filled," which is
literally true and nowhere else true. That's how a structural device earns its place.

### 4.7 `<FileChip>`

```
  ┌─────────────────────────────────────────────┐
  │ ▤  manifest_2026-07-17.csv    12 KB   ✓  ✕ │   ← data 14px, 36px tall
  └─────────────────────────────────────────────┘     border --rule-thin, radius --r-1
```
`▤` is an inline SVG document glyph (12×14, 1px stroke, `--ink-500`), not an emoji. Zero
emoji in the product UI. Emoji are a tell, and they're a different visual language than
hairline ink.

### 4.8 `<StepRail>` — the wayfinding

Fixed left column on desktop (`--s-10` wide), horizontal bar on mobile.

```
   ●───  1  The brief          ← done: filled dot, --ink-900, body-strong
   │
   ●───  2  Read-back          ← done
   │
   ◉───  3  Show me one        ← CURRENT: ring dot + --rule-heavy left border on the label
   │
   ○───  4  Training           ← todo: hollow dot --ink-300, label --ink-300
   │
   ○───  5  First day
```
- Andrei must always be able to answer "where am I, what's left, can I go back." Steps 1–3
  are clickable backwards once visited. <cite>Users need clearly marked emergency exits that
  let them undo or exit without navigating a complex process</cite> — the rail is that exit.
- The connecting line is `1px solid --ink-100`, `--ink-900` for completed segments. Progress
  is shown by the line darkening. No percentage bar anywhere in this product except the
  match score, so that the match score means something.

### 4.9 `<Table>` — file preview

```
  ┌──────────────┬─────────────┬──────────┬───────────┐
  │ SHIPMENT_ID  │ DESTINATION │ WEIGHT_KG│ CARRIER   │  ← label style, bg --paper-2,
  ├──────────────┼─────────────┼──────────┼───────────┤     bottom border --rule-thin
  │ SHP-1041     │ Fresno      │    1,240 │ TRK-08    │  ← data, tabular-nums
  │ SHP-1042     │ Bakersfield │      480 │ TRK-03    │     row border --rule-hair
  │ SHP-1043     │ Fresno      │    2,900 │ TRK-11    │     numbers RIGHT-aligned
  └──────────────┴─────────────┴──────────┴───────────┘
    radius --r-0 · no outer shadow (it sits inside a Sheet)
```
Numeric columns right-aligned with `tabular-nums`. Text left. Never center anything. Zebra
striping is `--paper-2` on even rows *only if* >8 rows; below that the hairlines suffice.

In the diff view, a wrong cell gets `background: --ink-900; color: --paper-0` — inverted ink.
Not red. Inversion is more legible than hue and works for the ~8% of men with color vision
deficiency, one of whom is statistically in the judging panel.

### 4.10 `<Well>` — the code display

```
  ╔══════════════════════════════════════════════════════╗
  ║  1  import pandas as pd                              ║   bg --paper-2
  ║  2  import sys                                       ║   shadow --press-1
  ║  3                                                   ║   radius --r-0
  ║  4  def run(manifest_path, rates_path, out_path):    ║   font --font-data, code scale
  ║  5      m = pd.read_csv(manifest_path)               ║   line numbers --ink-300
  ╚══════════════════════════════════════════════════════╝
```
No syntax highlighting. **This is deliberate** — colored code would be the only color in the
product and it would scream. Monochrome code with `--ink-900` on `--paper-2` and a bold
weight on `def`/`return` keywords only. Andrei isn't reading it anyway; the judges are, and
they'll read the shape.

---

## 5. Layout

- Container: `max-width: 1120px`, centered, `padding: 0 --s-6`.
- Desktop grid: `StepRail (128px) | gutter (48px) | content (1fr, max 720px)`.
- The content column never exceeds **720px**. Ever. Even the tables — they scroll
  horizontally inside a Sheet instead. A wide interface makes a person scan; we want him
  to read.
- Mobile (<768px): rail collapses to a horizontal step bar pinned to the top, content is
  full width with `--s-4` padding. **Everything must work at 390px** — it will be
  demoed on a projector at whatever resolution the venue gives you, and the judges may
  open it on a phone.

---

## 6. Copy voice

Read `frontend-design`'s writing guidance, then apply these product-specific rules:

- **Second person, active, present.** "Your intern got 97% of this right." Not "The agent
  has achieved a 97% accuracy score."
- **Never these words in UI:** agent, model, LLM, AI, prompt, token, pipeline, deploy,
  endpoint, schema, parse, execute, iterate, optimize, leverage, seamless, powerful.
- **Numbers are always concrete.** "5 tries, 41 seconds" not "training complete."
- **Errors state the fix.** "Your example output has 9 columns but I only see 8 kinds of
  information in the inputs. Which column am I supposed to invent?" — not "Schema mismatch."
- **Never apologize.** Never exclaim. Exactly one sentence in the product is allowed warmth
  and it's the display-2 on the final screen: *"Your intern is ready."*

---

## 7. Self-critique checklist — run before you call the UI done

- [ ] Is there a hex value in a component file? → move it to a token
- [ ] Is there a radius > 4px? → fix
- [ ] Is there color anywhere except `--focus-ring`? → delete
- [ ] Is any shadow using `rgba(0,0,0,·)` at opacity > 0.08? → too heavy, re-derive
- [ ] Does every card have BOTH a 1px border and a shadow? → shadow without edge = blur
- [ ] Is body text below 15px anywhere? → fix
- [ ] Are numbers using `tabular-nums`? → fix
- [ ] Can you complete Brief → First day with only the keyboard? → fix
- [ ] Is there more than one primary button on any screen? → fix
- [ ] Any emoji? → delete
- [ ] Does it work at 390px? → fix
- [ ] `prefers-reduced-motion` respected? → fix
- [ ] Take one thing off: is the stamp noise filter earning its place, or is it an
      accessory? If you're not sure, remove it.
