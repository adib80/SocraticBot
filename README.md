# SocraticBot
This Interactive Learning platform utilises RAG (Retrieval-Augmented Generation) and LLM (Large Language Models) to deliver personalized education. Teachers design exercises (title, question, answer, PDF reference) via an intuitive interface, building a structured library. Students engage by solving exercises, with RAG processing uploaded PDFs into a vector database to retrieve content directly tied to the learning material, ensuring accuracy. LLMs analyze responses, generating dynamic hints and explanations tailored to the student’s progress, adapting feedback as their understanding evolves.

## Table of Contents
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)

## Technologies Used

- Python
- Llama 3.2 (local llm)
- Streamlit

### Setup

1. **Install Ollama Software:**

    https://ollama.com/download

2. **Run Llama3.2:**

   cmd - ollama run llama3.2
   Shut down the program after it finishes.

4. **Install Required Packages**
    
    pip install -r requirements.txt

## Usage

1. **Run the Ollama Server**

    cmd
    ollama serve

2. **Run the Streamlit project**

    py run teacher_app.py
    py run student_app.py


