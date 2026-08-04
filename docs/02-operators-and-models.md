# 02 — Operators & Model Selection

## The roster (and why each)

| Role | Model | Why this model | Driven by |
|---|---|---|---|
| Architect | **Claude Fable 5** | strongest reasoner owns the artifact | Claude Code CLI (Max 5x seat) |
| Adversary | **GPT "Sol"** | *different family* → uncorrelated errors | Codex CLI (ChatGPT Plus seat) |
| Local | **Qwen3.6-27B** (Q6_K) | best quality/headroom on 32 GB, Apache-2 | Ollama HTTP |
| Fourth | DeepSeek *or* 2nd-GPU model | tiebreak/specialist, family diversity | HTTP OpenAI-compatible |

**Why cross-family matters.** A review panel's whole value is *uncorrelated
failure modes*. Two models from the same lineage tend to miss the same things.
The architect (Anthropic) and adversary (OpenAI) are deliberately different
families; the fourth slot, when local, should be a *third* family again (e.g.
`gpt-oss` if the primary local is Qwen).

Gemini was dropped from the roster by choice.

## Hardware sizing (the card is 32 GB)

**DECIDED 2026-08-04 — purchased: AMD Radeon AI PRO R9700** (32 GB GDDR6,
RDNA4/gfx1201, ~640 GB/s). The full field at the $1000–1300 price point:

| Option | Price | Killed by |
|---|---|---|
| Intel Arc Pro B70 (32 GB ECC) | ~$1000 | slower VRAM (~608 GB/s), far thinner software adoption, and Intel's AI software push visibly slowing (IPEX being abandoned) — while AMD is actively improving ROCm |
| Used RTX 3090 (24 GB) | ~$1200 | 24 GB on a heavily-used 5-year-old card = absurd long-term risk |
| **R9700 (32 GB)** | ~$1300 | — **bought** |

The premium bought **runtime breadth and a live, improving software path**:
ROCm *and* Vulkan both just work across the stack (Ollama, llama.cpp/KoboldCpp,
ComfyUI), including inside Unraid Docker where the card lives — and the
worst-case fallback is a plain Ubuntu VM with the card passed through. Arc is
rough even on bare Windows/Ubuntu, let alone Unraid Docker, and its fast path
(IPEX-LLM/SYCL) is a third toolchain whose vendor commitment is now in doubt.
Model sizing below is unchanged (the envelope was 32 GB either way).

32 GB VRAM sets the local-model envelope. Rough Q4/Q5/Q6 footprints:

| Model | Quant | ~VRAM | Fit on 32 GB | Notes |
|---|---|---|---|---|
| **Qwen3.6-27B** | Q6_K | ~22 GB | ✅ comfortable | **default** — quality + headroom for context |
| Qwen3.6-27B | Q4_K_M | ~17 GB | ✅ | more context / faster, slightly lower quality |
| **gpt-oss-20b** | Q8 | ~16 GB | ✅ | **agentic alt** — cleaner tool calls, big context |
| Qwen-Coder-32B class | Q4_K_M | ~20 GB | ✅ | if the local role is coding-heavy |
| Llama-3.3-70B / Qwen-70B | Q3/Q4 | ~34–40 GB | ⚠️ tight/over | 2nd-GPU or heavy offload only |

**Recommendation:**
- **Default local operator → `qwen3.6-27b` @ Q6_K.** Best all-round pick on 32 GB;
  strong coding + reasoning; leaves room for a large context window.
- **Agentic/tool-driven local work → `gpt-oss-20b` @ Q8.** Choose this when the
  local seat runs tool loops rather than prose critique.

## The fourth slot

Off by default (keeps runs cheap and fast). Two dials in `operators.yaml`:

- `enabled: true|false` — on the panel at all.
- `variant: cloud_api | second_gpu` — which backing it uses.

And a `mode`:

- `tiebreaker` — invoked only at a near-deadlock (architect and adversary still
  disagree near the round cap). It renders a decision the architect must honor.
- `specialist` — invoked in CRITIQUE for a domain angle (e.g. DeepSeek for a
  math/algorithm deep-dive).
- `off` — three-operator panel.

**Cloud variant** → DeepSeek reasoner via API: cheap, strong, and a *third*
family for diversity. It is the only **metered** operator; `max_cost_usd` gates
it and it defaults to at-most-once (`tiebreaker`) invocation.

**Second-GPU variant** → a different-family model on a second 32 GB card, served
by a second Ollama instance (e.g. `:11435`). Unmetered; adds panel diversity
without cloud spend.

Because the fourth slot is just another `OperatorAdapter`, switching cloud ↔
second-GPU is a one-line config change; the engine is oblivious.

## Model-version drift

`claude-fable-5`, `gpt-sol`, and the Ollama tags will move. They are **config
values, not code constants** (`operators.yaml`), and `warroom doctor` reports
each operator's live `model_id` so a silent swap is visible. The CLI output
parsers are covered by golden-file tests so a format change fails loudly rather
than poisoning the transcript.
