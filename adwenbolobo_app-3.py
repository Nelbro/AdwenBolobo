import streamlit as st

# Sample AI-generated question bank
questions = [
    {
        'question': 'What is the primary neurotransmitter at the neuromuscular junction?',
        'options': ['Dopamine', 'Acetylcholine', 'GABA', 'Serotonin'],
        'answer': 'Acetylcholine',
        'explanation': 'Acetylcholine is the key neurotransmitter that stimulates muscle contraction at the neuromuscular junction.'
    },
    {
        'question': 'Which of the following drugs is used to reverse opioid overdose?',
        'options': ['Naloxone', 'Atropine', 'Flumazenil', 'Physostigmine'],
        'answer': 'Naloxone',
        'explanation': 'Naloxone is a competitive opioid receptor antagonist used to rapidly reverse opioid overdose.'
    },
]

st.title("adwenBolobo: USMLE Practice App")

# Initialize session state variables
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = []
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'is_correct' not in st.session_state:
    st.session_state.is_correct = False

# Main quiz logic
if st.session_state.current_question < len(questions):
    q = questions[st.session_state.current_question]
    st.write(f"**Question {st.session_state.current_question + 1}:** {q['question']}")

    user_answer = st.radio("Select your answer:", q['options'], key='answer_radio')

    if not st.session_state.submitted:
        if st.button("Submit"):
            st.session_state.user_answers.append(user_answer)
            st.session_state.is_correct = (user_answer == q['answer'])
            if st.session_state.is_correct:
                st.session_state.score += 1
            st.session_state.submitted = True
            st.experimental_rerun()

    else:
        if st.session_state.is_correct:
            st.success("Correct!")
        else:
            st.error(f"Incorrect. Correct answer: {q['answer']}")

        st.info(f"Explanation: {q['explanation']}")

        if st.button("Next"):
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
