import json
import anthropic
from django.conf import settings


def evaluate_submission(task, submission_content):
    """
    Use Claude AI to evaluate a task submission.
    Returns dict with score, feedback, strengths, improvements.
    """
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    criteria_section = ""
    if task.evaluation_criteria:
        criteria_section = f"\nSpecific Evaluation Criteria:\n{task.evaluation_criteria}\n"

    prompt = f"""You are an expert evaluator for a professional task marketplace.

Task Title: {task.title}
Task Category: {task.get_category_display()}
Task Description:
{task.description}
{criteria_section}
Submission Content:
{submission_content}

Evaluate this submission rigorously on a scale of 0-100. Consider:
1. Relevance — Does it address what was asked?
2. Quality & Depth — Is it thorough and well-executed?
3. Clarity & Organization — Is it clear and well-structured?
4. Completeness — Does it fully satisfy the task requirements?
5. Originality & Value — Does it bring genuine insight or value?

Be fair but demanding. A score of 100 is near-perfect. A score below 40 means the submission did not meet basic requirements.

Respond ONLY with a valid JSON object, no markdown fences, no extra text:
{{
    "score": <integer 0-100>,
    "feedback": "<2-3 sentence overall assessment>",
    "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
    "improvements": ["<improvement 1>", "<improvement 2>", "<improvement 3>"]
}}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        result = json.loads(message.content[0].text.strip())
        return {
            'score': float(max(0, min(100, result.get('score', 0)))),
            'feedback': result.get('feedback', 'Evaluation completed.'),
            'strengths': result.get('strengths', []),
            'improvements': result.get('improvements', []),
        }
    except (json.JSONDecodeError, KeyError, anthropic.APIError) as e:
        return {
            'score': 50.0,
            'feedback': f'Automated evaluation could not be completed. Manual review required.',
            'strengths': ['Submission received'],
            'improvements': ['Could not fully evaluate at this time'],
        }


def calculate_earnings(task_reward, ai_score, worker_level_multiplier=1.0):
    """Calculate earnings based on score and level multiplier."""
    score_factor = ai_score / 100
    base_earnings = float(task_reward) * score_factor
    return round(base_earnings * worker_level_multiplier, 2)
