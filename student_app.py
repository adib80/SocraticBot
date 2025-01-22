# student_app.py
import streamlit as st
import logging
from pathlib import Path
import json
from core import DocumentProcessor, ResponseGenerator, LearningProgress

logger = logging.getLogger(__name__)

def setup_student_ui():
    logger.info("Starting student UI setup")
    st.set_page_config(
        page_title="Interactive Learning Interface",
        page_icon="👨‍🎓",
        layout="wide"
    )

    st.title("👨‍🎓 Interactive Learning Interface")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "progress" not in st.session_state:
        st.session_state.progress = LearningProgress()

    # Load exercises
    current_dir = Path(__file__).parent
    exercises_dir = current_dir / "exercises"

    if not exercises_dir.exists():
        st.error("No exercises available yet.")
        return

    # Get all exercise files
    exercise_files = list(exercises_dir.glob("*.json"))
    exercises = []

    for ex_file in exercise_files:
        with open(ex_file, 'r') as f:
            exercise_data = json.load(f)
            exercises.append(exercise_data)

    if not exercises:
        st.error("No exercises found.")
        return

    # Exercise selection
    selected_exercise = st.selectbox(
        "Select Exercise",
        options=exercises,
        format_func=lambda x: x['title']
    )

    if selected_exercise:
        st.write("### Exercise Details")
        st.write(f"**Question:** {selected_exercise['question']}")

        # Initialize or get vector store for RAG
        if "vector_db" not in st.session_state:
            with st.spinner("Loading exercise materials..."):
                pdf_path = exercises_dir / f"{selected_exercise['id']}.pdf"
                try:
                    with open(pdf_path, "rb") as f:
                        doc_processor = DocumentProcessor()
                        st.session_state.vector_db = doc_processor.create_vector_db(f)
                    st.success("Materials loaded successfully!")
                except Exception as e:
                    st.error(f"Error loading materials: {str(e)}")
                    return

        # Show chat history
        st.write("### Your Learning Session")
        chat_container = st.container()

        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # Progress information
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Attempts", st.session_state.progress.attempts)
        with col2:
            st.metric("Hints Given", len(st.session_state.progress.hints_given))

        # Input for student's answer
        user_input = st.chat_input("Type your answer here...")

        if user_input:
            # Show user's message
            with st.chat_message("user"):
                st.markdown(user_input)
            st.session_state.messages.append({"role": "user", "content": user_input})

            # Generate AI response
            with st.spinner("Analyzing your answer..."):
                try:
                    response_generator = ResponseGenerator()
                    response = response_generator.generate_response(
                        question=selected_exercise["question"],
                        vector_db=st.session_state.vector_db,
                        correct_answer=selected_exercise["correct_answer"],
                        user_answer=user_input,
                        progress=st.session_state.progress
                    )

                    # Show AI's response
                    with st.chat_message("assistant"):
                        st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

                    # If answer is correct, show celebration
                    if "Congratulations" in response:
                        st.balloons()

                except Exception as e:
                    st.error(f"Error generating response: {str(e)}")

            # Force a rerun to update the UI
            st.rerun()

        # Show hints given so far
        if st.session_state.progress.hints_given:
            with st.expander("Previous Hints"):
                for i, hint in enumerate(st.session_state.progress.hints_given, 1):
                    st.write(f"{i}. {hint}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    setup_student_ui()