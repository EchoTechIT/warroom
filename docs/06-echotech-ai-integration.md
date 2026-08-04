# 06 — EchoTech AI Integration (the seat map)

*Added 2026-08-04. How Warroom fits the wider EchoTech AI strategy: which seats
exist, what hardware backs them, what routes where, and when a panel is worth
convening. Companion doc on the homelab side:
`echotech-homelab/runbooks/claude-collab-playbook.md`.*

## Fleet reality (2026-08-04)

The fleet consolidated to **two boxes, one GPU**:

- **Unraid box** — Radeon **AI PRO R9700 32GB** (RDNA4/gfx1201, ROCm ≥ 6.4).
  The fleet's only GPU; hosts Ollama + Open WebUI, KoboldCpp, and ComfyUI.
  The gaming PC (with its 9070 XT) and the displaced RTX 5060 Ti were **sold** —
  the fleet is **CUDA-free**.
- **OptiPlex** — no GPU. Control plane: LiteLLM router, SillyTavern, and the
  natural host for the Warroom runner (it needs no GPU, only the CLIs + HTTP).

Consequences for this repo:

- The README's "Intel Arc Pro B70 **or** AMD R9700" framing is resolved:
  **deployed = R9700**. The Intel overlay in `deploy/` stays as a portable
  reference, nothing more.
- The **substrate compose is canonical in the homelab repo** at
  `echotech-homelab/compose/echotechai/` (Ollama `:rocm` image, `/dev/kfd` +
  `/dev/dri`, `OLLAMA_KEEP_ALIVE` tuned short). Earlier references to the
  EchoTechAIStack repo predate this — that repo remains superseded scratch.
  `deploy/ollama.rocm.yml` here is the same wiring as an overlay, kept for
  portability; the NVIDIA-only-overlay gap it patched no longer applies anywhere
  in the fleet.
- The **second-GPU fourth-seat variant is dead hardware-wise**: both Unraid PCIe
  slots are full (R9700 + HBA) and there is no second box with a slot. The
  realistic fourth chair is the **cloud variant (DeepSeek, metered, budget-gated
  by `max_cost_usd`)**. Keep `second_gpu` in `operators.yaml` as config — it
  costs nothing and revives if Phase-2+ hardware appears.

## The three tiers (and the rule that keeps accounts alive)

| Tier | Backed by | Warroom seat | Access path |
|---|---|---|---|
| Frontier, flat-rate | Claude **Max 5x** · ChatGPT **Plus** | Architect · Adversary | **Their own CLIs only** — Claude Code headless `-p`, Codex `exec` |
| Local, free | R9700 via Ollama | Local (default `qwen3.6-27b` Q6_K ≈ 22 GB) | OpenAI-compat HTTP `:11434` |
| Metered cloud | API keys (DeepSeek first) | Fourth (tiebreaker) | HTTP via LiteLLM/direct, budget-gated |

**Never route the Max or Plus subscriptions through LiteLLM or any custom API
surface.** Subscription ≠ API product; proxying is the ToS violation that gets
accounts flagged. Warroom is *already built correctly* for this — both frontier
seats are driven through their native CLIs. Keep it that way in every future
adapter.

## Shared-resource constraints (new since consolidation)

1. **The local seat shares the R9700 with the roleplay stack** (KoboldCpp +
   ComfyUI). Qwen3.6-27B Q6_K (~22 GB) does not coexist with a loaded roleplay
   model. Operational rule: **don't convene a panel during a roleplay session**,
   and keep Ollama's `keep_alive` short so the seat releases VRAM when idle.
   A rate-capped/unloadable local seat is already survivable — the engine
   treats `UNAVAILABLE` as skip-not-fatal while quorum holds — but don't make
   that the normal path.
2. **The architect seat shares the Max 5x pool with Connor's own Claude Code
   sessions.** Panels are decision-grade tools, not background noise: budget a
   run like you'd budget an Opus session. Don't schedule unattended recurring
   panels on a 5x plan.
3. **CPU fallback is silent on AMD.** Any Ollama misconfig (missing `/dev/kfd`,
   an nvidia-style `deploy.resources` block) degrades to CPU without erroring.
   `warroom doctor`'s planned GPU check (`# TODO(real)`) should land before the
   first serious panel; until then verify with `rocm-smi` during a generation.

## When to convene a panel

Warroom earns its overhead on **expensive-to-reverse, judgment-heavy decisions**
where uncorrelated review changes the answer — not on implementation work
(that's a normal Claude Code session).

Standing candidates from the homelab's open-items list, in rough order of value:

1. **Phase-2 gateway:** Omada ER707-M2 (+AP) vs keep Flint 3 — perfect inaugural
   run once real adapters land (bounded, well-documented, genuinely contested).
2. **Backup redesign:** post-consolidation offsite strategy (Proton-Beta risk,
   the lost gaming-PC local target, the parents'-site candidate).
3. **Phase-2 network cutover plan:** MoCA topology + fiber transition sequencing.
4. **SSO choice** (Authentik vs Authelia) when Phase 2 opens it.

Anti-candidates: compose authoring, deploy debugging, anything the repo's locked
decisions already answer.

## Roadmap (unchanged order, updated context)

1. **Codex adversarial review of this scaffold** (`docs/05-codex-review-brief.md`)
   — eat the dogfood before wiring transports.
2. Land the three real adapters (Claude Code CLI, Codex CLI, Ollama HTTP) against
   the R9700 substrate.
3. Real GPU check in `warroom doctor` (latency/log-based, not reachability).
4. First live run: the Phase-2 gateway question.
5. Then consider: ntfy notification on run completion (the OptiPlex already runs
   ntfy `:8090`), and a `warroom-ops` skill in the homelab repo so Claude sessions
   know how and when to convene panels.
