"""
app.py  --  Study interface (Streamlit)
=======================================
Participant flow:
  1. Opens their personalised link (…/?pid=PXX). The app reads the code from the URL,
     looks up their pre-assigned experience level (persona), and shows the consent page.
  2. Reads the information sheet and confirms consent (durable record is captured in
     Microsoft Forms; this app also writes a best-effort local log).
  3. Sees their 2 assigned prompts -- for each, the generated code and the explanation
     adapted to their level -- and reads them.
  4. Opens the single Microsoft Forms questionnaire (one 10-item Explanation Satisfaction
     questionnaire, answered once, overall, for all the prompts they saw).

Design notes:
  - Persona is PRE-ASSIGNED by the researcher (from a years-of-experience rule) and looked
    up from the participant code -- participants do NOT self-select their level.
  - Prompt assignment is DETERMINISTIC from the participant code, so a refresh/re-entry
    yields the SAME prompts (session resilience). The code is carried in the URL so a
    refresh restores identity without retyping.
  - Only the persona-adapted (adaptive) explanation is shown. A generic/control condition
    is parked as possible FUTURE WORK and is not part of the current study.

Run:  streamlit run app.py
"""

import json
import os
import csv
import datetime
import streamlit as st
from prompts import PROMPTS, PERSONAS, PERSONA_RANGES

# ----------------------------------------------------------------------------
# CONFIG  -- edit these
# ----------------------------------------------------------------------------
MS_FORMS_URL = "https://forms.cloud.microsoft/e/p6K19C5aik"   # <-- Form 2 (questionnaire)
CONSENT_FORM_URL = "https://forms.cloud.microsoft/e/MfaQxCW2Qs"  # <-- Form 1 (durable consent record)
PROMPTS_PER_PARTICIPANT = 2          # each participant sees 2 prompts (from their persona range)
SHOW_ORIGINAL_PROMPT = False         # keep False so the task isn't revealed (avoids bias)
GENERATE_LIVE = False                # keep False for the study. True = generate live (DANGER: see below)

# ============================================================================
# PARTICIPANT ROSTER  --  READ BEFORE THE STUDY
# ----------------------------------------------------------------------------
# Design A (researcher pre-assignment): YOU classify each participant BEFORE their
# session, applying the years-of-experience rule to what they told you at recruitment:
#     < 2 years            -> "beginner"
#     >= 2 and <= 5 years  -> "intermediate"
#     > 5 years            -> "senior"
# Then record each real code -> level below and build their link (…/?pid=CODE).
#
# ⚠️  The P01–P12 entries below are PLACEHOLDERS assigned 4/4/4 for testing only.
#     DO NOT use them for real data. Replace them with your actual participant codes
#     and their rule-based levels before collecting data. Aim to recruit roughly four
#     participants in each band so the personas stay balanced.
# ============================================================================
PARTICIPANT_PERSONA = {
    "P01": "beginner", "P02": "beginner", "P03": "beginner", "P04": "beginner",
    "P05": "intermediate", "P06": "intermediate", "P07": "intermediate", "P08": "intermediate",
    "P09": "senior", "P10": "senior", "P11": "senior", "P12": "senior",
}
# Registration order (derived from the roster) -- used for balanced coverage.
ASSIGNMENT_ORDER = list(PARTICIPANT_PERSONA.keys())

PROMPTS_BY_ID = {p["id"]: p for p in PROMPTS}


# ----------------------------------------------------------------------------
# STIMULI  (pre-generated; live path guarded)
# ----------------------------------------------------------------------------
@st.cache_data
def load_stimuli():
    with open("stimuli.json") as f:
        return json.load(f)


def get_stimulus(prompt_id: int, persona: str):
    """Return (code, adaptive explanation) for a prompt at the participant's level."""
    if GENERATE_LIVE:
        # Live path: generates a fresh explanation each call. This BREAKS the study's
        # controlled-stimulus property (participants would see different explanations),
        # so it must stay False for data collection. Kept only for demos/testing.
        from pregenerate import generate_code, interpret
        p = PROMPTS_BY_ID[prompt_id]
        code = generate_code(p["llm1"])
        return code, interpret(code, p["llm2"][persona])
    data = load_stimuli()[str(prompt_id)]
    return data["code"], data["explanations"][persona]


