import streamlit as st
import time
import json
from typing import List, Dict

# -- Helper functions --

def load_questions_from_json(json_str: str) -> List[Dict]:
    """Load questions from JSON string."""
    try:
        data = json.loads(json_str)
        # Expected format: List of dicts with 'question', 'options', 'answer', 'explanation'
        assert isinstance(data, list)
        return data
    except Exception as e:
        st.error(f"Failed to load questions: {e}")
        return []

def timer(seconds: int):
    """Simple countdown timer UI."""
    placeholder = st.empty()
    for remaining in range(seconds, 0, -1):
        placeholder.markdown(f"⏳ Time left: **{remaining} seconds**")
        time.sleep(1)
    placeholder.empty()

# -- Default question bank --
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

# -- Initialize session state variables --
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
    # Store user answers for review [{question, user_answer, correct_answer, explanation}]
    st.session_state.answers_log = []

# -- App Title --
st.title("adwenBolobo: USMLE Practice App")

# -- Upload your own questions --
with st.expander("Upload your own questions (JSON format)"):
    uploaded_file = st.file_uploader("Upload JSON file with questions", type=['json'])
    if uploaded_file is not None:
        file_content = uploaded_file.read().decode("utf-8")
        loaded_questions = load_questions_from_json(file_content)
        if loaded_questions:
            st.session_state.questions = loaded_questions
            st.session_state.score = 0
            st.session_state.current_q = 0
            st.session_state.submitted = False
            st.session_state.user_answer = None
            st.session_state.review_mode = False
            st.session_state.answers_log = []
            st.success("Questions uploaded successfully! Starting fresh.")
            st.experimental_rerun()

# -- If review mode active --
if st.session_state.review_mode:
    st.header("Review Mode")
    for idx, entry in enumerate(st.session_state.answers_log):
        st.write(f"**Q{idx + 1}:** {entry['question']}")
        st.write(f"Your answer: {entry['user_answer']}")
        if entry['user_answer'] == entry['correct_answer']:
            st.success("Correct")
        else:
            st.error(f"Incorrect (Correct: {entry['correct_answer']})")
        st.write(f"Explanation: {entry['explanation']}")
        st.markdown("---")
    if st.button("Restart Test"):
        st.session_state.score = 0
        st.session_state.current_q = 0
        st.session_state.submitted = False
        st.session_state.user_answer = None
        st.session_state.review_mode = False
        st.session_state.answers_log = []
        st.experimental_rerun()

else:
    # -- Quiz mode --
    if st.session_state.current_q < len(st.session_state.questions):
        q = st.session_state.questions[st.session_state.current_q]
        st.write(f"**Question {st.session_state.current_q + 1}/{len(st.session_state.questions)}**")
        st.write(q['question'])

        # Show timer only before submission
        if not st.session_state.submitted:
            timer_seconds = 20  # Set per question timer (seconds)
            timer(timer_seconds)

        # Options radio
        user_answer = st.radio("Select your answer:", q['options'], index=0, key='answer_radio')

        if not st.session_state.submitted:
            if st.button("Submit Answer"):
                st.session_state.user_answer = user_answer
                st.session_state.submitted = True

                # Update score
                if user_answer == q['answer']:
                    st.session_state.score += 1

                # Log answer for review
                st.session_state.answers_log.append({
                    'question': q['question'],
                    'user_answer': user_answer,
                    'correct_answer': q['answer'],
                    'explanation': q['explanation']
                })

                st.experimental_rerun()

        else:
            # Show feedback
            if st.session_state.user_answer == q['answer']:
                st.success("Correct!")
            else:
                st.error(f"Incorrect. Correct answer: {q['answer']}")

            st.info(f"Explanation: {q['explanation']}")

            if st.button("Next Question"):
                st.session_state.current_q += 1
                st.session_state.submitted = False
                st.session_state.user_answer = None
                st.experimental_rerun()

    else:
        # Test complete
        st.header("Test Completed!")
        st.write(f"Your score: **{st.session_state.score} / {len(st.session_state.questions)}**")

        if st.button("Review Answers"):
            st.session_state.review_mode = True
            st.experimental_rerun()

        if st.button("Restart Test"):
            st.session_state.score = 0
            st.session_state.current_q = 0
            st.session_state.submitted = False
            st.session_state.user_answer = None
            st.session_state.review_mode = False
            st.session_state.answers_log = []
            st.experimental_rerun()
