import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Callable
from django.conf import settings
from django.utils import timezone
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from analyzer.models import Video, Comment

logger = logging.getLogger(__name__)


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


def _format_http_error(e: HttpError, video_id: str) -> RuntimeError:
    err_str = str(e).lower()
    if "commentsdisabled" in err_str:
        return RuntimeError(f"Comments are disabled on YouTube for video '{video_id}'.")
    elif "quotaexceeded" in err_str or "daily limit exceeded" in err_str or (hasattr(e, 'resp') and e.resp.status == 403):
        return RuntimeError("YouTube API daily quota exceeded. Please try again later or configure an alternate API key.")
    elif (hasattr(e, 'resp') and e.resp.status == 404) or "videonotfound" in err_str:
        return RuntimeError(f"YouTube video '{video_id}' was not found or has been set to private.")
    return RuntimeError(f"YouTube API Error: {e}")


class YouTubeService:
    """
    Service wrapper around YouTube Data API v3 supporting full-depth comment pagination,
    reply fetching, quota estimation, and batch database storage.
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
            raise _format_http_error(e, video_id)

        items = response.get('items', [])
        if not items:
            raise ValueError(f"No video found on YouTube with ID: '{video_id}'")

        item = items[0]
        snippet = item.get('snippet', {})
        statistics = item.get('statistics', {})
        thumbnails = snippet.get('thumbnails', {})

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

    def fetch_comments(
        self, 
        video_id: str, 
        max_comments: Optional[int] = 100, 
        include_replies: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict]:
        """
        Fetches top-level comments (and optionally replies) using commentThreads.list.
        Paginates until max_comments is reached or no more comments exist.
        If max_comments is None, bounds retrieval by settings.ANALYSIS_HARD_CAP.
        """
        hard_cap = getattr(settings, 'ANALYSIS_HARD_CAP', 20000)
        target_limit = hard_cap if (max_comments is None or max_comments <= 0) else min(max_comments, hard_cap)

        comments: List[Dict] = []
        next_page_token: Optional[str] = None
        seen_ids = set()

        part_param = "snippet,replies" if include_replies else "snippet"

        while len(comments) < target_limit:
            batch_size = min(100, target_limit - len(comments))

            try:
                request = self.youtube.commentThreads().list(
                    part=part_param,
                    videoId=video_id,
                    maxResults=batch_size,
                    pageToken=next_page_token,
                    textFormat="plainText",
                    order="relevance"
                )
                response = request.execute()
            except HttpError as e:
                raise _format_http_error(e, video_id)

            items = response.get('items', [])
            if not items:
                break

            for item in items:
                snippet = item.get('snippet', {})
                top_comment = snippet.get('topLevelComment', {}).get('snippet', {})
                comment_id = item.get('id')

                if comment_id and comment_id not in seen_ids:
                    seen_ids.add(comment_id)
                    author = top_comment.get('authorDisplayName', 'Anonymous')
                    author_image = top_comment.get('authorProfileImageUrl', '')
                    text = top_comment.get('textDisplay') or top_comment.get('textOriginal') or ''
                    like_count = top_comment.get('likeCount', 0)
                    published_raw = top_comment.get('publishedAt')

                    published_at = None
                    if published_raw:
                        try:
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

                # Process replies returned directly in the thread if include_replies is enabled
                if include_replies and 'replies' in item and len(comments) < target_limit:
                    for rep in item['replies'].get('comments', []):
                        rep_id = rep.get('id')
                        if rep_id and rep_id not in seen_ids and len(comments) < target_limit:
                            seen_ids.add(rep_id)
                            rep_snip = rep.get('snippet', {})
                            rep_raw_ts = rep_snip.get('publishedAt')
                            rep_pub = None
                            if rep_raw_ts:
                                try:
                                    rep_pub = datetime.fromisoformat(rep_raw_ts.replace('Z', '+00:00'))
                                except Exception:
                                    rep_pub = timezone.now()

                            comments.append({
                                'comment_id': rep_id,
                                'author': rep_snip.get('authorDisplayName', 'Anonymous'),
                                'author_profile_image': rep_snip.get('authorProfileImageUrl', ''),
                                'text': rep_snip.get('textDisplay') or rep_snip.get('textOriginal') or '',
                                'like_count': rep_snip.get('likeCount', 0),
                                'published_at': rep_pub,
                            })

                if len(comments) >= target_limit:
                    break

            if progress_callback:
                try:
                    progress_callback(len(comments), target_limit)
                except Exception:
                    pass

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

        return comments

    def fetch_and_store(
        self, 
        video_url_or_id: str, 
        max_comments: Optional[int] = 100, 
        include_replies: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[Video, int, int]:
        """
        Full workflow:
        1. Parse video ID
        2. Fetch video metadata and update/create Video in Postgres
        3. Fetch comments in pages up to target limit
        4. Store comments using bulk_create(batch_size=1000, ignore_conflicts=True)
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
        raw_comments = self.fetch_comments(
            video_id, 
            max_comments=max_comments, 
            include_replies=include_replies,
            progress_callback=progress_callback
        )

        # 3. Store comments in database via bulk_create
        comment_objs = [
            Comment(
                video=video,
                comment_id=c['comment_id'],
                youtube_comment_id=c['comment_id'],
                author=c.get('author', 'Anonymous'),
                author_profile_image=c.get('author_profile_image', ''),
                text=c.get('text', ''),
                like_count=c.get('like_count', 0),
                published_at=c.get('published_at') or timezone.now(),
            )
            for c in raw_comments
            if c.get('comment_id')
        ]

        if comment_objs:
            Comment.objects.bulk_create(comment_objs, batch_size=1000, ignore_conflicts=True)

        return video, len(raw_comments), len(comment_objs)


def fetch_video_preview(video_url_or_id: str) -> Dict:
    """
    Returns lightweight video metadata and quota estimation before running a full analysis.
    """
    video_id = extract_video_id(video_url_or_id)
    yt = YouTubeService()
    details = yt.fetch_video_details(video_id)
    comment_count = details.get('comment_count', 0)
    hard_cap = getattr(settings, 'ANALYSIS_HARD_CAP', 20000)

    # 1 unit for videos.list, and ~1 unit per 100 comments fetched
    effective_comments = min(comment_count, hard_cap)
    estimated_units = 1 + max(1, (effective_comments + 99) // 100)

    return {
        'video_id': video_id,
        'title': details['title'],
        'channel': details['channel'],
        'thumbnail_url': details['thumbnail_url'],
        'comment_count': comment_count,
        'effective_count': effective_comments,
        'estimated_quota_units': estimated_units,
        'hard_cap': hard_cap,
    }
