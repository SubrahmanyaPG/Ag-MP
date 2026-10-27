import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from analyzer.models import Video, Comment


def extract_video_id(url_or_id: str) -> str:
    """
    Extracts an 11-character YouTube video ID from various URL formats or returns the raw ID.
    Supports:
    - https://www.youtube.com/watch?v=dQw4w9WgXcQ
    - https://youtu.be/dQw4w9WgXcQ
    - https://www.youtube.com/shorts/dQw4w9WgXcQ
    - https://www.youtube.com/embed/dQw4w9WgXcQ
    - dQw4w9WgXcQ
    """
    if not url_or_id:
        raise ValueError("Video URL or ID cannot be empty.")

    url_or_id = url_or_id.strip()

    # If it is already an 11-char ID without slashes/question marks
    if re.fullmatch(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id

    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?(?:.*&)?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    raise ValueError(f"Could not extract a valid YouTube video ID from: '{url_or_id}'")


class YouTubeService:
    """
    Service wrapper around YouTube Data API v3.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'YOUTUBE_API_KEY', '')
        if not self.api_key:
            raise ValueError(
                "YouTube Data API key is missing. "
                "Please configure YOUTUBE_API_KEY in your .env file or pass it to YouTubeService."
            )
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)

    def fetch_video_details(self, video_id: str) -> Dict:
        """
        Fetches metadata for a given video ID (title, channel, thumbnail, stats).
        """
        try:
            request = self.youtube.videos().list(
                part="snippet,statistics",
                id=video_id
            )
            response = request.execute()
        except HttpError as e:
            raise RuntimeError(f"YouTube API Error while fetching video details: {e}")

        items = response.get('items', [])
        if not items:
            raise ValueError(f"No video found on YouTube with ID: '{video_id}'")

        item = items[0]
        snippet = item.get('snippet', {})
        statistics = item.get('statistics', {})
        thumbnails = snippet.get('thumbnails', {})

        # Choose best available thumbnail
        thumb_url = (
            thumbnails.get('maxres', {}).get('url') or
            thumbnails.get('high', {}).get('url') or
            thumbnails.get('medium', {}).get('url') or
            thumbnails.get('default', {}).get('url') or
            ''
        )

        return {
            'youtube_video_id': video_id,
            'title': snippet.get('title', 'Untitled Video'),
            'channel': snippet.get('channelTitle', 'Unknown Channel'),
            'thumbnail_url': thumb_url,
            'view_count': int(statistics.get('viewCount', 0)),
            'like_count': int(statistics.get('likeCount', 0)),
            'comment_count': int(statistics.get('commentCount', 0)),
        }

    def fetch_comments(self, video_id: str, max_comments: int = 100) -> List[Dict]:
        """
        Fetches top-level comments for a video using commentThreads.list.
        Paginates until max_comments is reached or no more comments exist.
        """
        comments: List[Dict] = []
        next_page_token: Optional[str] = None

        while len(comments) < max_comments:
            batch_size = min(100, max_comments - len(comments))

            try:
                request = self.youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=batch_size,
                    pageToken=next_page_token,
                    textFormat="plainText",
                    order="relevance"
                )
                response = request.execute()
            except HttpError as e:
                # Handle comments disabled or private video
                if "commentsDisabled" in str(e):
                    raise RuntimeError(f"Comments are disabled for video {video_id}.")
                raise RuntimeError(f"YouTube API Error while fetching comments: {e}")

            for item in response.get('items', []):
                snippet = item.get('snippet', {})
                top_comment = snippet.get('topLevelComment', {}).get('snippet', {})
                
                comment_id = item.get('id')
                author = top_comment.get('authorDisplayName', 'Anonymous')
                author_image = top_comment.get('authorProfileImageUrl', '')
                text = top_comment.get('textDisplay') or top_comment.get('textOriginal') or ''
                like_count = top_comment.get('likeCount', 0)
                published_raw = top_comment.get('publishedAt')

                published_at = None
                if published_raw:
                    try:
                        # Parse ISO 8601 timestamp (e.g. 2026-10-26T12:00:00Z)
                        clean_ts = published_raw.replace('Z', '+00:00')
                        published_at = datetime.fromisoformat(clean_ts)
                    except Exception:
                        published_at = timezone.now()

                comments.append({
                    'comment_id': comment_id,
                    'author': author,
                    'author_profile_image': author_image,
                    'text': text,
                    'like_count': like_count,
                    'published_at': published_at,
                })

                if len(comments) >= max_comments:
                    break

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

        return comments

    def fetch_and_store(self, video_url_or_id: str, max_comments: int = 100) -> Tuple[Video, int, int]:
        """
        Full workflow:
        1. Parse video ID
        2. Fetch video metadata and update/create Video in Postgres
        3. Fetch comments and update/create Comment records in Postgres
        Returns (video_instance, total_fetched_count, new_or_updated_count)
        """
        video_id = extract_video_id(video_url_or_id)
        details = self.fetch_video_details(video_id)

        # 1. Update or create Video record
        video, _ = Video.objects.update_or_create(
            youtube_video_id=video_id,
            defaults={
                'title': details['title'],
                'channel': details['channel'],
                'thumbnail_url': details['thumbnail_url'],
            }
        )

        # 2. Fetch comments from API
        raw_comments = self.fetch_comments(video_id, max_comments=max_comments)

        # 3. Store comments in database
        saved_count = 0
        for c in raw_comments:
            _, created = Comment.objects.update_or_create(
                comment_id=c['comment_id'],
                defaults={
                    'video': video,
                    'author': c['author'],
                    'author_profile_image': c['author_profile_image'],
                    'text': c['text'],
                    'like_count': c['like_count'],
                    'published_at': c['published_at'],
                }
            )
            saved_count += 1

        return video, len(raw_comments), saved_count
