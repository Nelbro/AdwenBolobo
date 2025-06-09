import streamlit as st
import json
import re
import pdfplumber
import random
import time
from typing import List, Dict

# ----------------------
# --- Helper Functions -
# ----------------------

def init_session_state():
    defaults = {
        'questions': DEFAULT_QUESTIONS,
        'score': 0,
        'current_q': 0,
        'submitted': False,
        'user_answer': None,
        'review_mode': False,
        'answers_log': [],
        'randomized': False,
        'start_time': None,
        'elapsed_time': 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def load_questions_from_json(json_str: str) -> List[Dict]:
    try:
        data = json.loads(json_str)
        assert isinstance(data, list)
        valid = []
        for q in data:
            if all(k in q for k in ['question', 'options', 'answer', 'explanation']):
                valid.append(q)
        if len(valid) < len(data):
            st.warning("Some questions were skipped due to missing fields.")
        return valid
    except Exception as e:
        st.error(f"Failed to load JSON questions: {e}")
        return []

def load_questions_from_text(text: str) -> List[Dict]:
    questions = []
    blocks = text.strip().split('\n\n')
    for block in blocks:
        lines = block.strip().split('\n')
        question, options, answer_letter, explanation = '', [], '', ''
        current_section = ''
        for line in lines:
            line = line.strip()
            if line.startswith('Question:'):
                question = line[len('Question:'):].strip()
                current_section = 'question'
            elif line.startswith('Options:'):
                current_section = 'options'
            elif line.startswith('Answer:'):
                answer_letter = line[len('Answer:'):].strip()
                current_section = 'answer'
            elif line.startswith('Explanation:'):
                explanation = line[len('Explanation:'):].strip()
                current_section = 'explanation'
            elif current_section == 'options' and line:
                m = re.match(r'^([A-Z])\.\s*(.+)', line)
                if m:
                    options.append(m.group(2).strip())
            elif current_section == 'explanation':
                explanation += ' ' + line
        if question and options and answer_letter:
            answer_index = ord(answer_letter.upper()) - ord('A')
            if 0 <= answer_index < len(options):
                answer = options[answer_index]
            else:
                answer = None
            if answer:
                questions.append({
                    'question': question,
                    'options': options,
                    'answer': answer,
                    'explanation': explanation.strip() or "No explanation provided."
                })
    if not questions:
        st.warning("No valid questions found. Check your format.")
    return questions

def load_questions_from_pdf(file) -> List[Dict]:
    try:
        text = ''
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
        return load_questions_from_text(text)
    except Exception as e:
        st.error(f"Failed to load PDF questions: {e}")
        return []

# -------------------------
# --- Default Questions ----
# -------------------------
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

# -------------------------
# --- UI Design & Logic ----
# -------------------------
st.set_page_config("adwenBolobo USMLE Quiz", page_icon="🧠", layout="centered")
st.markdown("""
    <style>
    .title { font-size:2.7em; font-weight:900; color:#2e8b57;}
    .subtitle { font-size:1.2em; color:#666;}
    .stButton>button { background: #2e8b57; color: white;}
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #2e8b57, #16a085);}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">adwenBolobo: USMLE Practice App</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Practice with USMLE-style questions. Upload your own, randomize, track your progress, and get instant feedback!</div>', unsafe_allow_html=True)

init_session_state()

# --- Timer ---
if st.session_state['start_time'] is None:
    st.session_state['start_time'] = time.time()
st.session_state['elapsed_time'] = int(time.time() - st.session_state['start_time'])

# --- Upload and Randomize ---
with st.expander("📥 Upload your own questions (JSON, TXT, or PDF)"):
    st.write("**You can upload your own questions as JSON, TXT, or PDF files.**")
    st.write("For TXT/PDF files, use this format:")
    st.code("""
Question: <question text>
Options:
A. <option1>
B. <option2>
C. <option3>
D. <option4>
Answer: <correct option letter>
Explanation: <explanation text>
""")
    uploaded_file = st.file_uploader("Upload questions", type=['json', 'txt', 'pdf'])
    if uploaded_file is not None:
        file_type = uploaded_file.type
        if file_type == 'application/json':
            file_content = uploaded_file.read().decode("utf-8")
            loaded_questions = load_questions_from_json(file_content)
        elif file_type == 'text/plain':
            file_content = uploaded_file.read().decode("utf-8")
            loaded_questions = load_questions_from_text(file_content)
        elif file_type == 'application/pdf':
            loaded_questions = load_questions_from_pdf(uploaded_file)
        else:
            st.error("Unsupported file type. Please upload a JSON, TXT, or PDF file.")
            loaded_questions = []
        if loaded_questions:
            st.session_state.questions = loaded_questions
            st.session_state.score = 0
            st.session_state.current_q = 0
            st.session_state.submitted = False
            st.session_state.user_answer = None
            st.session_state.review_mode = False
            st.session_state.answers_log = []
            st.session_state.randomized = False
            st.session_state.start_time = time.time()
            st.success(f"{len(loaded_questions)} questions uploaded successfully! Starting fresh.")
            st.rerun()
        else:
            st.error("No valid questions found in the file. Please check the format.")

st.divider()

colA, colB = st.columns([1,1])
with colA:
    if not st.session_state.randomized and st.button("🔀 Randomize Questions"):
        random.shuffle(st.session_state.questions)
        st.session_state.current_q = 0
        st.session_state.score = 0
        st.session_state.answers_log = []
        st.session_state.submitted = False
        st.session_state.user_answer = None
        st.session_state.review_mode = False
        st.session_state.randomized = True
        st.session_state.start_time = time.time()
        st.success("Questions randomized! Starting fresh.")
        st.rerun()
with colB:
    st.info(f"⏱️ Time elapsed: {st.session_state['elapsed_time']} seconds", icon="⏱️")

# --- Review Mode ---
if st.session_state.review_mode:
    st.header("📖 Review Mode")
    for idx, entry in enumerate(st.session_state.answers_log):
        st.write(f"**Q{idx + 1}:** {entry['question']}")
        st.write(f"Your answer: {entry['user_answer']}")
        if entry['user_answer'] == entry['correct_answer']:
            st.success("✅ Correct")
        else:
            st.error(f"❌ Incorrect (Correct: {entry['correct_answer']})")
        st.info(f"💡 Explanation: {entry['explanation']}")
        st.markdown("---")
    if st.button("🔄 Restart Test"):
        st.session_state.score = 0
        st.session_state.current_q = 0
        st.session_state.submitted = False
        st.session_state.user_answer = None
        st.session_state.review_mode = False
        st.session_state.answers_log = []
        st.session_state.start_time = time.time()
        st.rerun()

# --- Quiz Mode ---
else:
    if st.session_state.current_q < len(st.session_state.questions):
        q = st.session_state.questions[st.session_state.current_q]

        st.markdown(
            f"<h3 style='color:#2e8b57;'>Question {st.session_state.current_q + 1} of {len(st.session_state.questions)}</h3>",
            unsafe_allow_html=True
        )
        st.progress((st.session_state.current_q) / len(st.session_state.questions))
        st.markdown(f"<div style='font-size:1.1em;'><b>{q['question']}</b></div>", unsafe_allow_html=True)

        # Answer Selection
        user_answer = st.radio("Select your answer:", q['options'], index=0, key=f'answer_radio_{st.session_state.current_q}',
                              label_visibility="collapsed")

        col1, col2, col3 = st.columns([1,2,1])
        with col1:
            if st.session_state.current_q > 0 and st.button("⬅️ Back"):
                st.session_state.current_q -= 1
                st.session_state.submitted = False
                st.session_state.user_answer = None
                st.rerun()
        with col2:
            if not st.session_state.submitted and st.button("✅ Submit Answer"):
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
                st.rerun()
        with col3:
            if st.button("➡️ Skip"):
                st.session_state.current_q += 1
                st.session_state.submitted = False
                st.session_state.user_answer = None
                st.rerun()

        if st.session_state.submitted:
            if st.session_state.user_answer == q['answer']:
                st.success("🎉 Correct!")
            else:
                st.error(f"🙁 Incorrect. Correct answer: {q['answer']}")
            st.info(f"💡 Explanation: {q['explanation']}")
            if st.button("Next Question ➡️"):
                st.session_state.current_q += 1
                st.session_state.submitted = False
                st.session_state.user_answer = None
                st.rerun()
    else:
        st.header("🏁 Test Completed!")
        st.write(f"Your score: **{st.session_state.score} / {len(st.session_state.questions)}**")
        st.info(f"⏱️ Total time: {st.session_state['elapsed_time']} seconds")
        col_review, col_restart = st.columns([1,1])
        with col_review:
            if st.button("📖 Review Answers"):
                st.session_state.review_mode = True
                st.rerun()
        with col_restart:
            if st.button("🔄 Restart Test"):
                st.session_state.score = 0
                st.session_state.current_q = 0
                st.session_state.submitted = False
                st.session_state.user_answer = None
                st.session_state.review_mode = False
                st.session_state.answers_log = []
                st.session_state.start_time = time.time()
                st.rerun()
