from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.http import require_POST
import json

from .models import Level, UserProfile, Task, Submission
from .ai_evaluator import evaluate_submission, calculate_earnings


# ─── Public Pages ────────────────────────────────────────────────────────────

def index(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    stats = {
        "total_tasks": Task.objects.filter(status="open").count(),
        "total_users": UserProfile.objects.filter(role="worker").count(),
        "total_paid": sum(
            s.earnings for s in Submission.objects.filter(status="evaluated")
        ),
        "top_workers": UserProfile.objects.filter(
            role="worker", total_submissions__gt=0
        ).order_by("-avg_score")[:5],
    }
    featured_tasks = Task.objects.filter(status="open").order_by("-reward")[:6]
    levels = Level.objects.all()
    return render(request, "core/index.html", {
        "stats": stats,
        "featured_tasks": featured_tasks,
        "levels": levels,
    })


# ─── Auth ─────────────────────────────────────────────────────────────────────
# All authentication is handled by Google OAuth via django-allauth.
# /accounts/google/login/  → starts the OAuth flow
# /accounts/google/login/callback/  → handled by allauth automatically

def login_view(request):
    """Redirect the old /login/ URL straight to Google OAuth."""
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "core/login.html")


def register_view(request):
    """Redirect the old /register/ URL straight to Google OAuth."""
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "core/login.html")


def logout_view(request):
    logout(request)
    return redirect("index")


# ─── Dashboard (role-aware) ───────────────────────────────────────────────────

@login_required
def dashboard(request):
    profile = request.user.profile
    if profile.role == "company":
        return company_dashboard(request)
    return worker_dashboard(request)


@login_required
def worker_dashboard(request):
    profile = request.user.profile
    all_open = Task.objects.filter(status="open")
    available_tasks = [t for t in all_open if t.is_accessible_by(request.user)][:8]

    recent_submissions = Submission.objects.filter(
        worker=request.user
    ).select_related("task")[:5]

    my_submissions = Submission.objects.filter(worker=request.user)
    evaluated = my_submissions.filter(status="evaluated")
    next_level = profile.next_level

    ctx = {
        "profile": profile,
        "available_tasks": available_tasks,
        "recent_submissions": recent_submissions,
        "total_submissions": my_submissions.count(),
        "evaluated_count": evaluated.count(),
        "pending_count": my_submissions.filter(status="pending").count(),
        "total_earnings": profile.total_earnings,
        "avg_score": round(profile.avg_score, 1),
        "level_progress": profile.level_progress,
        "next_level": next_level,
        "levels": Level.objects.all(),
    }
    return render(request, "core/worker_dashboard.html", ctx)


@login_required
def company_dashboard(request):
    profile = request.user.profile
    if profile.role != "company":
        return redirect("worker_dashboard")

    my_tasks = Task.objects.filter(company=request.user)
    open_tasks = my_tasks.filter(status="open")
    recent_submissions = Submission.objects.filter(
        task__company=request.user
    ).select_related("task", "worker").order_by("-submitted_at")[:10]

    ctx = {
        "profile": profile,
        "my_tasks": my_tasks[:10],
        "open_count": open_tasks.count(),
        "closed_count": my_tasks.filter(status="closed").count(),
        "total_tasks": my_tasks.count(),
        "total_submissions": Submission.objects.filter(task__company=request.user).count(),
        "recent_submissions": recent_submissions,
    }
    return render(request, "core/company_dashboard.html", ctx)


# ─── Tasks ───────────────────────────────────────────────────────────────────

