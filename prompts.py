"""
prompts.py
==========
The prompt bank for the adaptive-explanation study.

Structure (agreed with Dr Panda, Week 7):
  - 10 LLM 1 prompts (code-generation problems), complexity-graded.
  - Each LLM 1 prompt has 3 persona-adapted LLM 2 interpretation prompts
    (beginner / intermediate / senior)  ->  10 x 3 = 30 interpretation prompts.
  - Plus one GENERIC interpretation prompt per problem for the control condition
    (parked as possible future work; not part of the current adaptive-only study).

IMPORTANT (the core mechanism rule):
  LLM 2 never sees the original LLM 1 prompt. It receives ONLY the generated code
  plus the interpretation prompt below. The {code} placeholder is filled at run time
  with LLM 1's output.

The persona is folded into the interpretation prompt text. Each persona is given a
different *operation type* (analogy/trace, transformation, critique, etc.) so the
three explanations differ in kind, not just reading level.

FIX (data-integrity): Prompt 10's llm1 was reworded. It previously said
"Build an end-to-end pipeline ... and surface the key algorithmic and complexity
decisions", which led the Operator to return an ASCII architecture diagram instead
of code. It now explicitly requests runnable Python functions. (A uniform code-only
instruction is also appended to every llm1 at generation time in pregenerate.py.)
"""

PERSONAS = ["beginner", "intermediate", "senior"]

# The generic (control) instruction, identical for every problem, no persona.
GENERIC_INTERPRETATION = (
    "You are given a piece of code. Without any prior knowledge of the task it was "
    "written for, work out what it does and explain it clearly and completely.\n\n"
    "CODE:\n```\n{code}\n```"
)

