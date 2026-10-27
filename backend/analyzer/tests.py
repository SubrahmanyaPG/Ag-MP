from django.test import TestCase
from unittest.mock import patch, MagicMock
from analyzer.models import Video, Comment, AnalysisJob, Report
from analyzer.services.youtube import extract_video_id, YouTubeService


class VideoIdExtractionTests(TestCase):
    def test_standard_watch_url(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_short_url(self):
        url = "https://youtu.be/dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_shorts_url(self):
        url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_embed_url(self):
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_raw_id(self):
        video_id = "dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(video_id), "dQw4w9WgXcQ")

    def test_url_with_parameters(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s&feature=shared"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_invalid_url_raises(self):
        with self.assertRaises(ValueError):
            extract_video_id("https://example.com/not-youtube")

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError):
            extract_video_id("")


class DataModelTests(TestCase):
    def setUp(self):
        self.video = Video.objects.create(
            youtube_video_id="test_vid_123",
            title="NLP Project Demo",
            channel="Tech Channel",
            thumbnail_url="https://example.com/thumb.jpg"
        )

    def test_video_creation(self):
        self.assertEqual(self.video.youtube_video_id, "test_vid_123")
        self.assertEqual(str(self.video), "NLP Project Demo (test_vid_123)")

    def test_comment_creation(self):
        comment = Comment.objects.create(
            video=self.video,
            comment_id="c_101",
            author="Alice",
            text="Awesome explanation of sentiment analysis!",
            like_count=15
        )
        self.assertEqual(self.video.comments.count(), 1)
        self.assertIn("Alice", str(comment))
        self.assertEqual(comment.is_spam, False)
        self.assertIsNone(comment.sentiment_label)

    def test_analysis_job_and_report_relationship(self):
        job = AnalysisJob.objects.create(
            video=self.video,
            status=AnalysisJob.STATUS_PENDING
        )
        self.assertEqual(job.status, "pending")

        report = Report.objects.create(
            job=job,
            sentiment_summary={"positive": 10, "neutral": 2, "negative": 1},
            top_keywords=[{"keyword": "nlp", "count": 5}],
            top_requests=["make a part 2"],
            recommendations="Focus on deeper NLP topics.",
            suggested_titles=["Mastering NLP in 2026"]
        )
        self.assertEqual(job.report, report)
        self.assertEqual(report.sentiment_summary["positive"], 10)


class YouTubeServiceMockTests(TestCase):
    @patch('analyzer.services.youtube.build')
    def test_fetch_and_store_mocked(self, mock_build):
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube

        # Mock videos().list().execute()
        mock_youtube.videos().list().execute.return_value = {
            'items': [{
                'snippet': {
                    'title': 'Test Video Title',
                    'channelTitle': 'Test Channel',
                    'thumbnails': {'high': {'url': 'https://example.com/thumb.jpg'}}
                },
                'statistics': {'viewCount': '5000', 'likeCount': '250', 'commentCount': '2'}
            }]
        }

        # Mock commentThreads().list().execute()
        mock_youtube.commentThreads().list().execute.return_value = {
            'items': [
                {
                    'id': 'comment_mock_1',
                    'snippet': {
                        'topLevelComment': {
                            'snippet': {
                                'authorDisplayName': 'Bob',
                                'authorProfileImageUrl': 'https://example.com/bob.jpg',
                                'textDisplay': 'Great video, learned a lot!',
                                'likeCount': 5,
                                'publishedAt': '2026-10-20T10:00:00Z'
                            }
                        }
                    }
                },
                {
                    'id': 'comment_mock_2',
                    'snippet': {
                        'topLevelComment': {
                            'snippet': {
                                'authorDisplayName': 'Charlie',
                                'authorProfileImageUrl': 'https://example.com/charlie.jpg',
                                'textDisplay': 'Check out my crypto channel click here: http://spam.xyz',
                                'likeCount': 0,
                                'publishedAt': '2026-10-21T12:00:00Z'
                            }
                        }
                    }
                }
            ]
        }

        service = YouTubeService(api_key="dummy_test_key")
        video, fetched_count, stored_count = service.fetch_and_store(
            video_url_or_id="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            max_comments=10
        )

        self.assertEqual(video.youtube_video_id, "dQw4w9WgXcQ")
        self.assertEqual(video.title, "Test Video Title")
        self.assertEqual(fetched_count, 2)
        self.assertEqual(stored_count, 2)
        self.assertEqual(video.comments.count(), 2)

        comment1 = video.comments.get(comment_id="comment_mock_1")
        self.assertEqual(comment1.author, "Bob")
        self.assertEqual(comment1.text, "Great video, learned a lot!")

        # Verify idempotency (re-fetching same comments should update, not duplicate)
        _, fetched_count2, _ = service.fetch_and_store(
            video_url_or_id="dQw4w9WgXcQ",
            max_comments=10
        )
        self.assertEqual(video.comments.count(), 2)


from analyzer.nlp.preprocessor import clean_text, tokenize_and_filter
from analyzer.nlp.sentiment import analyze_sentiment, summarize_sentiment
from analyzer.nlp.spam_classifier import get_default_spam_classifier
from analyzer.nlp.topic_modeler import cluster_topics
from analyzer.nlp.request_extractor import extract_requests, extract_top_keywords
from analyzer.nlp.pipeline import run_nlp_pipeline


class NLPPreprocessorTests(TestCase):
    def test_clean_text_removes_urls_and_mentions(self):
        raw = "Check out my site https://example.com/test and follow @creator! Great job at 02:45!"
        cleaned = clean_text(raw)
        self.assertNotIn("https://example.com/test", cleaned)
        self.assertNotIn("@creator", cleaned)
        self.assertNotIn("02:45", cleaned)
        self.assertIn("Great job at", cleaned)

    def test_clean_text_unescapes_html(self):
        raw = "Me &amp; my team &quot;loved&quot; it!"
        cleaned = clean_text(raw)
        self.assertEqual(cleaned, 'Me & my team "loved" it!')

    def test_tokenize_and_filter_removes_stopwords(self):
        raw = "This video is really great and I watched the tutorial on python"
        tokens = tokenize_and_filter(raw)
        self.assertIn("great", tokens)
        self.assertIn("python", tokens)
        self.assertNotIn("video", tokens)
        self.assertNotIn("this", tokens)


class NLPSentimentTests(TestCase):
    def test_positive_sentiment(self):
        res = analyze_sentiment("This is the best explanation ever! Absolutely loved it!")
        self.assertEqual(res['label'], 'positive')
        self.assertGreater(res['compound'], 0.05)

    def test_negative_sentiment(self):
        res = analyze_sentiment("The audio was terrible, horrible buzzing noise and completely useless.")
        self.assertEqual(res['label'], 'negative')
        self.assertLess(res['compound'], -0.05)

    def test_neutral_sentiment(self):
        res = analyze_sentiment("The video length is 24 minutes.")
        self.assertEqual(res['label'], 'neutral')

    def test_summarize_sentiment(self):
        results = [
            {'label': 'positive', 'compound': 0.8},
            {'label': 'positive', 'compound': 0.6},
            {'label': 'neutral', 'compound': 0.0},
            {'label': 'negative', 'compound': -0.5},
        ]
        summary = summarize_sentiment(results)
        self.assertEqual(summary['total'], 4)
        self.assertEqual(summary['positive_count'], 2)
        self.assertEqual(summary['neutral_count'], 1)
        self.assertEqual(summary['negative_count'], 1)
        self.assertEqual(summary['positive_percentage'], 50.0)


class NLPSpamClassifierTests(TestCase):
    def setUp(self):
        self.clf = get_default_spam_classifier()

    def test_crypto_whatsapp_spam(self):
        spam_text = "Reach Mrs. Brenda on WhatsApp: +1-202-555-0184 to recover lost crypto funds!"
        res = self.clf.classify(spam_text)
        self.assertTrue(res['is_spam'])
        self.assertGreaterEqual(res['confidence'], 0.70)

    def test_promo_bot_spam(self):
        promo_text = "Please subscribe to my channel for free robux and v-bucks giveaway!"
        res = self.clf.classify(promo_text)
        self.assertTrue(res['is_spam'])

    def test_legitimate_comment_is_not_spam(self):
        ham_text = "I had a question about line 42 when importing django.db. Is anyone else having this error?"
        res = self.clf.classify(ham_text)
        self.assertFalse(res['is_spam'])


class NLPTopicModelerAndExtractorTests(TestCase):
    def test_extract_requests(self):
        comments = [
            "Could you please make a tutorial on Docker and Kubernetes?",
            "Please make a tutorial on React with Vite!",
            "Can you please share the GitHub repository link?",
            "Just a normal comment with no request.",
        ]
        requests = extract_requests(comments)
        self.assertGreaterEqual(len(requests), 2)
        req_texts = " ".join([r['request'].lower() for r in requests])
        self.assertTrue("docker" in req_texts or "react" in req_texts or "github" in req_texts)

    def test_extract_top_keywords(self):
        comments = [
            "Dynamic programming and recursion are key topics.",
            "Loved the dynamic programming explanation.",
            "Recursion was explained super well.",
        ]
        keywords = extract_top_keywords(comments, top_n=5)
        kw_names = [k['keyword'] for k in keywords]
        self.assertTrue(any("programming" in k or "recursion" in k or "dynamic" in k for k in kw_names))

    def test_run_nlp_pipeline_end_to_end(self):
        sample_batch = [
            {"text": "Amazing video on machine learning, thank you!"},
            {"text": "Could you please do a follow-up video on NLP?"},
            {"text": "Earn $5000 daily with crypto trader on WhatsApp +123456789"},
            {"text": "The audio is too low, couldn't hear the explanation."},
        ]
        results = run_nlp_pipeline(sample_batch)
        self.assertEqual(results['total_comments'], 4)
        self.assertEqual(results['spam_count'], 1)
        self.assertEqual(results['ham_count'], 3)
        self.assertIn('positive_count', results['sentiment_summary'])
        self.assertGreaterEqual(len(results['top_requests']), 1)


from rest_framework.test import APITestCase
from analyzer.tasks import analyze_video_task


class Phase3APITests(APITestCase):
    def setUp(self):
        self.video = Video.objects.create(
            youtube_video_id="dQw4w9WgXcQ",
            title="Never Gonna Give You Up",
            channel="Rick Astley"
        )
        self.comment1 = Comment.objects.create(
            video=self.video,
            comment_id="c_p3_1",
            author="User A",
            text="Amazing classic song, love this!",
            like_count=100
        )
        self.comment2 = Comment.objects.create(
            video=self.video,
            comment_id="c_p3_2",
            author="User B",
            text="Contact Mrs. Brenda on WhatsApp: +1-202-555-0184 to recover crypto!",
            like_count=0
        )
        self.comment3 = Comment.objects.create(
            video=self.video,
            comment_id="c_p3_3",
            author="User C",
            text="Could you please make a tutorial on audio remastering?",
            like_count=5
        )

    def test_post_analyze_endpoint(self):
        response = self.client.post('/api/videos/analyze/', {
            'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'max_comments': 50
        })
        self.assertEqual(response.status_code, 202)
        self.assertIn('job_id', response.data)
        job_id = response.data['job_id']
        job = AnalysisJob.objects.get(id=job_id)
        self.assertEqual(job.video.youtube_video_id, "dQw4w9WgXcQ")

    def test_job_status_endpoint(self):
        job = AnalysisJob.objects.create(
            video=self.video,
            status=AnalysisJob.STATUS_RUNNING
        )
        response = self.client.get(f'/api/jobs/{job.id}/status/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'running')
        self.assertEqual(response.data['video_id'], 'dQw4w9WgXcQ')

    def test_end_to_end_analysis_task(self):
        job = AnalysisJob.objects.create(
            video=self.video,
            status=AnalysisJob.STATUS_PENDING
        )
        # Execute Celery task directly
        result = analyze_video_task(job.id, max_comments=10)
        self.assertEqual(result['status'], 'done')

        job.refresh_from_db()
        self.assertEqual(job.status, AnalysisJob.STATUS_DONE)
        self.assertIsNotNone(job.completed_at)

        # Verify Report was created in DB
        self.assertTrue(hasattr(job, 'report'))
        report = job.report
        self.assertIn('positive_count', report.sentiment_summary)
        self.assertGreaterEqual(len(report.top_keywords), 1)

        # Verify Comments were updated in DB
        self.comment2.refresh_from_db()
        self.assertTrue(self.comment2.is_spam)

        self.comment1.refresh_from_db()
        self.assertEqual(self.comment1.sentiment_label, 'positive')

    def test_get_report_endpoint(self):
        job = AnalysisJob.objects.create(
            video=self.video,
            status=AnalysisJob.STATUS_DONE
        )
        report = Report.objects.create(
            job=job,
            sentiment_summary={"positive_percentage": 66.7, "neutral_percentage": 33.3, "negative_percentage": 0.0},
            top_keywords=[{"keyword": "song", "count": 10}],
            top_requests=[{"request": "remastering tutorial", "count": 1}]
        )
        response = self.client.get(f'/api/reports/{job.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['job_id'], job.id)
        self.assertIn('sentiment_summary', response.data)
        self.assertEqual(response.data['top_keywords'][0]['keyword'], 'song')

    def test_get_recent_reports(self):
        job = AnalysisJob.objects.create(
            video=self.video,
            status=AnalysisJob.STATUS_DONE
        )
        Report.objects.create(
            job=job,
            sentiment_summary={"positive_percentage": 80.0},
            top_keywords=[{"keyword": "music", "count": 12}],
            suggested_titles=["Epic Track 2026"]
        )
        response = self.client.get('/api/reports/recent/')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['video']['youtube_video_id'], self.video.youtube_video_id)

    def test_get_video_comments_with_filters(self):
        # Annotate
        self.comment1.sentiment_label = 'positive'
        self.comment1.is_spam = False
        self.comment1.save()

        self.comment2.is_spam = True
        self.comment2.save()

        # Filter by sentiment=positive
        res = self.client.get(f'/api/videos/{self.video.youtube_video_id}/comments/?sentiment=positive')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['comment_id'], 'c_p3_1')

        # Filter by is_spam=true
        res_spam = self.client.get(f'/api/videos/{self.video.youtube_video_id}/comments/?is_spam=true')
        self.assertEqual(res_spam.status_code, 200)
        self.assertEqual(res_spam.data['count'], 1)
        self.assertEqual(res_spam.data['results'][0]['comment_id'], 'c_p3_2')

    def test_export_report_csv(self):
        job = AnalysisJob.objects.create(
            video=self.video,
            status=AnalysisJob.STATUS_DONE
        )
        Report.objects.create(
            job=job,
            sentiment_summary={"positive_percentage": 50.0}
        )
        response = self.client.get(f'/api/reports/{job.id}/export/?format=csv')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        content = response.content.decode('utf-8')
        self.assertIn("Never Gonna Give You Up", content)
        self.assertIn("User A", content)


from unittest.mock import patch, MagicMock
from analyzer.llm.prompts import build_analysis_prompt
from analyzer.llm.client import LLMClient
from analyzer.llm.service import generate_recommendations_and_titles


class Phase4LLMTests(TestCase):
    def test_build_analysis_prompt_structure(self):
        prompt = build_analysis_prompt(
            video_title="Learn Django & React",
            channel="Code Academy",
            sentiment_summary={"positive_percentage": 80.0, "neutral_percentage": 15.0, "negative_percentage": 5.0, "total": 50},
            top_keywords=[{"keyword": "django rest", "count": 10}],
            top_requests=[{"request": "make a docker tutorial", "category": "video_request", "count": 4}],
            topic_clusters=[{"topic_name": "Tutorial Feedback", "percentage": 70.0, "keywords": ["django", "react"]}]
        )
        self.assertIn("Learn Django & React", prompt)
        self.assertIn("80.0% Positive", prompt)
        self.assertIn("django rest", prompt)
        self.assertIn("make a docker tutorial", prompt)
        self.assertIn("suggested_titles", prompt)

    @patch('groq.Groq')
    def test_llm_client_mock_groq(self, mock_groq_class):
        mock_instance = MagicMock()
        mock_groq_class.return_value = mock_instance

        mock_choice = MagicMock()
        mock_choice.message.content = '{"recommendations": "Focus on Docker deployment in next episode.", "suggested_titles": ["Title 1", "Title 2", "Title 3", "Title 4", "Title 5"]}'
        mock_instance.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        client = LLMClient(api_key="gsk_mock_test_key_12345")
        res = client.generate("system prompt", "user prompt")

        self.assertEqual(res['provider'], 'groq')
        self.assertIn("Focus on Docker deployment", res['recommendations'])
        self.assertEqual(len(res['suggested_titles']), 5)
        self.assertEqual(res['suggested_titles'][0], "Title 1")

    def test_llm_client_fallback_when_unconfigured(self):
        client = LLMClient(api_key="")
        res = client.generate("system prompt", "user prompt")
        self.assertEqual(res['provider'], 'heuristic_fallback')
        self.assertGreaterEqual(len(res['suggested_titles']), 3)
        self.assertIn("Recommendations", res['recommendations'])

    @patch('analyzer.tasks.generate_recommendations_and_titles')
    def test_celery_task_updates_report_with_llm_insights(self, mock_generate_llm):
        mock_generate_llm.return_value = {
            'recommendations': '### AI Recommendations:\n1. Expand on Celery setup.\n2. Add React frontend demo.',
            'suggested_titles': ['How to Build Async Apps with Celery', 'Django and React Masterclass 2026'],
            'provider': 'groq'
        }

        video = Video.objects.create(
            youtube_video_id="test_llm_vid",
            title="Async Pipelines",
            channel="Tech Guru"
        )
        Comment.objects.create(
            video=video,
            comment_id="c_llm_1",
            author="Dev",
            text="Please show how to use Celery with Redis!"
        )
        job = AnalysisJob.objects.create(
            video=video,
            status=AnalysisJob.STATUS_PENDING
        )

        analyze_video_task(job.id, max_comments=10)

        job.refresh_from_db()
        self.assertEqual(job.status, AnalysisJob.STATUS_DONE)
        report = job.report
        self.assertIn("Expand on Celery setup", report.recommendations)
        self.assertEqual(len(report.suggested_titles), 2)
        self.assertEqual(report.suggested_titles[0], 'How to Build Async Apps with Celery')


from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User


class PdfExportTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.video = Video.objects.create(
            youtube_video_id="pdf_vid_99",
            title="Building NLP Dashboards with React and Django",
            channel="Python Academy"
        )
        self.job = AnalysisJob.objects.create(
            video=self.video,
            status=AnalysisJob.STATUS_DONE
        )
        self.report = Report.objects.create(
            job=self.job,
            sentiment_summary={
                'total': 10,
                'positive': 7,
                'neutral': 2,
                'negative': 1,
                'positive_percentage': 70.0,
                'neutral_percentage': 20.0,
                'negative_percentage': 10.0,
                'average_compound': 0.65,
                'spam_filtered': 1
            },
            top_keywords=[{'keyword': 'react', 'count': 5}, {'keyword': 'django', 'count': 4}],
            top_requests=[{'request': 'make a part 2 with auth', 'count': 3}],
            recommendations='### Content Recommendations:\n1. Provide GitHub repo.\n2. Add JWT auth video.',
            suggested_titles=['React + Django NLP in 2026', 'Fullstack AI Dashboard Tutorial']
        )
        Comment.objects.create(
            video=self.video,
            comment_id="c_pdf_1",
            author="Student",
            text="This is an awesome project walkthrough!",
            sentiment_label="positive",
            sentiment_score=0.75,
            is_spam=False,
            like_count=5
        )

    def test_export_pdf_endpoint(self):
        url = reverse('report-export', kwargs={'job_id': self.job.id})
        response = self.client.get(f"{url}?format=pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename="youtube_sentiment_report_pdf_vid_99.pdf"', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF'))
        self.assertGreater(len(response.content), 1000)

    def test_pdf_generator_service_direct(self):
        from analyzer.services.pdf_generator import generate_report_pdf
        pdf_bytes = generate_report_pdf(self.report)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))
        self.assertGreater(len(pdf_bytes), 1000)


class AuthenticationAndUserTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_registration(self):
        url = reverse('auth-register')
        payload = {
            'username': 'demouser',
            'email': 'demouser@example.com',
            'password': 'StrongPassword123!'
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertEqual(response.data['user']['username'], 'demouser')

    def test_user_token_login(self):
        # Register first
        User.objects.create_user(username='loginuser', email='login@example.com', password='Password123!')

        url = reverse('token-obtain-pair')
        response = self.client.post(url, {'username': 'loginuser', 'password': 'Password123!'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        # Access Me endpoint with token
        access_token = response.data['access']
        me_url = reverse('auth-me')
        me_response = self.client.get(me_url, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.data['username'], 'loginuser')

    def test_me_endpoint_unauthorized_without_token(self):
        me_url = reverse('auth-me')
        response = self.client.get(me_url)
        self.assertEqual(response.status_code, 401)


class V2AdvancedFeaturesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='creator_alice',
            email='alice@example.com',
            password='Password123!'
        )
        login_res = self.client.post(
            reverse('token-obtain-pair'),
            {'username': 'creator_alice', 'password': 'Password123!'},
            format='json'
        )
        self.token = login_res.data['access']

        # Create two test videos
        self.v1 = Video.objects.create(
            youtube_video_id="vid_cmp_1",
            title="Python Tutorial 2026",
            channel="Code Lab"
        )
        self.v2 = Video.objects.create(
            youtube_video_id="vid_cmp_2",
            title="Django Masterclass",
            channel="Web Dev Pro"
        )

        # Create jobs and reports
        self.job1 = AnalysisJob.objects.create(
            video=self.v1,
            user=self.user,
            status=AnalysisJob.STATUS_DONE
        )
        self.report1 = Report.objects.create(
            job=self.job1,
            sentiment_summary={"positive": 80, "neutral": 15, "negative": 5, "total": 100, "positive_percentage": 80.0, "average_compound": 0.55, "spam_filtered": 2},
            weighted_compound=0.62,
            aspect_sentiment={"content": {"count": 10, "average_score": 0.45}},
            emotion_breakdown={"joy": {"count": 40, "percentage": 40.0}},
            sentiment_timeline=[{"date": "2026-10-25", "avg_sentiment": 0.55, "volume": 10}],
            top_keywords=[{"keyword": "python", "count": 12}],
            top_requests=["more django projects"]
        )

        self.job2 = AnalysisJob.objects.create(
            video=self.v2,
            user=None,
            status=AnalysisJob.STATUS_DONE
        )
        self.report2 = Report.objects.create(
            job=self.job2,
            sentiment_summary={"positive": 60, "neutral": 20, "negative": 20, "total": 80, "positive_percentage": 60.0, "average_compound": 0.25, "spam_filtered": 6},
            weighted_compound=0.31,
            aspect_sentiment={"content": {"count": 8, "average_score": 0.20}},
            emotion_breakdown={"joy": {"count": 20, "percentage": 25.0}},
            sentiment_timeline=[{"date": "2026-10-25", "avg_sentiment": 0.25, "volume": 8}],
            top_keywords=[{"keyword": "django", "count": 10}],
            top_requests=["make part 2"]
        )

    def test_my_analyses_authenticated(self):
        url = reverse('analyses-my')
        res = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], self.job1.id)

    def test_my_analyses_unauthenticated(self):
        url = reverse('analyses-my')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 401)

    def test_compare_videos_endpoint(self):
        url = reverse('analyses-compare')
        res = self.client.get(f"{url}?job1={self.job1.id}&job2={self.job2.id}")
        self.assertEqual(res.status_code, 200)
        self.assertIn("video1", res.data)
        self.assertIn("video2", res.data)
        self.assertIn("comparison_insights", res.data)
        self.assertEqual(res.data["comparison_insights"]["higher_positivity_video_id"], "vid_cmp_1")

    def test_compare_videos_missing_param_fails(self):
        url = reverse('analyses-compare')
        res = self.client.get(f"{url}?job1={self.job1.id}")
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.data)

    def test_draft_reply_endpoint(self):
        comment = Comment.objects.create(
            video=self.v1,
            comment_id="c_q_1",
            author="CuriousStudent",
            text="Could you please explain how Django signals work?",
            needs_response=True
        )
        url = reverse('comment-draft-reply', kwargs={'comment_id': comment.id})
        res = self.client.post(url)
        self.assertEqual(res.status_code, 200)
        self.assertIn("draft_reply", res.data)
        self.assertTrue(len(res.data["draft_reply"]) > 10)
        comment.refresh_from_db()
        self.assertEqual(comment.draft_reply, res.data["draft_reply"])

    def test_hinglish_slang_lexicon(self):
        from analyzer.nlp.sentiment import analyze_sentiment
        # 'zabardast' and 'shandar' should yield positive sentiment
        res_pos = analyze_sentiment("Sir yeh lecture bohot zabardast aur shandar tha!")
        self.assertEqual(res_pos["label"], "positive")
        self.assertGreater(res_pos["compound"], 0.3)

        # 'bakwas' and 'bekar' should yield negative sentiment
        res_neg = analyze_sentiment("bilkul bakwas aur bekar video time waste scam")
        self.assertEqual(res_neg["label"], "negative")
        self.assertLess(res_neg["compound"], -0.3)