@login_required
def task_list(request):
    profile = request.user.profile
    tasks = Task.objects.filter(status="open")

    category = request.GET.get("category", "")
    search = request.GET.get("q", "")
    level_filter = request.GET.get("level", "")
    sort = request.GET.get("sort", "-created_at")

    if category:
        tasks = tasks.filter(category=category)
    if search:
        tasks = tasks.filter(Q(title__icontains=search) | Q(description__icontains=search))
    if level_filter:
        tasks = tasks.filter(min_level__level_number=level_filter)

    valid_sorts = ["-created_at", "created_at", "-reward", "reward", "deadline"]
    if sort in valid_sorts:
        tasks = tasks.order_by(sort)

    task_data = []
    for task in tasks:
        task_data.append({
            "task": task,
            "accessible": task.is_accessible_by(request.user),
            "submitted": task.user_has_submitted(request.user),
        })

    ctx = {
        "task_data": task_data,
        "profile": profile,
        "categories": Task.CATEGORY_CHOICES,
        "levels": Level.objects.all(),
        "current_category": category,
        "current_search": search,
        "current_sort": sort,
    }
    return render(request, "core/task_list.html", ctx)


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    profile = request.user.profile
    accessible = task.is_accessible_by(request.user)
    submitted = task.user_has_submitted(request.user)
    user_submission = None
    if submitted:
        user_submission = Submission.objects.filter(task=task, worker=request.user).first()

    top_submissions = task.submissions.filter(
        status="evaluated"
    ).order_by("-ai_score")[:5]

    ctx = {
        "task": task,
        "profile": profile,
        "accessible": accessible,
        "submitted": submitted,
        "user_submission": user_submission,
        "top_submissions": top_submissions,
        "spots_left": task.spots_left,
    }
    return render(request, "core/task_detail.html", ctx)


@login_required
@require_POST
def submit_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    profile = request.user.profile

    if not task.is_accessible_by(request.user):
        messages.error(request, "You do not meet the level requirement for this task.")
        return redirect("task_detail", pk=pk)

    if task.user_has_submitted(request.user):
        messages.error(request, "You have already submitted this task.")
        return redirect("task_detail", pk=pk)

    if task.status != "open":
        messages.error(request, "This task is no longer accepting submissions.")
        return redirect("task_detail", pk=pk)

    if task.spots_left <= 0:
        messages.error(request, "This task has reached its maximum submissions.")
        return redirect("task_detail", pk=pk)

    content = request.POST.get("content", "").strip()
    if len(content) < 50:
        messages.error(request, "Submission must be at least 50 characters.")
        return redirect("task_detail", pk=pk)

    submission = Submission.objects.create(
        task=task,
        worker=request.user,
        content=content,
        status="evaluating",
    )

    try:
        result = evaluate_submission(task, content)
        multiplier = profile.level.reward_multiplier if profile.level else 1.0
        earnings = calculate_earnings(task.reward, result["score"], multiplier)

        submission.ai_score = result["score"]
        submission.ai_feedback = result["feedback"]
        submission.ai_strengths = json.dumps(result["strengths"])
        submission.ai_improvements = json.dumps(result["improvements"])
        submission.status = "evaluated"
        submission.evaluated_at = timezone.now()
        submission.earnings = earnings
        submission.save()

        profile.total_earnings += earnings
        profile.save()
        try:
            profile.update_stats()
        except Exception:
            pass  # stats will self-correct on next submission

        messages.success(
            request,
            f'Submission evaluated! Score: {result["score"]}/100 — Earned: ${earnings}',
        )
    except Exception as e:
            submission.status = "pending"
            submission.ai_feedback = f"Evaluation failed: {str(e)}"
            submission.save()
            messages.warning(request, f"Submission received but AI evaluation failed: {e}")

    return redirect("submission_detail", pk=submission.pk)


