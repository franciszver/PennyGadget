"""
Practice Item Generator
AI-powered practice question generation
"""

from typing import List, Dict, Optional
from src.services.ai.openai_client import openai_client
from src.services.ai.prompts import PromptTemplates
from src.services.practice.quality import PracticeQualityService
from src.models.practice import PracticeBankItem
import uuid
import json
import re


class PracticeGenerator:
    """Service for generating AI practice items"""
    
    def __init__(self):
        self.openai = openai_client
        self.quality_service = PracticeQualityService()
    
    def generate_practice_item(
        self,
        subject: str,
        topic: str,
        difficulty_level: int,
        goal_tags: Optional[List[str]] = None,
        student_history: Optional[List[Dict]] = None
    ) -> Dict[str, any]:
        """
        Generate a practice item using AI with quality validation
        
        Args:
            subject: Subject name
            topic: Topic name
            difficulty_level: Difficulty level (1-10)
            goal_tags: Optional goal tags for alignment
            student_history: Optional student practice history for context
        
        Returns:
            dict with question_text, answer_text, explanation, quality_score
        """
        # Use quality service for context-aware generation
        item = self.quality_service.generate_with_context(
            subject=subject,
            topic=topic,
            difficulty_level=difficulty_level,
            student_history=student_history,
            goal_tags=goal_tags
        )
        
        # Validate quality
        validation = self.quality_service.validate_practice_item(item)
        item["quality_score"] = validation["quality_score"]
        item["quality_issues"] = validation["issues"]
        
        return item

