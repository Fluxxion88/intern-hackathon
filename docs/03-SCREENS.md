# 03 — Screens

> Copy in this file is **final**. Do not "improve" it. Every line was written to be read by
> a 38-year-old dispatch manager who is deciding, in about four seconds, whether this is
> another thing that will waste his time.
>
> Routes are Next.js App Router. State lives in the URL (`/train/[jobId]/[step]`) so that
> back/refresh never destroys work — Andrei *will* hit back.

---

## Screen map

```
  /                          Landing
  /start                     Sign in (mocked)
  /train/new                 ①  The brief
  /train/[id]/questions      ②  Three questions
  /train/[id]/readback       ③  Read-back            ← the trust moment
  /train/[id]/example        ④  Show me one you did
  /train/[id]/training       ⑤  Training (the Ledger) ← the signature moment
  /train/[id]/ready          ⑥  First day
  /i/[slug]                  The trained intern's own page (public-ish, behind Pomerium)
```

---

## 0. `/` — Landing

**Job of this page:** in four seconds, make Andrei believe this is not for programmers.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│   INTERN                                                    Sign in        │  ← label / QUIET
│   ─────────────────────────────────────────────────────────────────────    │  ← --rule-thin, full bleed
│                                                                            │
│                                                                            │
│                                                                            │
│      Train an intern to do                                                 │  ← display-1, 56/60
│      the boring half of your job.                                          │     max-width 62ch
│                                                                            │
│      You explain it once, the way you'd explain it to a new hire.          │  ← body, --ink-500
│      You show it one you did earlier. It practises until it matches.       │
│      Then it works for you, forever, at a web address of your own.         │
│                                                                            │
│      ┌────────────────────────┐   ┌────────────────────────┐              │
│      │  Train your first one  │   │  Watch a 60-second one │              │  ← PRIMARY / SECONDARY
│      └────────────────────────┘   └────────────────────────┘              │
│                                                                            │
│      No installing. No subscription. $20 once, per intern.                 │  ← label, --ink-500
│                                                                            │
│                                                                            │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │  ╭───╮                                                           │    │  ← THE HERO IS THE
│   │  │ 1 │  ATTEMPT 1                                        41%     │    │     LEDGER ITSELF,
│   │  ╰───╯                                                   match   │    │     auto-playing on
│   │  ├───────────────────────────────────────────────────────────┤  │    │     a 6-second loop,
│   │  Read both files. Named the columns wrong, used kilos.         │    │     4 slips landing
│   │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  20/48        │    │     one after another,
│   └──────────────────────────────────────────────────────────────────┘    │     then the stamp.
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │  ╭───╮                                                           │    │     Nothing else on
│   │  │ 4 │  ATTEMPT 4                                        97%     │    │     this page moves.
│   │  ╰───╯                                                   match   │    │
│   │  Sorted the rows the way you asked. One cost is a dollar off.    │    │
│   │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░  47/48        │    │
│   └────────────────────────────────────────────────────┬─────────────┘    │
│                                                   ╔════╧═════════╗        │
│                                                   ║  M A T C H E D ║       │
│                                                   ║  100% · 5 TRIES║       │
│                                                   ╚═══════════════╝        │
│                                                                            │
│   ──────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   THREE THINGS THAT ARE TRUE                                               │  ← label
│                                                                            │
│   It learns from your file, not your explanation.                          │  ← title-2 ×3,
│   You give it two you started with and one you finished. That's the        │     body under each,
│   whole specification. It practises against your own work until it         │     3 columns desktop,
│   matches, and it tells you the number.                                    │     stacked mobile
│                                                                            │
│   What you get back has no AI inside it.                                   │
│   Once it has learned the job, the intelligence is thrown away. What       │
│   runs every morning is a plain, boring program. It does the same thing    │
│   every time, in about a second, and it can't invent anything.             │
│                                                                            │
│   It tells you what it can't do.                                           │
│   If it only ever gets to 87%, it says 87%, and it marks the rows it       │
│   wasn't sure about. You finish those three. You still got your morning    │
│   back.                                                                    │
│                                                                            │
│   ──────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   Built at the Loop Engineering Hackathon · AWS Builder Loft · July 2026   │  ← label, --ink-300
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

**Notes for the implementer:**
- The hero is the Ledger animation, not a headline over a screenshot. The most characteristic
  thing in this product's world is *watching the intern get better*, so that's what opens.
