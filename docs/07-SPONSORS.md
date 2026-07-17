# 07 — Sponsors

> Requirement: **at least 3 sponsor tools, used effectively.** `Tool Use` is 20% of the score.
> The judges from Pomerium, Nexla, Akash and ZeroClick are **in the room** and will watch your
> demo. A judge can tell in four seconds whether their product is load-bearing or decorative.
>
> **Golden rule: every adapter has a `MOCK_MODE` and no sponsor is on the critical path of the
> happy path.** An integration that breaks your demo scores worse than no integration.

---

## 1. The one-slide map

```
   Zero.xyz  ──▶  the intern's hands.     It hits something it can't do → finds a service.
   Pomerium  ──▶  the intern's badge.     Model-written code doesn't get to roam. Andrei's
                                          files are Andrei's.
   Akash     ──▶  the intern's desk.      Each trained intern is a container. $0.30/month is
                                          why $20 once works.
   Nexla     ──▶  the intern's inbox/out. Files arrive from where Andrei's files already live.
   AWS       ──▶  the trainer.            Bedrock teaches it, then leaves. Runtime is AI-free.
```

Every one of these is a *body part of the metaphor*. That's not a coincidence — if an
integration can't be named as something the intern has or does, it doesn't belong in the demo.

---

## 2. Zero.xyz — **$2,500, the biggest single prize**

### The pitch to their judge

> <cite>Zero unblocks AI agents, giving them instant access to thousands of tools, APIs, and
> services without keys or configuration.</cite> Our whole product exists because Andrei will
> not configure anything. **We are Zero's thesis pointed at a person instead of a developer.**
> Zero unblocks the agent; we unblock the human. Neither of us asks anyone for an API key.

That framing is worth more than the code. Say it in exactly those terms.

### Where it's load-bearing

The training loop hits capability walls that have nothing to do with the transform:

| Wall | Without Zero | With Zero |
|---|---|---|
| Andrei's manifest is a scanned PDF, not a CSV | ask him for a CSV — **product dead** | agent discovers an OCR service, extracts, continues |
| He wants results emailed back | build SMTP, get creds, verify a domain | agent discovers a mail service, sends |
| The trained tool needs a public URL | provision, DNS, TLS | agent discovers a deploy service |

The pattern that makes it real:

```python
# engine/adapters/zero.py
class ZeroAdapter:
    """
    When the runner reports a CRASH finding whose hint matches a capability gap
    (PDF, xlsx-with-macros, image, an unreachable format), we do NOT hand the model
    a bigger prompt. We hand it a capability.
    """
    def resolve(self, need: str) -> Capability | None:
        # need: "extract a table from a scanned PDF"
        # → discovers via Zero, returns something the codegen can call as a plain
        #   function, and — critically — RECORDS THE RESULT so the artifact stays
        #   deterministic. See §2.1.
```

### 2.1 The subtlety you must get right — and it's a *feature*

The shipped artifact must have **no network calls** (`guards/no_llm_at_runtime.py` bans
`requests`). So Zero can't be *in* the tool. Correct — and it isn't a conflict, it's the
architecture:

> **Zero is used at training time, by the trainer. The result is baked in.**

The agent uses Zero to *learn how* to get a table out of a scanned PDF; what ships is the
extraction step it learned. The intelligence and the discovery happen once, during training;
the tool that runs every morning is inert. This is the same principle as "the LLM is the
trainer, not the worker," applied to capabilities instead of reasoning.

**Where Zero stays live at runtime:** the email path (`/i/{slug}` inbound/outbound), which is
transport, not transform. That's outside the guard's scope by design and you should be able to
draw that boundary on a whiteboard.

### Demo beat (15 seconds, do it *after* the main demo lands)

Drop a **scanned PDF** manifest instead of the CSV. The Ledger shows an extra phase:

