# 00 — Overview

## What Warroom is

Warroom is a CLI that convenes a **panel of AI operators** in fixed roles and
runs a task through structured **debate rounds**, emitting a transcript plus a
final artifact. It is deliberately small and auditable — a deterministic state
machine, not an agent framework.

The value proposition is **uncorrelated judgment**. A single strong model,
asked to critique its own work, is a sycophant. Two models from different
families — one owning the artifact, one paid (in role, not dollars) to attack it
— surface failure modes neither would alone. Warroom formalizes that into roles,
rounds, and an adversary-driven stop condition.

## Why this document set exists (the greenfield story)

The `EchoTechIT/warroom` repo was **empty** — no commits, nothing on the remote.
There was no Warroom program to examine. The neighboring `EchoTechAIStack` repo
holds the *substrate* Warroom runs on (Ollama + Open WebUI + ComfyUI, Docker
Compose, Tailscale-only), but not Warroom itself. So Warroom was designed fresh:
this repo is the result — docs + a runnable scaffold, built for handoff to
OpenAI **Codex** as an adversarial reviewer.

## Use cases

1. **Design / architecture review.** The architect proposes a design; the
   adversary red-teams it; they converge on a hardened plan with an audit trail.
2. **Code / PR adversarial review.** Draft → objections → revise, gated by a
   machine-readable "no material objection" certification from the adversary.
3. **Decision docs / RFCs.** Multi-perspective synthesis where the reasoning,
   not just the conclusion, is preserved.
4. **Cheap bulk pre-processing.** The free local model summarizes and triages
   before the metered/rate-limited seats engage.

## The four seats

- **Architect** — owns the artifact. Strongest reasoner (Claude Fable 5).
- **Adversary** — attacks the artifact. Different family (GPT "Sol") for
  uncorrelated errors. Its certification is the stop condition.
- **Local** — cheap on-GPU workhorse: summaries, consistency checks, a second
  critique voice. Never the artifact owner, never the deciding vote.
- **Fourth** *(off by default)* — pluggable tiebreaker/specialist, backed by a
  cloud API or a second local GPU.

Gemini was intentionally dropped from the roster.

## The hybrid transport model (why it's not just API calls)

The seats are **subscriptions, not API plans**: a Claude Max 5x seat and a
ChatGPT Plus seat. Warroom drives them through their own CLIs (`claude -p`,
`codex exec`) in headless mode, using the CLI's logged-in session — it never
stores keys. The local and cloud-API operators use HTTP. So the orchestrator
speaks **two transports** behind one adapter contract:

- **CLI-shell** — subprocess, prompt on stdin, isolated scratch cwd.
- **HTTP OpenAI-compatible** — one class for both Ollama and any cloud endpoint.

This is the single most important design constraint, and the seam Codex should
scrutinize first. See [`01-architecture.md`](01-architecture.md).

## Where to go next

- [`01-architecture.md`](01-architecture.md) — adapters, rounds, memory, termination.
- [`02-operators-and-models.md`](02-operators-and-models.md) — the roster and model picks.
- [`03-hardware-substrate.md`](03-hardware-substrate.md) — the GPU story and the NVIDIA-only gap.
- [`04-shortcomings.md`](04-shortcomings.md) — the risks, stated plainly.
- [`05-codex-review-brief.md`](05-codex-review-brief.md) — the adversarial-review handoff.
