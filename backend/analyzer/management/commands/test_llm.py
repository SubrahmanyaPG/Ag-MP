import json
from django.core.management.base import BaseCommand
from analyzer.models import Report, Video
from analyzer.llm.prompts import build_analysis_prompt
from analyzer.llm.service import generate_recommendations_and_titles
from analyzer.llm.client import LLMClient


class Command(BaseCommand):
    help = 'Tests Phase 4 LLM recommendation and title generation using Groq API (or fallback).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--video-id',
            type=str,
            default=None,
            help='YouTube video ID from DB to run LLM analysis on.'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 70))
        self.stdout.write(self.style.MIGRATE_HEADING(" Phase 4: LLM Layer Verification (Groq API) "))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 70))

        client = LLMClient()
        is_configured = client.is_configured()
        if is_configured:
            self.stdout.write(self.style.SUCCESS(f"  Groq API Key : CONFIGURED (Model: {client.model})"))
        else:
            self.stdout.write(self.style.WARNING("  Groq API Key : NOT CONFIGURED (Using heuristic fallback preview)"))
            self.stdout.write("  Add your Groq API key in backend/.env: GROQ_API_KEY=gsk_...")

        video_id = options.get('video_id')
        report = None
        if video_id:
            report = Report.objects.filter(job__video__youtube_video_id=video_id).first()
        if not report:
            report = Report.objects.first()

        if report:
            video_title = report.job.video.title
            channel = report.job.video.channel
            sentiment_summary = report.sentiment_summary
            top_keywords = report.top_keywords
            top_requests = report.top_requests
            topic_clusters = []
            self.stdout.write(f"\nUsing real video data from DB: '{video_title}' by '{channel}'")
        else:
            video_title = "Building a Full-Stack NLP Web Application with Django and React"
            channel = "Tech With Code"
            sentiment_summary = {
                "total": 120,
                "positive_count": 85,
                "positive_percentage": 70.8,
                "neutral_count": 25,
                "neutral_percentage": 20.8,
                "negative_count": 10,
                "negative_percentage": 8.3,
                "average_compound": 0.42,
                "spam_filtered": 5
            }
            top_keywords = [
                {"keyword": "react vite", "count": 18},
                {"keyword": "celery redis", "count": 14},
                {"keyword": "jwt auth", "count": 9},
                {"keyword": "deployment", "count": 8}
            ]
            top_requests = [
                {"request": "make a tutorial on Docker deployment", "count": 12, "category": "video_request"},
                {"request": "share GitHub repository code", "count": 8, "category": "resource_request"},
                {"request": "terminal font was too small", "count": 3, "category": "visual_feedback"}
            ]
            topic_clusters = [
                {"topic_name": "Architecture & Celery Setup", "percentage": 45.0, "keywords": ["celery", "redis", "async"]},
                {"topic_name": "Frontend Integration", "percentage": 35.0, "keywords": ["react", "vite", "tailwind"]},
                {"topic_name": "Bugs & Troubleshooting", "percentage": 20.0, "keywords": ["import error", "version", "path"]}
            ]
            self.stdout.write("\n(No DB report found; using sample data for testing)")

        # 1. Preview Prompt
        self.stdout.write(self.style.NOTICE("\n--- Generated Prompt Preview (Aggregated Data Only) ---"))
        prompt_text = build_analysis_prompt(
            video_title=video_title,
            channel=channel,
            sentiment_summary=sentiment_summary,
            top_keywords=top_keywords,
            top_requests=top_requests,
            topic_clusters=topic_clusters
        )
        self.stdout.write(prompt_text[:300] + "\n...[truncated for display]...")

        # 2. Call LLM Service
        self.stdout.write(self.style.NOTICE("\n--- Invoking LLM Service... ---"))
        insights = generate_recommendations_and_titles(
            video_title=video_title,
            channel=channel,
            sentiment_summary=sentiment_summary,
            top_keywords=top_keywords,
            top_requests=top_requests,
            topic_clusters=topic_clusters
        )

        self.stdout.write(self.style.SUCCESS(f"\nProvider Used : {insights.get('provider')} (Model: {insights.get('model')})"))

        self.stdout.write(self.style.SUCCESS("\n--- AI-Generated Recommendations ---"))
        self.stdout.write(insights.get('recommendations', 'None'))

        self.stdout.write(self.style.SUCCESS("\n--- 5 AI-Suggested Video Titles ---"))
        for i, title in enumerate(insights.get('suggested_titles', []), 1):
            self.stdout.write(f"  {i}. {title}")

        # Update report if existed
        if report:
            report.recommendations = insights.get('recommendations', '')
            report.suggested_titles = insights.get('suggested_titles', [])
            report.save(update_fields=['recommendations', 'suggested_titles'])
            self.stdout.write(self.style.SUCCESS(f"\nUpdated Report #{report.id} in PostgreSQL with LLM insights!"))

        self.stdout.write(self.style.MIGRATE_HEADING("\n" + "=" * 70))
        self.stdout.write(self.style.SUCCESS(" Phase 4 Verification Completed Successfully! "))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 70 + "\n"))