# ----------------------------------------------------------------------------
# DETERMINISTIC ASSIGNMENT (balanced within each persona)
# ----------------------------------------------------------------------------
def assign_prompts(participant_code: str, persona: str, n: int = 2):
    """
    Assign n=2 prompts from the participant's PERSONA RANGE, guaranteeing at least one
    from that persona's CORE sub-range (so pairs are complexity-appropriate). All 10
    prompts are available across the study; the persona restricts only the *range* drawn
    from (and, separately, selects the adapted explanation shown).

    Deterministic: the same code always yields the same pair, so a refresh or re-entry is
    consistent. Coverage is balanced using the participant's position within their persona
    group in the roster.
    """
    r = PERSONA_RANGES[persona]
    allowed, core = r["allowed"], r["core"]

    same_persona = [c for c in ASSIGNMENT_ORDER if PARTICIPANT_PERSONA.get(c) == persona]
    k = same_persona.index(participant_code) if participant_code in same_persona else 0

    first = core[k % len(core)]
    others = [i for i in allowed if i != first]
    second = others[k % len(others)]
    return [first, second]


def forms_link(participant_code: str) -> str:
    """The single questionnaire link (Form 2), with the participant code prefilled if the form reads it."""
    sep = "&" if "?" in MS_FORMS_URL else "?"
    return f"{MS_FORMS_URL}{sep}pid={participant_code}"


def consent_form_link(participant_code: str) -> str:
    """The durable consent form link (Form 1), with the participant code prefilled if the form reads it."""
    sep = "&" if "?" in CONSENT_FORM_URL else "?"
    return f"{CONSENT_FORM_URL}{sep}pid={participant_code}"


# ----------------------------------------------------------------------------
# CONSENT
# ----------------------------------------------------------------------------
CONSENT_STATEMENTS = [
    "I have carefully read and understood the Participant Information Sheet.",
    "I have had an opportunity to ask questions and discuss this study and I have received satisfactory answers.",
    "I understand I am free to withdraw from the study at any time, without having to give a reason for withdrawing, and without prejudice.",
    "I agree to take part in this study.",
]
CONSENT_LOG = "consent_log.csv"


def record_consent(participant_code: str, persona: str):
    """
    Best-effort local consent log. NOTE: on Streamlit Community Cloud the filesystem is
    ephemeral, so this file is NOT a reliable record -- the DURABLE consent record is the
    consent question(s) in Microsoft Forms. This write is wrapped so it never breaks the
    app if the filesystem is read-only.
    """
    try:
        new_file = not os.path.exists(CONSENT_LOG)
        with open(CONSENT_LOG, "a", newline="") as f:
            w = csv.writer(f)
            if new_file:
                w.writerow(["timestamp", "participant_code", "persona",
                            "statements_agreed", "consent_given"])
            w.writerow([datetime.datetime.now().isoformat(timespec="seconds"),
                        participant_code, persona, len(CONSENT_STATEMENTS), "yes"])
    except Exception:
        pass  # durable record is in MS Forms; never block the participant


# ----------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------
st.set_page_config(page_title="Code Explanation Study", layout="centered")

if GENERATE_LIVE:
    st.warning("GENERATE_LIVE is ON — explanations are generated live and will differ "
               "between participants. Turn this OFF for data collection.", icon="⚠️")

ss = st.session_state
ss.setdefault("started", False)
ss.setdefault("participant", "")
ss.setdefault("persona", None)
ss.setdefault("assigned", [])
ss.setdefault("idx", 0)
ss.setdefault("stage", 0)   # per-task reveal stage: 0 = nothing, 1 = code shown, 2 = explanation shown

# Read the participant code from the URL (…/?pid=PXX) for refresh-resilient identity.
url_pid = st.query_params.get("pid", "")
if url_pid and not ss.participant:
    ss.participant = url_pid