- The auto-play loop uses `web/mocks/events.json` — the same data shape the real SSE emits.
  Build it once, use it in two places.
- `prefers-reduced-motion`: show the final state (4 slips + stamp), no landing animation.
- **Do not** add logos-of-companies-you've-heard-of, testimonials, or a pricing table.

---

## 1. `/start` — Sign in (mocked, 15 minutes of work, no more)

```
┌────────────────────────────────────────────────────────────────────────────┐
│   INTERN                                                                   │
│   ─────────────────────────────────────────────────────────────────────    │
│                                                                            │
│                    ┌────────────────────────────────────┐                  │
│                    │                                    │                  │  ← Sheet, --lift-1
│                    │   Let's get you started.           │                  │     max-width 420px
│                    │                                    │                  │     centered vertically
│                    │   YOUR NAME                        │                  │
│                    │  ┌──────────────────────────────┐  │                  │
│                    │  │ Andrei                       │  │                  │
│                    │  └──────────────────────────────┘  │                  │
│                    │   So your intern knows who it      │                  │
│                    │   works for.                       │                  │
│                    │                                    │                  │
│                    │   WORK EMAIL                       │                  │
│                    │  ┌──────────────────────────────┐  │                  │
│                    │  │ andrei@                      │  │                  │
│                    │  └──────────────────────────────┘  │                  │
│                    │   We send the web address here     │                  │
│                    │   when it's trained. Nothing else. │                  │
│                    │                                    │                  │
│                    │  ┌──────────────────────────────┐  │                  │
│                    │  │          Continue            │  │                  │  ← PRIMARY, full width
│                    │  └──────────────────────────────┘  │                  │
│                    │                                    │                  │
│                    └────────────────────────────────────┘                  │
│                                                                            │
│                     No password. We'll email you a link.                   │  ← label, --ink-500
└────────────────────────────────────────────────────────────────────────────┘
```

**Implementation:** name + email → signed cookie → done. **There is no magic link.** Do not
build email auth. If a judge asks, "passwordless, magic link, standard stuff" and move on.
Two fields is itself the pitch: every field here is a reason for Andrei to close the tab.

---

## 2. `/train/new` — ① The brief

**Job:** get him talking in his own words with zero prompt-engineering anxiety.

```
┌──────────────┬─────────────────────────────────────────────────────────────┐
│              │                                                             │
│  ◉  1 Brief  │   Tell your intern what the job is.                         │  ← display-2
│  │           │                                                             │
│  ○  2 Ques.  │   Explain it the way you'd explain it to someone starting   │  ← body, --ink-500
│  │           │   on Monday. Where the files come from, what you do to      │     max-width 62ch
│  ○  3 Read-  │   them, what the finished thing looks like. Don't tidy it   │
│  │    back   │   up — it's better if you ramble.                           │
│  ○  4 Show   │                                                             │
│  │    me     │  ┌───────────────────────────────────────────────────────┐  │
│  ○  5 Train  │  │ Every morning I get the manifest for the day and the   │  │  ← textarea
│  │           │  │ rate card from accounts. I put them together into one  │  │     min-height 260px
│  ○  6 First  │  │ summary for the drivers — my columns, my order. Loads  │  │     bg --paper-2
│       day    │  │ in tonnes not kilos because nobody thinks in kilos.    │  │     press-1
│              │  │ Work out the cost per run. Total at the bottom. Skip   │  │     font: body 15px
│              │  │ the little stuff, under half a tonne isn't worth the   │  │     NOT mono
│              │  │ diesel.                                                │  │
│              │  │                                                        │  │
│              │  └───────────────────────────────────────────────────────┘  │
│              │   Say as much or as little as you like. It'll ask if it     │  ← help text
│              │   needs more.                                               │
│              │                                                             │
│              │   ┌──────────────────────┐   ┌──────────────────────────┐   │
│              │   │  Send it to your     │   │  Use the freight example │   │  ← PRIMARY / SECONDARY
│              │   │  intern              │   │                          │   │
│              │   └──────────────────────┘   └──────────────────────────┘   │
│              │                                                             │
└──────────────┴─────────────────────────────────────────────────────────────┘
```

**"Use the freight example"** pre-fills the textarea with the demo brief and jumps to the
prefilled path. **This button is your demo insurance.** Wire it first. If the venue wifi
dies at 16:05 you press that button and the whole flow still runs from fixtures.

---

## 3. `/train/[id]/questions` — ② Three questions

