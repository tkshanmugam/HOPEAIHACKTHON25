from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from apps.aistudycompanion.views import (
    chatbot_view, chatbot_api,
    register_view, conversation_history, conversation_detail, delete_conversation, delete_all_conversations,
    logout_view, login_view,
    subject_help_api, learning_materials_view, upload_learning_material, delete_learning_material
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', chatbot_view, name='chatbot'),  # Make chatbot the default page
    path('chatbot/', chatbot_view, name='chatbot'),
    path('chatbot/api/', chatbot_api, name='chatbot_api'),
    path('subject-help/api/', subject_help_api, name='subject_help_api'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('conversations/', conversation_history, name='conversation_history'),
    path('conversations/<int:conversation_id>/', conversation_detail, name='conversation_detail'),
    path('conversations/<int:conversation_id>/delete/', delete_conversation, name='delete_conversation'),
    path('conversations/delete-all/', delete_all_conversations, name='delete_all_conversations'),
    path('learning-materials/', learning_materials_view, name='learning_materials'),
    path('upload-material/', upload_learning_material, name='upload_learning_material'),
    path('delete-material/<int:material_id>/', delete_learning_material, name='delete_learning_material'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
