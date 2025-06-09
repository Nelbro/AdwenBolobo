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
                questions.append({
                    'question': question,
                    'options': options,
                    'answer': answer,
                    'explanation': explanation.strip() or "No explanation provided."
                })
            else:
                st.warning(f"Skipped a question due to invalid answer option: {answer_letter}")
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