**Job:** resolve the ambiguities that would otherwise silently poison training — but cap it
at three, because a form that grows is a form that gets abandoned.

Questions arrive one at a time, land like ledger slips. Answered ones collapse to a single
line. <cite>Different levels of explanation suit different users; explanations should manage
expectations rather than let the user discover errors later</cite> — each question says
*why* it's being asked.

```
┌──────────────┬─────────────────────────────────────────────────────────────┐
│  ●  1 Brief  │   Three things I'm not sure about.                          │  ← display-2
│  │           │                                                             │
│  ◉  2 Ques.  │   ┌──────────────────────────────────────────────────────┐  │
│  │           │   │ ✓  What counts as "little stuff"?                    │  │  ← ANSWERED: collapsed
│  ○  3 Read-  │   │    Under 500 kg.                              edit   │  │     --ink-500, 44px tall
│  │    back   │   └──────────────────────────────────────────────────────┘  │
│  ○  4 Show   │                                                             │
│  ○  5 Train  │   ┌──────────────────────────────────────────────────────┐  │
│  ○  6 First  │   │  ╭───╮                                               │  │  ← CURRENT: Sheet,
│              │   │  │ 2 │  If a truck isn't on the rate card, what do    │  │     --lift-2
│              │   │  ╰───╯  I do with that run?                          │  │     title-2 question
│              │   │                                                       │  │
│              │   │         I need this because I can't work out a cost   │  │  ← body --ink-500,
│              │   │         without a rate, and I'd rather ask than       │  │     THE "WHY"
│              │   │         guess and be wrong every morning.            │  │
│              │   │                                                       │  │
│              │   │         ┌─────────────────────┐                       │  │  ← suggested answers
│              │   │         │ Leave it out        │                       │  │     as SECONDARY btns,
│              │   │         └─────────────────────┘                       │  │     because typing is
│              │   │         ┌─────────────────────┐                       │  │     work and clicking
│              │   │         │ Keep it, mark the   │                       │  │     is not
│              │   │         │ cost as "TBC"       │                       │  │
│              │   │         └─────────────────────┘                       │  │
│              │   │                                                       │  │
│              │   │         ┌─────────────────────────────────────────┐   │  │
│              │   │         │ or tell me in your own words…           │   │  │  ← Field
│              │   │         └─────────────────────────────────────────┘   │  │
│              │   └──────────────────────────────────────────────────────┘  │
│              │                                                             │
│              │   ░░░  3 · not asked yet                                    │  ← --ink-300, 44px
│              │                                                             │
└──────────────┴─────────────────────────────────────────────────────────────┘
```

**Hard rule: maximum three questions.** The planner is instructed to rank ambiguities by how
much they'd cost in training and ask only the top three (`05-LOOP-ENGINE.md §4.2`). If it
wants to ask a fourth, it must instead *guess, state the guess in the read-back, and let
Andrei catch it there.* A guess he can veto is cheaper than a question he has to answer.

---

## 4. `/train/[id]/readback` — ③ Read-back  ★ THE TRUST MOMENT

**Job:** Andrei sees his own job described back to him in his own words, and thinks *"yes,
it actually understood."* This is the screen the whole product is about. If a judge
remembers one screen, it should be this one or the Ledger.

