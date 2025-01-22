import logging
import os
import tempfile
import shutil
from typing import Optional, Dict, Any
from dataclasses import dataclass
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings import OllamaEmbeddings, logger
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOllama
from sentence_transformers import util



@dataclass
class LearningProgress:
    completed: bool = False
    attempts: int = 0
    hints_given: list[str] = None

    def __post_init__(self):
        if self.hints_given is None:
            self.hints_given = []


class DocumentProcessor:
    def __init__(self):
        self.temp_dir: Optional[str] = None
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.logger = logging.getLogger(__name__)  # Add this line

    def create_vector_db(self, file_upload) -> Optional[Chroma]:
        """
        Create a vector database from an uploaded PDF file with improved error handling
        and document processing.
        """
        try:
            self.logger.info("Creating vector DB from file upload")  # Use self.logger
            self.temp_dir = tempfile.mkdtemp()
            path = os.path.join(self.temp_dir, "temp.pdf")

            with open(path, "wb") as f:
                f.write(file_upload.read())  # Changed from getvalue() to read()

            loader = PyPDFLoader(path)
            documents = loader.load()

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=5000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
                length_function=len
            )
            chunks = text_splitter.split_documents(documents)

            vector_db = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                collection_name="enhanced_RAG",
                collection_metadata={"description": "Enhanced RAG for interactive learning"}
            )

            self.logger.info("Vector DB created successfully")  # Use self.logger
            return vector_db

        except Exception as e:
            self.logger.error(f"Error creating vector DB: {str(e)}")  # Use self.logger
            raise  # Re-raise the exception to be handled by the caller

        finally:
            if self.temp_dir:
                shutil.rmtree(self.temp_dir, ignore_errors=True)


class ResponseGenerator:
    def __init__(self):
        self.llm = ChatOllama(model="llama3.2", temperature=0.9)
        self.similarity_threshold = 0.85
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")

    def generate_response(self, question: str, vector_db: Chroma,
                          correct_answer: str, user_answer: str,
                          progress: LearningProgress) -> str:
        """
        Generate a comprehensive response based on the user's answer and current progress.
        """
        try:
            similarity = self._calculate_similarity(correct_answer, user_answer)

            if similarity > self.similarity_threshold:
                return self._handle_correct_answer(progress)

            context = self._get_enhanced_context(question, vector_db)
            template = self._get_dynamic_prompt_template(progress)
            response = self._generate_llm_response(template, context, question,
                                                   user_answer, correct_answer, progress)

            progress.attempts += 1
            return response

        except Exception as e:
            logger.error(f"Error in generate_response: {str(e)}")
            return "I encountered an issue processing your answer. Please try again."

    def _calculate_similarity(self, correct_answer: str, user_answer: str) -> float:
        """Calculate semantic similarity with improved accuracy."""
        correct_embedding = self.embeddings.embed_query(correct_answer)
        user_embedding = self.embeddings.embed_query(user_answer)
        return util.cos_sim(correct_embedding, user_embedding).item()

    def _get_enhanced_context(self, question: str, vector_db: Chroma) -> str:
        """Retrieve and process relevant context with improved relevance."""
        retriever = vector_db.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5, "fetch_k": 8}
        )
        relevant_docs = retriever.get_relevant_documents(question)
        return "\n".join([doc.page_content for doc in relevant_docs[:3]])

    def _handle_correct_answer(self, progress: LearningProgress) -> str:
        """Generate appropriate response for correct answers based on progress."""
        if not progress.completed:
            progress.completed = True
            attempts_feedback = (
                "Excellent work! You found the solution on your first try!"
                if progress.attempts == 0 else
                f"Well done! You persevered and found the correct answer after {progress.attempts + 1} attempts."
            )
            return f"🎉 Congratulations! {attempts_feedback} Your understanding has grown through this process."
        return "."

    def _get_dynamic_prompt_template(self, progress: LearningProgress) -> str:
        """Generate a dynamic prompt template based on user progress."""
        if progress.attempts == 0:
            return """
            You are an encouraging educational AI assistant. The user is just starting to work on this problem. 

            Context: {context}

            Question: {question}
            User's First Attempt: {user_answer}

            Provide gentle guidance and a starting point for thinking about the problem. 
            Focus on understanding the question and identifying key concepts.
            """
        elif progress.attempts < 3:
            return """
            You are an educational AI assistant helping a student who is making progress.
            

            Context: {context}
            Previous Attempts: {attempts}

            Question: {question}
            Latest Answer: {user_answer}

            Provide more specific hints based on their answer. Point out what they've understood correctly
            and gently guide them toward areas they might have missed.  
            """
        else:
            return """
            You are an educational AI assistant helping a student who might be struggling.

            Context: {context}
            Attempts Made: {attempts}

            Question: {question}
            Latest Answer: {user_answer}

            Break down the problem into smaller steps. Provide more structured guidance
            while still encouraging independent thinking. Consider suggesting different
            approaches or ways of thinking about the problem. 
            """

    def _generate_llm_response(self, template: str, context: str,
                               question: str, user_answer: str,
                               correct_answer: str, progress: LearningProgress) -> str:
        """Generate LLM response using the provided template and context."""
        prompt = ChatPromptTemplate.from_template(template)

        messages = prompt.format_prompt(
            context=context,
            question=question,
            user_answer=user_answer,
            attempts=progress.attempts,
            previous_hints=", ".join(progress.hints_given)
        ).to_messages()

        try:
            response = self.llm.generate([messages])
            hint = response.generations[0][0].text.strip()

            if hint not in progress.hints_given:
                progress.hints_given.append(hint)

            return self._format_response(hint, progress)
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return "I encountered an issue generating feedback. Please try again or rephrase your answer."

    def _format_response(self, hint: str, progress: LearningProgress) -> str:
        """Format the response with appropriate encouragement based on progress."""
        encouragement = self._get_encouragement(progress.attempts)
        return f"{encouragement}\n\n{hint}"

    def _get_encouragement(self, attempts: int) -> str:
        """Get appropriate encouragement based on number of attempts."""
        encouragements = {
            0: "Let's start exploring this together!",
            1: "You're making progress! Keep thinking about it.",
            2: "You're getting closer! Consider these points:",
            3: "Don't give up! Here's a different way to think about it:",
            4: "You're putting in great effort! Let's break this down further:"
        }
        return encouragements.get(attempts, "Keep persevering! Here's some guidance:")

