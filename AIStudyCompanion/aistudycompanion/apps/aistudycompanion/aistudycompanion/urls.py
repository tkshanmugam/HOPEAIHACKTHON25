from django.contrib import admin
from django.urls import path
from apps.aistudycompanion.views import (
    chatbot_view, chatbot_api,
    register_view, conversation_history, conversation_detail,
    logout_view, login_view,
    subject_help_api
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chatbot/', chatbot_view, name='chatbot'),
    path('chatbot/api/', chatbot_api, name='chatbot_api'),
    path('subject-help/api/', subject_help_api, name='subject_help_api'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('conversations/', conversation_history, name='conversation_history'),
    path('conversations/<int:conversation_id>/', conversation_detail, name='conversation_detail'),
] 