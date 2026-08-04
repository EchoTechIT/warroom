# 03 — Hardware & Substrate

## The substrate

Warroom runs on top of **EchoTechAIStack**: a Docker-Compose stack of **Ollama**
(OpenAI-compatible LLM API on `:11434`) + **Open WebUI** (`:3000`) + **ComfyUI**
(`:8188`), reachable only over a **Tailscale** tailnet, with **no auth on the
Ollama API**. Warroom only needs the Ollama HTTP endpoint, so it is
**transport-decoupled from GPU provisioning** — a GPU swap never touches
orchestrator code.

Warroom inherits the tailnet-only security posture: it adds no auth of its own,
and assumes the Ollama endpoint is reachable only on the tailnet/LAN. Keep the
host off the public internet.

## The gap: the stock GPU overlay is NVIDIA-only

EchoTechAIStack's `docker-compose.gpu.yml` reserves GPUs with:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

That path is **NVIDIA Container Toolkit-specific**. On an Intel Arc or an AMD
ROCm card it binds nothing and Ollama **silently falls back to CPU** — slow, and
easy to miss. The replacement overlays ship in this repo under
[`deploy/`](../deploy/).

## AMD Radeon AI PRO R9700 (RDNA4 / gfx1201) — THE card (locked in 2026-08-04)

- 32 GB GDDR6, native **ROCm**. Goes into the **Unraid box** (the sold 5060 Ti's
  slot) — the fleet's only dGPU. In hand 2026-08-05, install pending.
- RDNA4 needs ROCm ≥ 6.4. In the container path that means the *image's* ROCm
  (`ollama/ollama:rocm` bundles its userspace); the host only needs the in-kernel
  `amdgpu` driver, which Unraid ships.
- Use [`deploy/ollama.rocm.yml`](../deploy/ollama.rocm.yml): the `ollama/ollama:rocm`
  image, `/dev/kfd` + `/dev/dri` devices, `video`/`render` groups. No
  `deploy.resources` block (that's NVIDIA-only).
- `HSA_OVERRIDE_GFX_VERSION` may be needed until ROCm ships native RDNA4 tuning;
  leave it unset first, add it only if the model won't load on GPU.

```bash
COMPOSE_FILE=docker-compose.yml:ollama.rocm.yml docker compose up -d
```

## Intel Arc Pro B70 (Battlemage / Xe2) — NOT purchased, kept for reference

The B70 was the cheaper alternative; the R9700 was bought instead (see
[`02-operators-and-models.md`](02-operators-and-models.md) for the rationale).
This section and its overlay stay as reference in case an Arc card ever joins
the fleet.

- 32 GB ECC GDDR6, ~608 GB/s.
- **The SYCL fast path is DEAD (verified 2026-08-04, part of why the B70
  lost).** Earlier drafts of this doc recommended IPEX-LLM's SYCL backend as
  "roughly 2× faster" than Vulkan on Arc — but `intel/ipex-llm` was **archived
  read-only on 2026-01-28**, with Intel's notice: no maintenance, no patches
  accepted, and *"identified as having known security issues"* (last real
  updates ~May 2025). IPEX itself (`intel-extension-for-pytorch`) was
  discontinued after 2.8 — features upstreamed into PyTorch, maintenance ended
  March 2026.
- **The realistic Arc path is therefore upstream `ollama/ollama` ≥ 0.12.11 with
  the Vulkan backend** and `/dev/dri` passed through — see
  [`deploy/ollama.intel.yml`](../deploy/ollama.intel.yml). Do not deploy the
  archived IPEX-LLM images. Intel's remaining first-party consumer AI story
  (AI Playground) is **Windows-only** — irrelevant to a headless Linux/Unraid
  fleet, which is why post-IPEX Arc is effectively community-supported here.

```bash
COMPOSE_FILE=docker-compose.yml:ollama.intel.yml docker compose up -d
```

## Verifying the GPU is actually used

A reachable Ollama endpoint is **not** proof the GPU is bound. `warroom doctor`
health-checks reachability; the real GPU check (a `# TODO(real)` once transports
land) is a trivial generation whose latency/logs confirm GPU, not CPU, execution.
Until then, verify manually:

```bash
docker compose exec ollama ollama run qwen3.6-27b "ok" --verbose   # check eval rate
# or watch the GPU: `rocm-smi` (AMD) / `intel_gpu_top` (Intel) during a generation
```

## Second GPU (the fourth-slot hardware option)

Adding a second 32 GB card lets the fourth operator run **locally** instead of in
the cloud: bring up a second Ollama instance on another port (e.g. `:11435`)
bound to the second card, and point `operators.yaml`'s `fourth.variants.second_gpu.http.base_url`
at it. Prefer a *different model family* than the primary local seat for panel
diversity.
