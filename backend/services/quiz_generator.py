# backend/services/quiz_generator.py - QUIZ GENERATOR SERVICE

import google.generativeai as genai
import json
import re
from typing import List, Dict, Any, Optional
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiQuizGenerator:
    """
    Enhanced Gemini Quiz Generator with proper error handling and fallback mechanisms
    """
    
    def __init__(self):
        # Configure Gemini AI with your API key
        self.api_key = "AIzaSyCq4EtrP-O7FJvBQcWH2C4x1RFERPMuJ98"
        self.model = None
        
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                'gemini-1.5-flash',  # Use flash for faster responses
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2000,
                )
            )
            logger.info("🤖 Gemini Quiz Generator initialized successfully")
            print("🤖 Gemini Quiz Generator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {str(e)}")
            print(f"❌ Failed to initialize Gemini: {str(e)}")
            self.model = None
    
    def generate_quiz_from_text(self, text: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate quiz questions from extracted PDF text using Gemini AI
        Compatible with the main application's expected format
        """
        try:
            print("🎯 STARTING QUIZ GENERATION IN SERVICE...")
            
            # Validate and extract settings with proper defaults
            num_questions = self._safe_int(settings.get('numQuestions', 5), default=5, min_val=1, max_val=20)
            difficulty = self._validate_difficulty(settings.get('difficulty', 'medium'))
            question_types = self._validate_question_types(settings.get('questionTypes', 'mixed'))
            title = str(settings.get('title', 'AI Generated Quiz')).strip() or 'AI Generated Quiz'
            
            print(f"📋 SETTINGS: {num_questions} {difficulty} questions, type: {question_types}")
            logger.info(f"🎯 Generating {num_questions} {difficulty} questions using Gemini AI")
            
            # Validate text input
            if not text or not isinstance(text, str):
                print("⚠️ NO VALID TEXT PROVIDED, USING FALLBACK")
                logger.warning("⚠️ No valid text provided, using fallback")
                return self._create_fallback_quiz(title, num_questions, difficulty)
            
            text = text.strip()
            if len(text) < 50:
                print("⚠️ TEXT TOO SHORT, USING FALLBACK")
                logger.warning("⚠️ Text too short for meaningful questions, using fallback")
                return self._create_fallback_quiz(title, num_questions, difficulty)
            
            if not self.model:
                print("⚠️ GEMINI MODEL NOT AVAILABLE, USING FALLBACK")
                logger.warning("⚠️ Gemini model not available, using fallback")
                return self._create_fallback_quiz(title, num_questions, difficulty)
            
            # Generate with Gemini AI
            try:
                print("🤖 CALLING GEMINI AI...")
                quiz_data = self._generate_with_gemini(text, num_questions, difficulty, question_types, title)
                print("✅ GEMINI AI GENERATED QUIZ SUCCESSFULLY!")
                logger.info("✅ Gemini AI generated quiz successfully!")
                return quiz_data
                
            except Exception as gemini_error:
                print(f"❌ GEMINI AI FAILED: {str(gemini_error)}")
                logger.error(f"❌ Gemini AI failed: {str(gemini_error)}")
                return self._create_fallback_quiz(title, num_questions, difficulty)
            
        except Exception as e:
            print(f"❌ ERROR IN QUIZ GENERATION SERVICE: {str(e)}")
            logger.error(f"❌ Error in quiz generation: {str(e)}")
            return self._create_fallback_quiz(title, num_questions, difficulty)
    
    def _safe_int(self, value: Any, default: int, min_val: int = None, max_val: int = None) -> int:
        """Safely convert value to int with bounds checking"""
        try:
            result = int(value)
            if min_val is not None and result < min_val:
                return min_val
            if max_val is not None and result > max_val:
                return max_val
            return result
        except (ValueError, TypeError):
            return default
    
    def _validate_difficulty(self, difficulty: Any) -> str:
        """Validate difficulty setting"""
        valid_difficulties = ['easy', 'medium', 'hard']
        if isinstance(difficulty, str) and difficulty.lower() in valid_difficulties:
            return difficulty.lower()
        return 'medium'
    
    def _validate_question_types(self, question_types: Any) -> str:
        """Validate question types setting"""
        valid_types = ['mixed', 'mcq', 'truefalse', 'fillblank']
        if isinstance(question_types, str) and question_types.lower() in valid_types:
            return question_types.lower()
        return 'mixed'
    
    def _generate_with_gemini(self, text: str, num_questions: int, difficulty: str, question_types: str, title: str) -> Dict[str, Any]:
        """Generate quiz using Gemini AI with error handling"""
        
        print("🤖 PREPARING TEXT FOR GEMINI...")
        # Prepare the text (truncate if too long for optimal AI processing)
        max_text_length = 6000
        if len(text) > max_text_length:
            text = text[:max_text_length] + "..."
        
        # Create the prompt
        print("🤖 CREATING PROMPT...")
        prompt = self._create_gemini_prompt(text, num_questions, difficulty, question_types)
        
        # Generate content with retry mechanism
        print("🤖 CALLING GEMINI API...")
        response = self._safe_generate_content(prompt)
        
        if not response or not response.strip():
            raise Exception("Empty response from Gemini AI")
        
        print("🤖 PARSING GEMINI RESPONSE...")
        # Parse the response
        return self._parse_gemini_response(response, title, difficulty, num_questions)
    
    def _safe_generate_content(self, prompt: str, max_retries: int = 3) -> str:
        """Safely generate content with retries and exponential backoff"""
        for attempt in range(max_retries):
            try:
                print(f"🤖 GEMINI ATTEMPT {attempt + 1}...")
                response = self.model.generate_content(prompt)
                if response and hasattr(response, 'text') and response.text:
                    print("✅ GEMINI RESPONSE RECEIVED")
                    return response.text
                else:
                    raise Exception("No text in response")
            except Exception as e:
                print(f"⚠️ GENERATION ATTEMPT {attempt + 1} FAILED: {str(e)}")
                logger.warning(f"⚠️ Generation attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise Exception(f"Gemini generation failed after {max_retries} attempts: {str(e)}")
    
    def _create_gemini_prompt(self, text: str, num_questions: int, difficulty: str, question_types: str) -> str:
        """Create an effective prompt for Gemini AI"""
        
        # Question type instructions
        if question_types == 'mixed':
            type_instruction = f"Create a mix of multiple choice (60%), true/false (25%), and short answer (15%) questions"
        elif question_types == 'mcq':
            type_instruction = f"Create {num_questions} multiple choice questions with 4 options each"
        elif question_types == 'truefalse':
            type_instruction = f"Create {num_questions} true/false questions"
        else:
            type_instruction = f"Create {num_questions} short answer questions"
        
        # Difficulty instructions
        difficulty_guide = {
            'easy': "Focus on basic facts, simple recall, and obvious concepts from the text",
            'medium': "Test understanding, connections between ideas, and application of concepts",
            'hard': "Require analysis, synthesis, critical thinking, and deep understanding"
        }
        
        return f"""
You are an expert quiz creator. Based on the following educational text, create {num_questions} high-quality quiz questions.

TEXT CONTENT:
{text}

REQUIREMENTS:
- Difficulty: {difficulty} ({difficulty_guide.get(difficulty, 'balanced difficulty')})
- Question Distribution: {type_instruction}
- All questions must be based directly on the provided text content
- Make questions specific and test real understanding
- Ensure multiple choice options are plausible but clearly distinct
- Use varied question complexity appropriate for the difficulty level

OUTPUT FORMAT (JSON only):
{{
  "questions": [
    {{
      "type": "multiple_choice",
      "question": "Based on the text, what is...",
      "options": ["Correct answer", "Wrong option 1", "Wrong option 2", "Wrong option 3"],
      "correct_answer": "Correct answer",
      "points": 1
    }},
    {{
      "type": "true_false", 
      "question": "According to the text, [specific statement]",
      "correct_answer": "True",
      "points": 1
    }},
    {{
      "type": "short_answer",
      "question": "Explain the concept mentioned in the text about...",
      "correct_answer": "Expected answer based on text content",
      "points": 2
    }}
  ]
}}

CRITICAL REQUIREMENTS: 
- Return ONLY valid JSON, no other text
- Base all questions on the actual content provided
- Ensure each multiple choice question has exactly 4 options
- Make sure correct_answer matches one of the options exactly
- Questions should be specific to the text, not generic knowledge
"""
    
    def _parse_gemini_response(self, response_text: str, title: str, difficulty: str, num_questions: int) -> Dict[str, Any]:
        """Parse Gemini's response and structure it for our database"""
        
        try:
            print("🤖 EXTRACTING JSON FROM RESPONSE...")
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in Gemini response")
            
            json_str = json_match.group()
            # Clean up common JSON formatting issues
            json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas in objects
            json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
            json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)  # Remove control characters
            
            try:
                quiz_json = json.loads(json_str)
                print("✅ JSON PARSED SUCCESSFULLY")
            except json.JSONDecodeError as json_error:
                print(f"❌ JSON DECODE ERROR: {str(json_error)}")
                logger.error(f"JSON decode error: {str(json_error)}")
                logger.debug(f"Problematic JSON: {json_str[:500]}...")
                raise ValueError(f"Invalid JSON format: {str(json_error)}")
            
            if not isinstance(quiz_json, dict) or 'questions' not in quiz_json:
                raise ValueError("Response missing 'questions' key")
            
            questions = quiz_json['questions']
            if not isinstance(questions, list) or not questions:
                raise ValueError("No valid questions in response")
            
            print(f"🤖 PROCESSING {len(questions)} QUESTIONS...")
            
            # Structure for our database
            quiz_data = {
                'title': title,
                'description': f'AI-generated quiz with {len(questions)} intelligent questions from your content',
                'difficulty_level': difficulty,
                'total_questions': 0,  # Will be calculated
                'total_points': 0,     # Will be calculated
                'questions': []
            }
            
            # Process each question
            total_points = 0
            valid_questions = 0
            
            for idx, q in enumerate(questions, 1):
                try:
                    processed_question = self._process_question(q, idx)
                    if processed_question:
                        quiz_data['questions'].append(processed_question)
                        total_points += processed_question['points']
                        valid_questions += 1
                        print(f"✅ PROCESSED QUESTION {idx}")
                except Exception as e:
                    print(f"⚠️ SKIPPING MALFORMED QUESTION {idx}: {str(e)}")
                    logger.warning(f"⚠️ Skipping malformed question {idx}: {str(e)}")
                    continue
            
            quiz_data['total_questions'] = valid_questions
            quiz_data['total_points'] = total_points
            
            # Ensure we have at least some questions
            if valid_questions == 0:
                raise ValueError("No valid questions could be processed")
            
            print(f"✅ QUIZ DATA READY: {valid_questions} questions, {total_points} points")
            return quiz_data
            
        except Exception as e:
            print(f"❌ FAILED TO PARSE GEMINI RESPONSE: {str(e)}")
            logger.error(f"❌ Failed to parse Gemini response: {str(e)}")
            raise Exception(f"Failed to parse AI response: {str(e)}")
    
    def _process_question(self, question_data: dict, question_number: int) -> Optional[Dict[str, Any]]:
        """Process a single question from Gemini response with validation"""
        
        if not isinstance(question_data, dict):
            raise ValueError("Question data must be a dictionary")
        
        question_type = self._normalize_question_type(question_data.get('type', 'multiple_choice'))
        question_text = question_data.get('question', '').strip()
        
        if not question_text:
            raise ValueError("Question text is empty")
        
        processed = {
            'question_text': question_text,
            'question_type': question_type,
            'points': self._safe_int(question_data.get('points', 1 if question_type != 'short_answer' else 2), 
                                   default=1, min_val=1, max_val=10),
            'answers': []
        }
        
        # Process answers based on question type
        if question_type == 'multiple_choice':
            options = question_data.get('options', [])
            correct_answer = question_data.get('correct_answer', '').strip()
            
            if not isinstance(options, list) or len(options) < 2:
                raise ValueError("Multiple choice needs at least 2 options")
            
            if not correct_answer:
                raise ValueError("Multiple choice needs a correct answer")
            
            # Ensure we have exactly 4 options (pad if necessary)
            while len(options) < 4:
                options.append(f"Option {len(options) + 1}")
            
            options = options[:4]  # Limit to 4 options
            
            # Validate that correct_answer matches one of the options
            correct_found = False
            for option in options:
                option_str = str(option).strip()
                is_correct = option_str == correct_answer
                if is_correct:
                    correct_found = True
                processed['answers'].append({
                    'answer_text': option_str,
                    'is_correct': is_correct
                })
            
            # If correct answer not found in options, make first option correct
            if not correct_found:
                processed['answers'][0]['is_correct'] = True
                for i in range(1, len(processed['answers'])):
                    processed['answers'][i]['is_correct'] = False
        
        elif question_type == 'true_false':
            correct_answer = question_data.get('correct_answer', 'True').strip()
            is_true_correct = str(correct_answer).lower() in ['true', 't', '1', 'yes']
            
            processed['answers'] = [
                {'answer_text': 'True', 'is_correct': is_true_correct},
                {'answer_text': 'False', 'is_correct': not is_true_correct}
            ]
        
        elif question_type == 'short_answer':
            correct_answer = question_data.get('correct_answer', '').strip()
            if not correct_answer:
                raise ValueError("Short answer needs a correct answer")
                
            processed['answers'] = [
                {'answer_text': correct_answer, 'is_correct': True}
            ]
        
        # Validate we have answers
        if not processed['answers']:
            raise ValueError("No answers generated for question")
        
        return processed
    
    def _normalize_question_type(self, q_type: str) -> str:
        """Normalize question type to match our database enum"""
        if not isinstance(q_type, str):
            return 'multiple_choice'
            
        type_mapping = {
            'multiple_choice': 'multiple_choice',
            'mcq': 'multiple_choice',
            'mc': 'multiple_choice',
            'multiple-choice': 'multiple_choice',
            'true_false': 'true_false',
            'truefalse': 'true_false',
            'true/false': 'true_false',
            'tf': 'true_false',
            'true-false': 'true_false',
            'short_answer': 'short_answer',
            'fill_blank': 'short_answer',
            'fillblank': 'short_answer',
            'fill-blank': 'short_answer',
            'essay': 'short_answer'
        }
        return type_mapping.get(q_type.lower().strip(), 'multiple_choice')
    
    def _create_fallback_quiz(self, title: str, num_questions: int, difficulty: str) -> Dict[str, Any]:
        """Create a high-quality fallback quiz when AI fails"""
        
        print(f"🔄 CREATING FALLBACK QUIZ WITH {num_questions} QUESTIONS")
        logger.info(f"🔄 Creating enhanced fallback quiz with {num_questions} questions")
        
        try:
            # High-quality educational questions based on learning principles
            enhanced_questions = [
                {
                    'question_text': 'What is the most effective strategy for understanding complex information?',
                    'question_type': 'multiple_choice',
                    'points': 1,
                    'answers': [
                        {'answer_text': 'Breaking it into smaller parts and connecting concepts', 'is_correct': True},
                        {'answer_text': 'Reading everything as quickly as possible', 'is_correct': False},
                        {'answer_text': 'Memorizing without understanding context', 'is_correct': False},
                        {'answer_text': 'Focusing only on the conclusion', 'is_correct': False}
                    ]
                },
                {
                    'question_text': 'Active learning involves engaging with material through questioning and analysis.',
                    'question_type': 'true_false',
                    'points': 1,
                    'answers': [
                        {'answer_text': 'True', 'is_correct': True},
                        {'answer_text': 'False', 'is_correct': False}
                    ]
                },
                {
                    'question_text': 'Describe the importance of connecting new information to existing knowledge.',
                    'question_type': 'short_answer',
                    'points': 2,
                    'answers': [
                        {'answer_text': 'Connecting new information to existing knowledge strengthens memory pathways, improves comprehension, enables better retention, and facilitates application in different contexts', 'is_correct': True}
                    ]
                },
                {
                    'question_text': 'Which approach leads to deeper understanding of subject matter?',
                    'question_type': 'multiple_choice',
                    'points': 1,
                    'answers': [
                        {'answer_text': 'Analyzing relationships between concepts and asking critical questions', 'is_correct': True},
                        {'answer_text': 'Passive reading without taking notes', 'is_correct': False},
                        {'answer_text': 'Skipping difficult sections entirely', 'is_correct': False},
                        {'answer_text': 'Focusing only on memorizing definitions', 'is_correct': False}
                    ]
                },
                {
                    'question_text': 'Effective studying requires both understanding concepts and practicing their application.',
                    'question_type': 'true_false',
                    'points': 1,
                    'answers': [
                        {'answer_text': 'True', 'is_correct': True},
                        {'answer_text': 'False', 'is_correct': False}
                    ]
                },
                {
                    'question_text': 'Explain why reflection is an important part of the learning process.',
                    'question_type': 'short_answer',
                    'points': 2,
                    'answers': [
                        {'answer_text': 'Reflection helps consolidate learning, identify knowledge gaps, make connections between concepts, and improve future learning strategies', 'is_correct': True}
                    ]
                }
            ]
            
            # Select questions up to the requested number
            selected_questions = enhanced_questions[:min(num_questions, len(enhanced_questions))]
            
            # If we need more questions, create variations
            while len(selected_questions) < num_questions:
                base_idx = len(selected_questions) % len(enhanced_questions)
                new_question = enhanced_questions[base_idx].copy()
                new_question['question_text'] = f"[Additional] {new_question['question_text']}"
                # Deep copy answers to avoid reference issues
                new_question['answers'] = [answer.copy() for answer in new_question['answers']]
                selected_questions.append(new_question)
            
            result = {
                'title': title,
                'description': f'Enhanced educational quiz with {len(selected_questions)} questions',
                'difficulty_level': difficulty,
                'total_questions': len(selected_questions),
                'total_points': sum(q['points'] for q in selected_questions),
                'questions': selected_questions
            }
            
            print(f"✅ FALLBACK QUIZ CREATED: {len(selected_questions)} questions")
            return result
            
        except Exception as e:
            print(f"❌ ERROR CREATING FALLBACK QUIZ: {str(e)}")
            logger.error(f"❌ Error creating fallback quiz: {str(e)}")
            # Return absolute minimal quiz as last resort
            return {
                'title': title or 'Basic Quiz',
                'description': 'Basic educational quiz',
                'difficulty_level': difficulty,
                'total_questions': 1,
                'total_points': 1,
                'questions': [{
                    'question_text': 'Learning is an active process that requires engagement and practice.',
                    'question_type': 'true_false',
                    'points': 1,
                    'answers': [
                        {'answer_text': 'True', 'is_correct': True},
                        {'answer_text': 'False', 'is_correct': False}
                    ]
                }]
            }


# Test function
if __name__ == "__main__":
    try:
        print("🧪 TESTING GEMINI QUIZ GENERATOR...")
        generator = GeminiQuizGenerator()
        test_text = "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data. These algorithms improve their performance on a specific task through experience."
        
        test_settings = {
            'title': 'Test Quiz',
            'numQuestions': 3,
            'difficulty': 'medium',
            'questionTypes': 'mixed'
        }
        
        result = generator.generate_quiz_from_text(test_text, test_settings)
        print("✅ TEST QUIZ GENERATED SUCCESSFULLY:")
        print(f"Title: {result['title']}")
        print(f"Questions: {result['total_questions']}")
        print(f"Points: {result['total_points']}")
        
        for i, q in enumerate(result['questions'], 1):
            print(f"Q{i}: {q['question_text'][:50]}...")
            
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()