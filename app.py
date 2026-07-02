import json
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st
from openai import OpenAI
from supabase import create_client


st.set_page_config(
    page_title="AI Study Assistance",
    page_icon="🧠",
    layout="wide",
)


CSS = """
<style>
    html, body, [class*="css"] {
        color: #111111;
    }

    .stApp {
        background: #F7F7F5;
        color: #111111;
    }

    .block-container {
        padding-top: 2rem;
        max-width: 1180px;
    }

    h1, h2, h3, h4, h5, h6, p, li, span, div {
        letter-spacing: -0.01em;
    }

    .asa-card {
        border: 1px solid #DADADA;
        border-radius: 18px;
        padding: 20px 22px;
        background: #FFFFFF;
        color: #111111 !important;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
    }

    .asa-card h1,
    .asa-card h2,
    .asa-card h3,
    .asa-card p,
    .asa-card strong,
    .asa-card span {
        color: #111111 !important;
    }

    .asa-small {
        color: #555555 !important;
        font-size: 0.92rem;
    }

    .asa-pill {
        display: inline-block;
        border: 1px solid #CFCFCF;
        border-radius: 999px;
        padding: 5px 11px;
        margin: 3px 5px 3px 0;
        font-size: 0.85rem;
        background: #F2F2F2;
        color: #111111 !important;
    }

    .asa-critical {
        display: inline-block;
        border-radius: 999px;
        padding: 3px 9px;
        font-size: 0.78rem;
        background: #111111;
        color: #FFFFFF !important;
        margin-left: 6px;
    }

    section[data-testid="stSidebar"] {
        background: #111111;
    }

section[data-testid="stSidebar"] {
    background: #111111;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
    color: #F5F5F5 !important;
}

    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E0E0E0;
        padding: 14px;
        border-radius: 16px;
    }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def secret_value(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def require_password() -> None:
    app_password = secret_value("APP_PASSWORD", "")
    if not app_password:
        st.warning("APP_PASSWORD is not set. The app is open to anyone with the URL. Set it in Streamlit secrets.")
        return

    if st.session_state.get("authenticated"):
        return

    st.title("AI Study Assistance")
    st.caption("Private access")
    entered = st.text_input("Enter app password", type="password")

    if st.button("Enter", type="primary"):
        if entered == app_password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Wrong password.")
    st.stop()


@st.cache_resource
def get_supabase_client():
    url = secret_value("SUPABASE_URL")
    key = secret_value("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in Streamlit secrets.")
    return create_client(url, key)


@st.cache_resource
def get_openai_client():
    api_key = secret_value("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def fetch_rows(table: str, order_col: Optional[str] = None) -> List[Dict[str, Any]]:
    db = get_supabase_client()
    query = db.table(table).select("*")
    if order_col:
        query = query.order(order_col)
    result = query.execute()
    return result.data or []


def fetch_topic(topic_id: str) -> Optional[Dict[str, Any]]:
    db = get_supabase_client()
    result = db.table("topics").select("*").eq("id", topic_id).limit(1).execute()
    return (result.data or [None])[0]


def fetch_lesson(topic_id: str) -> Optional[Dict[str, Any]]:
    db = get_supabase_client()
    result = (
        db.table("lessons")
        .select("*")
        .eq("topic_id", topic_id)
        .eq("status", "published")
        .limit(1)
        .execute()
    )
    return (result.data or [None])[0]


def fetch_assessment(topic_id: str) -> Optional[Dict[str, Any]]:
    db = get_supabase_client()
    result = db.table("assessments").select("*").eq("topic_id", topic_id).limit(1).execute()
    return (result.data or [None])[0]


def fetch_questions(assessment_id: str) -> List[Dict[str, Any]]:
    db = get_supabase_client()
    result = (
        db.table("assessment_questions")
        .select("*")
        .eq("assessment_id", assessment_id)
        .order("sort_order")
        .execute()
    )
    return result.data or []


def save_attempt(payload: Dict[str, Any]) -> None:
    db = get_supabase_client()
    db.table("attempts").insert(payload).execute()


def save_note(topic_id: str, lesson_id: Optional[str], note_text: str, learner_name: str) -> None:
    db = get_supabase_client()
    db.table("notes").insert(
        {
            "topic_id": topic_id,
            "lesson_id": lesson_id,
            "learner_name": learner_name,
            "note_text": note_text,
        }
    ).execute()


def evaluate_descriptive_answer(
    lesson: Dict[str, Any],
    question: Dict[str, Any],
    answer: str,
) -> Dict[str, Any]:
    clean_answer = answer.strip()
    if len(clean_answer.split()) < 35:
        return {
            "stars": 1,
            "feedback": "Too short. This does not demonstrate architect-level reasoning yet.",
            "strengths": [],
            "gaps": ["Explain decision logic, production risk, and architecture implications."],
        }

    client = get_openai_client()
    if client is None:
        return fallback_evaluation(clean_answer)

    model = secret_value("OPENAI_MODEL", "gpt-4.1-mini")
    lesson_content = json.dumps(lesson.get("content", {}), ensure_ascii=False)
    rubric = json.dumps(question.get("rubric", {}), ensure_ascii=False)

    prompt = f"""
