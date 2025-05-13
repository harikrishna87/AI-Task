import os
import google.generativeai as genai

def get_system_prompt():
    """Returns the system prompt that defines the chatbot's behavior"""
    return """
    You are TalentBot, an AI hiring assistant for TalentScout recruitment agency. Your purpose is to:
    1. Greet candidates warmly and explain you'll help with initial screening
    2. Collect the following candidate information:
       - Full name
       - Email address
       - Phone number
       - Years of experience
       - Current location
       - Desired position(s)
    3. Once all information is collected, generate position-based technical MCQs
    4. Maintain professional, friendly tone throughout
    5. If user says goodbye or similar, conclude conversation gracefully

    Rules:
    - Be concise but friendly
    - Ask one question at a time
    - Verify email/phone format
    - Don't ask for sensitive information beyond what's specified
    - If unsure how to respond, say "I'm not sure I understand. Could you rephrase that?"
    """

def generate_tech_questions(position=None):
    """Generate technical questions using Google's Generative AI API"""
    if not position:
        return "Error: Position is required to generate relevant technical questions."
    
    try:
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        Generate 15 technical multiple-choice questions specifically for a '{position}' position.
        Each question should have 4 options (A, B, C, D) with only one correct answer.
        Questions should assess core competencies, practical knowledge, and problem-solving abilities 
        required for the '{position}' role.

        Format each question as:

        1. [Question text]
           - A) [Option A]
           - B) [Option B]
           - C) [Option C]
           - D) [Option D]

        Please provide only the questions and options, no additional commentary or explanation.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating technical questions: {str(e)}"