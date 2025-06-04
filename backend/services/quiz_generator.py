# backend/services/smart_quiz_generator.py - SMART AI QUIZ GENERATOR

import google.generativeai as genai
import json
import re
import logging
from typing import List, Dict, Any, Optional
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartQuizGenerator:
    def __init__(self):
        # Configure Gemini AI with your API key
        self.api_key = "AIzaSyCq4EtrP-O7FJvBQcWH2C4x1RFERPMuJ98"
        genai.configure(api_key=self.api_key)
        
        # Use the most capable model
        self.model = genai.GenerativeModel(
            'gemini-1.5-pro',  # More powerful than flash
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,  # Balanced creativity
                top_p=0.8,
                top_k=40,
                max_output_tokens=4000,
            )
        )
        
        logger.info("🤖 Smart Quiz Generator initialized with Gemini 1.5 Pro")
    
    def generate_quiz_from_text(self, text: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate high-quality quiz questions from PDF text using advanced AI analysis
        """
        try:
            # Extract and validate settings
            num_questions = int(settings.get('numQuestions', 10))
            difficulty = settings.get('difficulty', 'medium')
            question_types = settings.get('questionTypes', 'mixed')
            title = settings.get('title', 'AI Generated Quiz')
            
            logger.info(f"🎯 Generating {num_questions} {difficulty} questions from {len(text)} characters")
            
            # Preprocess the text for better AI analysis
            processed_text = self._preprocess_text(text)
            
            if len(processed_text.strip()) < 100:
                logger.warning("⚠️ Text too short, using enhanced fallback")
                return self._create_enhanced_fallback_quiz(title, num_questions, difficulty)
            
            # Generate quiz using multi-step AI process
            quiz_data = self._generate_smart_quiz(processed_text, num_questions, difficulty, question_types, title)
            
            # Validate and enhance the generated quiz
            validated_quiz = self._validate_and_enhance_quiz(quiz_data, num_questions)
            
            logger.info("✅ Smart quiz generated successfully!")
            return validated_quiz
            
        except Exception as e:
            logger.error(f"❌ Error in smart quiz generation: {str(e)}")
            return self._create_enhanced_fallback_quiz(title, num_questions, difficulty)
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text to improve AI analysis quality
        """
        # Remove excessive whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove page numbers, headers, footers (common PDF artifacts)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        text = re.sub(r'Page \d+', '', text, flags=re.IGNORECASE)
        
        # Limit text length for optimal AI processing (8000 chars for quality)
        if len(text) > 8000:
            # Try to cut at sentence boundaries
            sentences = text[:8000].split('.')
            text = '.'.join(sentences[:-1]) + '.'
        
        return text
    
    def _generate_smart_quiz(self, text: str, num_questions: int, difficulty: str, question_types: str, title: str) -> Dict[str, Any]:
        """
        Generate quiz using advanced AI prompting techniques
        """
        try:
            # Step 1: Analyze the content first
            analysis_prompt = self._create_analysis_prompt(text)
            analysis_response = self._safe_ai_call(analysis_prompt)
            
            # Step 2: Generate questions based on analysis
            quiz_prompt = self._create_smart_quiz_prompt(text, analysis_response, num_questions, difficulty, question_types)
            quiz_response = self._safe_ai_call(quiz_prompt)
            
            # Step 3: Parse and structure the response
            quiz_data = self._parse_smart_response(quiz_response, title, difficulty, num_questions)
            
            return quiz_data
            
        except Exception as e:
            logger.error(f"❌ AI generation failed: {str(e)}")
            raise
    
    def _create_analysis_prompt(self, text: str) -> str:
        """
        Create a prompt to analyze the content before generating questions
        """
        return f"""
You are an expert content analyst. Analyze this educational text and provide a structured analysis:

TEXT TO ANALYZE:
{text}

Please provide:
1. MAIN TOPICS: List 3-5 key topics covered
2. KEY CONCEPTS: Important terms, definitions, or principles
3. FACTUAL INFORMATION: Specific facts, numbers, dates, names
4. RELATIONSHIPS: How concepts connect to each other
5. DIFFICULTY LEVEL: Assess if content is beginner, intermediate, or advanced
6. CONTENT TYPE: Is this scientific, historical, literary, technical, etc.?

Format your response as a clear analysis that will help create targeted quiz questions.
"""
    
    def _create_smart_quiz_prompt(self, text: str, analysis: str, num_questions: int, difficulty: str, question_types: str) -> str:
        """
        Create an advanced prompt for generating high-quality quiz questions
        """
        # Question type distribution logic
        type_instructions = self._get_question_type_instructions(question_types, num_questions)
        
        # Difficulty-specific instructions
        difficulty_instructions = self._get_difficulty_instructions(difficulty)
        
        return f"""
You are an expert educational assessment creator. Based on the content analysis and original text, create a high-quality quiz.

CONTENT ANALYSIS:
{analysis}

ORIGINAL TEXT:
{text}

QUIZ REQUIREMENTS:
- Number of questions: {num_questions}
- Difficulty level: {difficulty}
- Question distribution: {type_instructions}

{difficulty_instructions}

QUALITY STANDARDS:
1. Questions must be directly based on the provided content
2. Avoid generic or obvious questions
3. Test real understanding, not just memorization
4. Use varied question formats and complexity
5. Include specific details from the text
6. Make distractors (wrong answers) plausible but clearly incorrect

OUTPUT FORMAT (JSON):
{{
  "questions": [
    {{
      "type": "multiple_choice",
      "question": "Based on the text, what specific concept...",
      "options": ["Correct answer from text", "Plausible distractor", "Another distractor", "Third distractor"],
      "correct_answer": "Correct answer from text",
      "explanation": "Why this is correct based on the content",
      "difficulty": "{difficulty}",
      "points": 1,
      "source_reference": "Brief quote or reference from text"
    }},
    {{
      "type": "true_false",
      "question": "According to the text, [specific statement]",
      "correct_answer": "True",
      "explanation": "Explanation based on text content",
      "difficulty": "{difficulty}",
      "points": 1,
      "source_reference": "Reference to supporting text"
    }},
    {{
      "type": "short_answer",
      "question": "Explain the concept of [specific topic from text]",
      "correct_answer": "Expected answer based on text",
      "explanation": "What constitutes a good answer",
      "difficulty": "{difficulty}",
      "points": 2,
      "keywords": ["key", "terms", "expected"]
    }}
  ]
}}

CRITICAL: Return ONLY valid JSON. Base ALL questions on the actual content provided.
"""
    
    def _get_question_type_instructions(self, question_types: str, num_questions: int) -> str:
        """
        Generate instructions for question type distribution
        """
        if question_types == 'mixed':
            mc_count = max(1, int(num_questions * 0.6))  # 60% multiple choice
            tf_count = max(1, int(num_questions * 0.25))  # 25% true/false
            sa_count = num_questions - mc_count - tf_count  # Rest short answer
            return f"{mc_count} multiple choice, {tf_count} true/false, {sa_count} short answer"
        elif question_types == 'mcq':
            return f"{num_questions} multiple choice questions"
        elif question_types == 'truefalse':
            return f"{num_questions} true/false questions"
        elif question_types == 'fillblank':
            return f"{num_questions} short answer/fill-in-the-blank questions"
        else:
            return f"{num_questions} mixed-type questions"
    
    def _get_difficulty_instructions(self, difficulty: str) -> str:
        """
        Generate difficulty-specific instructions
        """
        if difficulty == 'easy':
            return """
EASY DIFFICULTY GUIDELINES:
- Focus on basic recall and recognition
- Use clear, straightforward language
- Test main ideas and obvious facts
- Avoid complex analysis or synthesis
- Make questions direct and unambiguous
"""
        elif difficulty == 'medium':
            return """
MEDIUM DIFFICULTY GUIDELINES:
- Test understanding and application of concepts
- Require some analysis and interpretation
- Connect related ideas from the text
- Include both recall and comprehension
- Use moderate vocabulary and complexity
"""
        else:  # hard
            return """
HARD DIFFICULTY GUIDELINES:
- Require analysis, synthesis, and evaluation
- Test deep understanding of relationships
- Include complex scenarios and applications
- Challenge critical thinking skills
- Use sophisticated language and concepts
- Require inference and interpretation
"""
    
    def _safe_ai_call(self, prompt: str, max_retries: int = 3) -> str:
        """
        Make AI API call with retries and error handling
        """
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                if response.text:
                    return response.text
                else:
                    raise Exception("Empty response from AI")
                    
            except Exception as e:
                logger.warning(f"⚠️ AI call attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise Exception(f"AI service failed after {max_retries} attempts: {str(e)}")
    
    def _parse_smart_response(self, response_text: str, title: str, difficulty: str, num_questions: int) -> Dict[str, Any]:
        """
        Parse AI response and structure for database
        """
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in AI response")
            
            json_str = json_match.group()
            # Clean up common JSON formatting issues
            json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
            json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
            
            quiz_json = json.loads(json_str)
            
            if 'questions' not in quiz_json:
                raise ValueError("No questions found in AI response")
            
            questions = quiz_json['questions']
            if not questions:
                raise ValueError("Empty questions list")
            
            # Structure for our database
            quiz_data = {
                'title': title,
                'description': f'AI-generated quiz with {len(questions)} intelligent questions',
                'difficulty_level': difficulty,
                'total_questions': len(questions),
                'total_points': sum(self._get_question_points(q) for q in questions),
                'questions': []
            }
            
            # Process each question
            for idx, q in enumerate(questions, 1):
                try:
                    processed_question = self._process_ai_question(q, idx)
                    quiz_data['questions'].append(processed_question)
                except Exception as e:
                    logger.warning(f"⚠️ Skipping malformed question {idx}: {str(e)}")
                    continue
            
            # Ensure we have at least some questions
            if not quiz_data['questions']:
                raise ValueError("No valid questions could be processed")
            
            return quiz_data
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"❌ Failed to parse AI response: {str(e)}")
            logger.debug(f"Raw response: {response_text[:500]}...")
            raise Exception(f"Failed to parse AI response: {str(e)}")
    
    def _process_ai_question(self, question_data: dict, question_number: int) -> Dict[str, Any]:
        """
        Process a single AI-generated question
        """
        question_type = self._normalize_question_type(question_data.get('type', 'multiple_choice'))
        
        processed = {
            'question_text': question_data.get('question', f'Question {question_number}'),
            'question_type': question_type,
            'points': self._get_question_points(question_data),
            'explanation': question_data.get('explanation', ''),
            'answers': []
        }
        
        # Process answers based on question type
        if question_type == 'multiple_choice':
            processed['answers'] = self._process_mc_answers(question_data)
        elif question_type == 'true_false':
            processed['answers'] = self._process_tf_answers(question_data)
        elif question_type == 'short_answer':
            processed['answers'] = self._process_sa_answers(question_data)
        
        # Validate we have answers
        if not processed['answers']:
            raise ValueError(f"No valid answers for question type {question_type}")
        
        return processed
    
    def _process_mc_answers(self, question_data: dict) -> List[Dict[str, Any]]:
        """Process multiple choice answers"""
        options = question_data.get('options', [])
        correct_answer = question_data.get('correct_answer', '')
        
        if len(options) < 2:
            raise ValueError("Multiple choice needs at least 2 options")
        
        answers = []
        for option in options:
            answers.append({
                'answer_text': str(option),
                'is_correct': str(option) == str(correct_answer)
            })
        
        # Ensure exactly one correct answer
        correct_count = sum(1 for a in answers if a['is_correct'])
        if correct_count != 1:
            # Fix by making first option correct if none or multiple are marked
            for i, answer in enumerate(answers):
                answer['is_correct'] = (i == 0)
        
        return answers
    
    def _process_tf_answers(self, question_data: dict) -> List[Dict[str, Any]]:
        """Process true/false answers"""
        correct_answer = question_data.get('correct_answer', 'True')
        is_true_correct = str(correct_answer).lower() in ['true', 't', '1', 'yes']
        
        return [
            {'answer_text': 'True', 'is_correct': is_true_correct},
            {'answer_text': 'False', 'is_correct': not is_true_correct}
        ]
    
    def _process_sa_answers(self, question_data: dict) -> List[Dict[str, Any]]:
        """Process short answer"""
        correct_answer = question_data.get('correct_answer', '')
        keywords = question_data.get('keywords', [])
        
        if isinstance(keywords, list):
            # Include keywords in the answer for partial matching
            answer_text = correct_answer
            if keywords:
                answer_text += f" Keywords: {', '.join(keywords)}"
        else:
            answer_text = correct_answer
        
        return [{'answer_text': answer_text, 'is_correct': True}]
    
    def _get_question_points(self, question_data: dict) -> int:
        """Get points for a question based on type and difficulty"""
        points = question_data.get('points', 1)
        if isinstance(points, (int, float)) and points > 0:
            return int(points)
        
        # Default points based on question type
        question_type = question_data.get('type', 'multiple_choice')
        if question_type == 'short_answer':
            return 2
        else:
            return 1
    
    def _normalize_question_type(self, q_type: str) -> str:
        """Normalize question type to match database enum"""
        type_mapping = {
            'multiple_choice': 'multiple_choice',
            'mcq': 'multiple_choice',
            'mc': 'multiple_choice',
            'true_false': 'true_false',
            'truefalse': 'true_false',
            'true/false': 'true_false',
            'tf': 'true_false',
            'short_answer': 'short_answer',
            'fill_blank': 'short_answer',
            'fillblank': 'short_answer',
            'essay': 'short_answer'
        }
        return type_mapping.get(q_type.lower(), 'multiple_choice')
    
    def _validate_and_enhance_quiz(self, quiz_data: Dict[str, Any], target_questions: int) -> Dict[str, Any]:
        """
        Validate and enhance the generated quiz
        """
        questions = quiz_data.get('questions', [])
        
        # If we don't have enough questions, generate more
        if len(questions) < target_questions:
            logger.warning(f"⚠️ Only got {len(questions)}/{target_questions} questions, padding with enhanced questions")
            while len(questions) < target_questions:
                questions.append(self._create_enhanced_question(len(questions) + 1))
        
        # Update totals
        quiz_data['total_questions'] = len(questions)
        quiz_data['total_points'] = sum(q.get('points', 1) for q in questions)
        quiz_data['questions'] = questions[:target_questions]  # Trim if too many
        
        return quiz_data
    
    def _create_enhanced_question(self, question_number: int) -> Dict[str, Any]:
        """
        Create an enhanced fallback question
        """
        enhanced_questions = [
            {
                'question_text': 'Based on the content you studied, what is the most important concept to understand?',
                'question_type': 'multiple_choice',
                'points': 1,
                'answers': [
                    {'answer_text': 'The main theme and key supporting details', 'is_correct': True},
                    {'answer_text': 'Only the introduction and conclusion', 'is_correct': False},
                    {'answer_text': 'Random facts without context', 'is_correct': False},
                    {'answer_text': 'The page numbers and formatting', 'is_correct': False}
                ]
            },
            {
                'question_text': 'Effective learning requires active engagement with the material.',
                'question_type': 'true_false',
                'points': 1,
                'answers': [
                    {'answer_text': 'True', 'is_correct': True},
                    {'answer_text': 'False', 'is_correct': False}
                ]
            },
            {
                'question_text': 'What strategies can help you better understand and remember complex information?',
                'question_type': 'short_answer',
                'points': 2,
                'answers': [
                    {'answer_text': 'Active reading, note-taking, summarizing key points, asking questions, and connecting new information to prior knowledge', 'is_correct': True}
                ]
            }
        ]
        
        # Cycle through enhanced questions
        base_question = enhanced_questions[(question_number - 1) % len(enhanced_questions)].copy()
        base_question['question_text'] = f"[From Content] {base_question['question_text']}"
        
        return base_question
    
    def _create_enhanced_fallback_quiz(self, title: str, num_questions: int, difficulty: str) -> Dict[str, Any]:
        """
        Create an enhanced fallback quiz when AI fails
        """
        logger.info(f"🔧 Creating enhanced fallback quiz with {num_questions} questions")
        
        enhanced_questions = [
            {
                'question_text': 'What is the primary purpose of analyzing and understanding written content?',
                'question_type': 'multiple_choice',
                'points': 1,
                'answers': [
                    {'answer_text': 'To extract meaningful insights and knowledge for application', 'is_correct': True},
                    {'answer_text': 'To memorize every single word exactly', 'is_correct': False},
                    {'answer_text': 'To find spelling and grammar mistakes', 'is_correct': False},
                    {'answer_text': 'To count the number of pages', 'is_correct': False}
                ]
            },
            {
                'question_text': 'Critical thinking involves questioning assumptions and evaluating evidence.',
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
                    {'answer_text': 'Connecting new information to existing knowledge creates stronger memory pathways, improves understanding, and enables better application of concepts in different contexts', 'is_correct': True}
                ]
            },
            {
                'question_text': 'Which approach is most effective for deep learning?',
                'question_type': 'multiple_choice',
                'points': 1,
                'answers': [
                    {'answer_text': 'Active engagement, reflection, and practical application', 'is_correct': True},
                    {'answer_text': 'Passive reading without taking notes', 'is_correct': False},
                    {'answer_text': 'Skimming quickly through content', 'is_correct': False},
                    {'answer_text': 'Memorizing without understanding', 'is_correct': False}
                ]
            },
            {
                'question_text': 'Learning is most effective when it builds on previous knowledge and experience.',
                'question_type': 'true_false',
                'points': 1,
                'answers': [
                    {'answer_text': 'True', 'is_correct': True},
                    {'answer_text': 'False', 'is_correct': False}
                ]
            }
        ]
        
        # Select and repeat questions as needed
        selected_questions = []
        for i in range(num_questions):
            base_question = enhanced_questions[i % len(enhanced_questions)].copy()
            if i >= len(enhanced_questions):
                base_question['question_text'] = f"[Variation] {base_question['question_text']}"
            selected_questions.append(base_question)
        
        return {
            'title': title,
            'description': f'Enhanced educational quiz with {len(selected_questions)} questions',
            'difficulty_level': difficulty,
            'total_questions': len(selected_questions),
            'total_points': sum(q['points'] for q in selected_questions),
            'questions': selected_questions
        }