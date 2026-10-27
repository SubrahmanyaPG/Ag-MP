from io import BytesIO
from typing import Any, Dict
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print total page numbers (e.g. Page 1 of 3).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748B"))
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(40, 40, 572, 40)
        self.drawString(40, 26, "PulseYT NLP — Audience Sentiment & Feedback Analysis Platform")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(572, 26, page_text)
        self.restoreState()


def generate_report_pdf(report, comments=None) -> bytes:
    """
    Generates a beautifully formatted, executive-style PDF analysis report.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=55
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A")
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B")
    )
    section_heading = ParagraphStyle(
        'SectionHead',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=14,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#334155")
    )
    bold_body = ParagraphStyle(
        'BoldBody',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    story = []

    # 1. Header
    story.append(Paragraph("YouTube Audience Sentiment & Feedback Report", title_style))
    story.append(Paragraph("Natural Language Processing & Content Intelligence Analysis", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#E2E8F0"), spaceAfter=12))

    # 2. Video Overview Table
    video = report.job.video
    overview_data = [
        [Paragraph("Video Title", bold_body), Paragraph(video.title or "N/A", body_style)],
        [Paragraph("Channel", bold_body), Paragraph(video.channel or "N/A", body_style)],
        [Paragraph("Video ID", bold_body), Paragraph(video.youtube_video_id, body_style)],
        [Paragraph("Analysis Date", bold_body), Paragraph(str(report.job.completed_at)[:19] if report.job.completed_at else "Recent", body_style)],
    ]
    overview_table = Table(overview_data, colWidths=[120, 412])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(overview_table)
    story.append(Spacer(1, 14))

    # 3. Sentiment Summary
    story.append(Paragraph("1. Audience Sentiment Breakdown", section_heading))
    ss = report.sentiment_summary or {}
    total_comments = ss.get('total', 0)
    pos_pct = ss.get('positive_percentage', 0)
    neu_pct = ss.get('neutral_percentage', 0)
    neg_pct = ss.get('negative_percentage', 0)
    avg_compound = ss.get('average_compound', 0)
    spam_filtered = ss.get('spam_filtered', 0)

    sentiment_table_data = [
        [
            Paragraph("Metric", bold_body),
            Paragraph("Total Comments", bold_body),
            Paragraph("Positive", bold_body),
            Paragraph("Neutral", bold_body),
            Paragraph("Negative", bold_body),
            Paragraph("Spam Filtered", bold_body),
            Paragraph("Polarity Index", bold_body)
        ],
        [
            Paragraph("Value", body_style),
            Paragraph(str(total_comments), body_style),
            Paragraph(f"{pos_pct}%", body_style),
            Paragraph(f"{neu_pct}%", body_style),
            Paragraph(f"{neg_pct}%", body_style),
            Paragraph(str(spam_filtered), body_style),
            Paragraph(f"{avg_compound:+.2f} (Weighted: {getattr(report, 'weighted_compound', 0.0):+.2f})", body_style)
        ]
    ]
    sent_table = Table(sentiment_table_data, colWidths=[70, 80, 75, 75, 75, 80, 77])
    sent_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (2, 1), (2, 1), colors.HexColor("#ECFDF5")),
        ('BACKGROUND', (4, 1), (4, 1), colors.HexColor("#FEF2F2")),
    ]))
    story.append(sent_table)
    story.append(Spacer(1, 14))

    # 4. Top Keywords & Topic Clusters
    story.append(Paragraph("2. Top Discussion Topics & Extracted Keywords", section_heading))
    top_kw = [k.get('keyword', '') for k in (report.top_keywords or [])[:8]]
    kw_str = ", ".join(top_kw) if top_kw else "None extracted"
    story.append(Paragraph(f"<b>Key Terms:</b> {kw_str}", body_style))
    story.append(Spacer(1, 6))

    top_reqs = report.top_requests or []
    if top_reqs:
        story.append(Paragraph("<b>Audience Feature & Tutorial Requests:</b>", bold_body))
        for r in top_reqs[:4]:
            req_text = r.get('request', '')
            count = r.get('count', 1)
            story.append(Paragraph(f"&bull; <i>\"{req_text}\"</i> (Requested by {count} viewers)", body_style))
        story.append(Spacer(1, 10))

    # 5. AI Recommendations & Titles
    story.append(Paragraph("3. AI Content Strategy & Title Recommendations (Groq LLaMA)", section_heading))
    recs_text = report.recommendations or "No AI recommendations generated."
    story.append(Paragraph(recs_text.replace('\n', '<br/>'), body_style))
    story.append(Spacer(1, 10))

    titles = report.suggested_titles or []
    if titles:
        story.append(Paragraph("<b>High-CTR Title Suggestions for Upcoming Videos:</b>", bold_body))
        for idx, title in enumerate(titles[:5], 1):
            story.append(Paragraph(f"<b>{idx}.</b> {title}", body_style))
        story.append(Spacer(1, 14))

    # 6. Sample Comments Table
    story.append(Paragraph("4. Sample Audience Comments (Annotated)", section_heading))
    comments_qs = comments or report.job.video.comments.all()[:12]
    comment_rows = [
        [Paragraph("Author", bold_body), Paragraph("Comment", bold_body), Paragraph("Sentiment", bold_body), Paragraph("Likes", bold_body)]
    ]
    for c in comments_qs:
        author_p = Paragraph(c.author[:20] if c.author else "Anonymous", body_style)
        text_p = Paragraph(c.text[:120] + ("..." if len(c.text) > 120 else ""), body_style)
        sent_badge = f"{c.sentiment_label.capitalize() if c.sentiment_label else 'N/A'} ({c.sentiment_score:+.2f})" if c.sentiment_score is not None else "N/A"
        sent_p = Paragraph(sent_badge, body_style)
        like_p = Paragraph(str(c.like_count), body_style)
        comment_rows.append([author_p, text_p, sent_p, like_p])

    comments_table = Table(comment_rows, colWidths=[90, 312, 90, 40])
    comments_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(comments_table)

    # Build Document with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
