from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import FileExtensionValidator, MaxValueValidator
import os

# Create your models here.

class UserProfile(models.Model):
    """Extended user profile for study companion features."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    study_level = models.CharField(max_length=50, blank=True, help_text="e.g., High School, College, University")
    preferred_subjects = models.TextField(blank=True, help_text="Comma-separated list of subjects")
    study_goals = models.TextField(blank=True, help_text="User's study goals and objectives")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Conversation(models.Model):
    """Represents a chat conversation session."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=200, blank=True)
    subject = models.CharField(max_length=100, blank=True, help_text="Main subject of conversation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.title or 'Untitled'} ({self.created_at.strftime('%Y-%m-%d')})"

    def get_message_count(self):
        return self.messages.count()

class ChatMessage(models.Model):
    """Individual messages in a conversation."""
    MESSAGE_TYPES = [
        ('user', 'User Message'),
        ('bot', 'Bot Response'),
        ('system', 'System Message'),
    ]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='user')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional data like confidence scores, etc.")

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.conversation.user.username} - {self.message_type} ({self.timestamp.strftime('%H:%M')})"

class StudySession(models.Model):
    """Tracks study sessions and progress."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_sessions')
    subject = models.CharField(max_length=100)
    topic = models.CharField(max_length=200, blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    questions_asked = models.IntegerField(default=0)
    concepts_learned = models.TextField(blank=True)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.user.username} - {self.subject} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"

    def calculate_duration(self):
        if self.end_time:
            duration = self.end_time - self.start_time
            return int(duration.total_seconds() / 60)
        return None

class CustomLearningMaterial(models.Model):
    """User-uploaded learning materials (PDFs, DOCs)."""
    DOCUMENT_TYPES = [
        ('pdf', 'PDF Document'),
        ('doc', 'Word Document'),
        ('docx', 'Word Document (DOCX)'),
        ('txt', 'Text File'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_materials')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    subject = models.CharField(max_length=100, blank=True)
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPES)
    file = models.FileField(
        upload_to='learning_materials/',
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt']),
        ]
    )
    file_size = models.IntegerField(help_text="File size in bytes")
    pages = models.IntegerField(null=True, blank=True, help_text="Number of pages (for PDFs)")
    is_processed = models.BooleanField(default=False, help_text="Whether the document has been processed for RAG")
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.document_type.upper()})"

    def get_file_size_mb(self):
        """Return file size in MB."""
        return round(self.file_size / (1024 * 1024), 2)

    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

class DocumentChunk(models.Model):
    """Chunks of processed documents for RAG functionality."""
    material = models.ForeignKey(CustomLearningMaterial, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField(help_text="Order of chunk in document")
    content = models.TextField(help_text="Text content of the chunk")
    page_number = models.IntegerField(null=True, blank=True, help_text="Page number (for PDFs)")
    embedding = models.JSONField(null=True, blank=True, help_text="Vector embedding of the chunk")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata like section headers, etc.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['material', 'chunk_index']
        unique_together = ['material', 'chunk_index']

    def __str__(self):
        return f"{self.material.title} - Chunk {self.chunk_index}"

class RAGQuery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rag_queries')
    material = models.ForeignKey(CustomLearningMaterial, on_delete=models.CASCADE, related_name='queries')
    query = models.TextField(help_text="User's question")
    response = models.TextField(help_text="AI response")
    relevant_chunks = models.ManyToManyField(DocumentChunk, blank=True, help_text="Chunks used to generate response")
    confidence_score = models.FloatField(
        null=True, 
        blank=True,
        validators=[MaxValueValidator(1.0)],
        help_text="Confidence score of the response (0-1)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "RAG Queries"

    def __str__(self):
        return f"{self.user.username} - {self.material.title} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