# ---- Consent screen (FIRST page) ----
if not ss.started:
    st.title("Code Explanation Study — Consent")
    st.write(
        "Please read the information below and give your consent before taking part. "
        "You will not see any study material until you have consented."
    )

    with st.expander("Participant Information Sheet (please read in full)", expanded=True):
        st.markdown(
            "**Study title:** Adaptive Explanations of LLM-Generated Code  \n"
            "**Investigator:** Iyanuoluwa Opadotun\n\n"
            "You are being invited to take part in this research study. Before you decide it is "
            "important for you to read this leaflet so you understand why the study is being carried "
            "out and what it will involve. Reading this leaflet, discussing it with others or asking "
            "any questions you might have will help you decide whether or not you would like to take part.\n\n"

            "**What is the purpose of the study?**  \n"
            "This study looks at how computer-generated explanations of code can be made clearer for "
            "people with different levels of programming experience. An LLM Model 1 generates a piece of code"
            "in response to a prompt, and a second Model 2 provides explanation of the generated code"
            "in response to a prompt adapted to your experience level. We want to find out whether explanations"
            "that are matched to your level of experience are more helpful and satisfying than a single general explanation.\n\n"

            "**Why have I been invited to take part?**  \n"
            "You have been invited to take part as you meet the following criteria:\n"
            "- You are an adult aged 18+ years.\n"
            "- You have some experience reading and/or writing code.\n\n"

            "**Do I have to take part?**  \n"
            "You are under no obligation to take part and you will not experience any loss of benefit or "
            "penalty if you choose not to participate.\n\n"

            "**What will I have to do?**  \n"
            "You will take part in a single session lasting approximately 20–30 minutes, which can be "
            "completed online at a convenient time. You will be shown one or more pieces of "
            "computer-generated code together with an explanation of what was done to the code. You will "
            "then answer a short questionnaire rating how clear, complete and satisfying you found each "
            "explanation. You will not be tested personally — the study evaluates the explanations, not "
            "your ability.\n\n"

            "**What are the exclusion criteria (i.e. are there any reasons why I should not take part)?**  \n"
            "You should not take part in this study if:\n"
            "- You are under 18 years of age.\n"
            "- You have no experience with any programming language.\n\n"

            "**What are the possible disadvantages/risks in taking part?**  \n"
            "There are no significant risks. The only minor discomfort is the short period of reading code "
            "and explanations on a screen. This is minimised by keeping the session brief (around 20–30 "
            "minutes) and allowing you to take breaks or stop at any time.\n\n"

            "**What are the possible benefits of taking part?**  \n"
            "There are no direct benefits, but you will experience a contemporary research technique in "
            "explainable AI, and your input will help improve how AI systems explain code to people with "
            "different levels of experience. You may request a summary of the findings.\n\n"

            "**Will my taking part be kept confidential and anonymous?**  \n"
            "Yes. You will be allocated a unique participant code that will be used to identify any data "
            "that you provide. Your name and other personal details will not be associated with your data, "
            "for example any signed informed consent forms will be stored separately. Only the research "
            "team will have access to any identifiable information; paper records will be stored in a "
            "locked filing cabinet and electronic information will be stored on the secure University "
            "network. This will be kept separate from any data and will be treated in accordance with the "
            "Data Protection Act.\n\n"

            "**How will my data be stored?**  \n"
            "All data will be stored on Northumbria University’s official OneDrive network and where "
            "appropriate additionally protected with a password. Any paper data collected will be locked "
            "away in a secure folder.\n\n"

            "**What will happen to the results of the study?**  \n"
            "The results will be used for a postgraduate project that will be examined as part of an MSc "
            "Computer Science & Digital Technologies degree. Occasionally some results might be presented "
            "at a conference or published in a journal, but they will always remain anonymous. All "
            "information and data gathered during this research will be stored in line with the Data "
            "Protection Act and will be destroyed after a maximum of 3 years following the conclusion of "
            "the study. During that time the data may be used by members of the research team, only for "
            "purposes appropriate to the research question, but at no point will your personal information "
            "or data be revealed.\n\n"

            "**Who is organizing and funding the study?**  \n"
            "The present research project has received no funding.\n\n"

            "**Who has reviewed the study?**  \n"
            "The study and its protocol has received full ethical approval from the School of Computer "
            "Science ethics committee. If you require confirmation of this, please contact the School "
            "Ethics Lead using the details below and stating the full title and principal investigator of "
            "the study:  \n"
            "Name of relevant School Ethics Lead: Prof. Yifeng Zeng  \n"
            "School: Computer Science  \n"
            "Email: yifeng.zeng@northumbria.ac.uk\n\n"

            "**How can I withdraw from the project?**  \n"
            "The research you take part in will be most valuable if few people withdraw from it, so please "
            "discuss any concerns you might have with the investigators. During the study itself, if you "
            "do decide that you do not wish to take any further part then please inform one of the research "
            "team as soon as possible, and they will facilitate your withdrawal and discuss with you how "
            "you would like your data to be treated in the future. After you have completed the research, "
            "you can still withdraw your data by contacting one of the research team (their contact details "
            "are provided in the last section of the leaflet), give them your participant number, or if you "
            "have lost this, give them your name. If for any reason you wish to withdraw your data please "
            "contact the investigator within two weeks of your participation. After this date, it might not "
            "be possible to withdraw your individual data as the results might already have been published. "
            "As all data are anonymous, your individual data will not be identifiable in any way.\n\n"

            "**What happens if there is a problem?**  \n"
            "If you are unhappy about anything during or after your participation, you should contact the "
            "principal investigator in the first instance. If you feel this is not appropriate, you should "
            "contact the Computer and Information Sciences Departmental Ethics Lead via the contact details "
            "given above.\n\n"

            "**Contact for further information:**  \n"
            "Researcher email: iyanuoluwa.opadotun@northumbria.ac.uk  \n"
            "Supervisor email: swaroop.panda@northumbria.ac.uk"
        )

    st.divider()
    code = st.text_input("Participant code", value=ss.participant,
                         help="Use the anonymous code from the link you were sent.")
    ss.participant = code.strip()

    # Look up the pre-assigned persona; reject codes that aren't in the roster.
    persona = PARTICIPANT_PERSONA.get(ss.participant)
    code_valid = persona is not None
    if ss.participant and not code_valid:
        st.error("This participant code is not recognised. Please check the link or code "
                 "you were given, or contact the researcher.")

    st.write("**Please confirm each statement to give your consent:**")
    agreed = [st.checkbox(s, key=f"c{i}") for i, s in enumerate(CONSENT_STATEMENTS)]
    all_agreed = all(agreed)

    # Durable consent record: the consent form link is shown on the page at all times.
    st.divider()
    st.markdown("**Step 1 — Complete the consent form**")
    st.write("Please open and complete the short consent form to record your consent:")
    st.link_button("Open the consent form", consent_form_link(ss.participant))
    st.markdown("**Step 2 — Begin the study**")
    st.warning("Only click **Begin the study** below once you have completed the consent form above.",
               icon="⚠️")

    ready = code_valid and all_agreed
    if st.button("Begin the study", type="primary", disabled=not ready):
        st.query_params["pid"] = ss.participant     # persist code in URL for refresh
        ss.persona = persona
        record_consent(ss.participant, persona)      # best-effort; durable record is in Form 1
        ss.assigned = assign_prompts(ss.participant, persona, PROMPTS_PER_PARTICIPANT)
        ss.idx = 0
        ss.stage = 0            # reveal stage for the current task (0=nothing, 1=code, 2=explanation)
        ss.started = True
        st.rerun()
    if not all_agreed:
        st.caption("All statements must be confirmed before you can begin.")

