import streamlit as st
import json
import re
import random
import time
from typing import List, Dict

# -- Cleaning and Parsing function for raw NBME-like text --
def clean_and_parse_nbme_text(raw_text: str) -> List[Dict]:
    # Basic cleaning: unify line breaks, remove excessive spaces
    text = raw_text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'\n+', '\n', text)  # multiple newlines -> single newline
    text = re.sub(r' +', ' ', text)    # multiple spaces -> single space
    
    questions = []
    # Split by double newlines to separate questions
    blocks = re.split(r'\n\s*\n', text.strip())
    
    for block in blocks:
        lines = block.strip().split('\n')
        question, options, answer_letter, explanation = '', [], '', ''
        current_section = None
        
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
            else:
                if current_section == 'options':
                    # Expect lines like: A. option text
                    m = re.match(r'^([A-Z])\.\s*(.+)', line)
                    if m:
                        options.append(m.group(2).strip())
                elif current_section == 'explanation':
                    explanation += ' ' + line
        
        if question and options and answer_letter:
            answer_index = ord(answer_letter.upper()) - ord('A')
            if 0 <= answer_index < len(options):
                answer = options[answer_index]
                questions.append({
                    'question': question,
                    'options': options,
                    'answer': answer,
                    'explanation': explanation.strip() or "No explanation provided."
                })
    if not questions:
        st.warning("No valid questions found after cleaning. Check the file format.")
    return questions

# -- Load from JSON --
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

# -- Default Questions --
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

# -- Initialize session state --
def init_session_state():
    defaults = {
        'questions': DEFAULT_QUESTIONS,
        'score': 0,
        'current_q': 0,
        'submitted': False,
        'user_answer': None,
        'review_mode': False,
        'answers_log': [],
        'start_time': None,
        'elapsed_time': 0,
        'randomized': False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# -- App Title --
st.title("adwenBolobo: USMLE Practice App")

# -- Timer --
if st.session_state['start_time'] is None:
    st.session_state['start_time'] = time.time()
st.session_state['elapsed_time'] = int(time.time() - st.session_state['start_time'])

if st.session_state.review_mode:
    st.info(f"Total time: {st.session_state['elapsed_time']} seconds")

# -- Upload or Paste Questions --
with st.expander("Upload your own questions (JSON or TXT) or Paste Raw Questions Here"):
    st.write("**For TXT files or paste, use this format:**")
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
    uploaded_file = st.file_uploader("Upload questions file", type=['json', 'txt'])

    raw_text_input = st.text_area("Or paste your questions here (same format as above)", height=200)

    loaded_questions = []
    # If uploaded file present, use that
    if uploaded_file is not None:
        file_type = uploaded_file.type
        file_content = uploaded_file.read().decode("utf-8")
        if file_type == 'application/json':
            loaded_questions = load_questions_from_json(file_content)
        elif file_type == 'text/plain':
            loaded_questions = clean_and_parse_nbme_text(file_content)
        else:
            st.error("Unsupported file type. Please upload a JSON or TXT file.")
    # Else if text pasted, parse that
    elif raw_text_input.strip():
        loaded_questions = clean_and_parse_nbme_text(raw_text_input)

    if loaded_questions:
        if st.button("Load Questions"):
            st.session_state.questions = loaded_questions
            st.session_state.score = 0
            st.session_state.current_q = 0
            st.session_state.submitted = False
            st.session_state.user_answer = None
            st.session_state.review_mode = False
            st.session_state.answers_log = []
            st.session_state.randomized = False
            st.session_state.start_time = time.time()
            st.success(f"{len(loaded_questions)} questions loaded successfully! Starting fresh.")
            st.experimental_rerun()

# -- Randomize Questions Button --
if not st.session_state.randomized and st.button("Randomize Questions"):
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
    st.experimental_rerun()

# -- Review Mode --
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
        st.session_state.start_time = time.time()
        st.experimental_rerun()

# -- Quiz Mode --
else:
    if st.session_state.current_q < len(st.session_state.questions):
        q = st.session_state.questions[st.session_state.current_q]
        st.write(f"**Question {st.session_state.current_q + 1}/{len(st.session_state.questions)}**")
        st.progress((st.session_state.current_q) / len(st.session_state.questions))
        st.write(q['question'])

        # Timer for each question (optional)
        st.info(f"Time elapsed: {st.session_state['elapsed_time']} seconds")

        # Answer Selection
        user_answer = st.radio("Select your answer:", q['options'], index=0, key=f'answer_radio_{st.session_state.current_q}')

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.session_state.current_q > 0 and st.button("Back"):
                st.session_state.current_q -= 1
                st.session_state.submitted = False
                st.session_state.user_answer = None
                st.experimental_rerun()
        with col2:
            if not st.session_state.submitted and st.button("Submit Answer"):
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
        with col3:
            if st.button("Skip"):
                st.session_state.current_q += 1
                st.session_state.submitted = False
                st.session_state.user_answer = None
                st.experimental_rerun()

        if st.session_state.submitted:
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
        st.info(f"Total time: {st.session_state['elapsed_time']} seconds")
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
            st.session_state.start_time = time.time()
            st.experimental_rerun()
