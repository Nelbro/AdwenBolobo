import streamlit as st
import time
import json
import fitz  
import re
from typing import List, Dict

# --- Helper functions ---

def load_questions_from_json(json_str: str) -> List[Dict]:
    """Load questions from JSON string."""
    try:
        data = json.loads(json_str)
        assert isinstance(data, list)
        return data
    except Exception as e:
        st.error(f"Failed to load questions: {e}")
        return []

def parse_pdf_questions(pdf_bytes):
    """Parse questions from uploaded PDF bytes."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()

    raw_questions = re.split(r'\n\d+\.\s', full_text)
    parsed_questions = []

    for raw_q in raw_questions[1:]:
        try:
            question_match = re.match(r'(.+?)(?=\nA\.)', raw_q, re.DOTALL)
            question_text = question_match.group(1).strip()

            options_match = re.findall(r'\n([A-D])\.\s(.+?)(?=\n[A-D]\.|Answer:)', raw_q + "\nZ.", re.DOTALL)
            options = [opt[1].strip() for opt in options_match]

            answer_match = re.search(r'Answer:\s*([A-D])', raw_q)
            answer_letter = answer_match.group(1).strip()
            answer_index = ord(answer_letter) - ord('A')
            correct_answer = options[answer_index]

            explanation_match = re.search(r'Explanation:\s*(.+)', raw_q, re.DOTALL)
            explanation = explanation_match.group(1).strip() if explanation_match else ""

            parsed_questions.append({
                'question': question_text,
                'options': options,
                'answer': correct_answer,
                'explanation': explanation
            })
        except Exception as e:
            st.warning(f"Failed to parse a question: {e}")

    return parsed_questions

def timer(seconds: int):
    """Simple countdown timer UI."""
    placeholder = st.empty()
    for remaining in range(seconds, 0, -1):
        placeholder.markdown(f"⏳ Time left: **{remaining} seconds**")
        time.sleep(1)
    placeholder.empty()

# --- Default question bank ---
DEFAULT_QUESTIONS = [
    {
        'question': 'What is the primary neurotransmitter at the neuromuscular junction?',
        'options': ['Dopamine', 'Acetylcholine', 'GABA', 'Serotonin'],
        'answer': 'Acetylcholine',
        'explanation': 'Acetylcholine stimulates muscle contraction at the neuromuscular junction.'
    },
    {
        'question': 'Which drug is used to reverse opioid overdose?',
        'options': ['Naloxone', 'Atropine', 'Flumazenil', 'Physostigmine'],
        'answer': 'Naloxone',
        'explanation': 'Naloxone is a competitive opioid receptor antagonist used to reverse opioid overdose.'
    },
]

# --- Initialize session state ---
if 'questions' not in st.session_state:
    st.session_state.questions = DEFAULT_QUESTIONS

if 'score' not in st.session_state:
    st.session_state.score = 0

if 'current_q' not in st.session_state:
    st.session_state.current_q = 0

if 'submitted' not in st.session_state:
    st.session_state.submitted = False

if 'user_answer' not in st.session_state:
    st.session_state.user_answer = None

if 'review_mode' not in st.session_state:
    st.session_state.review_mode = False

if 'answers_log' not in st.session_state:
    st.session_state.answers_log = []

# --- App Title ---
st.title("adwenBolobo: USMLE Practice App")

# --- Upload Section ---
with st.expander("Upload your own questions (JSON or PDF)"):
    uploaded_file = st.file_uploader("Upload JSON or PDF file with questions", type=['json', 'pdf'])
    if uploaded_file is not None:
        file_ext = uploaded_file.name.split('.')[-1]

        if file_ext == 'json':
            file_content = uploaded_file.read().decode("utf-8")
            loaded_questions = load_questions_from_json(file_content)
        elif file_ext == 'pdf':
            file_content = uploaded_file.read()
            loaded_questions = parse_pdf_questions(file_content)
        else:
            loaded_questions = []

        if loaded_questions:
            st.session_state.questions = loaded_questions
            st.session_state.score = 0
            st.session_state.current_q = 0
            st.session_state.submitted = False
            st.session_state.user_answer = None
            st.session_state.review_mode = False
            st.session_state.answers_log = []
            st.success(f"Loaded {len(loaded_questions)} questions successfully!")

# --- Review Mode ---
if st.session_state.review_mode:
    st.header("Review Mode")
    for idx, entry in enumerate(st.session_state.answers_log):
        st.write(f"**Q{idx + 1}:** {entry['question']}")
        st.write(f"Your answer: {entry['user_answer']}")
        if entry['user_answer'] == entry['correct_answer']:
            st.success("Correct")
        else:
            st.error(f"Incorrect (Correct: {entry['correct_answer']})")
        st.info(f"Explanation: {entry['explanation']}")
        st.markdown("---")

    if st.button("Restart Test"):
        st.session_state.score = 0
        st.session_state.current_q = 0
        st.session_state.submitted = False
        st.session_state.user_answer = None
        st.session_state.review_mode = False
        st.session_state.answers_log = []

else:
    # --- Quiz Mode ---
    if st.session_state.current_q < len(st.session_state.questions):
        q = st.session_state.questions[st.session_state.current_q]
        st.write(f"### Question {st.session_state.current_q + 1} of {len(st.session_state.questions)}")
        st.write(q['question'])

        if not st.session_state.submitted:
            timer_seconds = 20  # Timer per question in seconds
            timer(timer_seconds)

        user_answer = st.radio("Select your answer:", q['options'], key=f"answer_{st.session_state.current_q}")

        if not st.session_state.submitted:
            if st.button("Submit Answer"):
                st.session_state.user_answer = user_answer
                st.session_state.submitted = True

                if user_answer == q['answer']:
                    st.session_state.score += 1

                st.session_state.answers_log.append({
                    'question': q['question'],
                    'user_answer': user_answer,
                    'correct_answer': q['answer'],
                    'explanation': q['explanation']
                })

        else:
            if st.session_state.user_answer == q['answer']:
                st.success("Correct!")
            else:
                st.error(f"Incorrect. Correct answer: {q['answer']}")

            st.info(f"Explanation: {q['explanation']}")

            if st.button("Next Question"):
                st.session_state.current_q += 1
                st.session_state.submitted = False
                st.session_state.user_answer = None

    else:
        st.header("Test Completed!")
        st.write(f"Your final score: **{st.session_state.score} / {len(st.session_state.questions)}**")

        if st.button("Review Answers"):
            st.session_state.review_mode = True

        if st.button("Restart Test"):
            st.session_state.score = 0
            st.session_state.current_q = 0
            st.session_state.submitted = False
            st.session_state.user_answer = None
            st.session_state.review_mode = False
            st.session_state.answers_log = []