# Each entry: id, a short label, the LLM 1 prompt, and the three persona prompts.
# LLM 2 prompts must NOT reveal the original task; they only reference "this code".
PROMPTS = [
    {
        "id": 1,
        "label": "Fibonacci",
        "llm1": "Write a function that computes the nth Fibonacci number.",
        "llm2": {
            "beginner": (
                "You are explaining a piece of code to a BEGINNER programmer. "
                "Read the code below and explain what it does using an everyday analogy, "
                "then trace it step by step for a small input, showing the values as they build up. "
                "Keep the language simple and define any terms you use.\n\nCODE:\n```\n{code}\n```"
            ),
            "intermediate": (
                "You are explaining a piece of code to an INTERMEDIATE programmer. "
                "Read the code below, state what it computes and its current time complexity, "
                "then provide a more efficient version and explain precisely why it is better.\n\nCODE:\n```\n{code}\n```"
            ),
            "senior": (
                "You are explaining a piece of code to a SENIOR engineer. "
                "Read the code below, then reconstruct the likely design reasoning: why implement it this way, "
                "what alternatives were probably rejected, and the complexity and memory trade-offs of each.\n\nCODE:\n```\n{code}\n```"
            ),
        },
    },
    {
        "id": 2,
        "label": "Duplicate finding (O(n^2) -> O(n))",
        "llm1": "Refactor an inefficient O(n^2) duplicate-finding function into an O(n) solution using a hash set.",
        "llm2": {
            "beginner": (
                "Explain this code to a BEGINNER. In plain steps, say what problem it solves, "
                "then predict its output for a small example list and describe what happens as it runs.\n\nCODE:\n```\n{code}\n```"
            ),
            "intermediate": (
                "Explain this code to an INTERMEDIATE programmer. Identify what it does, "
                "then propose two alternative approaches to the same problem and explain the trade-offs of each.\n\nCODE:\n```\n{code}\n```"
            ),
            "senior": (
                "Explain this code to a SENIOR engineer. Stress-test it: construct inputs that expose its weaknesses "
                "(very large inputs, unhashable elements, heavy collisions) and explain the time and memory behaviour under each.\n\nCODE:\n```\n{code}\n```"
            ),
        },
    },
    {
        "id": 3,
        "label": "Recursion -> iteration + dictionary lookup",
        "llm1": "Reimplement a recursive function iteratively to avoid stack overflow, and replace a list-based lookup with a dictionary/hash-map.",
        "llm2": {
            "beginner": (
                "Explain this code to a BEGINNER. Say what it does, then answer three questions a learner would ask: "
                "why loop instead of calling itself? why use a lookup table? what would break in the old version? Use a simple analogy.\n\nCODE:\n```\n{code}\n```"
            ),
            "intermediate": (
                "Explain this code to an INTERMEDIATE programmer. Confirm what it does, then change the lookup to guaranteed O(1) "
                "where possible and explain how the iterative structure removes the risk of stack overflow.\n\nCODE:\n```\n{code}\n```"
            ),
            "senior": (
                "Review this code as a SENIOR engineer. Assess correctness, unhandled edge cases, naming, error handling, "
                "and whether the data-structure choice is appropriate, giving specific improvements.\n\nCODE:\n```\n{code}\n```"
            ),
        },
    },
    {
        "id": 4,
        "label": "Binary search vs linear",
        "llm1": "Implement binary search over a large sorted dataset and contrast its complexity and memory profile with linear search.",
        "llm2": {
            "beginner": (
                "Explain this code to a BEGINNER. Say what it searches for, then trace it on a small sorted array searching for the last element, "
                "counting how many comparisons it makes and why.\n\nCODE:\n```\n{code}\n```"
            ),
            "intermediate": (
                "Explain this code to an INTERMEDIATE programmer. Identify the algorithm, then say what to use instead when the data is not sorted, "
                "and explain the trade-offs (sorting cost, hash lookup, memory) between the options.\n\nCODE:\n```\n{code}\n```"
            ),
            "senior": (
                "Analyse this code as a SENIOR engineer. Identify where it breaks: mid-point overflow on huge indices, behaviour on an empty array "
                "or absent target, and concurrent modification of the data. Explain each failure and how to guard against it.\n\nCODE:\n```\n{code}\n```"
            ),
        },
    },
    {
        "id": 5,
        "label": "Fetch, compare, visualise",
        "llm1": "Write code that fetches data from an external source, compares it against an analysis published elsewhere, and visualises the comparison.",
        "llm2": {
            "beginner": (
                "Explain this code to a BEGINNER. Walk through what it does from start to finish in plain language: "
                "where it gets data, what it compares, and what the chart shows.\n\nCODE:\n```\n{code}\n```"
            ),
            "intermediate": (
                "Explain this code to an INTERMEDIATE programmer. Identify the stages, then review it for robustness: "
                "where could it fail (network, missing fields, empty data), and what error handling would you add?\n\nCODE:\n```\n{code}\n```"
            ),
            "senior": (
                "Analyse this code as a SENIOR engineer. Separate the concerns (retrieval, transformation, comparison, presentation) "
                "and critically assess whether the comparison metric and the chosen visualisation are statistically appropriate.\n\nCODE:\n```\n{code}\n```"
            ),
        },
    },
    {
        "id": 6,
        "label": "Clean + grouped statistics",
        "llm1": "Build a data pipeline that ingests a dataset, cleans missing/malformed values, and computes grouped summary statistics with appropriate data structures.",
        "llm2": {
            "beginner": (
                "Explain this code to a BEGINNER. Using a simple analogy for 'tidying up', explain what it does to the data "
                "and what summary it ends up producing.\n\nCODE:\n```\n{code}\n```"
            ),
            "intermediate": (
                "Explain this code to an INTERMEDIATE programmer. Identify the cleaning and grouping strategy, then propose an alternative "
                "cleaning approach (e.g. imputation vs dropping) and explain the trade-off.\n\nCODE:\n```\n{code}\n```"
            ),
            "senior": (
                "Analyse this code as a SENIOR engineer. Critically assess how the handling of missing and malformed values could bias the "
                "resulting statistics, and explain what a reviewer should check before trusting the output.\n\nCODE:\n```\n{code}\n```"
            ),
        },
    },
    {
        "id": 7,
        "label": "Reconcile two APIs",
        "llm1": "Retrieve data from two public APIs, reconcile them on a common key, and compute a derived comparison metric, handling rate limits and errors.",
        "llm2": {
            "beginner": (
                "Explain this code to a BEGINNER. In plain language, say what two things it brings together and what it works out, "
                "including what it does when a request fails.\n\nCODE:\n```\n{code}\n```"
            ),
            "intermediate": (
                "Explain this code to an INTERMEDIATE programmer. Identify the join and the metric, then propose an alternative reconciliation "
                "strategy (e.g. a different join type or matching rule) and explain when it would be preferable.\n\nCODE:\n```\n{code}\n```"
            ),
            "senior": (
                "Analyse this code as a SENIOR engineer. Stress the reconciliation: duplicate keys, missing matches, one API failing, or rate limits "
                "hit mid-run. Evaluate the correctness of the derived metric under each and the robustness of the retry/error handling.\n\nCODE:\n```\n{code}\n```"
            ),
        },
    },
    {
        "id": 8,
        "label": "Caching layer",
        "llm1": "Implement a caching layer over a repeated expensive computation and explain the time/space trade-off it introduces.",
        "llm2": {
            "beginner": (
                "Explain this code to a BEGINNER. Using an everyday analogy for 'remembering past answers', explain what it speeds up "
                "and what the downside is.\n\nCODE:\n```\n{code}\n```"
            ),
            "intermediate": (
                "Explain this code to an INTERMEDIATE programmer. Identify the caching mechanism, then add a sensible eviction policy "
                "(e.g. a size limit or expiry) and explain why unbounded caching is risky.\n\nCODE:\n```\n{code}\n```"
            ),
            "senior": (
                "Review this code as a SENIOR engineer. Assess thread-safety, when the cache could return stale results, its memory footprint, "
                "and the conditions under which caching would actually hurt performance.\n\nCODE:\n```\n{code}\n```"
            ),
        },
    },
    {
        "id": 9,
        "label": "ETL routine",
        "llm1": "Write a small ETL routine that extracts records from an external source, transforms them under a non-trivial rule set, loads them into a structured store, and validates integrity.",
        "llm2": {
            "beginner": (
                "Explain this code to a BEGINNER. Walk through what it moves and changes, stage by stage, and explain how it checks "
                "that nothing went wrong.\n\nCODE:\n```\n{code}\n```"
            ),
            "intermediate": (
                "Explain this code to an INTERMEDIATE programmer. Identify the ETL stages, then add one additional validation rule that would "
                "improve data integrity and explain what failure it guards against.\n\nCODE:\n```\n{code}\n```"
            ),
            "senior": (
                "Analyse this code as a SENIOR engineer. Reconstruct why the transformation rules are structured this way, scrutinise them for "
                "edge cases, and assess whether the integrity checks are sufficient for the target store.\n\nCODE:\n```\n{code}\n```"
            ),
        },
    },
    {
        "id": 10,
        "label": "End-to-end pipeline",
        "llm1": (
            "Write complete, runnable Python code for a script that retrieves data from multiple "
            "sources (for example a CSV/API source, a database source, and a JSON source), performs "
            "a statistical comparison of the combined data against a published baseline, and produces "
            "a visualisation of the result. Implement each stage (retrieval, merge, comparison, "
            "visualisation) as actual Python functions."
        ),
        "llm2": {
            "beginner": (
                "Explain this code to a BEGINNER. Give the big picture of what it does from beginning to end in plain language, using an analogy, "
                "and explain what the final result tells us.\n\nCODE:\n```\n{code}\n```"
            ),
            "intermediate": (
                "Explain this code to an INTERMEDIATE programmer. Identify each stage and the statistical comparison used, then propose an alternative "
                "architecture for the pipeline and explain the trade-offs.\n\nCODE:\n```\n{code}\n```"
            ),
            "senior": (
                "Analyse this code as a SENIOR engineer. Provide a full architectural read: decompose the stages, judge whether the statistical "
                "comparison against the baseline is valid, locate the complexity hot-spots, and identify the failure modes scale would expose.\n\nCODE:\n```\n{code}\n```"
            ),
        },
    },
]

