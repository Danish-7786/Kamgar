import os
import json
from groq import Groq
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AIScorer:
    def __init__(self):
        # 1. Configure the Gemini client
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing from the .env file")
            
        self.client = Groq(api_key=api_key)
        
        
        # Hardcoding the profile so the AI knows who it is evaluating
        self.candidate_profile = """
        Role: Backend-focused Full-Stack Engineer
        Education: B.E. in Computer Science (CGPA: 8.0)
        Experience: ~1 year (Product company internships at Falabella & UnQue.me)
        Core Stack: Java, Python, TypeScript, Node.js, Spring Boot, React, React Native, React, JavaScript,C , C++ 
        Databases & DevOps: MongoDB, PostgreSQL, Docker, AWS, CI/CD
        Concepts: Microservices, REST, GraphQL, scalable distributed systems, DSA (300+ LeetCode)
        """

    def evaluate_job(self, job_title: str, job_description: str) -> dict:
        """
        Passes the job description to GPT-4o-mini with extremely strict filtering rules.
        """
        prompt = f"""
        You are an expert technical recruiter evaluating a job posting for this candidate:
        
        Candidate Profile:
        {self.candidate_profile}
        
        Job Title: {job_title}
        Job Description: 
        {job_description}
        
        CRITICAL EVALUATION RULES (YOU MUST FOLLOW THESE STRICTLY):
        1. STRICT EXPERIENCE LIMIT: The candidate has ~1 year of experience. If the job description explicitly requires 3 or more years of experience (e.g., "3+ years", "3 to 5 years", "min 3 yrs"), you MUST score it 0 and set the verdict to "Poor Match". 
        2. SKILL RELEVANCE: If the job requires a primary language or framework NOT in the candidate's stack (e.g., .NET, C#, PHP, Ruby, Golang as a primary), you MUST score it below 40 and mark it a "Poor Match".
        3. SCORING RUBRIC:
           - Strong Match (80-100): Requires 0-2 years experience AND tech stack matches almost perfectly (e.g., heavily uses Java/Spring Boot or Node.js).
           - Partial Match (50-79): Fits experience level, but missing 1-2 nice-to-have skills (e.g., missing Kubernetes, but has core Java).
           - Poor Match (0-49): Requires 3+ years experience, OR completely wrong core tech stack.
        
        Return ONLY a valid JSON object with the following schema:
        {{
            "ai_score": <int 0-100>,
            "verdict": "<Strong Match | Partial Match | Poor Match>",
            "missing_skills": [<list of mandatory skills the candidate lacks>],
            "red_flags": [<list of reasons why this is a bad fit, e.g., 'Requires 3+ years experience', 'Requires C#'>]
        }}
        """

        max_retries = 4
        base_delay = 3

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="openai/gpt-oss-120b", 
                    response_format={ "type": "json_object" },
                    messages=[
                        # We updated the system prompt to force the AI to act strictly
                        {
                            "role": "system", 
                            "content": "You are a ruthless and strict technical recruiter AI. You immediately reject jobs if the candidate doesn't meet the minimum experience required or lacks the core primary tech stack. You output only JSON."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    # Lowering temperature to 0.0 makes the AI completely deterministic and strict
                    temperature=0.0 
                )
                
                # Parse the JSON string returned by OpenAI into a Python dictionary
                result_json = json.loads(response.choices[0].message.content)
                return result_json
                
            except Exception as e:
                if attempt < max_retries - 1:
                    sleep_time = base_delay * (2 ** attempt)  # Pauses for 3s, then 6s, then 12s
                    print(f"⚠️ Rate limit (429) hit. Backing off for {sleep_time}s (Attempt {attempt + 1}/{max_retries})...")
                    time.sleep(sleep_time)
                else:
                    print("❌ Max retries reached. API Rate Limit completely exhausted.")
                    return {
                        "ai_score": 0,
                        "verdict": "Error",
                        "missing_skills": [],
                        "red_flags": ["API Rate Limit Exceeded"]
                    }
            except Exception as e:
                print(f"Error calling OpenAI API: {e}")
                return {
                    "ai_score": 0,
                    "verdict": "Error",
                    "missing_skills": [],
                    "red_flags": [f"AI API Failure: {str(e)}"]
                }