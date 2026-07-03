import re
import json

class DeterministicJobScorer:
    def __init__(self):
        # 1. KNOCKOUT CRITERIA (Immediate Rejections)
        self.forbidden_title_keywords = [
            "senior", "lead", "principal", "architect", "manager", 
            "director", "staff", "ios", "android", "data scientist"
        ]
      

    import re
import json

class DeterministicJobScorer:
    def __init__(self):
        # 1. KNOCKOUT CRITERIA (Immediate Rejections)
        self.forbidden_title_keywords = [
            "senior", "lead", "principal", "architect", "manager", 
            "director", "staff", "ios", "android", "data scientist"
        ]
        
        # Regex pattern for levels (2, 3, 4, 5, II, III, IV, V)
        # \b ensures it only matches whole words, preventing false positives like "B2B"
        self.forbidden_level_pattern = re.compile(r'\b(ii|iii|iv|v|2|3|4|5)\b', re.IGNORECASE)

    def score_job(self, title: str, description: str) -> dict:
        title_lower = title.lower()

        # STAGE 1: Title Keyword Knockout
        for keyword in self.forbidden_title_keywords:
            if keyword in title_lower:
                return {
                    "verdict": "REJECTED",
                    "reason": f"Title contains forbidden keyword: '{keyword}'",
                    "score": 0,
                    "matched_skills": []
                }
                
        # STAGE 2: Title Level Knockout (e.g., Software Engineer II, 3)
        level_match = self.forbidden_level_pattern.search(title)
        if level_match:
            matched_level = level_match.group()
            return {
                "verdict": "REJECTED",
                "reason": f"Title contains advanced level indicator: '{matched_level}'",
                "score": 0,
                "matched_skills": []
            }

        return {
            "verdict": "MATCH",
            "reason": "Passed title check. Deferring to AI."
        }