# ADR 0001: Bootstrap Seat Topology

**Status:** accepted  
**Date:** 2026-09-19

## Decision

- **Seat 1:** Codex/OpenAI leads the bootstrap build. Astra handles architecture and synthesis, Sol handles difficult implementation or fallback architecture, and Terra/Luna handle bounded implementation work.
- **Seat 2:** Claude Pro remains an independent, bounded reviewer. Opus handles difficult adversarial review and Sonnet handles routine review/test work when available.
- **Seat 3:** the Radeon AI PRO R9700 32 GB hosts the local grunt seat through an OpenAI-compatible endpoint. Benchmark Qwen3.8-27B Q6 against Qwen3-Coder-30B-A3B Q4_K_M before pinning the model.
- **Seat 4:** disabled for v1.

Codex owns the first complete vertical slice. Claude is invoked once at the end for independent verification; the user does not manually shuttle files or intermediate reviews between agents.

## Why

The deciding constraint is sustained building capacity, not a claim that one vendor wins every model comparison. In observed use, the Codex subscription provided materially more usable build volume, while Claude Pro exhausted a much larger share of its allowance after only two review responses.

Codex also provides one subscription ladder for architecture, heavy implementation, ordinary coding, and volume work. Claude retains more value as the cross-vendor reviewer because independence reduces correlated blind spots.

The original Claude-lead recommendation was reasonable when Claude Code appeared to be the easiest orchestration hub and the comparison focused on maximum model breadth. It became the wrong operational choice once actual usage showed that the lead seat must prioritize throughput and finish the application before WarRoom can automate collaboration.

## Consequences

- Bootstrap work does not wait for Claude or the R9700 seat.
- Seat 1 must produce bounded tasks, tests, diffs, and reviewable artifacts rather than relying on self-certification.
- Claude review is valuable precisely because it is independent; it does not continuously co-author the first build.
- Seat 3 performs cheap, bounded work and never certifies its own output.
- The architecture must keep role-to-provider mappings configurable so a future model, plan, or policy change does not require a rewrite.

## Revisit when

- actual Codex limits prevent sustained implementation;
- Claude usage economics materially change;
- the local model proves capable enough to take a larger bounded workload;
- vendor CLI terms or supported automation surfaces change;
- WarRoom can run a controlled, repeatable bake-off without manual coordination.

## Historical evidence

The downloadable project handoff retains the initial Claude-lead brief, the revised Codex-lead brief, and the subsequent subscription comparison. They are decision evidence, not current authority.