```
┌──────────────┬─────────────────────────────────────────────────────────────┐
│  ●  1 Brief  │   Here's the job as I understand it.                        │  ← display-2
│  │           │                                                             │
│  ●  2 Ques.  │   Read it like you'd read a new hire's notes. If anything   │  ← body --ink-500
│  │           │   is wrong, say so — it's much cheaper to fix now.          │
│  ◉  3 Read-  │                                                             │
│  │    back   │   ┌──────────────────────────────────────────────────────┐  │
│  ○  4 Show   │   │                                                       │  │  ← Sheet --lift-1,
│  ○  5 Train  │   │  EVERY MORNING I WILL                                 │  │     padding --s-6
│  ○  6 First  │   │                                                       │  │
│              │   │  1  Take two files from you: the day's manifest and    │  │  ← Numbered list.
│              │   │     the current rate card.                            │  │     Numbers earn their
│              │   │                                                       │  │     place here: this
│              │   │  2  Throw away any run under 500 kg.                   │  │     IS an ordered
│              │   │                                                       │  │     procedure, and
│              │   │  3  Match each run to its truck's rate. If the truck   │  │     order changes the
│              │   │     isn't on the card, keep the run and write "TBC"    │  │     answer.
│              │   │     where the cost goes.                              │  │
│              │   │                                                       │  │     body 15/24,
│              │   │  4  Work out the cost: the base fee, plus the rate per │  │     --s-4 between,
│              │   │     km times the distance. Round to whole dollars.     │  │     hanging indent on
│              │   │                                                       │  │     the numeral
│              │   │  5  Turn kilos into tonnes, two decimal places.        │  │
│              │   │                                                       │  │
│              │   │  6  Sort by destination A→Z, then dearest run first.   │  │
│              │   │                                                       │  │
│              │   │  7  Name the columns your way: Date, Route, Truck,     │  │
│              │   │     Load (t), Cost ($).                               │  │
│              │   │                                                       │  │
│              │   │  8  Put a TOTAL row at the bottom with the load and    │  │
│              │   │     the cost added up, and nothing in the other        │  │
│              │   │     columns.                                          │  │
│              │   │                                                       │  │
│              │   │  ├────────────────────────────────────────────────┤   │  │  ← hairline
│              │   │                                                       │  │
│              │   │  I'M GUESSING ON TWO THINGS                           │  │  ← label. THE HONESTY
│              │   │                                                       │  │     BLOCK. Non-optional.
│              │   │  ·  Dates like 17.07.2026, because that's how your     │  │
│              │   │     files are written.                               │  │
│              │   │  ·  A comma in the thousands, no cents.                │  │
│              │   │                                                       │  │
│              │   │  Your example will settle both. If I'm wrong you'll    │  │
│              │   │  see it in the practice.                              │  │
│              │   │                                                       │  │
│              │   └──────────────────────────────────────────────────────┘  │
│              │                                                             │
│              │   ┌──────────────────────┐   ┌──────────────────────────┐   │
│              │   │  That's the job      │   │  Something's wrong       │   │  ← PRIMARY / SECONDARY
│              │   └──────────────────────┘   └──────────────────────────┘   │
│              │                                                             │
└──────────────┴─────────────────────────────────────────────────────────────┘
```

**"Something's wrong"** → the list becomes inline-editable: each rule gets a hover state
with an `edit` QUIET button; editing a rule opens a one-line Field with the rule's text.
Changed rules are marked with a `--rule-heavy` left border and re-sent to the planner, which
regenerates `job_spec.json` and re-renders. **Do not** open a chat. A chat here means he has
to explain himself again; a text field on the wrong line means he fixes exactly the wrong
thing. This is the whole difference between our product and a chatbot.

**The "I'm guessing on two things" block is mandatory** even when the planner is confident —
if it has no guesses, it must surface its two lowest-confidence inferences anyway.
<cite>Users are meaningfully more likely to rely on AI that displays confidence levels or
explains its reasoning than on black-box output.</cite> This block is that, in his language.

---

## 5. `/train/[id]/example` — ④ Show me one you did

```
┌──────────────┬─────────────────────────────────────────────────────────────┐
│  ●  1 Brief  │   Now show me one you did yourself.                         │  ← display-2
│  ●  2 Ques.  │                                                             │
│  ●  3 Read-  │   Two you started with, and the one you finished. Last      │  ← body --ink-500
│  │    back   │   Tuesday's is fine. This is how I'll know I've got it      │
│  ◉  4 Show   │   right — I'll practise until mine matches yours exactly.   │
│  ○  5 Train  │                                                             │
│  ○  6 First  │   WHAT YOU STARTED WITH                                     │  ← label
│              │  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐    │
│              │                       ↓                                     │  ← DropZone, 180px
│              │  │           Drop your two files here                  │    │
│              │                   or click to choose                         │
│              │  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘    │
│              │  ┌───────────────────────────────────────────────────┐     │
│              │  │ ▤  manifest_2026-07-14.csv        12 KB   ✓    ✕  │     │  ← FileChips appear
│              │  └───────────────────────────────────────────────────┘     │     below, --s-2 gap
│              │  ┌───────────────────────────────────────────────────┐     │
│              │  │ ▤  carrier_rates_2026-07.csv       3 KB   ✓    ✕  │     │
│              │  └───────────────────────────────────────────────────┘     │
│              │                                                             │
│              │   WHAT YOU FINISHED                                         │  ← label
│              │  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐    │
│              │  │        Drop the summary you made from them          │    │
│              │  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘    │
│              │  ┌───────────────────────────────────────────────────┐     │
│              │  │ ▤  dispatch_summary_14.07.csv      2 KB   ✓    ✕  │     │
│              │  └───────────────────────────────────────────────────┘     │
│              │                                                             │
│              │   ├─────────────────────────────────────────────────────┤   │  ← hairline
│              │                                                             │
│              │   HERE'S WHAT I CAN SEE                    show all rows ↓  │  ← label + QUIET
│              │   ┌───────────┬─────────────┬──────────┬──────────────┐    │
│              │   │ DATE      │ ROUTE       │ TRUCK    │ LOAD (T)     │    │  ← Table preview,
│              │   ├───────────┼─────────────┼──────────┼──────────────┤    │     first 5 rows of
│              │   │ 17.07.2026│ Bakersfield │ TRK-03   │         2.90 │    │     the EXPECTED file
│              │   │ 17.07.2026│ Fresno      │ TRK-11   │         1.24 │    │
│              │   └───────────┴─────────────┴──────────┴──────────────┘    │
│              │                                                             │
│              │   ┌──────────────────────┐                                  │
│              │   │  Start practising    │                                  │  ← PRIMARY, disabled
│              │   └──────────────────────┘                                  │     until 2+1 files
│              │                                                             │
└──────────────┴─────────────────────────────────────────────────────────────┘
```

