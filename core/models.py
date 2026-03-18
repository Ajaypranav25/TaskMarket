from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Level(models.Model):
    name = models.CharField(max_length=50)
    level_number = models.IntegerField(unique=True)
    min_avg_score = models.FloatField(default=0)
    min_submissions = models.IntegerField(default=0)
    reward_multiplier = models.FloatField(default=1.0)
    description = models.TextField(blank=True)
    badge_color = models.CharField(max_length=20, default='#6b7280')
    icon = models.CharField(max_length=10, default='⬡')

    class Meta:
        ordering = ['level_number']

    def __str__(self):
        return f"Level {self.level_number}: {self.name}"


class UserProfile(models.Model):
    ROLE_CHOICES = [('worker', 'Worker'), ('company', 'Company')]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='worker')
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avg_score = models.FloatField(default=0)
    total_submissions = models.IntegerField(default=0)
    bio = models.TextField(blank=True)
    company_name = models.CharField(max_length=100, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    def update_stats(self):
        """Recalculate avg score and level after each submission."""
        evaluated = Submission.objects.filter(
            worker=self.user, status='evaluated'
        )
        self.total_submissions = evaluated.count()
        if self.total_submissions > 0:
            total_score = sum(s.ai_score for s in evaluated if s.ai_score)
            self.avg_score = total_score / self.total_submissions
        self._update_level()
        self.save()

    def _update_level(self):
        eligible = Level.objects.filter(
            min_avg_score__lte=self.avg_score,
            min_submissions__lte=self.total_submissions
        ).order_by('-level_number').first()
        if eligible:
            self.level = eligible

    @property
    def level_progress(self):
        """Percentage progress to next level."""
        if not self.level:
            return 0
        next_level = Level.objects.filter(
            level_number__gt=self.level.level_number
        ).first()
        if not next_level:
            return 100
        current_min = self.level.min_avg_score
        next_min = next_level.min_avg_score
        if next_min == current_min:
            return 100
        progress = ((self.avg_score - current_min) / (next_min - current_min)) * 100
        return min(100, max(0, round(progress)))

    @property
    def next_level(self):
        if not self.level:
            return Level.objects.first()
        return Level.objects.filter(
            level_number__gt=self.level.level_number
        ).first()


class Task(models.Model):
    STATUS_CHOICES = [('open', 'Open'), ('closed', 'Closed'), ('completed', 'Completed')]
    CATEGORY_CHOICES = [
        ('writing', 'Writing'),
        ('coding', 'Coding'),
        ('research', 'Research'),
        ('design', 'Design'),
        ('data', 'Data Entry'),
        ('analysis', 'Analysis'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    company = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_tasks')
    reward = models.DecimalField(max_digits=10, decimal_places=2)
    min_level = models.ForeignKey(
        Level, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks'
    )
    deadline = models.DateTimeField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    max_submissions = models.IntegerField(default=20)
    evaluation_criteria = models.TextField(
        blank=True,
        help_text="Specific criteria for AI evaluation"
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def submission_count(self):
        return self.submissions.count()

    @property
    def spots_left(self):
        return max(0, self.max_submissions - self.submission_count)

    @property
    def avg_score(self):
        evaluated = self.submissions.filter(status='evaluated')
        if not evaluated.exists():
            return None
        scores = [s.ai_score for s in evaluated if s.ai_score is not None]
        return round(sum(scores) / len(scores), 1) if scores else None

    def is_accessible_by(self, user):
        if not hasattr(user, 'profile'):
            return False
        profile = user.profile
        if not self.min_level:
            return True
        user_level = profile.level
        if not user_level:
            return self.min_level.level_number == 1
        return user_level.level_number >= self.min_level.level_number

    def user_has_submitted(self, user):
        return self.submissions.filter(worker=user).exists()


class Submission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('evaluating', 'Evaluating'),
        ('evaluated', 'Evaluated'),
        ('rejected', 'Rejected'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='submissions')
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    content = models.TextField()
    ai_score = models.FloatField(null=True, blank=True)
    ai_feedback = models.TextField(blank=True)
    ai_strengths = models.TextField(blank=True)
    ai_improvements = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    evaluated_at = models.DateTimeField(null=True, blank=True)
    earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['task', 'worker']

    def __str__(self):
        return f"{self.worker.username} → {self.task.title}"

    @property
    def score_grade(self):
        if self.ai_score is None:
            return 'N/A'
        if self.ai_score >= 90:
            return 'Exceptional'
        if self.ai_score >= 75:
            return 'Good'
        if self.ai_score >= 60:
            return 'Acceptable'
        if self.ai_score >= 40:
            return 'Below Average'
        return 'Poor'

    @property
    def score_color(self):
        if self.ai_score is None:
            return '#6b7280'
        if self.ai_score >= 90:
            return '#10b981'
        if self.ai_score >= 75:
            return '#3b82f6'
        if self.ai_score >= 60:
            return '#d97706'
        if self.ai_score >= 40:
            return '#f59e0b'
        return '#ef4444'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        level_1 = Level.objects.filter(level_number=1).first()
        UserProfile.objects.create(user=instance, level=level_1)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
