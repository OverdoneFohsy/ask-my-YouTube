from dotenv import load_dotenv
from google import genai

_llm_service_instance = None

class LLMService:
    def __init__(self):
        self.client = genai.Client()

    def generate_response(self, question:str, context_chunks:list, history:list):
        try:
            context_text = "\n\n".join(c['text'] for c in context_chunks)

            formatted_history = "\n".join([f"{msg.role.capitalize()}: {msg.content}" for msg in history])

            prompt = f"""
            You are an Assistant. You help users analyze their uploaded videos and PDFs.

            CONVERSATION HISTORY:
            {formatted_history if formatted_history else "No previous history."}

            PRIMARY SOURCE (Video Transcript OR PDF):
            {context_text}

            SECONDARY SOURCE (Your Knowledge):
            Use your general knowledge if the primary source doesn't contain the answer.
            
            INSTRUCTIONS:
            1. PRIORITIZE the "Uploaded Content Context" above. If the answer is found there, cite the source type (e.g., "According to the video..." or "Based on the PDF..."). The source type can be determined from the "source_type" metdata of the source.
            2. If the answer is NOT in the provided context, answer the question using your general knowledge (Secondary Source). 
            3. TRANSPARENCY: If using general knowledge, briefly mention that the information was not found in their specific files.
            4. For every factual claim, you MUST cite the source in brackets using this format: [Source Name, Timestamp/Page]. Example: 'Photosynthesis occurs in the chloroplast [Biology Lecture, 12:45].'

            USER QUESTION:
            {question}
            """

            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )

            print(f"response: {response}")

            return response.text
        
        except Exception as e:
            print(f"Error in generating response: {e}")
            return None
    
def get_llm_service():
    global _llm_service_instance
    if not _llm_service_instance:
        _llm_service_instance = LLMService()

    return _llm_service_instance