**The preview table is not decoration.** It is the receipt that we can actually read his
file. If parsing fails, this is where he finds out — while he can still fix it — not four
minutes into training.

**Empty state of the drop zone is an invitation, not a mood:** "Drop your two files here."
**Error state states the fix:** "This one's a spreadsheet with three tabs. Save the tab you
use as a CSV and drop it again." — never "Unsupported file type."

---

## 6. `/train/[id]/training` — ⑤ Training  ★ THE SIGNATURE MOMENT

**Job:** make an agent loop legible to a person who doesn't know what an agent is, and make
it feel like something is genuinely at stake.

```
┌──────────────┬─────────────────────────────────────────────────────────────┐
│  ●  1 Brief  │   It's practising.                                          │  ← display-2
│  ●  2 Ques.  │                                                             │
│  ●  3 Read-  │   It writes a program, runs it on your two files, compares  │  ← body --ink-500
│  ●  4 Show   │   what came out against the one you made, and fixes what    │
│  ◉  5 Train  │   doesn't line up. You can watch, or come back in a minute. │
│  ○  6 First  │                                                             │
│              │   ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────┐ │
│              │   │  5 tries  │  │    97%    │  │  41 sec   │  │ WRITING │ │  ← 4 stat cells,
│              │   │           │  │   match   │  │           │  │ ·  ·  · │ │     data-lg numbers,
│              │   └───────────┘  └───────────┘  └───────────┘  └─────────┘ │     label under.
│              │                                                             │     4th cell is the
│              │   ├─────────────────────────────────────────────────────┤   │     LIVE PHASE:
│              │                                                             │     WRITING / RUNNING
│              │   ┌──────────────────────────────────────────────────────┐ │     / CHECKING /
│              │   │  ╭───╮                                               │ │     FIXING, with 3
│              │   │  │ 5 │  ATTEMPT 5 · 11:04:51                 100%   │ │     dots cycling.
│              │   │  ╰───╯                                       match  │ │     NO SPINNER.
│              │   │  ├──────────────────────────────────────────────┤   │ │
│              │   │  Every cell matches yours.                           │ │  ← newest slip on top,
│              │   │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  48/48   │ │     --lift-2, lands with
│              │   │  Changed: rounding on Cost      [ see the diff ]     │ │     --lift-3 → --lift-1
│              │   └───────────────────────────────────┬──────────────────┘ │
│              │                              ╔════════╧════════╗           │
│              │                              ║  M A T C H E D  ║           │  ← Stamp, on convergence
│              │                              ║  100% · 5 TRIES ║           │     only. 220ms.
│              │                              ╚═════════════════╝           │
│              │   ┌──────────────────────────────────────────────────────┐ │
│              │   │  ╭───╮                                               │ │
│              │   │  │ 4 │  ATTEMPT 4 · 11:04:22                  97%   │ │  ← older slips:
│              │   │  ╰───╯                                       match  │ │     --lift-1, text
│              │   │  Sorted the rows the way you asked. One cost is a    │ │     --ink-500
│              │   │  dollar off.                                         │ │
│              │   │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░  47/48   │ │
│              │   └──────────────────────────────────────────────────────┘ │
│              │   ┌──────────────────────────────────────────────────────┐ │
│              │   │  │ 3 │  ATTEMPT 3 · 11:03:58                  89%   │ │
│              │   │  Added the total row. Rows are in the wrong order.   │ │
│              │   │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░  43/48   │ │
│              │   └──────────────────────────────────────────────────────┘ │
│              │                          ⋮  (2 more)                        │
│              │                                                             │
│              │   ┌──────────────────────┐   ┌──────────────────────────┐   │
│              │   │  It's ready — go     │   │  Show me what it wrote   │   │  ← PRIMARY appears
│              │   └──────────────────────┘   └──────────────────────────┘   │     only on converge
└──────────────┴─────────────────────────────────────────────────────────────┘
```

