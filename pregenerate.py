"""
pregenerate.py
==============
Runs the two-LLM mechanism ONCE, offline, to produce a frozen set of stimuli
(stimuli.json) that the study interface then serves. Pre-generating means every
participant sees an identical, vetted explanation for a given (prompt, persona),
which is what a controlled comparison needs.

The full mechanism is still built and exercised here -- pre-generation just freezes
its outputs for the study. Set LIVE = False to produce placeholder outputs so you
(and the interface) can run end-to-end without an API key; set LIVE = True to call
the real Claude API.

Mechanism (per the agreed design):
  Stage 1 (Context A): LLM 1 receives the LLM 1 prompt -> generates code.
  Stage 2 (Context B, fresh call): LLM 2 receives ONLY the generated code + an
           interpretation prompt (persona folded in) -> returns an explanation.
  The two stages are separate API calls with NO shared history.

Output: stimuli.json  ->  { prompt_id: { "llm1_prompt", "code",
                              "explanations": { persona: text, ... "generic": text } } }
"""

import json
import os
from prompts import PROMPTS, PERSONAS, GENERIC_INTERPRETATION

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
LIVE = True   # True = call the real Claude API (needs ANTHROPIC_API_KEY). False = mock text.

# BOTH stages use the SAME model (supervisor's requirement). Using one model isolates
# the effect of the persona-adapted PROMPT from any difference in model capability: if
# LLM 1 and LLM 2 were different models, a difference in explanation quality could be
# due to the models rather than the adaptation. The separation between the two stages
# is CONTEXTUAL -- LLM 2 never sees LLM 1's prompt -- not a difference in model.
#
# Set MODEL to the single Claude model you are using. Verify the exact string in the
# Anthropic Console before running (model IDs change). Current options include
# "claude-opus-4-8" (most capable) or "claude-sonnet-4-6" (faster/cheaper, very capable).
MODEL = "claude-opus-4-8"

LLM1_MODEL = "claude-opus-4-8"   # do not change independently -- both stages must match
LLM2_MODEL = "claude-opus-4-8"   # do not change independently -- both stages must match

MAX_TOKENS = 1500
OUTPUT_PATH = "stimuli.json"


# ----------------------------------------------------------------------------
# LLM CALLS
# ----------------------------------------------------------------------------
def _client():
    from anthropic import Anthropic
    return Anthropic()  # reads ANTHROPIC_API_KEY from the environment


def call_claude(model: str, prompt: str) -> str:
    """A single, self-contained Claude call (its own context)."""
    if not LIVE:
        # MOCK output so the pipeline and interface are runnable without a key.
        return f"[MOCK OUTPUT]\n\n{prompt[:280]}..."
    client = _client()
    resp = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    # Concatenate any text blocks in the response.
    return "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")


def extract_code(text: str) -> str:
    """Pull the code out of LLM 1's response (first fenced block if present)."""
    if "```" in text:
        parts = text.split("```")
        # parts[1] is the first fenced block; strip an optional language tag on line 1.
        block = parts[1]
        lines = block.splitlines()
        if lines and lines[0].strip().isalpha():
            lines = lines[1:]
        return "\n".join(lines).strip()
    return text.strip()


# ----------------------------------------------------------------------------
# STAGE 1 + STAGE 2
# ----------------------------------------------------------------------------
def generate_code(llm1_prompt: str) -> str:
    """Stage 1 (Context A): generate code from the original problem prompt."""
    raw = call_claude(LLM1_MODEL, llm1_prompt)
    return extract_code(raw)


def interpret(code: str, interpretation_prompt: str) -> str:
    """Stage 2 (Context B, fresh call): interpret code only -- no original prompt."""
    filled = interpretation_prompt.format(code=code)
    return call_claude(LLM2_MODEL, filled)


# ----------------------------------------------------------------------------
# DRIVER
# ----------------------------------------------------------------------------
def build_stimuli() -> dict:
    stimuli = {}
    for p in PROMPTS:
        pid = p["id"]
        print(f"Prompt {pid}: {p['label']}")
        code = generate_code(p["llm1"])

        explanations = {}
        # all three persona explanations (any prompt may be shown to any persona)
        for persona in PERSONAS:
            print(f"  - {persona}")
            explanations[persona] = interpret(code, p["llm2"][persona])
        # generic control condition
        print("  - generic (control)")
        explanations["generic"] = interpret(code, GENERIC_INTERPRETATION)

        stimuli[str(pid)] = {
            "llm1_prompt": p["llm1"],
            "label": p["label"],
            "code": code,
            "explanations": explanations,
            "models": {"llm1": LLM1_MODEL, "llm2": LLM2_MODEL},
            "live": LIVE,
        }
    return stimuli


def main():
    assert LLM1_MODEL == LLM2_MODEL, (
        "LLM1_MODEL and LLM2_MODEL must be the SAME model (set via MODEL). "
        "Using different models would confound the study."
    )
    print(f"Using single model for both stages: {MODEL}\n")
    stimuli = build_stimuli()
    with open(OUTPUT_PATH, "w") as f:
        json.dump(stimuli, f, indent=2)
    mode = "LIVE (real Claude API)" if LIVE else "MOCK (placeholder text)"
    print(f"\nWrote {OUTPUT_PATH} for {len(stimuli)} prompts in {mode} mode.")
    if not LIVE:
        print("Set LIVE = True and export ANTHROPIC_API_KEY to generate real explanations.")


if __name__ == "__main__":
    main()