@login_required
def post_task(request):
    profile = request.user.profile
    if profile.role != "company":
        messages.error(request, "Only companies can post tasks.")
        return redirect("dashboard")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        category = request.POST.get("category", "other")
        reward = request.POST.get("reward", "0")
        deadline = request.POST.get("deadline", "")
        min_level_id = request.POST.get("min_level", "")
        max_submissions = request.POST.get("max_submissions", "20")
        evaluation_criteria = request.POST.get("evaluation_criteria", "").strip()

        errors = []
        if not title:
            errors.append("Title is required.")
        if len(description) < 50:
            errors.append("Description must be at least 50 characters.")
        try:
            reward = float(reward)
            if reward <= 0:
                errors.append("Reward must be greater than 0.")
        except ValueError:
            errors.append("Invalid reward amount.")

        if errors:
            return render(request, "core/post_task.html", {
                "errors": errors,
                "levels": Level.objects.all(),
                "categories": Task.CATEGORY_CHOICES,
                "form_data": request.POST,
            })

        min_level = None
        if min_level_id:
            min_level = Level.objects.filter(pk=min_level_id).first()

        from datetime import datetime
        try:
            deadline_dt = datetime.fromisoformat(deadline)
            deadline_dt = timezone.make_aware(deadline_dt)
        except (ValueError, TypeError):
            deadline_dt = timezone.now() + timezone.timedelta(days=7)

        task = Task.objects.create(
            title=title,
            description=description,
            company=request.user,
            reward=reward,
            category=category,
            deadline=deadline_dt,
            min_level=min_level,
            max_submissions=int(max_submissions) if max_submissions else 20,
            evaluation_criteria=evaluation_criteria,
        )
        messages.success(request, f'Task "{title}" posted successfully!')
        return redirect("task_detail", pk=task.pk)

    return render(request, "core/post_task.html", {
        "levels": Level.objects.all(),
        "categories": Task.CATEGORY_CHOICES,
    })


@login_required
def close_task(request, pk):
    task = get_object_or_404(Task, pk=pk, company=request.user)
    task.status = "closed"
    task.save()
    messages.success(request, f'Task "{task.title}" has been closed.')
    return redirect("company_dashboard")


# ─── Submissions ─────────────────────────────────────────────────────────────

@login_required
def submission_detail(request, pk):
    submission = get_object_or_404(Submission, pk=pk)
    if submission.worker != request.user and submission.task.company != request.user:
        messages.error(request, "You do not have permission to view this submission.")
        return redirect("dashboard")

    strengths, improvements = [], []
    try:
        if submission.ai_strengths:
            strengths = json.loads(submission.ai_strengths)
        if submission.ai_improvements:
            improvements = json.loads(submission.ai_improvements)
    except json.JSONDecodeError:
        pass

    return render(request, "core/submission_detail.html", {
        "submission": submission,
        "strengths": strengths,
        "improvements": improvements,
        "profile": request.user.profile,
    })


@login_required
def my_submissions(request):
    subs = Submission.objects.filter(worker=request.user).select_related("task")
    return render(request, "core/my_submissions.html", {
        "submissions": subs,
        "profile": request.user.profile,
    })


@login_required
def task_submissions(request, pk):
    task = get_object_or_404(Task, pk=pk, company=request.user)
    subs = task.submissions.select_related("worker", "worker__profile").order_by("-ai_score")
    return render(request, "core/task_submissions.html", {
        "task": task,
        "submissions": subs,
        "profile": request.user.profile,
    })


# ─── Profile ─────────────────────────────────────────────────────────────────

@login_required
def profile(request):
    prof = request.user.profile
    if request.method == "POST":
        bio = request.POST.get("bio", "").strip()
        company_name = request.POST.get("company_name", "").strip()
        role = request.POST.get("role", "").strip()
        prof.bio = bio
        prof.company_name = company_name
        if role in ("worker", "company"):
            prof.role = role
        prof.save()
        messages.success(request, "Profile updated.")
        return redirect("profile")

    submissions = Submission.objects.filter(worker=request.user).select_related("task")[:10]
    return render(request, "core/profile.html", {
        "profile": prof,
        "submissions": submissions,
        "levels": Level.objects.all(),
    })


def leaderboard(request):
    workers = UserProfile.objects.filter(
        role="worker", total_submissions__gt=0
    ).select_related("user", "level").order_by("-avg_score", "-total_submissions")[:20]
    return render(request, "core/leaderboard.html", {
        "workers": workers,
        "profile": request.user.profile if request.user.is_authenticated else None,
    })