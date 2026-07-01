import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AIScorer:
    def __init__(self):
        # 1. Configure the Gemini client
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing from the .env file")
            
        genai.configure(api_key=api_key)
        
        # 2. Initialize the model with strict JSON output enabled
        self.model = genai.GenerativeModel(
            model_name='gemini-3.5-flash', # Fast, cheap, perfect for repetitive tasks
            generation_config={
                "temperature": 0.2, # Keep it low for analytical consistency
                "response_mime_type": "application/json",
            }
        )
        
        # Hardcoding the profile so the AI knows who it is evaluating
        self.candidate_profile = """
        Role: Backend-focused Full-Stack Engineer
        Education: B.E. in Computer Science (CGPA: 8.0)
        Experience: ~1 year (Product company internships at Falabella & UnQue.me)
        Core Stack: Java, Python, TypeScript, Node.js, Spring Boot, React, React, JavaScript, 
        Databases & DevOps: MongoDB, PostgreSQL, Docker, AWS, CI/CD
        Concepts: Microservices, REST, GraphQL, scalable distributed systems, DSA (300+ LeetCode)
        """

    def evaluate_job(self, job_title: str, job_description: str) -> dict:
        """
        Passes the job description to Gemini to get a deep-context match score.
        """
        prompt = f"""
        You are an expert technical recruiter evaluating a job posting for this candidate:
        
        {self.candidate_profile}
        
        Job Title: {job_title}
        Job Description: 
        {job_description}
        
        Evaluate the match based on required years of experience, core tech stack alignment, and role responsibilities.
        
        CRITICAL RULES:
        1. Distinguish between "years of company history" and "years of required experience".
        2. If the Job Description is missing or extremely short, evaluate based purely on the Job Title being a fit for a Junior/1 YOE profile, and note the missing description in red flags.
        3. Always keep the roles that is hiring freshers/ Juniors or 1+ year experience  
        Return ONLY a valid JSON object with this exact schema:
        {{
            "ai_score": <int 0-100>,
            "verdict": "<Strong Match | Partial Match | Poor Match>",
            "missing_skills": [<list of mandatory skills the candidate lacks>],
            "red_flags": [<list of reasons why this might be a bad fit>]
        }}
        """

        try:
            # 3. Call the Gemini API
            response = self.model.generate_content(prompt)
            
            # 4. Parse the guaranteed JSON response
            result_json = json.loads(response.text)
            return result_json
            
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return {
                "ai_score": 0,
                "verdict": "Error",
                "missing_skills": [],
                "red_flags": [f"API Failure: {str(e)}"]
            }

# --- Testing the AI Engine ---