### Behaviour

- **Never a spinner.** The phase cell (`WRITING · · ·`) plus the landing slips *are* the
  progress. A spinner says "wait"; a slip landing says "it's getting closer."
- Slips arrive over SSE (`04-ARCHITECTURE.md §6`). Each `attempt.scored` event appends a slip.
- The stat cells update live. `match` shows the **best** score so far, not the latest — it
  must never go down in front of Andrei, and the loop guarantees we keep the best artifact.
- **`[ see the diff ]`** opens a Sheet overlay with the expected-vs-produced table, wrong
  cells inverted (`--ink-900` bg, `--paper-0` text). This is what a judge will click. Make
  it good: side-by-side at ≥1024px, stacked below.
- **Non-convergence** (`PLATEAU`/`BUDGET`): no stamp. Instead, a Sheet with `--rule-heavy`:

  > **It gets 87% of this right on its own.**
  > Six rows it can't work out — they're marked `CHECK` in the file so you'll spot them.
  > That's still most of your morning back. You can take it as it is, or add one more
  > example you did and let it practise again.
  >
  > `[ Take it at 87% ]`   `[ Give it another example ]`

  This screen is not a failure state. Ship it, demo it if you have time, and say out loud:
  "most demos today will tell you they succeeded; ours tells you the number."
- **Hard failure** (`FAILED`, score <0.4): say what we couldn't do and give the money back
  language. "I couldn't work this one out. Your example has a column I can't find anywhere
  in the two files — `Driver`. Where does that come from?" Then link back to step ③.

---

## 7. `/train/[id]/ready` — ⑥ First day

```
┌──────────────┬─────────────────────────────────────────────────────────────┐
│  ●  1 Brief  │                                                             │
│  ●  2 Ques.  │   Your intern is ready.                                     │  ← display-2. THE ONE
│  ●  3 Read-  │                                                             │     WARM SENTENCE IN
│  ●  4 Show   │   It learned the job in 5 tries and 41 seconds. From now    │     THE PRODUCT.
│  ●  5 Train  │   on it takes about a second, and it costs you nothing to   │
│  ◉  6 First  │   run.                                                      │
│       day    │                                                             │
│              │   ┌──────────────────────────────────────────────────────┐ │
│              │   │  ITS ADDRESS                                          │ │  ← Sheet --lift-2,
│              │   │                                                       │ │     the hero of the
│              │   │  ┌─────────────────────────────────────────┬───────┐ │ │     screen
│              │   │  │ intern.works/i/andrei-dispatch          │ copy  │ │ │
│              │   │  └─────────────────────────────────────────┴───────┘ │ │  ← data 17px, Field-
│              │   │                                                       │ │     styled, copy btn
│              │   │  Bookmark it. Drop your two files, get your summary.  │ │
│              │   │  Send it to your drivers if you like — it's yours.    │ │
│              │   │                                                       │ │
│              │   │  ┌────────────────────────┐                           │ │
│              │   │  │  Open it now           │                           │ │  ← PRIMARY
│              │   │  └────────────────────────┘                           │ │
│              │   └──────────────────────────────────────────────────────┘ │
│              │                                                             │
│              │   ├─────────────────────────────────────────────────────┤   │
│              │                                                             │
│              │   WHAT IT LEARNED                            download ↓     │  ← label + QUIET
│              │   ╔══════════════════════════════════════════════════════╗ │
│              │   ║  1  import pandas as pd                              ║ │  ← Well, monochrome,
│              │   ║  2  import sys                                       ║ │     max-height 320px,
│              │   ║  3                                                   ║ │     scrolls
│              │   ║  4  MIN_KG = 500                                     ║ │
│              │   ║  5  COLS = ["Date","Route","Truck","Load (t)","Cost  ║ │
│              │   ║  6                                                   ║ │
│              │   ║  7  def run(manifest, rates, out):                   ║ │
│              │   ║ ...                                                  ║ │
│              │   ╚══════════════════════════════════════════════════════╝ │
│              │                                                             │
│              │   ┌──────────────────────────────────────────────────────┐ │
│              │   │  ✓  No AI inside                                      │ │  ← THE CLAIM, checked
│              │   │                                                       │ │     by the guard and
│              │   │  This program has no model in it, makes no calls to   │ │     rendered from its
│              │   │  the internet, and can't invent anything. It does the │ │     actual PASS output
│              │   │  same thing every time. We checked — that's why it's  │ │
│              │   │  $20 once and not a meter.                            │ │
│              │   │                                                       │ │
│              │   │  network calls  0   ·   model calls  0   ·  checked   │ │  ← data 13px, --ink-500
│              │   │  at 11:05:33                                          │ │
│              │   └──────────────────────────────────────────────────────┘ │
└──────────────┴─────────────────────────────────────────────────────────────┘
```

