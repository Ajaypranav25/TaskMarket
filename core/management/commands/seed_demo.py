"""
Management command to seed demo data.
Usage: python manage.py seed_demo
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Seed demo users and tasks'

    def handle(self, *args, **kwargs):
        from core.models import Level, UserProfile, Task

        self.stdout.write('Seeding demo data...')

        # Company user
        company, _ = User.objects.get_or_create(username='acmecorp')
        company.set_password('demo1234')
        company.email = 'company@acme.com'
        company.save()
        profile = company.profile
        profile.role = 'company'
        profile.company_name = 'Acme Corp'
        profile.save()

        # Worker users
        for i, (uname, score, subs) in enumerate([
            ('alice_dev', 88, 30),
            ('bob_writer', 72, 15),
            ('carol_pro', 95, 55),
        ]):
            worker, _ = User.objects.get_or_create(username=uname)
            worker.set_password('demo1234')
            worker.save()
            wp = worker.profile
            wp.role = 'worker'
            wp.avg_score = score
            wp.total_submissions = subs
            wp.total_earnings = round(score * subs * 0.4, 2)
            wp._update_level()
            wp.save()

        # Tasks
        levels = list(Level.objects.all())
        tasks_data = [
            {
                'title': 'Write a product description for a SaaS analytics tool',
                'description': (
                    'We need a compelling product description (200-250 words) for our new B2B analytics platform '
                    'called DataLens. It helps marketing teams track campaign performance in real time.\n\n'
                    'Target audience: Marketing managers at mid-size companies.\n'
                    'Tone: Professional but approachable.\n'
                    'Must include: Key benefits, target user, and a call to action.'
                ),
                'category': 'writing',
                'reward': 18.00,
                'min_level': None,
                'evaluation_criteria': 'Must be 200-250 words. Should highlight 3 concrete benefits. Ends with a CTA.',
            },
            {
                'title': 'Research & summarize 5 top AI coding assistants (2024)',
                'description': (
                    'Research the top 5 AI coding assistant tools available in 2024 and write a structured summary '
                    'comparing them.\n\nFor each tool, cover: name, key features, pricing model, and best use case.\n'
                    'Format as a brief comparison table followed by 2-3 sentence recommendation for each type of developer.'
                ),
                'category': 'research',
                'reward': 25.00,
                'min_level': levels[1] if len(levels) > 1 else None,
                'evaluation_criteria': 'Must cover at least 5 tools. Should include pricing. Must have a comparison structure.',
            },
            {
                'title': 'Write a Python function to flatten nested dictionaries',
                'description': (
                    'Write a Python function `flatten_dict(d, parent_key="", sep=".")` that takes a nested '
                    'dictionary and returns a flat one with dot-separated keys.\n\n'
                    'Example input: {"a": {"b": {"c": 1}}, "d": 2}\n'
                    'Expected output: {"a.b.c": 1, "d": 2}\n\n'
                    'Include: the function, type hints, docstring, and 3 test cases.'
                ),
                'category': 'coding',
                'reward': 30.00,
                'min_level': levels[1] if len(levels) > 1 else None,
                'evaluation_criteria': 'Code must run correctly. Must have type hints, docstring, and 3+ test cases.',
            },
            {
                'title': 'Analyze and critique this marketing email subject line strategy',
                'description': (
                    'Review the following 10 email subject lines for an e-commerce brand and provide:\n'
                    '1. A quality score (1-10) for each with one-line reasoning\n'
                    '2. Three patterns that make subject lines ineffective\n'
                    '3. Three rewritten alternatives (top 3 weakest ones)\n\n'
                    'Subject lines:\n'
                    '1. "You won\'t believe this deal"\n'
                    '2. "Weekly Newsletter #47"\n'
                    '3. "Limited time offer inside"\n'
                    '4. "Your cart is waiting..."\n'
                    '5. "We miss you! Come back"\n'
                    '6. "New arrivals"\n'
                    '7. "Important update to your account"\n'
                    '8. "Flash sale — 4 hours only"\n'
                    '9. "Hey"\n'
                    '10. "Here\'s your exclusive gift"'
                ),
                'category': 'analysis',
                'reward': 22.00,
                'min_level': None,
                'evaluation_criteria': 'Must score all 10. Must identify 3 patterns. Must rewrite at least 3.',
            },
            {
                'title': 'Create a structured onboarding checklist for a remote software engineer',
                'description': (
                    'Design a comprehensive 30-day onboarding checklist for a new remote software engineer joining a startup.\n\n'
                    'Organize it into 3 phases: Week 1 (orientation), Weeks 2-3 (ramp-up), Week 4 (independence).\n'
                    'Each phase should have 5-8 specific, actionable checklist items.\n'
                    'Also include a section on "red flags" — things that indicate a poor onboarding experience.'
                ),
                'category': 'other',
                'reward': 20.00,
                'min_level': levels[2] if len(levels) > 2 else None,
                'evaluation_criteria': 'Must have 3 phases. 5+ items per phase. Must include red flags section.',
            },
            {
                'title': 'Write SQL queries to extract customer cohort retention data',
                'description': (
                    'Given a hypothetical PostgreSQL database with two tables:\n'
                    '- users(id, created_at)\n'
                    '- events(user_id, event_type, created_at)\n\n'
                    'Write SQL queries to:\n'
                    '1. Calculate monthly user cohorts (users by signup month)\n'
                    '2. Calculate 30-day retention rate for each cohort\n'
                    '3. Find the cohort with the highest 60-day retention\n\n'
                    'Add comments explaining each query step.'
                ),
                'category': 'data',
                'reward': 45.00,
                'min_level': levels[3] if len(levels) > 3 else None,
                'evaluation_criteria': 'All 3 queries must be syntactically correct. Must include comments. Must handle edge cases.',
            },
        ]

        for data in tasks_data:
            if not Task.objects.filter(title=data['title']).exists():
                Task.objects.create(
                    title=data['title'],
                    description=data['description'],
                    company=company,
                    category=data['category'],
                    reward=data['reward'],
                    min_level=data['min_level'],
                    deadline=timezone.now() + timedelta(days=14),
                    max_submissions=30,
                    evaluation_criteria=data.get('evaluation_criteria', ''),
                )

        self.stdout.write(self.style.SUCCESS('✓ Demo data seeded successfully!'))
        self.stdout.write('')
        self.stdout.write('Demo accounts:')
        self.stdout.write('  Company:  username=acmecorp        password=demo1234')
        self.stdout.write('  Worker:   username=alice_dev       password=demo1234')
        self.stdout.write('  Worker:   username=carol_pro       password=demo1234')
        self.stdout.write('')
        self.stdout.write('Admin: python manage.py createsuperuser')
