import streamlit as st
import json
import re
import pdfplumber

class QuestionLoader:
    @staticmethod
    def load_questions_from_json(json_str):
        try:
            data = json.loads(json_str)
            if not isinstance(data, list):
                raise ValueError("JSON must be a list of questions")
            questions = []
            for item in data:
                # Validate keys
                if not all(k in item for k in ("question", "options", "answer_letter", "explanation")):
                    raise ValueError("Each question must have 'question', 'options', 'answer_letter', and 'explanation'")
                if not isinstance(item["options"], list) or len(item["options"]) < 2:
                    raise ValueError("Options must be a list with at least 2 choices")
                # Validate answer_letter
                letters = [chr(ord('A') + i) for i in range(len(item["options"]))]
                if item["answer_letter"] not in letters:
                    raise ValueError(f"Answer letter {item['answer_letter']} is invalid for given options")
                questions.append(item)
            return questions
        except Exception as e:
            st.error(f"Failed to load JSON questions: {e}")
            return []

    @staticmethod
    def load_questions_from_text(text):
        questions = []
        pattern_question = re.compile(r"^Question\s*\d+:\s*(.+)", re.IGNORECASE)
        pattern_option = re.compile(r"^([A-Z])\.\s*(.+)")
        lines = text.strip().split('\n')

        current_question = None
        current_options = []
        answer_letter = None
        explanation = None
        stage = None

        for line in lines:
            line = line.strip()
            if not line:
                continue
            q_match = pattern_question.match(line)
            if q_match:
                if current_question:
                    if current_options and answer_letter and explanation:
                        questions.append({
                            "question": current_question,
                            "options": current_options,
                            "answer_letter": answer_letter,
                            "explanation": explanation
                        })
                    else:
                        st.warning(f"Incomplete question skipped: {current_question}")
                current_question = q_match.group(1)
                current_options = []
                answer_letter = None
                explanation = None
                stage = 'options'
                continue
            if stage == 'options':
                opt_match = pattern_option.match(line)
                if opt_match:
                    current_options.append(opt_match.group(2))
                    continue
                if line.lower().startswith("answer:"):
                    ans = line.split(":", 1)[1].strip().upper()
                    if ans and ans in [chr(ord('A') + i) for i in range(len(current_options))]:
                        answer_letter = ans
                    else:
                        st.warning(f"Invalid answer letter '{ans}' for question: {current_question}")
                    stage = 'explanation'
                    continue
            if stage == 'explanation':
                if line.lower().startswith("explanation:"):
                    explanation = line.split(":", 1)[1].strip()
                    stage = None
                else:
                    # Support multi-line explanation
                    explanation = (explanation or "") + " " + line

        # Append last question
        if current_question and current_options and answer_letter and explanation:
            questions.append({
                "question": current_question,
                "options": current_options,
                "answer_letter": answer_letter,
                "explanation": explanation.strip()
            })

        if not questions:
            st.error("No valid questions found in the uploaded text.")
        return questions

    @staticmethod
    def load_questions_from_pdf(file):
        try:
            text = ""
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            return QuestionLoader.load_questions_from_text(text)
        except Exception as e:
            st.error(f"Failed to load PDF questions: {e}")
            return []

class QuizManager:
    def __init__(self, questions):
        self.questions = questions
        if "current_index" not in st.session_state:
            st.session_state.current_index = 0
        if "score" not in st.session_state:
            st.session_state.score = 0
        if "answers" not in st.session_state:
            st.session_state.answers = []

    def current_question(self):
        if self.questions and 0 <= st.session_state.current_index < len(self.questions):
            return self.questions[st.session_state.current_index]
        return None

    def submit_answer(self, selected_option):
        question = self.current_question()
        if not question:
            return

        correct_letter = question["answer_letter"]
        correct_option = question["options"][ord(correct_letter) - ord('A')]

        is_correct = (selected_option == correct_option)

        # Save answer
        if len(st.session_state.answers) <= st.session_state.current_index:
            st.session_state.answers.append(is_correct)
        else:
            st.session_state.answers[st.session_state.current_index] = is_correct

        if is_correct:
            st.session_state.score += 1

        return is_correct, question["explanation"]

    def next_question(self):
        if st.session_state.current_index < len(self.questions) - 1:
            st.session_state.current_index += 1
        else:
            st.session_state.current_index = 0  # Or end quiz

    def previous_question(self):
        if st.session_state.current_index > 0:
            st.session_state.current_index -= 1

def main():
    st.title("adwenBolobo Quiz App")

    # Upload questions
    upload_type = st.radio("Select upload type:", ["JSON", "Text", "PDF"])

    questions = []
    if upload_type == "JSON":
        uploaded_file = st.file_uploader("Upload JSON file", type=["json"])
        if uploaded_file:
            content = uploaded_file.read().decode("utf-8")
            questions = QuestionLoader.load_questions_from_json(content)
    elif upload_type == "Text":
        uploaded_file = st.file_uploader("Upload TXT file", type=["txt"])
        if uploaded_file:
            content = uploaded_file.read().decode("utf-8")
            questions = QuestionLoader.load_questions_from_text(content)
    elif upload_type == "PDF":
        uploaded_file = st.file_uploader("Upload PDF file", type=["pdf"])
        if uploaded_file:
            questions = QuestionLoader.load_questions_from_pdf(uploaded_file)

    if not questions:
        st.info("Upload a valid questions file to start the quiz.")
        return

    quiz = QuizManager(questions)

    question = quiz.current_question()
    if question:
        st.markdown(f"### Question {st.session_state.current_index + 1} / {len(questions)}")
        st.write(question["question"])

        option = st.radio("Select an answer:", question["options"], key=f"q{st.session_state.current_index}")

        if st.button("Submit Answer"):
            is_correct, explanation = quiz.submit_answer(option)
            if is_correct:
                st.success("Correct!")
            else:
                st.error(f"Incorrect! The correct answer is {question['answer_letter']}: {question['options'][ord(question['answer_letter']) - ord('A')]}")
            st.info(f"Explanation: {explanation}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Previous Question") and st.session_state.current_index > 0:
                quiz.previous_question()
        with col2:
            if st.button("Next Question") and st.session_state.current_index < len(questions) - 1:
                quiz.next_question()

        st.markdown(f"Score: {st.session_state.score} / {len(questions)}")

if __name__ == "__main__":
    main()