```
   ┌──────────────────────────────────────────────────────────┐
   │  ╭───╮                                                   │
   │  │ 2 │  ATTEMPT 2 · 11:03:40                      0%     │
   │  ╰───╯                                            match  │
   │  ├──────────────────────────────────────────────────┤   │
   │  This one's a scan, not a spreadsheet. Found something   │
   │  that can read it. Trying again.                         │
   │                                                          │
   │  got a new skill · via Zero                              │  ← label, --ink-500
   └──────────────────────────────────────────────────────────┘
```

**"got a new skill"** — the agent acquiring a capability mid-loop, rendered in the intern
metaphor, in front of the person who built the capability broker. That's the beat.

### Practical

- Free, $5 welcome credit, installs via a setup prompt to a CLI agent, works with Claude Code.
- **Do this at 11:05, not at 15:00.** Get one call working end-to-end before you build around it.
- Ask in the Zero Discord channel for the programmatic (non-CLI) path — you need to call it
  from `engine/`, not from a terminal.
- `ZERO_MODE=mock` replays a recorded discovery+call. Record it the moment live works.

---

## 3. Pomerium — **$1,000, and the least contested prize**

### The pitch to their judge

> **We execute code written by a language model, on files a stranger uploaded, on our
> infrastructure, on behalf of someone who cannot read the code.** Every one of those clauses
> is a reason someone should never use our product. Pomerium is the reason they can.

Most teams today will bolt Pomerium in front of a demo app and call it auth. You have an
actual, unforced security problem in the centre of your architecture. **Lead with the threat
model, not the config file** — their judge has seen a hundred `docker-compose` diffs today and
zero threat models.

### Two placements, both real

**① In front of everything** — the standard, 20 minutes:

```yaml
# deploy/pomerium/config.yaml
authenticate_service_url: https://authenticate.localhost.pomerium.io
routes:
  - from: https://intern.localhost.pomerium.io
    to: http://web:3000
    policy:
      - allow:
          or:
            - email:
                is: andrei@example.com
    pass_identity_headers: true          # → X-Pomerium-Jwt-Assertion

  - from: https://intern.localhost.pomerium.io
    prefix: /api/
    to: http://api:8000
    policy:
      - allow: { or: [ { email: { is: andrei@example.com } } ] }
    pass_identity_headers: true

  # ★ the interesting one: each trained intern is its own route with its own policy
  - from: https://intern.localhost.pomerium.io
    prefix: /i/andrei-dispatch
    to: http://api:8000
    policy:
      - allow:
          or:
            - domain: { is: andrei-freight.com }     # his drivers, nobody else
    pass_identity_headers: true
```

The API reads the identity from the Pomerium header and **never trusts a client-supplied
user id.** Show that line of code.

**② The interesting one — the sandbox egress story.** The generated script runs with
`--network=none` and `env={}` (`04-ARCHITECTURE.md §7`). When a tool legitimately needs to
reach out (the Zero email path), it goes **through Pomerium as an egress policy point**, not
around it. Phrase it for their judge:

> "The agent writes the code. It doesn't get to decide what the code is allowed to reach.
> That's a policy decision, it lives outside the model, and Pomerium enforces it."

That is precisely their positioning — *secure your agentic runtime* — and it's true of our
system rather than retrofitted onto it. If you only have time for one Pomerium sentence in
three minutes, **that's the sentence.**

### Practical

- `POMERIUM_ENABLED=false` for local dev; the app must work without it. Turn it on for the
  recording.
- Their Developer Advocate (Nick Taylor) is a judge **and** a speaker — find him in the
  Discord channel early and describe the threat model. Ten minutes with him is worth more
  than an hour of reading docs, and he'll remember your project at 16:45.

---

## 4. Akash — **$500 + $250 credits**

### The pitch to their judge

> Our unit economics are the product. **$20 once** only works if a trained intern costs
> approximately nothing to keep alive. It's a container with no GPU, no model, and no state
> that runs for 1.2 seconds a day. That's the cheapest possible workload — and it's exactly
> the workload a decentralised compute marketplace prices best. **We're not using Akash for
> GPUs. We're using it because a trained intern is a rounding error, and it should be
> priced like one.**

