from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot_view, name='chatbot'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('conversation-history/', views.conversation_history, name='conversation_history'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('delete-conversation/<int:conversation_id>/', views.delete_conversation, name='delete_conversation'),
    path('delete-all-conversations/', views.delete_all_conversations, name='delete_all_conversations'),
    path('learning-materials/', views.learning_materials_view, name='learning_materials'),
    path('upload-material/', views.upload_learning_material, name='upload_learning_material'),
    path('delete-material/<int:material_id>/', views.delete_learning_material, name='delete_learning_material'),
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
    path('api/subject-help/', views.subject_help_api, name='subject_help_api'),
] 