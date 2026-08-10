# Adaptive Explanations of LLM-Generated Code — Study Scaffold

A runnable starting codebase for the two-LLM mechanism and the participant study
interface. Built on the **pre-generation** model (explanations are generated once,
offline, then served to every participant identically), with a single flag to switch
to live generation if needed.

## Files

| File | What it is |
|---|---|
| `prompts.py` | The 9 LLM 1 prompts, each with 3 persona-adapted LLM 2 prompts + a generic control prompt. |
| `pregenerate.py` | Runs the two-LLM mechanism offline and writes `stimuli.json` (the frozen explanations). |
| `stimuli.json` | The generated stimuli the interface serves (currently MOCK placeholders). |
| `app.py` | The Streamlit participant interface: assigns prompts, shows code + explanation, hands off to MS Forms. |
| `requirements.txt` | Dependencies. |

## The mechanism (what happens)

1. **Stage 1 (Context A):** LLM 1 gets a problem prompt → generates code.
2. **Boundary:** only the *code* is kept; the original prompt is discarded.
3. **Stage 2 (Context B, fresh call):** LLM 2 gets **only the code** plus an
   interpretation prompt (persona folded in) → produces an explanation. LLM 2 never
   sees the original task, so it must reverse-engineer and verify the code itself.

Both are Claude models; the two stages are separate API calls with no shared history
(same model allowed, different context).

## Quick start (no API key needed)

```bash
pip install -r requirements.txt
python pregenerate.py      # writes stimuli.json with MOCK placeholder text
streamlit run app.py       # opens the interface in your browser
```

The app runs end-to-end on the mock stimuli so you can see the whole flow immediately.

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
| `MS_FORMS_URL` | Your Microsoft Forms questionnaire link (the 10-item scale lives here). |
| `PROMPTS_PER_PARTICIPANT` | How many prompts each participant sees (default 3). |
| `CONDITION` | `"adaptive"` (persona-tailored) or `"generic"` (control condition). |
| `SHOW_ORIGINAL_PROMPT` | Keep `False` so the original task isn't revealed to participants. |
| `GENERATE_LIVE` | `False` = serve pre-generated stimuli; `True` = run the mechanism live. |
| `ASSIGNMENT_ORDER` | Your 12 participant codes, in order — controls balanced coverage. |

## Balanced coverage

With 9 prompts and 12 participants seeing 3 each, `ASSIGNMENT_ORDER` distributes the
prompts so **all 9 are covered evenly** (4 views each). Fill it with your real
participant codes in registration order.

## The adaptive-vs-generic condition (study design)

`stimuli.json` stores both a persona-adapted explanation and a generic one for every
prompt. To test the hypothesis (adapted explanations score higher), you compare
satisfaction between the two conditions. Set `CONDITION` accordingly, or extend the
app to show each participant both and record which is which.

> **Design note for your supervisor:** the `prompts.py` LLM 2 prompts currently give
> each persona a *different operation type* as well as a different reading level. If
> you want the study to isolate the effect of adaptation alone, consider holding the
> operation constant per prompt and varying only the persona framing. This is flagged
> for discussion.

## Deploying online (for remote participants)

The simplest route is **Streamlit Community Cloud**: push this folder to a GitHub repo
and deploy `app.py`. Add `ANTHROPIC_API_KEY` as a secret only if `GENERATE_LIVE = True`
(with pre-generation you don't need the key in the deployed app at all — safer). Share
the resulting URL with participants alongside the MS Forms link.

## Questionnaire

The 10-item Explanation Satisfaction questionnaire is delivered via **Microsoft Forms**
(not in this app). The app links out to it per task and can prefill the participant
code, prompt id, and level as URL parameters if your form is set up to read them.


## Updated design (current)

- **Persona is pre-assigned, not self-selected.** Fill `PARTICIPANT_PERSONA` in `app.py`
  with each anonymous code mapped to a level (apply your years-of-experience rule:
  e.g. <2 = beginner, 2-5 = intermediate, 5+ = senior). Codes not in this map are rejected.
- **Personalised links.** Give each participant a link with their code, e.g.
  `https://your-app.streamlit.app/?pid=P07`. The app reads the code from the URL, so they
  don't type it, and a refresh restores their identity. Assignment is deterministic, so a
  refresh gives the same prompts.
- **One questionnaire.** Each participant sees 2 prompts, then opens a single Microsoft
  Forms questionnaire answered **overall** for both. Set `MS_FORMS_URL` to that form.
- **Consent.** The app shows the information sheet and gates on the consent checkboxes, and
  writes a best-effort local log -- but the **durable consent record must be in Microsoft
  Forms** (Streamlit Cloud storage is ephemeral). Add consent question(s) to your Forms.
- **Adaptive only.** Only the persona-adapted explanation is shown; the generic/control
  condition is parked as possible future work and is not part of the current study.
- **`GENERATE_LIVE`** must stay `False` for data collection (a visible warning shows if it's on).

### Quick test
`PARTICIPANT_PERSONA` ships with P01-P12 (4 per level) so you can run immediately:
```
python pregenerate.py     # (LIVE=True + key) or leave mock to test the UI
streamlit run app.py
```
Then open `http://localhost:8501/?pid=P07` to simulate a participant.
