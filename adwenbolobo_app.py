import streamlit as st
import re
import random
import time
from typing import List, Dict, Optional

# --------------------
# --- Constants ---
# --------------------
DEFAULT_QUESTIONS = [
    {
        "question": "What is the primary neurotransmitter at the neuromuscular junction?",
        "options": ["Dopamine", "Acetylcholine", "GABA", "Serotonin"],
        "answer": 1,
        "explanation": "Acetylcholine is the primary neurotransmitter at the neuromuscular junction."
    },
    {
        "question": "Which vitamin deficiency causes scurvy?",
        "options": ["Vitamin A", "Vitamin B12", "Vitamin C", "Vitamin D"],
        "answer": 2,
        "explanation": "Vitamin C deficiency causes scurvy."
    }
]

# --------------------
# --- Helpers ---
# --------------------

def init_session_state():
    defaults = {
        'questions': DEFAULT_QUESTIONS,
        'score': 0,
        'current_q': 0,
        'submitted': False,
        'user_answer': None,
        'review_mode': False,
        'answers_log': [],
        'start_time': time.time(),
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def parse_questions_from_text(text: str) -> List[Dict]:
    """
    Parse questions from a plain text string.
    Format example per question:
    Question: What is ...?
    A. Option 1
    B. Option 2
    C. Option 3
    D. Option 4
    Answer: B
    Explanation: ...
    """
    questions = []
    blocks = re.split(r'\n\s*\n', text.strip())
    for block in blocks:
        lines = block.strip().split('\n')
        q_data = {"question": "", "options": [], "answer": None, "explanation": ""}
        options = []
        answer_letter = None
        for line in lines:
            line = line.strip()
            if line.lower().startswith("question:"):
                q_data["question"] = line[len("question:"):].strip()
            elif re.match(r'^[A-Z]\.\s*', line):
                # Option line like "A. Text"
                m = re.match(r'^([A-Z])\.\s*(.*)', line)
                if m:
                    options.append(m.group(2).strip())
            elif line.lower().startswith("answer:"):
                ans = line[len("answer:"):].strip().upper()
                if len(ans) == 1 and 'A' <= ans <= chr(ord('A') + len(options) - 1):
                    answer_letter = ans
                else:
                    answer_letter = None
            elif line.lower().startswith("explanation:"):
                q_data["explanation"] = line[len("explanation:"):].strip()

        if q_data["question"] and options and answer_letter:
            q_data["options"] = options
            q_data["answer"] = ord(answer_letter) - ord('A')
            questions.append(q_data)
        # else skip malformed question block

    return questions

def load_questions_from_uploaded_file(uploaded_file) -> Optional[List[Dict]]:
    """
    Supports .txt files with the format described in parse_questions_from_text.
    """
    try:
        content = uploaded_file.read().decode("utf-8")
        questions = parse_questions_from_text(content)
        if not questions:
            st.error("No valid questions found in the uploaded file.")
            return None
        return questions
    except Exception as e:
        st.error(f"Failed to load questions: {e}")
        return None

def show_question(q_idx: int):
    questions = st.session_state.questions
    if q_idx >= len(questions):
        st.write("No more questions.")
        return
    q = questions[q_idx]
    st.markdown(f"### Question {q_idx+1} of {len(questions)}")
    st.write(q["question"])

    # Radio buttons for options
    options = q["options"]
    user_answer = st.radio("Select an answer:", options, key=f"answer_{q_idx}")

    if st.button("Submit Answer", key=f"submit_{q_idx}"):
        st.session_state.submitted = True
        st.session_state.user_answer = user_answer
        # Check correctness
        selected_idx = options.index(user_answer)
        correct_idx = q["answer"]
        correct = selected_idx == correct_idx

        if correct:
            st.session_state.score += 1

        st.session_state.answers_log.append({
            "question_idx": q_idx,
            "selected": selected_idx,
            "correct": correct
        })

    # Show feedback after submission
    if st.session_state.submitted and st.session_state.current_q == q_idx:
        selected_idx = options.index(st.session_state.user_answer)
        correct_idx = q["answer"]
        if selected_idx == correct_idx:
            st.success("Correct! 🎉")
        else:
            st.error(f"Incorrect. The correct answer is **{options[correct_idx]}**.")
        st.markdown(f"**Explanation:** {q.get('explanation','No explanation provided.')}")

def show_progress():
    progress = (st.session_state.current_q) / len(st.session_state.questions)
    st.progress(progress)

def show_navigation():
    col1, col2, col3, col4 = st.columns([1,1,2,1])

    with col1:
        if st.session_state.current_q > 0:
            if st.button("Back"):
                st.session_state.current_q -= 1
                st.session_state.submitted = False
                st.session_state.user_answer = None
                st.experimental_rerun()

    with col2:
        if st.button("Skip"):
            if st.session_state.current_q < len(st.session_state.questions) - 1:
                st.session_state.current_q += 1
                st.session_state.submitted = False
                st.session_state.user_answer = None
                st.experimental_rerun()

    with col4:
        if st.session_state.current_q < len(st.session_state.questions) - 1:
            if st.button("Next"):
                st.session_state.current_q += 1
                st.session_state.submitted = False
                st.session_state.user_answer = None
                st.experimental_rerun()

def show_summary():
    st.markdown(f"## Quiz Complete! Your score: {st.session_state.score} / {len(st.session_state.questions)}")
    st.markdown("Review your answers:")
    for log in st.session_state.answers_log:
        q = st.session_state.questions[log["question_idx"]]
        st.markdown(f"**Q:** {q['question']}")
        selected = q["options"][log["selected"]]
        correct = q["options"][q["answer"]]
        if log["correct"]:
            st.success(f"Your answer: {selected} (Correct)")
        else:
            st.error(f"Your answer: {selected} (Incorrect). Correct: {correct}")
        st.markdown(f"Explanation: {q.get('explanation', 'No explanation provided.')}")

def randomize_questions():
    random.shuffle(st.session_state.questions)
    st.session_state.current_q = 0
    st.session_state.score = 0
    st.session_state.answers_log = []
    st.session_state.submitted = False
    st.session_state.user_answer = None
    st.experimental_rerun()

def show_timer():
    elapsed = int(time.time() - st.session_state.start_time)
    st.write(f"⏱️ Time elapsed: {elapsed // 60}m {elapsed % 60}s")

# --------------------
# --- Main app ---
# --------------------

def main():
    st.title("adwenBolobo Quiz App")

    init_session_state()

    # File uploader
    uploaded_file = st.file_uploader("Upload your questions (.txt format)", type=["txt"])
    if uploaded_file:
        loaded_questions = load_questions_from_uploaded_file(uploaded_file)
        if loaded_questions:
            st.session_state.questions = loaded_questions
            st.session_state.current_q = 0
            st.session_state.score = 0
            st.session_state.answers_log = []
            st.session_state.submitted = False
            st.session_state.user_answer = None
            st.session_state.start_time = time.time()
            st.success(f"Loaded {len(loaded_questions)} questions successfully!")

    # Show timer
    show_timer()

    # Randomize button
    if st.button("Randomize Questions"):
        randomize_questions()

    if st.session_state.current_q >= len(st.session_state.questions):
        show_summary()
        return

    show_progress()
    show_question(st.session_state.current_q)
    show_navigation()

if __name__ == "__main__":
    main()
