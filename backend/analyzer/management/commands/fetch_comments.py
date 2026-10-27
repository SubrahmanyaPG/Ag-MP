from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from analyzer.services.youtube import YouTubeService, extract_video_id
from analyzer.models import Video, Comment


class Command(BaseCommand):
    help = 'Fetches comments for a given YouTube video ID or URL and saves them to PostgreSQL.'

    def add_arguments(self, parser):
        parser.add_argument(
            'video_id_or_url',
            type=str,
            help='YouTube video ID (e.g. dQw4w9WgXcQ) or full YouTube URL'
        )
        parser.add_argument(
            '--max-comments',
            type=int,
            default=50,
            help='Maximum number of comments to fetch (default: 50)'
        )

    def handle(self, *args, **options):
        video_input = options['video_id_or_url']
        max_comments = options['max_comments']

        self.stdout.write(self.style.NOTICE(f"\n[Phase 1] YouTube Comment Fetcher"))
        self.stdout.write(f"Input: {video_input}")
        self.stdout.write(f"Max comments requested: {max_comments}")

        # Check API key
        api_key = getattr(settings, 'YOUTUBE_API_KEY', '')
        if not api_key:
            raise CommandError(
                "YOUTUBE_API_KEY is not set!\n"
                "Please add your YouTube Data API v3 key in backend/.env: YOUTUBE_API_KEY=your_key_here\n"
                "You can obtain a free API key at: https://console.cloud.google.com/"
            )

        try:
            service = YouTubeService(api_key=api_key)
            self.stdout.write(self.style.NOTICE("Connecting to YouTube Data API v3..."))
            
            video, fetched_count, stored_count = service.fetch_and_store(
                video_url_or_id=video_input,
                max_comments=max_comments
            )

            self.stdout.write(self.style.SUCCESS(
                f"\n--- SUCCESS: Video and Comments Stored in PostgreSQL ---"
            ))
            self.stdout.write(f"  Video Title : {video.title}")
            self.stdout.write(f"  Channel     : {video.channel}")
            self.stdout.write(f"  Video ID    : {video.youtube_video_id}")
            self.stdout.write(f"  Fetched     : {fetched_count} comments")
            self.stdout.write(f"  DB Total    : {video.comments.count()} comments currently in database")

            # Print a preview of stored comments
            self.stdout.write(self.style.NOTICE("\n--- Sample Stored Comments (First 3) ---"))
            for i, comment in enumerate(video.comments.all()[:3], 1):
                author = comment.author or "Anonymous"
                self.stdout.write(
                    f"{i}. [{author}] ({comment.published_at.strftime('%Y-%m-%d %H:%M') if comment.published_at else 'N/A'}):\n"
                    f"   \"{comment.text.strip()}\"\n"
                )

        except Exception as e:
            raise CommandError(f"Error fetching comments: {e}")
