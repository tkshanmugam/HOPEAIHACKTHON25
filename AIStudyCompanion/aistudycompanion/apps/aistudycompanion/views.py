from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import logging
import re
import os
from .models import UserProfile, Conversation, ChatMessage, StudySession, CustomLearningMaterial, DocumentChunk, RAGQuery
from .agents import StudyCompanionAgents
from .rag_service import RAGService
import openai

logger = logging.getLogger(__name__)

def chatbot_view(request):
    """Renders the chatbot interface with subject selection and welcome message."""
    try:
        # Define available subjects (can be extended or made dynamic)
        available_subjects = [
            {'key': 'science', 'label': 'Science'},
            {'key': 'math', 'label': 'Math'},
            {'key': 'english', 'label': 'English'},
            {'key': 'history', 'label': 'History'},
            {'key': 'computer_science', 'label': 'Computer Science'},
            {'key': 'geography', 'label': 'Geography'},
            {'key': 'economics', 'label': 'Economics'},
            {'key': 'psychology', 'label': 'Psychology'},
            {'key': 'philosophy', 'label': 'Philosophy'},
            {'key': 'arts', 'label': 'Arts'},
        ]
        selected_subject = request.GET.get('subject')
        welcome_message = None
        if selected_subject:
            # Generate welcome message from agent
            agents = StudyCompanionAgents()
            agent_label = f"[{selected_subject.replace('_', ' ').title()} Agent]: "
            # You can customize welcome messages per subject if desired
            welcome_text = f"Welcome to {selected_subject.replace('_', ' ').title()}! How can I help you today?"
            welcome_message = agent_label + welcome_text
        
        if request.user.is_authenticated:
            recent_conversations = Conversation.objects.filter(
                user=request.user, 
                is_active=True
            ).order_by('-updated_at')[:5]
            current_session, created = StudySession.objects.get_or_create(
                user=request.user,
                end_time__isnull=True,
                defaults={'subject': 'General Study'}
            )
            conversation_id = request.GET.get('conversation')
            current_conversation = None
            if conversation_id:
                try:
                    current_conversation = Conversation.objects.get(
                        id=conversation_id, 
                        user=request.user
                    )
                except Conversation.DoesNotExist:
                    messages.error(request, 'Conversation not found.')
            learning_materials = CustomLearningMaterial.objects.filter(
                user=request.user
            ).order_by('-created_at')[:10]
            context = {
                'recent_conversations': recent_conversations,
                'current_session': current_session,
                'current_conversation': current_conversation,
                'learning_materials': learning_materials,
                'available_subjects': available_subjects,
                'selected_subject': selected_subject,
                'welcome_message': welcome_message,
            }
        else:
            context = {
                'available_subjects': available_subjects,
                'selected_subject': selected_subject,
                'welcome_message': welcome_message,
            }
        return render(request, 'aistudycompanion/chatbot.html', context)
    except Exception as e:
        logger.error(f"Error in chatbot_view: {e}")
        return render(request, 'aistudycompanion/chatbot.html', {
            'recent_conversations': [],
            'current_session': None,
            'current_conversation': None,
            'learning_materials': [],
            'available_subjects': [],
            'selected_subject': None,
            'welcome_message': None,
            'error_message': 'There was an error loading the chatbot. Please try refreshing the page.'
        })

