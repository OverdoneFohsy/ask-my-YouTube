from dotenv import load_dotenv
from google import genai

class LLMService:
    def __init__(self):
        self.client = genai.Client()

    def generate_response(self, question:str, context_chunks:list):
        try:
            context_text = "\n\n".join(c['text'] for c in context_chunks)

            prompt = f"""
            You are a YouTube Video Assistant. Use the transctript snippets below to answer the question.
            If the answer is not in the transcript, say you don't have enough information.

            TRANSCRIPT CONTEXT:
            {context_text}

            USER QUESTION:
            {question}
            """

            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )

            return response.text
        
        except Exception as e:
            print(f"Error in generating response: {e}")
            return None
    
def get_llm_service():
    return LLMService()