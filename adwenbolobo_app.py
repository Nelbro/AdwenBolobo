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

# -- Your existing default questions, init_session_state, etc. remain the same --

def load_questions_from_json(json_str: str) -> List[Dict]:
    # your existing function, unchanged
    ...

# Replace load_questions_from_text with our new cleaner + parser
load_questions_from_text = clean_and_parse_nbme_text


# -- Streamlit app code continues --

# In the Upload section, when file is uploaded:

uploaded_file = st.file_uploader("Upload questions", type=['json', 'txt'])
if uploaded_file is not None:
    file_type = uploaded_file.type
    file_content = uploaded_file.read().decode("utf-8")
    if file_type == 'application/json':
        loaded_questions = load_questions_from_json(file_content)
    elif file_type == 'text/plain':
        loaded_questions = load_questions_from_text(file_content)  # uses cleaner/parser here
    else:
        st.error("Unsupported file type. Please upload a JSON or TXT file.")
        loaded_questions = []
    if loaded_questions:
        st.session_state.questions = loaded_questions
        # reset states
        st.session_state.score = 0
        st.session_state.current_q = 0
        st.session_state.submitted = False
        st.session_state.user_answer = None
        st.session_state.review_mode = False
        st.session_state.answers_log = []
        st.session_state.randomized = False
        st.session_state.start_time = time.time()
        st.success(f"{len(loaded_questions)} questions uploaded successfully! Starting fresh.")
        st.experimental_rerun()
    else:
        st.error("No valid questions found in the file. Please check the format.")

# ... rest of your app code continues as is ...