def register_view(request):
    """User registration view."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('chatbot')
    else:
        form = UserCreationForm()
    
    return render(request, 'aistudycompanion/register.html', {'form': form})

def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect('chatbot')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('chatbot')
    else:
        form = AuthenticationForm()
    
    return render(request, 'aistudycompanion/login.html', {'form': form})

def logout_view(request):
    """User logout view."""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('chatbot')

@login_required
def conversation_history(request):
    """Display conversation history with pagination."""
    try:
        conversations_list = Conversation.objects.filter(
            user=request.user
        ).order_by('-updated_at').prefetch_related('messages')
        
        paginator = Paginator(conversations_list, 10)
        page = request.GET.get('page')
        
        try:
            conversations = paginator.page(page)
        except PageNotAnInteger:
            conversations = paginator.page(1)
        except EmptyPage:
            conversations = paginator.page(paginator.num_pages)
        
        # Fetch learning materials for sidebar
        learning_materials = CustomLearningMaterial.objects.filter(user=request.user).order_by('-created_at')
        
        return render(request, 'aistudycompanion/conversation_history.html', {
            'conversations': conversations,
            'paginator': paginator,
            'learning_materials': learning_materials,
        })
    except Exception as e:
        logger.error(f"Error in conversation_history view: {e}")
        return render(request, 'aistudycompanion/conversation_history.html', {
            'conversations': [],
            'error_message': 'Sorry, there was a problem loading your conversation history.'
        })

@login_required
def conversation_detail(request, conversation_id):
    """Display detailed view of a specific conversation."""
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    messages_list = conversation.messages.all().order_by('timestamp')
    
    return render(request, 'aistudycompanion/conversation_detail.html', {
        'conversation': conversation,
        'messages': messages_list
    })

@login_required
@csrf_exempt
def delete_conversation(request, conversation_id):
    """Delete a conversation and all its messages."""
    if request.method == 'POST':
        try:
            conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
            
            # Delete all messages in the conversation first
            conversation.messages.all().delete()
            
            # Delete the conversation
            conversation.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Conversation deleted successfully'
            })
            
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Error deleting conversation'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

@login_required
@csrf_exempt
def delete_all_conversations(request):
    """Delete all conversations and messages for the current user."""
    if request.method == 'POST':
        try:
            conversations = Conversation.objects.filter(user=request.user)
            conversation_count = conversations.count()
            
            if conversation_count == 0:
                return JsonResponse({
                    'success': True,
                    'message': 'No conversations to delete',
                    'deleted_count': 0
                })
            
            # Delete all messages first (cascade delete)
            total_messages = 0
            for conversation in conversations:
                message_count = conversation.messages.count()
                total_messages += message_count
                conversation.messages.all().delete()
            
            # Delete all conversations
            conversations.delete()
            
            logger.info(f"Deleted {conversation_count} conversations and {total_messages} messages for user {request.user.username}")
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully deleted {conversation_count} conversations and {total_messages} messages',
                'deleted_count': conversation_count,
                'deleted_messages': total_messages
            })
            
        except Exception as e:
            logger.error(f"Error deleting all conversations: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Error deleting conversations'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

@login_required
def learning_materials_view(request):
    """Display user's learning materials."""
    try:
        materials_list = CustomLearningMaterial.objects.filter(
            user=request.user
        ).order_by('-created_at')
        
        paginator = Paginator(materials_list, 12)
        page = request.GET.get('page')
        
        try:
            materials = paginator.page(page)
        except PageNotAnInteger:
            materials = paginator.page(1)
        except EmptyPage:
            materials = paginator.page(paginator.num_pages)
        
        return render(request, 'aistudycompanion/learning_materials.html', {
            'materials': materials,
            'paginator': paginator
        })
    except Exception as e:
        logger.error(f"Error in learning_materials_view: {e}")
        return render(request, 'aistudycompanion/learning_materials.html', {
            'materials': [],
            'error_message': 'Sorry, there was a problem loading your learning materials.'
        })

@login_required
@csrf_exempt
def upload_learning_material(request):
    """Handle file upload for learning materials."""
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'file' not in request.FILES:
                return JsonResponse({
                    'success': False,
                    'message': 'No file uploaded'
                }, status=400)
            
            uploaded_file = request.FILES['file']
            
            # Validate file size (15MB limit)
            max_size = 15 * 1024 * 1024  # 15MB
            if uploaded_file.size > max_size:
                return JsonResponse({
                    'success': False,
                    'message': 'File size exceeds 15MB limit'
                }, status=400)
            
            # Get file extension
            file_name = uploaded_file.name
            file_extension = file_name.split('.')[-1].lower()
            
            # Validate file type
            allowed_extensions = ['pdf', 'doc', 'docx', 'txt']
            if file_extension not in allowed_extensions:
                return JsonResponse({
                    'success': False,
                    'message': f'File type not supported. Allowed types: {", ".join(allowed_extensions)}'
                }, status=400)
            
            # Get form data
            title = request.POST.get('title', file_name)
            description = request.POST.get('description', '')
            subject = request.POST.get('subject', '')
            
            # Create learning material
            material = CustomLearningMaterial.objects.create(
                user=request.user,
                title=title,
                description=description,
                subject=subject,
                document_type=file_extension,
                file=uploaded_file,
                file_size=uploaded_file.size
            )
            
            # Process document for RAG (async)
            try:
                rag_service = RAGService()
                # Process in background (you might want to use Celery for this)
                success = rag_service.process_document(material)
                if not success:
                    logger.warning(f"Failed to process document: {material.title}")
            except Exception as e:
                logger.error(f"Error processing document: {e}")
            
            return JsonResponse({
                'success': True,
                'message': 'File uploaded successfully',
                'material_id': material.id,
                'material_title': material.title
            })
            
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Error uploading file'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

