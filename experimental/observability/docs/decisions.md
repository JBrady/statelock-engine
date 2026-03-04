# Decisions

## Deterministic token_count_est

The MVP uses one deterministic tokenizer for span sizing, budget pruning, and test assertions.

1. Normalize text by collapsing all whitespace runs to a single ASCII space.
2. Tokenize with regex `\\w+|[^\\w\\s]`.
3. `token_count_est` is the exact number of produced regex tokens.
4. `token_count_est` for assembled contexts is computed from final rendered context text.

This keeps behavior debuggable and stable across environments without model-specific tokenizers.

## Telemetry dual snapshots

When ablation is scheduled, telemetry writes two rows with a shared `run_group_id`:

1. `method=grad_proxy` with `proxy_kind` set.
2. `method=ablation_kl` with `proxy_kind=null`.

Dashboard labels proxy rows as `Proxy (<proxy_kind>)` and ablation rows as `Measured (ablation_kl)`.

## KL definition

KL ablation is computed on first-token softmax distributions:

- Baseline: `p = softmax(logits(Z))`
- Ablated span `i`: `q_i = softmax(logits(Z\\i))`
- Influence: `I_i = KL(p || q_i)`
- Normalize: `w_i = I_i / sum(I)`

with epsilon `1e-12` for numeric stability.
