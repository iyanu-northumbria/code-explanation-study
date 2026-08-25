# Adaptive Explanations of LLM-Generated Code — Study Scaffold

A runnable starting codebase for the two-LLM mechanism and the participant study
interface. Built on the **pre-generation** model (explanations are generated once,
offline, then served to every participant identically), with a single flag to switch
to live generation if needed.

## Files

|---|---|
| `prompts.py` | The 10 LLM 1 prompts, each with 3 persona-adapted LLM 2 prompts + a generic control prompt. |
| `pregenerate.py` | Runs the two-LLM mechanism offline and writes `stimuli.json` (the explanations). |
| `stimuli.json` | The generated stimuli the interface serves (currently MOCK placeholders). |
| `app.py` | The Streamlit participant interface: assigns prompts, shows code + explanation, hands off to MS Forms. |
| `requirements.txt` | Dependencies. |

## The mechanism (what happens)

 **Stage 1 (Context A):** LLM 1 gets a problem prompt → generates code.
 **Stage 2 (Context B):** LLM 2 gets **only the code** plus an
   interpretation prompt (to personalise for the participant profile ) → produces an explanation. LLM 2 never
   sees the original task, so it must reverse-engineer and verify the code itself.

Both are Claude models; the two stages are separate API calls with no shared history
(same model but different instances/context).

## Quick start (no API key needed)

```bash
pip install -r requirements.txt
python pregenerate.py      # writes stimuli.json with MOCK placeholder text
streamlit run app.py       # opens the interface in your browser
```

## Generating real explanations

1. Set your Claude API key: `export ANTHROPIC_API_KEY=sk-...`
2. In `pregenerate.py` set `LIVE = True` and set `LLM1_MODEL` / `LLM2_MODEL` to the
   Claude model(s) you are using.
3. Run `python pregenerate.py` — this regenerates `stimuli.json` with real outputs.
4. **Review the outputs** (this is the point of pre-generation): open `stimuli.json`
   and check each explanation actually reverse-engineered the code correctly. Re-run
   or adjust prompts as needed. Share with your supervisor for sign-off.

## Configuration (top of `app.py`)

| Setting | Meaning |
|---|---|
| `MS_FORMS_URL` | The Microsoft Forms questionnaire link  |
| `PROMPTS_PER_PARTICIPANT` | How many prompts each participant sees (default 3). |
| `CONDITION` | `"adaptive"` (persona-tailored) or `"generic"` (control condition). |
| `SHOW_ORIGINAL_PROMPT` | Kept `False` so the original task isn't revealed to participants. |
| `GENERATE_LIVE` | `False` = serve pre-generated stimuli; `True` = run the mechanism live. |
| `ASSIGNMENT_ORDER` | The 12 participant codes, in order — controls balanced coverage. |

## Balanced coverage

With 10 prompts and 12 participants seeing 3 each, `ASSIGNMENT_ORDER` distributes the
prompts


## Questionnaire

The 10-item Explanation Satisfaction questionnaire is delivered via **Microsoft Forms**


## Design

- **Persona is pre-assigned, not self-selected.** Fill `PARTICIPANT_PERSONA` in `app.py`
  with each anonymous code mapped to a level (apply your years-of-experience rule:
  e.g. <2 = beginner, 2-5 = intermediate, 5+ = senior). Codes not in this map are rejected.
- **Personalised links.** Each participant can now access their context with their code, e.g.
  `https://code-explanation-study.streamlit.app/?pid=P03`. The app reads the code from the URL,
  and a refresh restores based on identity. Assignment is deterministic, so a
  refresh gives the same prompts.
- **One questionnaire.** Each participant sees 2 prompts, then opens a single Microsoft
  Forms questionnaire answered **overall** for both.
- **Consent.** The app shows the information sheet and gates on the consent checkboxes, and
  writes a best-effort local log -- but the consent record is also stored in a Microsoft
  Form as Streamlit Cloud storage is ephemeral.
- **`GENERATE_LIVE`** is `False` to maintain data collection.

### Quick test
`PARTICIPANT_PERSONA` includes ID P01-P12 (4 per level):
```
python pregenerate.py     # (LIVE=True + key) or leave mock to test the UI
streamlit run app.py
```
Then open `http://localhost:8501/?pid=P03` to simulate a participant.