You are evaluating a learner's architect-level answer.

Strict rule:
Evaluate only against concepts taught in the lesson content below.
Do not penalize the learner for concepts that were not taught.

Return valid JSON only with:
{{
  "stars": integer from 1 to 5,
  "feedback": "direct feedback",
  "strengths": ["..."],
  "gaps": ["..."]
}}

Lesson content:
{lesson_content}

Question:
{question.get("question")}

Rubric:
{rubric}

Learner answer:
{clean_answer}
""".strip()

    try:
        response = client.responses.create(
            model=model,
            input=prompt,
        )
        text = response.output_text.strip()
        parsed = json.loads(text)
        stars = int(parsed.get("stars", 1))
        parsed["stars"] = max(1, min(5, stars))
        return parsed
    except Exception as exc:
        fallback = fallback_evaluation(clean_answer)
        fallback["feedback"] += f" OpenAI evaluation failed, fallback used. Error: {str(exc)[:120]}"
        return fallback


def fallback_evaluation(answer: str) -> Dict[str, Any]:
    terms = [
        "control plane",
        "policy",
        "rollback",
        "audit",
        "evaluation",
        "permission",
        "human",
        "failure",
        "production",
        "architecture",
    ]
    text = answer.lower()
    hits = sum(1 for term in terms if term in text)
    stars = 2
    if len(answer.split()) >= 80 and hits >= 4:
        stars = 3
    if len(answer.split()) >= 130 and hits >= 6:
        stars = 4
    return {
        "stars": stars,
        "feedback": "Fallback evaluation based on answer depth and key architecture terms.",
        "strengths": ["Answer has some production/architecture framing."] if hits >= 3 else [],
        "gaps": ["Add sharper trade-offs, failure mode, and decision checklist reasoning."],
    }


def render_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="asa-card">
            <h3>{title}</h3>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pill_list(items: Any) -> str:
    if not items:
        return ""
    if isinstance(items, str):
        items = [items]
    return " ".join([f'<span class="asa-pill">{item}</span>' for item in items])


def select_active_topic(topics: List[Dict[str, Any]]) -> Optional[str]:
    if not topics:
        return None

    # If there is only one topic, do not show a pointless dropdown.
    if len(topics) == 1:
        active_topic = topics[0]
        st.session_state["active_topic_id"] = active_topic["id"]
        st.sidebar.markdown("### Active topic")
        st.sidebar.caption(active_topic["title"])
        return active_topic["id"]

    if "active_topic_id" not in st.session_state:
        st.session_state["active_topic_id"] = topics[0]["id"]

    topic_labels = {
        f"{t['domain']} · {t['title']}": t["id"]
        for t in topics
    }

    current_label = next(
        (
            label
            for label, topic_id in topic_labels.items()
            if topic_id == st.session_state["active_topic_id"]
        ),
        list(topic_labels.keys())[0],
    )

    st.sidebar.markdown("### Active topic")
    selected_label = st.sidebar.selectbox(
        "Choose topic",
        list(topic_labels.keys()),
        index=list(topic_labels.keys()).index(current_label),
        label_visibility="collapsed",
    )

    st.session_state["active_topic_id"] = topic_labels[selected_label]
    return st.session_state["active_topic_id"]

def page_home(topics: List[Dict[str, Any]]) -> None:
    st.title("AI Study Assistance")
    st.caption("Deep AI architecture learning. No thin tutor. No childish gamification. No forced locks.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Topics loaded", len(topics))
    c2.metric("Learning model", "Onion")
    c3.metric("V1 spine", "Lesson → Assessment → Attempt")

    st.markdown("### Product principle")
    render_card(
        "No thin tutor",
        "Every lesson must explain the concept, connect it upward to AI architecture, connect it downward to foundations, and expose production failure modes before assessment.",
    )

    st.markdown("### Current vertical slice")
    st.info("This build intentionally starts with one complete loop. Once stable, add 10 to 15 lessons. Do not build a complex progression engine yet.")


def page_topic_map(topics: List[Dict[str, Any]]) -> None:
    st.title("Onion Topic Map")
    if not topics:
        st.error("No topics found. Run the initial Supabase SQL migration first.")
        return

    df = pd.DataFrame(topics)
    for domain, group in df.groupby("domain", sort=False):
        st.markdown(f"## {domain}")
        for _, row in group.sort_values("sort_order").iterrows():
            st.markdown(
                f"""
                <div class="asa-card">
                    <h3>{row['title']}</h3>
                    <p class="asa-small">{row.get('onion_layer', '')}</p>
                    <p>{row.get('summary', '')}</p>
                    <p><strong>Architect relevance:</strong> {row.get('architect_relevance', '')}</p>
                    <p><strong>Higher systems:</strong> {pill_list(row.get('higher_systems'))}</p>
                    <p><strong>Lower foundations:</strong> {pill_list(row.get('lower_foundations'))}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def page_lesson(topic: Dict[str, Any], lesson: Optional[Dict[str, Any]]) -> None:
    st.title(topic["title"])
    st.caption(f"{topic['domain']} · {topic.get('onion_layer', '')}")

    st.markdown(
        f"""
        <div class="asa-card">
            <h3>Glue</h3>
            <p><strong>What this is:</strong> {topic.get('summary', '')}</p>
            <p><strong>Why an AI architect cares:</strong> {topic.get('architect_relevance', '')}</p>
            <p><strong>Production risks:</strong> {pill_list(topic.get('production_risks'))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not lesson:
        st.error("No published lesson found for this topic.")
        return

    content = lesson.get("content", {})
    section_order = [
        "executive_intuition",
        "plain_english",
        "step_by_step",
        "concrete_example",
        "architecture_translation",
        "common_mistakes",
        "failure_mode",
        "decision_checklist",
        "worked_scenario",
    ]

    labels = {
        "executive_intuition": "Executive intuition",
        "plain_english": "Plain-English explanation",
        "step_by_step": "Step-by-step concept explanation",
        "concrete_example": "Concrete example",
        "architecture_translation": "Architecture translation",
        "common_mistakes": "Common mistakes",
        "failure_mode": "Failure mode",
        "decision_checklist": "Decision checklist",
        "worked_scenario": "Worked scenario",
    }

    for key in section_order:
        value = content.get(key)
        if not value:
            continue
        with st.expander(labels[key], expanded=(key in ["executive_intuition", "plain_english"])):
            if isinstance(value, list):
                for item in value:
                    st.markdown(f"- {item}")
            else:
                st.markdown(value)

    if lesson.get("source_links"):
        st.markdown("### Source links")
        for link in lesson["source_links"]:
            st.markdown(f"- [{link.get('title', link.get('url'))}]({link.get('url')})")


def page_assessment(topic: Dict[str, Any], lesson: Optional[Dict[str, Any]]) -> None:
    st.title("Assessment")
    if not lesson:
        st.error("No lesson available. Assessment cannot run without lesson content.")
        return

    assessment = fetch_assessment(topic["id"])
    if not assessment:
        st.error("No assessment found for this topic.")
        return

    questions = fetch_questions(assessment["id"])
    mcqs = [q for q in questions if q["question_type"] == "mcq"]
    desc_questions = [q for q in questions if q["question_type"] == "descriptive"]

    st.info("Assessment rule: this evaluates only what the lesson teaches. Passing requires 70% MCQ, all critical MCQs correct, and descriptive answer of at least 3 stars.")

    with st.form("assessment_form"):
        answers = {}
        for q in mcqs:
            marker = '<span class="asa-critical">critical</span>' if q.get("is_critical") else ""
            st.markdown(f"**Q{q['sort_order']}. {q['question']}** {marker}", unsafe_allow_html=True)
            options = q.get("options") or {}
            keys = sorted(options.keys())
            answers[q["id"]] = st.radio(
                "Choose one",
                keys,
                format_func=lambda k, opts=options: f"{k}. {opts[k]}",
                key=f"mcq_{q['id']}",
                label_visibility="collapsed",
            )

        descriptive_answer = ""
        if desc_questions:
            dq = desc_questions[0]
            st.markdown(f"**Descriptive. {dq['question']}**")
            descriptive_answer = st.text_area(
                "Write your architect response",
                height=180,
                placeholder="Answer as an AI architect. Explain decision logic, risk, governance, and production implication.",
            )

        submitted = st.form_submit_button("Submit assessment", type="primary")

    if submitted:
        correct_count = 0
        critical_pass = True
        answer_details = []

        for q in mcqs:
            selected = answers.get(q["id"])
            is_correct = selected == q["correct_answer"]
            correct_count += int(is_correct)
            if q.get("is_critical") and not is_correct:
                critical_pass = False
            answer_details.append(
                {
                    "question_id": q["id"],
                    "selected": selected,
                    "correct": q["correct_answer"],
                    "is_correct": is_correct,
                    "is_critical": bool(q.get("is_critical")),
                }
            )

        mcq_score = round((correct_count / max(len(mcqs), 1)) * 100, 2)
        desc_eval = {"stars": None, "feedback": "", "strengths": [], "gaps": []}

        if desc_questions:
            desc_eval = evaluate_descriptive_answer(lesson, desc_questions[0], descriptive_answer)

        desc_stars = desc_eval.get("stars") or 0
        passed = (
            mcq_score >= float(assessment.get("pass_mcq_percent", 70))
            and critical_pass
            and int(desc_stars) >= int(assessment.get("descriptive_min_stars", 3))
        )

        payload = {
            "topic_id": topic["id"],
            "lesson_id": lesson["id"],
            "assessment_id": assessment["id"],
            "learner_name": secret_value("LEARNER_NAME", "Shri"),
            "mcq_score_percent": mcq_score,
            "critical_pass": critical_pass,
            "mcq_answers": answer_details,
            "descriptive_answer": descriptive_answer,
            "descriptive_stars": int(desc_stars) if desc_stars else None,
            "descriptive_feedback": desc_eval.get("feedback", ""),
            "passed": passed,
        }
        save_attempt(payload)

        c1, c2, c3 = st.columns(3)
        c1.metric("MCQ score", f"{mcq_score}%")
        c2.metric("Critical MCQs", "Pass" if critical_pass else "Fail")
        c3.metric("Descriptive", f"{desc_stars}★" if desc_stars else "Not scored")

        if passed:
            st.success("Passed. This topic can be marked strong enough for V1.")
        else:
            st.error("Not passed. Revise the lesson, especially the critical concepts and architecture translation.")

        st.markdown("### Descriptive feedback")
        st.write(desc_eval.get("feedback", ""))
        if desc_eval.get("strengths"):
            st.markdown("**Strengths**")
            for item in desc_eval["strengths"]:
                st.markdown(f"- {item}")
        if desc_eval.get("gaps"):
            st.markdown("**Gaps**")
            for item in desc_eval["gaps"]:
                st.markdown(f"- {item}")


def page_notes(topic: Dict[str, Any], lesson: Optional[Dict[str, Any]]) -> None:
    st.title("Notes / Revision")
    note_text = st.text_area("Write revision note", height=160)
    if st.button("Save note", type="primary"):
        if not note_text.strip():
            st.warning("Write something first.")
        else:
            save_note(topic["id"], lesson["id"] if lesson else None, note_text.strip(), secret_value("LEARNER_NAME", "Shri"))
            st.success("Note saved.")

    db = get_supabase_client()
    notes = (
        db.table("notes")
        .select("*")
        .eq("topic_id", topic["id"])
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    st.markdown("### Saved notes")
    for note in notes:
        st.markdown(
            f"""
            <div class="asa-card">
                <p class="asa-small">{note.get('created_at', '')}</p>
                <p>{note.get('note_text', '')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def page_progress() -> None:
    st.title("Progress Dashboard")
    attempts = fetch_rows("attempts", "created_at")
    if not attempts:
        st.info("No attempts yet.")
        return

    df = pd.DataFrame(attempts)
    df["created_at"] = pd.to_datetime(df["created_at"])
    latest = df.sort_values("created_at", ascending=False).head(10)

    c1, c2, c3 = st.columns(3)
    c1.metric("Attempts", len(df))
    c2.metric("Passes", int(df["passed"].sum()))
    c3.metric("Average MCQ", f"{round(df['mcq_score_percent'].mean(), 1)}%")

    st.dataframe(
        latest[
            [
                "created_at",
                "topic_id",
                "mcq_score_percent",
                "critical_pass",
                "descriptive_stars",
                "passed",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


def main() -> None:
    require_password()

    try:
        topics = fetch_rows("topics", "sort_order")
    except Exception as exc:
        st.title("AI Study Assistance")
        st.error("Database is not ready. Run the initial SQL migration in Supabase first.")
        st.code(str(exc))
        return

    active_topic_id = select_active_topic(topics)
    topic = fetch_topic(active_topic_id) if active_topic_id else None
    lesson = fetch_lesson(active_topic_id) if active_topic_id else None

    st.sidebar.markdown("---")
    page = st.sidebar.radio(
        "Navigate",
        ["Home", "Topic Map", "Lesson", "Assessment", "Notes", "Progress"],
    )

    if page == "Home":
        page_home(topics)
    elif page == "Topic Map":
        page_topic_map(topics)
    elif page == "Lesson":
        if topic:
            page_lesson(topic, lesson)
    elif page == "Assessment":
        if topic:
            page_assessment(topic, lesson)
    elif page == "Notes":
        if topic:
            page_notes(topic, lesson)
    elif page == "Progress":
        page_progress()


if __name__ == "__main__":
    main()
