import google.generativeai as genai
from system_prompt import system_prompt_5

def generate_sql_query(user_input):
    """
    Generate SQL query from natural language input using Google Gemini.
    
    Args:
        user_input (str): Natural language query from user
    
    Returns:
        str: Generated SQL query or None if error
    """
    try:
        # Configure API key
        genai.configure(api_key="")
        
        # Initialize the model with system instruction
        model = genai.GenerativeModel(
            model_name="models/gemini-2.0-flash",
            system_instruction=system_prompt_5
        )
        
        # Generate SQL query from user input
        response = model.generate_content(user_input)
        
        return response.text
        
    except Exception as e:
        print(f"LLM Error: {e}")
        return None