Every other team today will use Akash for inference. You're using it for the *absence* of
inference. That's memorable, and it's honest.

### Implementation

```yaml
# deploy/akash/deploy.sdl — one trained intern, one deployment
version: "2.0"
services:
  tool:
    image: <your-registry>/intern-tool-runtime:andrei-dispatch
    expose:
      - port: 8080
        as: 80
        to: [ { global: true } ]
    env:
      - TOOL_SLUG=andrei-dispatch
profiles:
  compute:
    tool:
      resources:
        cpu:    { units: 0.1 }      # ← the number IS the pitch. Show this block.
        memory: { size: 128Mi }
        storage:{ size: 128Mi }
  placement:
    dcloud:
      pricing:
        tool: { denom: uakt, amount: 100 }
deployment:
  tool:
    dcloud:
      profile: tool
      count: 1
```

`Dockerfile.tool-runtime` = python:3.12-slim + pandas + a 40-line FastAPI that accepts two
files, shells the artifact through the same sandbox, returns the CSV. **It is the same image
for every intern**; the artifact mounts in. So "how do you scale to 10,000 interns" has a
real answer: *10,000 of these, at 0.1 CPU each, and the marketplace bids them down.*

### Practical

- **Timebox to 45 minutes.** If a real deploy hasn't happened by 15:15, ship `deploy.sdl` +
  the built image + a validated manifest, show the SDL on screen, say "one command away, here
  are the resource units," and move on. A judge who sees an honest 0.1-CPU SDL and a clear
  economic argument scores you higher than a team that burned an hour on a wallet.
- Greg Osuri (founder) is a speaker **and** a judge. The economics framing is aimed squarely
  at him. Have the one-liner ready: *"we're the cheapest workload you'll see today, on
  purpose."*

---

## 5. Nexla — **$750 + $5,000 credits**

### The pitch to their judge

> Andrei's files are not in our app. They're in his inbox, on a shared drive, in a portal.
> **The last mile of "your intern works for you" is getting the files from where they
> actually live.** We do the transform; Nexla does the delivery. That's the whole
> enterprise version of this product.

### Implementation

Two integration points, both honest:

**① Inbound** — `andrei-dispatch@in.intern.works` (the line on `/i/[slug]`). A Nexla flow
watches the inbox, extracts the two attachments, POSTs them to `/api/i/{slug}/run`.

**② Outbound** — the produced CSV goes back to wherever his summaries already go: reply-all,
a drive folder, a warehouse table. One Nexla destination, swappable without touching the tool.

```python
# api/adapters/nexla.py
class NexlaAdapter:
    def register_intern(self, slug: str, spec: dict) -> str:
        """One trained intern → one Nexla flow. Source: his inbox. Destination: his folder.
           The transform in the middle is our artifact. We are a step in their pipeline,
           and that is exactly the right shape for both of us."""
```

Look at their **ADK** for the agent skeleton — docs and credits are in the Nexla Discord
channel; ask Abhijit or Amey (both judges, both in the room) what it buys you over rolling
your own. If their ADK gives you agent scaffolding you'd otherwise hand-write, use it and say
so; if it doesn't fit today's shape, use the data layer and be honest about why. **Judges
respect a considered "we used the part that fit" far more than a forced wrapper.**

### Practical

- `NEXLA_MODE=mock` renders the email address greyed with "coming for your inbox next."
- This is the easiest prize to win on *narrative* — the "data layer for AI" story maps onto our
  product with zero distortion. Spend 30 minutes, not 3 hours.

---

## 6. AWS — the trainer

- Bedrock, `claude-sonnet-4-5`, via `boto3` `converse`. Credits and setup are in the AWS
  Discord channel; **you must be registered at `events.builder.aws.com/LWl5ND`** — that's also
  your venue entry.