# ---- Trial screen ----
else:
    import time
    total = len(ss.assigned)
    prompt_id = ss.assigned[ss.idx]
    p = PROMPTS_BY_ID[prompt_id]

    st.caption(f"Participant {ss.participant}")
    st.progress((ss.idx + 1) / total, text=f"Task {ss.idx + 1} of {total}")

    code, explanation = get_stimulus(prompt_id, ss.persona)

    if SHOW_ORIGINAL_PROMPT:
        st.caption(f"Task given to the code generator: {p['llm1']}")

    # --- Stage 0: reveal the LLM 1 code ---
    if ss.stage == 0:
        if st.button("Click to view code generated by LLM 1", type="primary", key=f"showcode_{ss.idx}"):
            with st.spinner("LLM 1 is generating the code…"):
                time.sleep(2)
            ss.stage = 1
            st.rerun()

    # --- Stage 1+: code is shown ---
    if ss.stage >= 1:
        st.subheader("Code generated by LLM 1")
        st.code(code, language="python")

        # reveal the LLM 2 explanation
        if ss.stage == 1:
            if st.button("Click to view explanation by LLM 2", type="primary", key=f"showexp_{ss.idx}"):
                with st.spinner("LLM 2 is interpreting the code and preparing an explanation…"):
                    time.sleep(2)
                ss.stage = 2
                st.rerun()

    # --- Stage 2: explanation is shown ---
    if ss.stage >= 2:
        st.subheader("Explanation by LLM 2")
        st.write(explanation)

    # --- Navigation / questionnaire ---
    st.divider()
    if ss.idx < total - 1:
        # Not the last task: allow advancing only after the explanation has been revealed.
        if ss.stage >= 2:
            if st.button("Next task →", type="primary"):
                ss.idx += 1
                ss.stage = 0          # reset reveal so the next task starts collapsed
                st.rerun()
        else:
            st.info("Please view the code and the explanation above before moving on.")
    else:
        # Last task: show the questionnaire only after the explanation has been revealed.
        if ss.stage >= 2:
            st.success("You have now seen both tasks.")
            st.write("Please complete the short questionnaire, answering **overall** for the "
                     "explanations you have just read:")
            st.link_button("Open the questionnaire", forms_link(ss.participant), type="primary")
        else:
            st.info("Please view the code and the explanation above to finish.")

    st.caption("You may withdraw within two weeks of participating by contacting the researcher.")