# All 10 prompts are available to every persona. The persona changes only the
# EXPLANATION shown (each prompt keeps beginner/intermediate/senior variants).
#
# Each participant sees 2 prompts, drawn from their persona's ALLOWED RANGE, with at
# least one prompt from the persona's CORE sub-range (so the pair is complexity-
# appropriate for their level). Ranges are inclusive prompt ids.
PERSONA_RANGES = {
    #            full range each persona draws BOTH prompts from   |  core: >=1 must come from here
    "beginner":     {"allowed": list(range(1, 7)),  "core": list(range(1, 4))},   # 1-6, >=1 from 1-3
    "intermediate": {"allowed": list(range(4, 11)), "core": list(range(4, 11))},  # 4-10
    "senior":       {"allowed": list(range(7, 11)), "core": list(range(7, 11))},  # 7-10
}

ALL_IDS = [p["id"] for p in PROMPTS]

assert len(PROMPTS) == 10, "There must be exactly 10 LLM 1 prompts."
for p in PROMPTS:
    assert set(p["llm2"].keys()) == set(PERSONAS), f"Prompt {p['id']} missing a persona variant."
for _persona, _r in PERSONA_RANGES.items():
    assert set(_r["core"]).issubset(set(_r["allowed"])), f"{_persona} core must be within allowed."
    assert len(_r["allowed"]) >= 2, f"{_persona} needs at least 2 prompts to choose from."
