---
title: "The Claude Code experience, self-hosted"
excerpt: "How to run Claude Code against a self-hosted DeepSeek V3.2–class model using vLLM + LiteLLM, so agentic coding stays inside your perimeter."
publishDate: 2025-12-23
updatedDate: 2025-12-23
isFeatured: true
tags: [ "AI", "Engineering", "Consistency", "Claude Code", "DeepSeek" ]
seo:
  title: "Claude Code in your infra"
  description: "A practical setup for running Claude Code against a self-hosted umans-coder-v0 endpoint using vLLM and a LiteLLM gateway."
---

A new kind of developer tool has emerged over the past year. Claude Code, Codex CLI, and others. The pattern is similar: an agent that reads your codebase, makes edits across files, runs commands, and iterates when things break. The interaction feels different from autocomplete or chat.

Many teams can't use these tools. Security policies require code to stay inside the network. Compliance frameworks prohibit sending source code to external APIs. Client contracts explicitly forbid it. For these teams, the quality of the tool is irrelevant if the model endpoint is outside their perimeter.

The constraint isn't the agent. It's the model.

We put together a setup that runs Claude Code against a self-hosted model. The same approach works for other tools in this category. This post covers why we chose the model we did, how the pieces connect, and what we observed.

## Choosing a model for agentic coding

Not every capable model works well as a coding agent. Agentic coding requires a specific combination: the model needs to handle code generation, but it also needs to use tools reliably, maintain coherence across long interactions, and recover when something goes wrong. Models optimized for single-turn code completion often struggle when asked to operate as agents.

DeepSeek V3.2 is currently the strongest open-weights option for this use case. Their [technical report](https://arxiv.org/pdf/2512.02556) describes training specifically for agentic tasks, with a synthesis pipeline that generated prompts across code agents, search agents, and general tool-use scenarios. The results show up in benchmarks designed to measure this kind of work:

| Benchmark | DeepSeek V3.2 | Claude Sonnet 4.5 | GPT-5-High |
|-----------|---------------|-------------------|------------|
| SWE-bench Verified | 73.1% | 77.2% | 74.9% |
| SWE Multilingual | 70.2% | 68.0% | 55.3% |
| Terminal Bench 2.0 | 46.4% | 42.8% | 35.2% |
| τ²-Bench | 80.3% | 84.7% | 80.2% |

SWE-bench Verified is Python-only. SWE Multilingual covers the full language range, where DeepSeek outperforms the closed models. These benchmarks measure the ability to take a GitHub issue description and produce a working pull request, which is closer to real agent work than isolated code completion tasks.

Benchmark results can be gamed, and training data contamination is a real concern. Independent evaluations help validate these numbers. [SWE-rebench](https://swe-rebench.com/) runs continuously on new PRs specifically to resist contamination. [Artificial Analysis](https://artificialanalysis.ai/models?intelligence=agentic-index) runs these same benchmarks independently. Both rank DeepSeek V3.2 as the top open-weights model for agentic coding.

One practical consideration for self-hosting: DeepSeek V3.2 is a 671B mixture-of-experts model with 37B active parameters. A dense model of equivalent quality would be much larger and slower. Devstral 2, for example, is a dense 123B model that performs reasonably well on coding benchmarks. But because V3.2 only activates a fraction of its parameters per token, it runs roughly 3x faster at inference while having access to more total capacity. When you're paying for GPU time, this difference matters.

## Setup

We packaged the model as `umans-coder-v0` ([HuggingFace](https://huggingface.co/umans-ai/umans-coder-v0)). For text requests, it has the same capabilities as DeepSeek V3.2.

The architecture looks like this:

<iframe
  src="/blog/architecture_diagram.html"
  style="width: 100%; max-width:200%; height: 350px; border: none; background: transparent; transform: display: block; margin: 0 auto;"
  loading="lazy"
></iframe>

Claude Code expects to talk to an Anthropic-compatible API. The [gateway requirements](https://code.claude.com/docs/en/llm-gateway) specify what this means: the `/v1/messages` endpoint, the `/v1/messages/count_tokens` endpoint for token counting, and specific headers like `anthropic-beta` and `anthropic-version`.

[vLLM](https://github.com/vllm-project/vllm) now has an [Anthropic messages endpoint](https://docs.vllm.ai/en/stable/api/vllm/entrypoints/anthropic/), but it doesn't implement token counting or handle the required headers that Claude Code depends on. [LiteLLM](https://docs.litellm.ai/) fills this gap. It receives requests in the Anthropic format from Claude Code, translates them to the format vLLM expects, and handles the headers and endpoints that vLLM doesn't support natively.

## Deployment

We published Docker images built on our [vLLM fork](https://github.com/umans-ai/vllm). The primary runtime image is `umansai/vllm:0.1.2`.

It includes [DeepGEMM](https://github.com/deepseek-ai/DeepGEMM) for optimized inference on Hopper and Blackwell GPUs.

```bash
docker run --gpus all --rm --ipc=host -p 8000:8000 \
  -v /data:/data -e HF_HOME=/data/hf \
  umansai/vllm:0.1.2 \
  uv run vllm serve umans-ai/umans-coder-v0 \
    --host 0.0.0.0 --port 8000 \
    --tensor-parallel-size 8 \
    --tokenizer-mode deepseek_v32 \
    --tool-call-parser deepseek_v32 \
    --enable-auto-tool-choice \
    --reasoning-parser deepseek_v3
```

If you want interactive access (debugging, log inspection, manual launches), we also publish an SSH-enabled variant, `umansai/vllm:0.1.2-ssh`, which starts an `sshd` inside the container and lets you SSH in using your public key via environment variables in your platform template (useful on providers like Prime Intellect).

<!-- SCREENSHOT: Terminal showing model loading -->

We tested this on 8xH200 and 4xB300.

## Connecting Claude Code

Once the model is running, you need to configure LiteLLM and point Claude Code at it.

### LiteLLM configuration

<!-- TODO: Expand with full setup details -->

```yaml
model_list:
  - model_name: umans-coder
    litellm_params:
      model: openai/umans-ai/umans-coder-v0
      api_base: http://localhost:8000/v1
```

Start the proxy:

```bash
litellm --config config.yaml --port 4000
```

### Claude Code configuration

Point Claude Code at the LiteLLM proxy:

```bash
export ANTHROPIC_BASE_URL=http://localhost:4000
```

<!-- GIF: Claude Code session with umans-coder-v0, tool calls, file edits, the full loop -->

## What we observed

The workflow works. Multi-file edits, streaming responses, iterative debugging. The interface is unchanged since it's still Claude Code.

Capabilities land where the benchmarks suggest. Refactors, test generation, bug fixes all work. The model reasons through problems and recovers from errors. For agent frameworks that simulate tool calls via user messages, [DeepSeek's report](https://arxiv.org/pdf/2512.02556) notes that non-thinking mode tends to work better. Claude Code handles both modes.

<!-- SCREENSHOT: Multi-file edit completing successfully -->

## The remaining gap

The main thing missing is vision.

Claude Code's full workflow includes sending screenshots, mockups, and error traces. When you can show the agent what's wrong instead of describing it, the interaction changes.

DeepSeek V3.2 is text-only. Vision models exist in the open-weights space, but they're generally not at the same level on agentic coding tasks. Adding vision capabilities tends to come at the cost of performance on the tasks that matter for this use case.

We're working on closing that gap. The approach is to start from a strong agentic coding base and add vision without degrading the rest. `umans-coder-v0` is the foundation for that work.

More on that soon 👀.
