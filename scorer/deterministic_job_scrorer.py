import re
import json

class DeterministicJobScorer:
    def __init__(self):
        # 1. KNOCKOUT CRITERIA (Immediate Rejections)
        self.forbidden_title_keywords = [
            "senior", "lead", "principal", "architect", "manager", 
            "director", "staff", "ios", "android", "data scientist"
        ]
      

    def score_job(self, title: str, description: str) -> dict:
        title_lower = title.lower()


        # STAGE 1: Title Knockout
        for keyword in self.forbidden_title_keywords:
            if keyword in title_lower:
                return {
                    "verdict": "REJECTED",
                    "reason": f"Title contains forbidden keyword: '{keyword}'",
                    "score": 0,
                    "matched_skills": []
                }
                
        return {
            "verdict": "MATCH",
            "reason": "Passed title check. Deferring to AI."
        }

        
      

        

# --- Testing the Engine ---
if __name__ == "__main__":
    scorer = DeterministicJobScorer()

    print("--- Test Case 1: Perfect Match ---")
    job_1_title = "Backend Engineer I"
    job_1_desc = "We need an engineer with 1-2 years of experience. Must know Java, Spring Boot, and PostgreSQL. Familiarity with Microservices and Docker is a plus."
    print(json.dumps(scorer.score_job(job_1_title, job_1_desc), indent=2))

    print("\n--- Test Case 2: Rejected via Title ---")
    job_2_title = "Senior Software Engineer"
    job_2_desc = "Looking for a Java developer."
    print(json.dumps(scorer.score_job(job_2_title, job_2_desc), indent=2))

    print("\n--- Test Case 3: Rejected via Experience ---")
    job_3_title = "Software Engineer - Backend"
    job_3_desc = "Requirements: 4+ years of experience building Node.js applications with AWS."
    print(json.dumps(scorer.score_job(job_3_title, job_3_desc), indent=2))