import streamlit as st
import logging
from datetime import datetime
import json
from pathlib import Path
from core import DocumentProcessor

logger = logging.getLogger(__name__)

def setup_teacher_ui():
    # Create exercises directory in the same folder as the app
    current_dir = Path(__file__).parent  # Gets the directory where your script is
    exercises_dir = current_dir / "exercises"
    exercises_dir.mkdir(exist_ok=True)

    st.title("👨‍🏫 Exercise Creation Interface")

    # Show the exercises directory path
    st.sidebar.info(f"Exercises are stored in: {exercises_dir}")

    with st.form("exercise_form"):
        title = st.text_input("Exercise Title")
        question = st.text_area("Question:", height=200)
        correct_answer = st.text_area("Correct Answer:", height=300)
        pdf_file = st.file_uploader("Upload Reference Material (PDF):", type="pdf")

        if st.form_submit_button("Create Exercise"):
            if all([title, question, correct_answer, pdf_file]):
                try:
                    # Create unique filename for the exercise
                    exercise_id = datetime.now().strftime("%Y%m%d_%H%M%S")

                    # Save PDF file
                    pdf_path = exercises_dir / f"{exercise_id}.pdf"
                    pdf_path.write_bytes(pdf_file.getvalue())

                    # Save exercise metadata
                    metadata = {
                        "id": exercise_id,
                        "title": title,
                        "question": question,
                        "correct_answer": correct_answer
                    }

                    metadata_path = exercises_dir / f"{exercise_id}.json"
                    metadata_path.write_text(json.dumps(metadata, indent=2))

                    st.success(f"Exercise saved successfully in {exercises_dir}")

                except Exception as e:
                    st.error(f"Error saving exercise: {str(e)}")
            else:
                st.error("Please fill all required fields")

    # Show existing exercises with options to edit or delete
    st.subheader("Existing Exercises")
    for json_file in exercises_dir.glob("*.json"):
        with json_file.open() as f:
            data = json.load(f)
            st.text(f"• {data['title']} (ID: {data['id']})")

            col1, col2 = st.columns([1, 2])
            with col1:
                edit_button = st.button("Edit", key=f"edit_{data['id']}")
            with col2:
                delete_button = st.button("Delete", key=f"delete_{data['id']}")

            # Edit functionality
            if edit_button:
                with st.form(f"edit_form_{data['id']}"):
                    new_title = st.text_input("New Title", value=data['title'])
                    new_question = st.text_area("New Question", value=data['question'], height=200)
                    new_correct_answer = st.text_area("New Correct Answer", value=data['correct_answer'], height=300)
                    new_pdf_file = st.file_uploader("Upload New PDF Reference Material", type="pdf")

                    if st.form_submit_button("Save Changes"):
                        if all([new_title, new_question, new_correct_answer, new_pdf_file]):
                            try:
                                # Save the updated PDF file
                                new_pdf_path = exercises_dir / f"{data['id']}.pdf"
                                new_pdf_path.write_bytes(new_pdf_file.getvalue())

                                # Update metadata
                                updated_metadata = {
                                    "id": data['id'],
                                    "title": new_title,
                                    "question": new_question,
                                    "correct_answer": new_correct_answer
                                }

                                updated_metadata_path = exercises_dir / f"{data['id']}.json"
                                updated_metadata_path.write_text(json.dumps(updated_metadata, indent=2))

                                st.success(f"Exercise {data['id']} updated successfully!")
                            except Exception as e:
                                st.error(f"Error updating exercise: {str(e)}")
                        else:
                            st.error("Please fill all required fields")

            # Delete functionality
            if delete_button:
                try:
                    # Delete the PDF file and metadata
                    pdf_path_to_delete = exercises_dir / f"{data['id']}.pdf"
                    json_path_to_delete = exercises_dir / f"{data['id']}.json"

                    if pdf_path_to_delete.exists():
                        pdf_path_to_delete.unlink()

                    if json_path_to_delete.exists():
                        json_path_to_delete.unlink()

                    st.success(f"Exercise {data['id']} deleted successfully!")
                except Exception as e:
                    st.error(f"Error deleting exercise: {str(e)}")

if __name__ == "__main__":
    setup_teacher_ui()