@login_required
@csrf_exempt
def delete_learning_material(request, material_id):
    """Delete a learning material and all its chunks."""
    if request.method == 'POST':
        try:
            material = get_object_or_404(CustomLearningMaterial, id=material_id, user=request.user)
            
            # Delete file from storage
            if material.file:
                if default_storage.exists(material.file.name):
                    default_storage.delete(material.file.name)
            
            # Delete all chunks
            material.chunks.all().delete()
            
            # Delete the material
            material.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Learning material deleted successfully'
            })
            
        except Exception as e:
            logger.error(f"Error deleting learning material: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Error deleting learning material'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

@csrf_exempt
def chatbot_api(request):
    """API endpoint for chatbot responses."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            conversation_id = data.get('conversation_id')
            material_id = data.get('material_id')  # For RAG queries
            # subject is now optional and not required
            subject = data.get('subject', '').strip() or None
            
            if not user_message:
                return JsonResponse({'response': 'Please enter a message.'})
            
            # Handle authenticated and anonymous users
            if request.user.is_authenticated:
                response_data = handle_authenticated_chat(request.user, user_message, conversation_id, material_id, subject)
            else:
                response_data = handle_anonymous_chat(user_message)
            
            return JsonResponse(response_data)
            
        except json.JSONDecodeError:
            return JsonResponse({'response': 'Invalid request format.'}, status=400)
    
    return JsonResponse({'response': 'Only POST requests are allowed.'}, status=405)

@csrf_exempt
def subject_help_api(request):
    """API endpoint for subject-specific help."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            subject = data.get('subject', '').strip()
            question = data.get('question', '').strip()
            
            if not subject or not question:
                return JsonResponse({'error': 'Subject and question are required.'}, status=400)
            
            # Initialize agents
            agents = StudyCompanionAgents()
            
            # Get subject-specific help
            response = agents.get_subject_help(subject, question)
            
            return JsonResponse({
                'response': response,
                'subject': subject,
                'status': 'success'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid request format.'}, status=400)
    
    return JsonResponse({'error': 'Only POST requests are allowed.'}, status=405)

def handle_authenticated_chat(user, user_message, conversation_id=None, material_id=None, subject=None):
    """Handle chat for authenticated users by passing directly to the agent."""
    # Check if this is a RAG query (material_id provided)
    if material_id:
        try:
            material = CustomLearningMaterial.objects.get(id=material_id, user=user)
            if material.is_processed:
                rag_service = RAGService()
                response, confidence, relevant_chunks = rag_service.generate_rag_response(user, user_message, material_id)
                # Save RAG query
                rag_service.save_rag_query(user, material, user_message, response, relevant_chunks, confidence)
                return {
                    'response': f"[RAG Response - {material.title}]: {response}",
                    'status': 'success',
                    'confidence': confidence,
                    'material_title': material.title
                }
            else:
                return {
                    'response': f"Your document '{material.title}' is still being processed. Please wait a moment and try again.",
                    'status': 'processing'
                }
        except CustomLearningMaterial.DoesNotExist:
            return {
                'response': "The specified learning material was not found.",
                'status': 'error'
            }
    # Regular chat handling
    if conversation_id:
        conversation = get_object_or_404(Conversation, id=conversation_id, user=user)
    else:
        # Create new conversation with smart title
        title = generate_conversation_title(user_message)
        conversation = Conversation.objects.create(
            user=user,
            title=title,
            subject=subject or detect_subject(user_message)
        )
    # Always use LLM subject detection for routing
    subject_for_agent = subject if subject and subject != 'general' else detect_subject(user_message)
    if subject_for_agent and subject_for_agent != 'general':
        conversation.subject = subject_for_agent
        conversation.save()
    # Save user message
    ChatMessage.objects.create(
        conversation=conversation,
        message_type='user',
        content=user_message
    )
    # Initialize agents only once per request
    agents = StudyCompanionAgents()
    # Get bot response, passing the detected subject and agents
    bot_response = get_enhanced_chatbot_response(user, user_message, conversation, subject_for_agent, agents)
    # Save bot response
    ChatMessage.objects.create(
        conversation=conversation,
        message_type='bot',
        content=bot_response
    )
    # Update conversation
    conversation.updated_at = timezone.now()
    conversation.save()
    # Update study session
    update_study_session(user, user_message)
    return {
        'response': bot_response,
        'status': 'success',
        'conversation_id': conversation.id,
        'conversation_title': conversation.title
    }

def handle_anonymous_chat(user_message):
    """Handle chat for anonymous users by passing directly to the agent."""
    agents = StudyCompanionAgents()
    bot_response = agents.get_subject_help('general', user_message)
    return {
        'response': bot_response,
        'status': 'success',
        'conversation_id': None
    }

def get_enhanced_chatbot_response(user, user_message, conversation, subject_for_agent=None, agents=None):
    detected_subject = None
    # If a subject is provided (from conversation) and not 'general', use it
    if subject_for_agent and subject_for_agent != 'general':
        detected_subject = subject_for_agent
    else:
        # Otherwise, use the detected subject from the message
        detected_subject = detect_subject(user_message)

    if detected_subject and detected_subject != 'general':
        try:
            if agents is None:
                agents = StudyCompanionAgents()
            agent_response = agents.get_subject_help(detected_subject, user_message)
            # Always prepend agent name for clarity
            agent_label = f"[{detected_subject.title().replace('_', ' ')} Agent]: "
            if not agent_response.strip().lower().startswith(agent_label.lower()):
                return agent_label + agent_response
            return agent_response
        except Exception as e:
            logger.error(f"Error with {detected_subject} agent: {e}")
            # Fallback to science agent for general questions
            try:
                agent_response = agents.get_subject_help('science', user_message)
                agent_label = "[Science Agent]: "
                if not agent_response.strip().lower().startswith(agent_label.lower()):
                    return agent_label + agent_response
                return agent_response
            except Exception as e2:
                logger.error(f"Error with science fallback: {e2}")
                return "I'm sorry, but I cannot provide help at this time. Please try again later."

    # For general questions, try science agent first, then math, then english
    fallback_subjects = ['science', 'math', 'english']
    for subject in fallback_subjects:
        try:
            if agents is None:
                agents = StudyCompanionAgents()
            agent_response = agents.get_subject_help(subject, user_message)
            agent_label = f"[{subject.title()} Agent]: "
            if not agent_response.strip().lower().startswith(agent_label.lower()):
                return agent_label + agent_response
            return agent_response
        except Exception as e:
            logger.error(f"Error with {subject} fallback: {e}")
            continue

    return "I'm sorry, but I cannot provide help at this time. Please try again later."

def generate_conversation_title(user_message):
    """Generate a title for a new conversation based on the first message."""
    words = user_message.split()[:5]
    return " ".join(words).capitalize() + "..."

def llm_detect_subject(user_message):
    """Advanced LLM-based subject detection with confidence scoring and multi-subject support."""
    client = openai.OpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', None))
    # Comprehensive subject classification prompt
    prompt = f"""You are an expert educational subject classifier with high accuracy. Analyze the following question and provide a detailed classification.
                Available subjects and their scope:
                - math: Mathematics, calculations, equations, formulas, numbers, algebra, geometry, trigonometry, calculus, statistics, arithmetic, probability, logic, patterns, sequences
                - science: Physics, chemistry, biology, natural phenomena, experiments, technology, engineering, transport, vehicles, machines, nature, environment, space, astronomy, weather, climate, human body, animals, plants, materials, energy, forces, motion, atoms, molecules, cells, ecosystems
                - english: Language, grammar, literature, writing, reading, vocabulary, communication, stories, poetry, essays, linguistics, rhetoric, composition, literary analysis, language arts
                - history: Past events, historical figures, civilizations, wars, politics, social studies, cultural studies, ancient times, medieval period, modern era, revolutions, discoveries, historical analysis
                - computer_science: Programming, coding, software, computers, technology, algorithms, data structures, databases, networks, artificial intelligence, machine learning, web development, cybersecurity, digital systems
                - geography: Earth, countries, cities, maps, landforms, climate zones, population, natural resources, environmental issues, physical geography, human geography, cartography
                - economics: Money, finance, business, trade, markets, supply and demand, inflation, GDP, economic systems, banking, investment, economic theory, microeconomics, macroeconomics
                - psychology: Human behavior, mental processes, emotions, cognition, learning, memory, personality, social psychology, developmental psychology, mental health, brain function
                - philosophy: Ethics, logic, metaphysics, epistemology, moral philosophy, critical thinking, reasoning, philosophical theories, wisdom, knowledge, existence, values
                - arts: Visual arts, music, theater, dance, creative expression, artistic techniques, art history, cultural arts, design, aesthetics, creativity
                Question: "{user_message}"
                Instructions:
                1. Analyze the question carefully for main topic and context
                2. Identify the PRIMARY subject (most relevant)
                3. If multiple subjects are involved, identify the SECONDARY subject
                4. Provide a confidence score (1-10, where 10 is highest confidence)
                5. Consider sub-topics within each subject area
                6. For interdisciplinary questions, choose the most dominant subject
                Respond in this exact format:
                PRIMARY: [subject_name]
                SECONDARY: [subject_name or none]
                CONFIDENCE: [1-10]
                REASONING: [brief explanation]
                Examples:
                - "What is 2+2?" → PRIMARY: math, SECONDARY: none, CONFIDENCE: 10
                - "How do cars work?" → PRIMARY: science, SECONDARY: none, CONFIDENCE: 9
                - "What is the history of mathematics?" → PRIMARY: history, SECONDARY: math, CONFIDENCE: 8
                - "Explain photosynthesis" → PRIMARY: science, SECONDARY: none, CONFIDENCE: 10
                Classification:"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.1
        )
        
        response_text = response.choices[0].message.content.strip()
        primary_subject = 'general'
        confidence = 5
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('PRIMARY:'):
                primary_subject = line.replace('PRIMARY:', '').strip().lower()
            elif line.startswith('CONFIDENCE:'):
                try:
                    confidence = int(line.replace('CONFIDENCE:', '').strip())
                except ValueError:
                    confidence = 5
        
        # Validate the primary subject
        valid_subjects = ['math', 'science', 'english', 'history', 'computer_science', 
                         'geography', 'economics', 'psychology', 'philosophy', 'arts', 'general']
        if primary_subject not in valid_subjects:
            primary_subject = 'general'
        
        logger.debug(f"LLM subject detection: {primary_subject} (confidence: {confidence})")
        return primary_subject
        
    except Exception as e:
        logger.error(f"LLM Subject Detection Error: {e}")
        # Fallback to general on error
        return "general"

def detect_subject(user_message):
    detected = llm_detect_subject(user_message)
    math_patterns = [
        r'\b\d+\s*[\+\-\*/]\s*\d+\b',  # e.g., 2 + 90, 5*3, 10-4
        r'\b[a-z]\s*[+\-*/^]\s*[a-z]\b',
        r'\b[a-z]\s*=\s*[a-z0-9+\-*/^()]+\b',
        r'\b[a-z]\^[0-9]\b',
        r'\bsqrt\([a-z0-9+\-*/^()]+\)\b',
        r'\b[a-z]\s*[+\-*/]\s*[0-9]\b',
        r'\b[0-9]\s*[+\-*/]\s*[a-z]\b',
        r'\b\d+\s*[×*]\s*\d+\b',
        r'multiply\s+\d+\s*[×*]\s*\d+'
    ]
    
    # Override with math if clear mathematical patterns are found
    for pattern in math_patterns:
        if re.search(pattern, user_message.lower()):
            detected = 'math'
            logger.debug("Math pattern detected, overriding LLM result")
            break
    
    logger.debug(f"Final subject detection: '{user_message}' -> '{detected}'")
    return detected

def update_study_session(user, user_message):
    """Update the current study session with new activity."""
    try:
        session = StudySession.objects.get(user=user, end_time__isnull=True)
        session.questions_asked += 1
        
        # Detect subject from message
        detected_subject = detect_subject(user_message)
        if detected_subject != 'general':
            session.subject = detected_subject
        
        session.save()
    except StudySession.DoesNotExist:
        # Create new session if none exists
        StudySession.objects.create(
            user=user,
            subject=detect_subject(user_message),
            questions_asked=1
        )