**The "No AI inside" card is the money shot for the judges** and is rendered from the actual
output of `guards/no_llm_at_runtime.py`. Do not fake it. If the guard fails, this card must
show the failure — and if it's ever failing, the product is broken anyway.

---

## 8. `/i/[slug]` — The trained intern's own page

This is what Andrei actually uses every morning for the next two years. It should look like
it costs nothing to run, because it does.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│   ANDREI'S DISPATCH INTERN                          trained 17.07.2026     │  ← label / label
│   ─────────────────────────────────────────────────────────────────────    │
│                                                                            │
│                                                                            │
│              ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐             │
│                                                                            │  ← DropZone, big:
│              │                    ↓                          │             │     260px min-height.
│                          Drop today's two files                            │     THE ENTIRE PAGE
│              │           the manifest and the rate card      │             │     IS THE DROP ZONE.
│                                                                            │
│              └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘             │
│                                                                            │
│                                                                            │
│              It'll take about a second. You'll get                         │  ← body --ink-500,
│              dispatch_summary_17.07.csv back.                              │     centered
│                                                                            │
│              ─────────────────────────────────────────                     │
│                                                                            │
│              Or email them to                                              │  ← label
│              andrei-dispatch@in.intern.works                               │  ← data
│              and it'll reply with the file.                                │
│                                                                            │
│              ─────────────────────────────────────────                     │
│                                                                            │
│              Runs 38 · last run 16.07.2026 · always 1.2s                   │  ← label --ink-300
│              This one doesn't use AI. Same answer every time.              │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

**After a run**, the drop zone is replaced in place (no navigation) by:

```
              ┌──────────────────────────────────────────┐
              │  ▤  dispatch_summary_17.07.csv           │   ← Sheet --lift-2
              │     22 rows · 1 total · 1.2 seconds      │
              │                                          │
              │  ┌────────────────────────┐              │
              │  │  Download              │              │   ← PRIMARY. Auto-downloads
              │  └────────────────────────┘              │      too — don't make him click.
              │                                          │
              │  ┌───────────┬────────┬────────┬───────┐ │   ← Table, first 5 rows,
              │  │ DATE      │ ROUTE  │ TRUCK  │ LOAD  │ │      so he can see it's right
              │  ├───────────┼────────┼────────┼───────┤ │      before he opens it
              │  │ 17.07.2026│ Fresno │ TRK-11 │  1.24 │ │
              │  └───────────┴────────┴────────┴───────┘ │
              │                                do it again│   ← QUIET
              └──────────────────────────────────────────┘
```

The email address line is real if the Zero adapter is live, and greyed with the label
"coming for your inbox next" if it isn't. **Do not block the demo on email.** Dropping files
is the path; email is the "and it also does this" beat in the pitch.

---

## 9. Screen-level checklist

For every screen, before you call it done:

- [ ] Exactly one primary action
- [ ] A way back that doesn't lose work
- [ ] Every field has visible help text, no tooltips
- [ ] The empty state tells him what to do
- [ ] The error state tells him how to fix it, in his words, with no error code
- [ ] Nothing on screen uses a word from the banned list (`02-DESIGN-SYSTEM.md §6`)
- [ ] Works at 390px
- [ ] Tab through it: every stop is visible, the order is the reading order
