import streamlit as st
import fitz  
import re

def parse_pdf_questions(pdf_bytes):
    """Parse questions from uploaded PDF bytes.
    Assumes each question starts with a number and dot,
    options A-D, Answer: <letter>, Explanation: <text>
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()

    # Split questions by pattern: number dot space (e.g. 1. , 2. )
    raw_questions = re.split(r'\n\d+\.\s', full_text)
    parsed_questions = []

    for raw_q in raw_questions[1:]:  # skip first split which is before question 1
        try:
            # Extract question text (up to first option)
            question_match = re.match(r'(.+?)(?=\nA\.)', raw_q, re.DOTALL)
            question_text = question_match.group(1).strip()

            # Extract options
            options_match = re.findall(r'\n([A-D])\.\s(.+?)(?=\n[A-D]\.|Answer:)', raw_q + "\nZ.", re.DOTALL)
            options = [opt[1].strip() for opt in options_match]

            # Extract answer letter
            answer_match = re.search(r'Answer:\s*([A-D])', raw_q)
            answer_letter = answer_match.group(1).strip()

            # Map answer letter to actual option text
            answer_index = ord(answer_letter) - ord('A')
            correct_answer = options[answer_index]

            # Extract explanation
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


# Initialize session state variables
if 'questions' not in st.session_state:
    # Default sample questions if no PDF uploaded yet
    st.session_state.questions = [
        {
            'question': 'What is the primary neurotransmitter at the neuromuscular junction?',
            'options': ['Dopamine', 'Acetylcholine', 'GABA', 'Serotonin'],
            'answer': 'Acetylcholine',
            'explanation': 'Acetylcholine stimulates muscle contraction at the neuromuscular junction.'
        },
        {
            'question': 'Which of the following drugs is used to reverse opioid overdose?',
            'options': ['Naloxone', 'Atropine', 'Flumazenil', 'Physostigmine'],
            'answer': 'Naloxone',
            'explanation': 'Naloxone is a competitive opioid receptor antagonist used to rapidly reverse opioid overdose.'
        },
    ]
    st.session_state.score = 0
    st.session_state.current_question = 0
    st.session_state.user_answers = []
    st.session_state.submitted = False

st.title("adwenBolobo: USMLE Practice App with PDF Upload")

# PDF Upload
uploaded_pdf = st.file_uploader("Upload your questions PDF", type=["pdf"])
if uploaded_pdf is not None:
    pdf_bytes = uploaded_pdf.read()
    parsed = parse_pdf_questions(pdf_bytes)
    if parsed:
        st.session_state.questions = parsed
        st.session_state.score = 0
        st.session_state.current_question = 0
        st.session_state.user_answers = []
        st.session_state.submitted = False
        st.success(f"Loaded {len(parsed)} questions from PDF!")
        st.experimental_rerun()
    else:
        st.error("No valid questions found in the uploaded PDF.")

# Main Quiz Logic
questions = st.session_state.questions
current = st.session_state.current_question

if current < len(questions):
    q = questions[current]
    st.write(f"### Question {current + 1} of {len(questions)}")
    st.write(q['question'])

    if not st.session_state.submitted:
        user_answer = st.radio("Select your answer:", q['options'], key="answer_radio")

        if st.button("Submit"):
            st.session_state.submitted = True
            st.session_state.user_answers.append(user_answer)

            if user_answer == q['answer']:
                st.session_state.score += 1
                st.success("Correct!")
            else:
                st.error(f"Incorrect. Correct answer: {q['answer']}")

            st.info(f"Explanation: {q['explanation']}")

    else:
        st.info(f"Explanation: {q['explanation']}")
        if st.button("Next Question"):
            st.session_state.current_question += 1
            st.session_state.submitted = False
            st.experimental_rerun()

else:
    st.write("## Test Completed!")
    st.write(f"Your Score: {st.session_state.score} / {len(questions)}")
    if st.button("Restart Test"):
        st.session_state.score = 0
        st.session_state.current_question = 0
        st.session_state.user_answers = []
        st.session_state.submitted = False
        st.experimental_rerun()
