# Warroom

A multi-operator AI **war room**. Warroom convenes a panel of AI *operators* in
fixed roles — an **architect**, an **adversarial reviewer**, a cheap **local**
model, and an optional pluggable **fourth seat** — and drives a task through
deterministic debate rounds, emitting an auditable transcript plus a final
artifact.

The point is *uncorrelated judgment*: a strong model proposes, a
different-family model attacks, and the run only converges when the **adversary**
certifies "no material objection" — not when the author declares itself done.

> **Status: docs + runnable scaffold.** The engine, config, transcript,
> termination, and CLI are real and run end-to-end against a process-free fake
> panel. The three provider adapters (Claude Code, Codex, Ollama/cloud HTTP)
> ship as **stubs** with real `health_check()` and real parsing, marked
> `# TODO(real)`, so this can be handed to OpenAI **Codex** for adversarial
> review before the live transports land. See
> [`docs/05-codex-review-brief.md`](docs/05-codex-review-brief.md).

## The panel

| Role | Operator | Transport | Cost |
|---|---|---|---|
| **Architect** | Claude **Fable 5** (Max 5x seat) | Claude Code CLI, headless | flat seat |
| **Adversary** | **GPT "Sol"** (ChatGPT Plus seat) | Codex CLI `codex exec` | flat seat |
| **Local** | open model on a 32 GB GPU | Ollama OpenAI-compatible HTTP | local |
| **Fourth** *(off by default)* | cloud API **or** 2nd-GPU model | HTTP OpenAI-compatible | metered if cloud |

Runs on an **AMD Radeon AI PRO R9700** (32 GB) — **locked in 2026-08-04**
(reserved at a locked price; in hand 2026-08-05), chosen over the Intel Arc Pro
B70 alternative (that overlay is kept for reference).
See [`docs/02-operators-and-models.md`](docs/02-operators-and-models.md) and
[`docs/03-hardware-substrate.md`](docs/03-hardware-substrate.md).

## Quick start (offline, no external processes)

```bash
pip install -e .            # core deps: pydantic + pyyaml
warroom --panel fake doctor
warroom --panel fake run "Design a rate limiter for a homelab API gateway"
# -> writes runs/<ts>-<slug>/{final_artifact.md,transcript.jsonl,run_report.md}
```

`--panel fake` swaps every operator for the scripted fake adapter, so the whole
round loop, termination, and reporting run with zero CLIs or GPUs. Drop the flag
once the real seats are wired.

## How it works (one paragraph)

Operators share no memory, so the orchestrator **is** the memory: every turn is
appended to a canonical JSONL transcript, and each operator's prompt is rebuilt
from it every turn (the current artifact verbatim + attributed discussion). The
[`RoundEngine`](src/warroom/engine/round_engine.py) walks an explicit phase
sequence — `PROPOSE → CRITIQUE → REVISE → [ARBITRATE] → GATE`, repeated up to
`max_rounds` — then `SYNTHESIZE`. A rate-capped seat returns `UNAVAILABLE` and is
skipped, not fatal, as long as quorum (architect + ≥1 critic) holds. Full design
in [`docs/01-architecture.md`](docs/01-architecture.md).

## Repo layout

```
docs/            design, use cases, model + hardware choices, shortcomings, Codex brief
charters/        role system prompts (architect, adversary, local, fourth)
operators.yaml   the panel (+ fourth-slot variants)
warroom.yaml     run policy (rounds, budgets, compaction, termination)
deploy/          ROCm Ollama overlay (live, R9700) + Intel-Arc overlay (reference)
src/warroom/     the package (adapters, engine, config, cli, report)
tests/           config, transcript, termination, CLI-parsing tests
```

## Substrate

Warroom is the orchestration layer on top of the **EchoTechAIStack** substrate
(Ollama + Open WebUI + ComfyUI, Tailscale-only). It only needs Ollama's HTTP
endpoint, so a GPU swap never touches orchestrator code — but the substrate's
stock GPU overlay is **NVIDIA-only** and must be replaced with the ROCm overlay
in [`deploy/`](deploy/) for the R9700. Details in
[`docs/03-hardware-substrate.md`](docs/03-hardware-substrate.md).

## License

MIT.
