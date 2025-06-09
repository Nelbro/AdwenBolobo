import streamlit as st
import json
from typing import List, Dict
import pdfplumber

# -------- Helper Functions --------

def load_questions_from_json(json_str: str) -> List[Dict]:
    """Load questions from JSON string."""
    try:
        data = json.loads(json_str)
        assert isinstance(data, list)
        return data
    except Exception as e:
        st.error(f"Failed to load JSON questions: {e}")
        return []

def load_questions_from_text(text: str) -> List[Dict]:
    """Parse questions from text format."""
    questions = []
    blocks = text.strip().split('\n\n')  # Each question block separated by 2 newlines
    for block in blocks:
        lines = block.strip().split('\n')
        question = ''
        options = []
        answer_letter = ''
        explanation = ''
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
                if len(line) > 2 and line[1] == '.':
                    options.append(line[3:].strip())
            elif current_section == 'explanation':
                explanation += ' ' + line
        if question and options and answer_letter and explanation:
            answer_index = ord(answer_letter.upper()) - ord('A')
            if 0 <= answer_index < len(options):
                answer = options[answer_index]
                questions.append({
                    'question': question,
                    'options': options,
                    'answer': answer,
                    'explanation': explanation.strip()
                })
    return questions

def load_questions_from_pdf(file) -> List[Dict]:
    """Extract text from PDF and parse questions."""
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

# -------- Default Questions --------
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

# -------- Initialize Session State --------
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

# -------- App UI --------

st.title("adwenBolobo: USMLE Practice App")

with st.expander("Upload your own questions (JSON, TXT, or PDF)"):
    st.write("For TXT and PDF files, use this exact format:")
    st.code("""
Question: What is the primary neurotransmitter at the neuromuscular junction?
Options:
A. Dopamine
B. Acetylcholine
C. GABA
D. Serotonin
Answer: B
Explanation: Acetylcholine stimulates muscle contraction at the neuromuscular junction.
    """)
    uploaded_file = st.file_uploader("Upload questions", type=['json', 'txt', 'pdf'])
    if uploaded_file is not None:
        file_type = uploaded_file.type
        if file_type == 'application/json':
            content = uploaded_file.read().decode("utf-8")
            loaded_questions = load_questions_from_json(content)
        elif file_type == 'text/plain':
            content = uploaded_file.read().decode("utf-8")
            loaded_questions = load_questions_from_text(content)
        elif file_type == 'application/pdf':
            loaded_questions = load_questions_from_pdf(uploaded_file)
        else:
            st.error("Unsupported file type. Upload JSON, TXT, or PDF only.")
            loaded_questions = []

        if loaded_questions:
            st.session_state.questions = loaded_questions
            st.session_state.score = 0
            st.session_state.current_q = 0
            st.session_state.submitted = False
            st.session_state.user_answer = None
            st.session_state.review_mode = False
            st.session_state.answers_log = []
            st.success("Questions uploaded successfully! Starting new test.")
            st.experimental_rerun()
        else:
            st.error("No valid questions found. Check your file format.")

# ------ Review Mode ------
if st.session_state.review_mode:
    st.header("Review Your Answers")
    for idx, entry in enumerate(st.session_state.answers_log):
        st.markdown(f"### Question {idx + 1}")
        st.write(entry['question'])
        st.write(f"Your answer: **{entry['user_answer']}**")
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
        st.experimental_rerun()

# ------ Quiz Mode ------
else:
    if st.session_state.current_q < len(st.session_state.questions):
        q = st.session_state.questions[st.session_state.current_q]
        st.markdown(f"### Question {st.session_state.current_q + 1} / {len(st.session_state.questions)}")
        st.write(q['question'])

        user_answer = st.radio("Select your answer:", q['options'], key='answer_radio')

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
                st.experimental_rerun()
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
                st.experimental_rerun()

    else:
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
