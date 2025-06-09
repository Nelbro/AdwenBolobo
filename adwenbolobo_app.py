# adwenBolobo: USMLE-Style Question Practice App

## Repository Structure

Your GitHub repository should have the following structure:

adwenbolobo/
- app.py
- requirements.txt
- README.md

---

## 1. app.py (Python App)

```python
import streamlit as st
import random

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
    # You can add more questions here
]

st.title("adwenBolobo: USMLE Practice App")

if 'score' not in st.session_state:
    st.session_state.score = 0
    st.session_state.current_question = 0
    st.session_state.user_answers = []

if st.session_state.current_question < len(questions):
    q = questions[st.session_state.current_question]
    st.write(f"**Question {st.session_state.current_question + 1}:** {q['question']}")

    user_answer = st.radio("Select your answer:", q['options'])

    if st.button("Submit"):
        st.session_state.user_answers.append(user_answer)

        if user_answer == q['answer']:
            st.session_state.score += 1
            st.success("Correct!")
        else:
            st.error(f"Incorrect. Correct answer: {q['answer']}")

        st.info(f"Explanation: {q['explanation']}")

        st.session_state.current_question += 1
        st.experimental_rerun()

else:
    st.write("## Test Completed!")
    st.write(f"Your Score: {st.session_state.score} / {len(questions)}")

    if st.button("Restart Test"):
        st.session_state.score = 0
        st.session_state.current_question = 0
        st.session_state.user_answers = []
        st.experimental_rerun()
```

---

## 2. requirements.txt (Python Dependencies)

```txt
streamlit
```

---

## 3. README.md (Basic Instructions)

```md
# adwenBolobo: USMLE-Style Question Practice App

This is a simple USMLE practice app built with Streamlit. You can deploy it directly to Streamlit Cloud.

## How to Run Locally

1. Clone this repository.
2. Run `pip install -r requirements.txt`.
3. Run `streamlit run app.py`.

## How to Deploy on Streamlit Cloud

1. Upload this repository to GitHub.
2. Go to https://streamlit.io/cloud.
3. Click "New App" and connect your GitHub.
4. Select this repository and `app.py` as the main file.
5. Click Deploy and start practicing!
```
