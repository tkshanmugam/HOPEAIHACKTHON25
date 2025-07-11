from django.contrib import admin
from .models import UserProfile, Conversation, ChatMessage, StudySession, CustomLearningMaterial, DocumentChunk, RAGQuery

# Register your models here.

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'study_level', 'preferred_subjects', 'created_at']
    list_filter = ['study_level', 'created_at']
    search_fields = ['user__username', 'user__email', 'preferred_subjects']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'subject', 'created_at', 'updated_at', 'is_active', 'message_count']
    list_filter = ['subject', 'is_active', 'created_at', 'updated_at']
    search_fields = ['user__username', 'title', 'subject']
    readonly_fields = ['created_at', 'updated_at']
    
    def message_count(self, obj):
        return obj.get_message_count()
    message_count.short_description = 'Messages'

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'message_type', 'content_preview', 'timestamp']
    list_filter = ['message_type', 'timestamp']
    search_fields = ['conversation__user__username', 'content']
    readonly_fields = ['timestamp']
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'

@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'subject', 'topic', 'start_time', 'end_time', 'duration_minutes', 'questions_asked']
    list_filter = ['subject', 'start_time', 'end_time']
    search_fields = ['user__username', 'subject', 'topic']
    readonly_fields = ['start_time', 'duration_minutes']

@admin.register(CustomLearningMaterial)
class CustomLearningMaterialAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'document_type', 'file_size_mb', 'processing_status', 'created_at']
    list_filter = ['document_type', 'processing_status', 'created_at', 'subject']
    search_fields = ['user__username', 'title', 'description', 'subject']
    readonly_fields = ['file_size', 'created_at', 'updated_at']
    
    def file_size_mb(self, obj):
        return f"{obj.get_file_size_mb()} MB"
    file_size_mb.short_description = 'File Size'

@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ['material', 'chunk_index', 'page_number', 'content_preview', 'created_at']
    list_filter = ['material__document_type', 'created_at']
    search_fields = ['material__title', 'content']
    readonly_fields = ['created_at']
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'

@admin.register(RAGQuery)
class RAGQueryAdmin(admin.ModelAdmin):
    list_display = ['user', 'material', 'query_preview', 'confidence_score', 'created_at']
    list_filter = ['material__document_type', 'created_at']
    search_fields = ['user__username', 'material__title', 'query', 'response']
    readonly_fields = ['created_at']
    
    def query_preview(self, obj):
        return obj.query[:100] + '...' if len(obj.query) > 100 else obj.query
    query_preview.short_description = 'Query'
