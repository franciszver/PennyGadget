"""
Practice Item Quality Service
Quality validation and improvement for generated practice items
"""

import json
import re
from typing import Dict, Optional, List
from src.services.ai.openai_client import openai_client
from src.services.ai.prompts import PromptTemplates


class PracticeQualityService:
    """Service for validating and improving practice item quality"""
    
    def __init__(self):
        self.openai = openai_client
    
    def validate_practice_item(self, item: Dict) -> Dict:
        """
        Validate practice item quality
        
        Args:
            item: Practice item dict with question_text, answer_text, explanation
        
        Returns:
            Validation result with quality_score and issues
        """
        issues = []
        quality_score = 1.0
        
        # Check question quality
        question = item.get("question_text", "").strip()
        if not question:
            issues.append("Missing question text")
            quality_score -= 0.5
        elif len(question) < 20:
            issues.append("Question too short (minimum 20 characters)")
            quality_score -= 0.2
        elif len(question) > 500:
            issues.append("Question too long (maximum 500 characters)")
            quality_score -= 0.1
        
        # Check answer quality
        answer = item.get("answer_text", "").strip()
        if not answer:
            issues.append("Missing answer text")
            quality_score -= 0.3
        elif len(answer) < 5:
            issues.append("Answer too short")
            quality_score -= 0.2
        
        # Check explanation quality
        explanation = item.get("explanation", "").strip()
        if not explanation:
            issues.append("Missing explanation")
            quality_score -= 0.2
        elif len(explanation) < 30:
            issues.append("Explanation too short (minimum 30 characters)")
            quality_score -= 0.1
        
        # Check for common issues
        if "?" not in question and "what" not in question.lower() and "how" not in question.lower():
            issues.append("Question may not be properly formatted")
            quality_score -= 0.1
        
        quality_score = max(0.0, quality_score)
        
        return {
            "quality_score": round(quality_score, 2),
            "is_valid": quality_score >= 0.7,
            "issues": issues
        }
    
    def improve_practice_item(
        self,
        item: Dict,
        subject: str,
        topic: str,
        difficulty_level: int
    ) -> Dict:
        """
        Improve practice item quality using AI
        
        Args:
            item: Practice item to improve
            subject: Subject name
            topic: Topic name
            difficulty_level: Difficulty level
        
        Returns:
            Improved practice item
        """
        validation = self.validate_practice_item(item)
        
        if validation["is_valid"]:
            return item
        
        # Use AI to improve the item
        improvement_prompt = [
            {
                "role": "system",
                "content": f"You are an expert educational content creator. Improve the following practice question for {subject} - {topic} (Difficulty: {difficulty_level}/10)."
            },
            {
                "role": "user",
                "content": f"""Current practice item:
Question: {item.get('question_text', '')}
Answer: {item.get('answer_text', '')}
Explanation: {item.get('explanation', '')}

Issues found: {', '.join(validation['issues'])}

Please provide an improved version in JSON format:
{{
  "question_text": "...",
  "answer_text": "...",
  "explanation": "..."
}}"""
            }
        ]
        
        try:
            ai_response = self.openai.chat_completion(improvement_prompt)
            
            # Try to parse JSON response
            json_match = re.search(r'\{[^{}]*"question_text"[^{}]*\}', ai_response, re.DOTALL)
            if json_match:
                improved = json.loads(json_match.group())
                return improved
            
            # Fallback: parse similar to generator
            return self._parse_improved_response(ai_response, item)
            
        except Exception as e:
            # Return original if improvement fails
            return item
    
    def _parse_improved_response(self, response: str, original: Dict) -> Dict:
        """Parse improved response from AI"""
        # Try to extract sections
        question_match = re.search(r'(?:question|q):\s*(.+?)(?:\n|answer|$)', response, re.IGNORECASE | re.DOTALL)
        answer_match = re.search(r'(?:answer|a):\s*(.+?)(?:\n|explanation|$)', response, re.IGNORECASE | re.DOTALL)
        explanation_match = re.search(r'(?:explanation|explain):\s*(.+?)$', response, re.IGNORECASE | re.DOTALL)
        
        return {
            "question_text": question_match.group(1).strip() if question_match else original.get("question_text", ""),
            "answer_text": answer_match.group(1).strip() if answer_match else original.get("answer_text", ""),
            "explanation": explanation_match.group(1).strip() if explanation_match else original.get("explanation", "")
        }
    
    def generate_with_context(
        self,
        subject: str,
        topic: str,
        difficulty_level: int,
        student_history: Optional[List[Dict]] = None,
        goal_tags: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate practice item with student context
        
        Args:
            subject: Subject name
            topic: Topic name
            difficulty_level: Difficulty level
            student_history: List of previous practice attempts
            goal_tags: Goal tags for alignment
        
        Returns:
            Generated practice item
        """
        # Build context string
        context_str = ""
        if student_history:
            recent_attempts = student_history[:5]  # Last 5 attempts
            context_str = "\n\nStudent's recent practice history:\n"
            for attempt in recent_attempts:
                context_str += f"- {attempt.get('topic', 'Unknown')}: {'Correct' if attempt.get('correct') else 'Incorrect'}\n"
        
        # Enhanced prompt with context
        prompt = PromptTemplates.practice_generation_prompt(
            subject=subject,
            topic=topic,
            difficulty_level=difficulty_level,
            goal_tags=goal_tags
        )
        
        # Add context to prompt
        if context_str and len(prompt) > 0:
            if prompt[0].get("role") == "system":
                prompt[0]["content"] += context_str
        
        try:
            ai_response = self.openai.chat_completion(prompt)
            
            # Try JSON parsing first
            json_match = re.search(r'\{[^{}]*"question_text"[^{}]*\}', ai_response, re.DOTALL)
            if json_match:
                try:
                    item = json.loads(json_match.group())
                    # Validate and improve if needed
                    validation = self.validate_practice_item(item)
                    if not validation["is_valid"]:
                        item = self.improve_practice_item(item, subject, topic, difficulty_level)
                    return item
                except json.JSONDecodeError:
                    pass
            
            # Fallback to text parsing
            return self._parse_text_response(ai_response)
            
        except Exception as e:
            return {
                "question_text": f"Practice question for {subject} - {topic} (Difficulty: {difficulty_level})",
                "answer_text": "Answer generation failed. Please consult your tutor.",
                "explanation": f"AI generation encountered an error: {str(e)}"
            }
    
    def _parse_text_response(self, response: str) -> Dict:
        """Parse text response into practice item"""
        question_text = ""
        answer_text = ""
        explanation = ""
        
        # Try to find sections
        sections = re.split(r'(?:question|answer|explanation):', response, flags=re.IGNORECASE)
        
        if len(sections) >= 2:
            question_text = sections[1].strip() if len(sections) > 1 else ""
        if len(sections) >= 3:
            answer_text = sections[2].strip() if len(sections) > 2 else ""
        if len(sections) >= 4:
            explanation = sections[3].strip() if len(sections) > 3 else ""
        
        # Fallback: split by common patterns
        if not question_text:
            parts = re.split(r'(?:answer|a):', response, flags=re.IGNORECASE, maxsplit=1)
            if parts:
                question_text = parts[0].replace("Question:", "").replace("Q:", "").strip()
                if len(parts) > 1:
                    answer_parts = re.split(r'(?:explanation|explain):', parts[1], flags=re.IGNORECASE, maxsplit=1)
                    answer_text = answer_parts[0].strip()
                    if len(answer_parts) > 1:
                        explanation = answer_parts[1].strip()
        
        return {
            "question_text": question_text or response[:200],
            "answer_text": answer_text or "See explanation",
            "explanation": explanation or response
        }

