# backend/services/quiz_generator.py
import google.generativeai as genai
import json
import re
from typing import List, Dict, Any
import os
from flask import current_app

class GeminiQuizGenerator:
    def __init__(self):
        # Configure Gemini AI
        self.api_key = "AIzaSyCq4EtrP-O7FJvBQcWH2C4x1RFERPMuJ98"
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_quiz_from_text(self, text: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate quiz questions from extracted PDF text using Gemini AI
        """
        try:
            # Extract settings
            num_questions = int(settings.get('numQuestions', 10))
            difficulty = settings.get('difficulty', 'medium')
            question_types = settings.get('questionTypes', 'mixed')
            title = settings.get('title', 'AI Generated Quiz')
            
            # Create the prompt for Gemini
            prompt = self._create_prompt(text, num_questions, difficulty, question_types)
            
            # Generate content using Gemini
            response = self.model.generate_content(prompt)
            
            # Parse the response
            quiz_data = self._parse_gemini_response(response.text, title, difficulty)
            
            return quiz_data
            
        except Exception as e:
            current_app.logger.error(f"Error generating quiz with Gemini: {str(e)}")
            raise Exception(f"Failed to generate quiz: {str(e)}")
    
    def _create_prompt(self, text: str, num_questions: int, difficulty: str, question_types: str) -> str:
        """Create a detailed prompt for Gemini AI"""
        
        # Truncate text if too long (Gemini has token limits)
        max_text_length = 8000
        if len(text) > max_text_length:
            text = text[:max_text_length] + "..."
        
        base_prompt = f"""
You are an expert quiz generator. Based on the following text content, create {num_questions} quiz questions.

CONTENT TO ANALYZE:
{text}

REQUIREMENTS:
- Difficulty Level: {difficulty}
- Number of Questions: {num_questions}
- Question Types: {question_types}

INSTRUCTIONS:
1. Create questions that test understanding of the key concepts in the text
2. For {difficulty} difficulty:
   - easy: Basic recall and simple understanding
   - medium: Application and analysis of concepts
   - hard: Complex analysis and synthesis

3. Question Types Distribution:
"""
        
        if question_types == 'mixed':
            base_prompt += """
   - 60% Multiple Choice (4 options each)
   - 25% True/False
   - 15% Short Answer
"""
        elif question_types == 'mcq':
            base_prompt += "   - 100% Multiple Choice (4 options each)"
        elif question_types == 'truefalse':
            base_prompt += "   - 100% True/False"
        elif question_types == 'fillblank':
            base_prompt += "   - 100% Fill in the Blank"
        
        base_prompt += """

4. OUTPUT FORMAT (JSON):
{
  "questions": [
    {
      "type": "multiple_choice",
      "question": "What is the main concept discussed?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A",
      "explanation": "Brief explanation of why this is correct",
      "points": 1
    },
    {
      "type": "true_false",
      "question": "The statement X is correct.",
      "correct_answer": "True",
      "explanation": "Explanation",
      "points": 1
    },
    {
      "type": "short_answer",
      "question": "Explain the concept of...",
      "correct_answer": "Expected answer",
      "explanation": "What makes a good answer",
      "points": 2
    }
  ]
}

IMPORTANT: 
- Return ONLY valid JSON
- Ensure all questions are directly related to the provided content
- Make questions clear and unambiguous
- Provide accurate correct answers
- Include helpful explanations
"""
        
        return base_prompt
    
    def _parse_gemini_response(self, response_text: str, title: str, difficulty: str) -> Dict[str, Any]:
        """Parse Gemini's response and structure it for our database"""
        
        try:
            # Clean the response to extract JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                quiz_json = json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")
            
            # Structure the data for our models
            quiz_data = {
                'title': title,
                'description': f'AI-generated quiz with {len(quiz_json.get("questions", []))} questions',
                'difficulty_level': difficulty,
                'total_questions': len(quiz_json.get('questions', [])),
                'total_points': sum(q.get('points', 1) for q in quiz_json.get('questions', [])),
                'questions': []
            }
            
            # Process each question
            for idx, q in enumerate(quiz_json.get('questions', []), 1):
                question_data = {
                    'question_text': q.get('question', f'Question {idx}'),
                    'question_type': self._normalize_question_type(q.get('type', 'multiple_choice')),
                    'points': q.get('points', 1),
                    'explanation': q.get('explanation', ''),
                    'answers': []
                }
                
                # Handle different question types
                if question_data['question_type'] == 'multiple_choice':
                    options = q.get('options', [])
                    correct_answer = q.get('correct_answer', '')
                    
                    for option in options:
                        question_data['answers'].append({
                            'answer_text': option,
                            'is_correct': option == correct_answer
                        })
                
                elif question_data['question_type'] == 'true_false':
                    correct_answer = q.get('correct_answer', 'True')
                    question_data['answers'] = [
                        {'answer_text': 'True', 'is_correct': correct_answer.lower() == 'true'},
                        {'answer_text': 'False', 'is_correct': correct_answer.lower() == 'false'}
                    ]
                
                elif question_data['question_type'] == 'short_answer':
                    question_data['answers'] = [{
                        'answer_text': q.get('correct_answer', ''),
                        'is_correct': True
                    }]
                
                quiz_data['questions'].append(question_data)
            
            return quiz_data
            
        except json.JSONDecodeError as e:
            current_app.logger.error(f"JSON parsing error: {str(e)}")
            raise Exception("Failed to parse AI response")
        except Exception as e:
            current_app.logger.error(f"Error parsing response: {str(e)}")
            raise Exception(f"Error processing quiz data: {str(e)}")
    
    def _normalize_question_type(self, q_type: str) -> str:
        """Normalize question type to match our database enum"""
        type_mapping = {
            'multiple_choice': 'multiple_choice',
            'mcq': 'multiple_choice',
            'true_false': 'true_false',
            'truefalse': 'true_false',
            'true/false': 'true_false',
            'short_answer': 'short_answer',
            'fill_blank': 'short_answer',
            'fillblank': 'short_answer'
        }
        return type_mapping.get(q_type.lower(), 'multiple_choice')
    
    def generate_sample_quiz(self) -> Dict[str, Any]:
        """Generate a sample quiz for testing"""
        return {
            'title': 'Sample AI Quiz',
            'description': 'A sample quiz generated by AI',
            'difficulty_level': 'medium',
            'total_questions': 3,
            'total_points': 4,
            'questions': [
                {
                    'question_text': 'What is artificial intelligence?',
                    'question_type': 'multiple_choice',
                    'points': 1,
                    'explanation': 'AI refers to machine intelligence',
                    'answers': [
                        {'answer_text': 'Machine intelligence that mimics human cognitive functions', 'is_correct': True},
                        {'answer_text': 'A type of computer virus', 'is_correct': False},
                        {'answer_text': 'A programming language', 'is_correct': False},
                        {'answer_text': 'A type of database', 'is_correct': False}
                    ]
                },
                {
                    'question_text': 'Machine learning is a subset of artificial intelligence.',
                    'question_type': 'true_false',
                    'points': 1,
                    'explanation': 'Machine learning is indeed a subset of AI',
                    'answers': [
                        {'answer_text': 'True', 'is_correct': True},
                        {'answer_text': 'False', 'is_correct': False}
                    ]
                },
                {
                    'question_text': 'Explain the difference between supervised and unsupervised learning.',
                    'question_type': 'short_answer',
                    'points': 2,
                    'explanation': 'Should mention labeled vs unlabeled data',
                    'answers': [
                        {'answer_text': 'Supervised learning uses labeled data while unsupervised learning finds patterns in unlabeled data', 'is_correct': True}
                    ]
                }
            ]
        }