- The line that lands: **"Bedrock trains it. Then Bedrock leaves. What runs every morning has
  no model in it."** Nobody else today will use a model provider and then *remove it* — that
  inversion is memorable.
- `LLM_PROVIDER=anthropic` is your fallback if Bedrock creds are a mess. Don't burn 40 minutes
  on IAM at 12:30.

---

## 7. Cursor / Buildkite / Airbyte / Fillmore / Ghost

- **Cursor** — what you're building in. Mention it, don't integrate it.
- **Buildkite** — *tempting*: every loop attempt is genuinely a CI run, and "the agent's test
  suite is a real pipeline" is a beautiful sentence. **It is also a trap.** It puts a network
  round-trip inside your 40-second loop and turns a 35-second demo into a 3-minute one. Skip
  it. If you finish everything by 15:00 — you won't — wire it as an optional runner backend.
- **Airbyte** — overlaps Nexla. Pick one. Nexla has the prize.
- **Fillmore / Ghost** — different domain. Skip.

---

## 8. The 3-minute demo script

Rehearse this **twice** before 16:00. Time it. The most common way to lose is running long.

```
0:00  "Andrei is 38. He runs dispatch for a freight company. Every morning he takes two
       files and rebuilds them into one, his way. Forty minutes. Six years. He's asked
       twice for a script. It's still on the 'later' pile."
                                                        [ the landing page, Ledger looping ]

0:20  "So he tells his intern what the job is."         [ paste the brief — 3 seconds ]
      "It asks three questions. Not thirty."            [ answers, click click ]

0:40  "Then it reads the job back to him. In his words. This is the moment he decides
       whether to trust it — and notice it tells him what it's guessing."
                                                        [ ③ read-back, cursor on the
                                                          'I'M GUESSING ON TWO THINGS' block ]

1:00  "Now the part that matters. He shows it one he did himself. Two files in, one file
       out. That's not a demo — that's a test suite, and he wrote it by accident, last
       Tuesday, by doing his job."                      [ ④ drop the three files ]

1:15  "It writes a program. Runs it on his files. Diffs the result against his, cell by
       cell — with code, not vibes. Then it fixes the biggest thing that's wrong."
                                                        [ ⑤ TRAINING — LET IT PLAY.
                                                          Do not talk over attempt 1. ]
      "Forty-one percent. That's a good model, a clear brief, and less than half the job
       right. That's why this needs a loop and not a chatbot."

1:45  [ slips land — 68, 89, 97, 100 — STAMP ]
      "Five tries. Forty-one seconds. Every cell matches his."

2:00  "Here's what it learned."                         [ ⑥ ready → the Well ]
      "Sixty lines of Python. No model. No API key. No network. We check it —"
                                                        [ the guard card: PASS, 0, 0 ]
      "— because that's the whole business. The intelligence was the trainer. It's gone.
       What he owns is a boring program that costs thirty cents a month on Akash. That's
       why it's twenty dollars once and not a meter."

2:25  "It's Friday. Here are today's files."            [ /i/andrei-dispatch — drop 2 files ]
      [ 1.2s — the summary comes back ]
      "Data it's never seen. Same rules. One second."

2:40  "Zero gives it hands when it hits something it can't do. Pomerium means model-written
       code doesn't get to roam and Andrei's files stay Andrei's. Nexla brings the files
       from where they already live. Akash makes a trained intern cost nothing."

2:55  "He got his morning back. He never learned what an agent is."
```

**Rules for the recording:**
- Record it at **15:30 at the latest**, with whatever works then. A recorded 90% demo beats a
  live 100% demo that dies on venue wifi. `LLM_PROVIDER=mock` is allowed in the recording —
  it's a replay of a real run, and every hackathon demo on that stage is a replay of something.
- **Do not narrate attempt 1.** Let the room watch a slip land in silence. That's the moment.
- Full screen. No IDE. No terminal — except the guard, which you show for four seconds.
- Somebody who is not the presenter watches the clock and cuts at 2:55.
