import json
import anthropic
from django.conf import settings
from decimal import Decimal

def evaluate_submission(task, submission_content):
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    criteria_section = f"\nCriteria:\n{task.evaluation_criteria}" if task.evaluation_criteria else ""

    # Using XML tags to prevent prompt injection
    prompt = f"""You are an expert evaluator. 
    Evaluate the following submission based on these requirements:
    Title: {task.title}
    Description: {task.description}
    {criteria_section}

    <submission_to_evaluate>
    {submission_content}
    </submission_to_evaluate>

    Respond ONLY with a JSON object containing: score (0-100), feedback (string), strengths (list), improvements (list)."""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022", # Corrected model name
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Strip potential markdown code blocks if the AI includes them
        raw_content = message.content[0].text.strip().replace("```json", "").replace("```", "")
        result = json.loads(raw_content)
        
        return {
            'score': float(max(0, min(100, result.get('score', 0)))),
            'feedback': result.get('feedback', 'Evaluation completed.'),
            'strengths': result.get('strengths', []),
            'improvements': result.get('improvements', []),
        }
    except (json.JSONDecodeError, KeyError, anthropic.APIError, Exception) as e:
            # This will print the error type and the message to your console/logs
            print(f"ERROR in evaluate_submission: {type(e).__name__} - {str(e)}")
            
            return {
                'score': 50.0,
                'feedback': f'Automated evaluation could not be completed. Error: {str(e)}',
                'strengths': ['Submission received'],
                'improvements': ['Could not fully evaluate at this time'],
            }

def calculate_earnings(task_reward, ai_score, worker_level_multiplier=1.0):
    """Calculates earnings using Decimals for financial accuracy."""
    reward = Decimal(str(task_reward))
    score_factor = Decimal(str(ai_score)) / Decimal('100')
    multiplier = Decimal(str(worker_level_multiplier))
    
    total = reward * score_factor * multiplier
    return total.quantize(Decimal('0.01')) # Rounds to 2 decimal places