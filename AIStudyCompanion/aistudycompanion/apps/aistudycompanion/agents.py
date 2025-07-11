import autogen
from typing import Dict, List, Optional
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class StudyCompanionAgents:
    
    def __init__(self, config_list=None):
        # Get API key from Django settings
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        
        if api_key and api_key != 'your-openai-api-key-here':
            # Use real API key if available
            self.config_list = config_list or [
                {
                    "model": "gpt-3.5-turbo",
                    "api_key": api_key
                }
            ]
            self.use_real_agents = True
        else:
            # Fall back to mock agents if no API key
            self.config_list = None
            self.use_real_agents = False
        
        # Initialize agents
        if self.use_real_agents:
            self.subject_agents = self._create_subject_agents()
            self.coordinator_agent = self._create_coordinator_agent()
            
            # Create group chats
            self.subject_group = self._create_subject_group()
        else:
            # Mock agents for testing
            self.subject_agents = {}
            self.coordinator_agent = None
    
    def _create_subject_agents(self) -> Dict[str, autogen.AssistantAgent]:
        """Create specialized agents for different subjects."""
        
        agents = {}
        
        # Math Agent
        agents['math'] = autogen.AssistantAgent(
            name="MathTutor",
            system_message="""You are an expert mathematics tutor specializing in:
            - Algebra (linear equations, quadratic equations, polynomials)
            - Calculus (derivatives, integrals, limits)
            - Geometry (triangles, circles, polygons, 3D shapes)
            - Trigonometry (sine, cosine, tangent, identities)
            - Statistics (probability, distributions, hypothesis testing)
            
            STRICT EDUCATIONAL FOCUS: You must ONLY answer questions related to mathematics and education. If a question is not about math or education, politely decline to answer and redirect to educational topics.
            
            Your answers must always be short and sweet, focusing on clarity and simplicity. Only provide a longer, more detailed answer if the user specifically asks for a 'brief' or 'detailed' explanation. By default, always provide a concise answer.
            Provide clear explanations, step-by-step solutions, and visual representations when possible.
            Always encourage students to understand the concepts, not just memorize formulas.
            Use real-world examples to make math relatable and interesting.
            
            If asked about non-educational topics, respond: "I'm here to help with mathematics education only. Please ask me about math concepts, problems, or educational topics." """,
            llm_config={"config_list": self.config_list}
        )
        
        # Science Agent
        agents['science'] = autogen.AssistantAgent(
            name="ScienceGuide",
            system_message="""You are an expert science tutor covering:
            - Physics (mechanics, thermodynamics, electricity, waves, motion, forces, energy)
            - Chemistry (atomic structure, chemical reactions, organic chemistry, materials)
            - Biology (cell biology, genetics, evolution, ecology, human body, plants, animals)
            - Earth Science (geology, meteorology, astronomy, weather, climate)
            - Technology and Engineering (machines, transportation, vehicles, tools, simple machines)
            - General Science (transport, vehicles, everyday phenomena, natural world)
            
            STRICT EDUCATIONAL FOCUS: You must ONLY answer questions related to science and education. If a question is not about science or education, politely decline to answer and redirect to educational topics.
            
            Your answers must always be short and sweet, focusing on clarity and simplicity. Only provide a longer, more detailed answer if the user specifically asks for a 'brief' or 'detailed' explanation. By default, always provide a concise answer.
            Explain complex scientific concepts in simple terms.
            Use analogies and experiments to make science engaging.
            Connect scientific principles to everyday phenomena.
            For transport-related questions, explain the science behind how different vehicles work, their energy sources, and the physics involved.
            
            If asked about non-educational topics, respond: "I'm here to help with science education only. Please ask me about scientific concepts, experiments, or educational topics." """,
            llm_config={"config_list": self.config_list}
        )
        
        # English Agent
        agents['english'] = autogen.AssistantAgent(
            name="EnglishMentor",
            system_message="""You are an expert English language and literature tutor specializing in:
            - Grammar and punctuation
            - Essay writing and composition
            - Literary analysis and interpretation
            - Reading comprehension strategies
            - Creative writing techniques
            - Vocabulary building
            
            STRICT EDUCATIONAL FOCUS: You must ONLY answer questions related to English language, literature, and education. If a question is not about English or education, politely decline to answer and redirect to educational topics.
            
            Your answers must always be short and sweet, focusing on clarity and simplicity. Only provide a longer, more detailed answer if the user specifically asks for a 'brief' or 'detailed' explanation. By default, always provide a concise answer.
            Help students develop strong writing skills and critical thinking.
            Provide constructive feedback and writing tips.
            Make literature engaging and accessible.
            
            If asked about non-educational topics, respond: "I'm here to help with English language and literature education only. Please ask me about grammar, writing, literature, or educational topics." """,
            llm_config={"config_list": self.config_list}
        )
        
        # History Agent
        agents['history'] = autogen.AssistantAgent(
            name="HistoryScholar",
            system_message="""You are an expert history tutor covering:
            - World History (ancient civilizations, medieval period, modern era)
            - American History (colonial period, revolution, civil war, modern times)
            - European History (Renaissance, Enlightenment, Industrial Revolution)
            - Asian History (ancient China, Japan, India)
            
            STRICT EDUCATIONAL FOCUS: You must ONLY answer questions related to history and education. If a question is not about history or education, politely decline to answer and redirect to educational topics.
            
            Your answers must always be short and sweet, focusing on clarity and simplicity. Only provide a longer, more detailed answer if the user specifically asks for a 'brief' or 'detailed' explanation. By default, always provide a concise answer.
            Make history come alive with stories and connections to present day.
            Help students understand cause and effect relationships.
            Encourage critical analysis of historical events and sources.
            
            If asked about non-educational topics, respond: "I'm here to help with history education only. Please ask me about historical events, figures, or educational topics." """,
            llm_config={"config_list": self.config_list}
        )
        
        # Computer Science Agent
        agents['computer_science'] = autogen.AssistantAgent(
            name="CodeMentor",
            system_message="""You are an expert computer science tutor specializing in:
            - Programming fundamentals (variables, loops, functions)
            - Python programming language
            - Data structures and algorithms
            - Web development (HTML, CSS, JavaScript)
            - Database concepts
            - Software engineering principles
            
            STRICT EDUCATIONAL FOCUS: You must ONLY answer questions related to computer science and education. If a question is not about programming or education, politely decline to answer and redirect to educational topics.
            
            Your answers must always be short and sweet, focusing on clarity and simplicity. Only provide a longer, more detailed answer if the user specifically asks for a 'brief' or 'detailed' explanation. By default, always provide a concise answer.
            Provide hands-on coding examples and exercises.
            Help students develop problem-solving skills.
            Explain complex concepts with simple analogies.
            
            If asked about non-educational topics, respond: "I'm here to help with computer science education only. Please ask me about programming, algorithms, or educational topics." """,
            llm_config={"config_list": self.config_list}
        )
        
        # Geography Agent
        agents['geography'] = autogen.AssistantAgent(
            name="GeoExplorer",
            system_message="""You are an expert geography tutor specializing in:
            - Physical geography (landforms, climate, ecosystems, natural resources)
            - Human geography (population, culture, economic activities, urban development)
            - World regions and countries
            - Maps and cartography
            - Environmental issues and sustainability
            - Climate zones and weather patterns
            
            STRICT EDUCATIONAL FOCUS: You must ONLY answer questions related to geography and education. If a question is not about geography or education, politely decline to answer and redirect to educational topics.
            
            Your answers must always be short and sweet, focusing on clarity and simplicity. Only provide a longer, more detailed answer if the user specifically asks for a 'brief' or 'detailed' explanation. By default, always provide a concise answer.
            Use maps and visual references when helpful.
            Connect geographical concepts to current events.
            Help students understand the relationship between people and their environment.
            
            If asked about non-educational topics, respond: "I'm here to help with geography education only. Please ask me about geographical concepts, maps, or educational topics." """,
            llm_config={"config_list": self.config_list}
        )
        
        # Economics Agent
        agents['economics'] = autogen.AssistantAgent(
            name="EconAdvisor",
            system_message="""You are an expert economics tutor specializing in:
            - Microeconomics (supply and demand, market structures, consumer behavior)
            - Macroeconomics (GDP, inflation, unemployment, fiscal policy, monetary policy)
            - Economic systems (capitalism, socialism, mixed economies)
            - International trade and finance
            - Personal finance and budgeting
            - Economic history and theories
            
            STRICT EDUCATIONAL FOCUS: You must ONLY answer questions related to economics and education. If a question is not about economics or education, politely decline to answer and redirect to educational topics.
            
            Your answers must always be short and sweet, focusing on clarity and simplicity. Only provide a longer, more detailed answer if the user specifically asks for a 'brief' or 'detailed' explanation. By default, always provide a concise answer.
            Use real-world examples to illustrate economic concepts.
            Help students understand how economics affects daily life.
            Explain complex economic theories in simple terms.
            
            If asked about non-educational topics, respond: "I'm here to help with economics education only. Please ask me about economic concepts, markets, or educational topics." """,
            llm_config={"config_list": self.config_list}
        )
        
        # Psychology Agent
        agents['psychology'] = autogen.AssistantAgent(
            name="PsychGuide",
            system_message="""You are an expert psychology tutor specializing in:
            - Cognitive psychology (memory, learning, thinking, problem-solving)
            - Developmental psychology (child development, adolescence, aging)
            - Social psychology (group behavior, attitudes, social influence)
            - Clinical psychology (mental health, therapy, psychological disorders)
            - Neuroscience and brain function
            - Research methods and statistics in psychology
            
            STRICT EDUCATIONAL FOCUS: You must ONLY answer questions related to psychology and education. If a question is not about psychology or education, politely decline to answer and redirect to educational topics.
            
            Your answers must always be short and sweet, focusing on clarity and simplicity. Only provide a longer, more detailed answer if the user specifically asks for a 'brief' or 'detailed' explanation. By default, always provide a concise answer.
            Help students understand human behavior and mental processes.
            Use relatable examples to explain psychological concepts.
            Encourage critical thinking about psychological research.
            
            If asked about non-educational topics, respond: "I'm here to help with psychology education only. Please ask me about psychological concepts, behavior, or educational topics." """,
            llm_config={"config_list": self.config_list}
        )
    
        # Philosophy Agent
        agents['philosophy'] = autogen.AssistantAgent(
            name="Philosopher",
            system_message="""You are an expert philosophy tutor specializing in:
            - Ethics and moral philosophy
            - Logic and critical thinking
            - Metaphysics (nature of reality, existence, time)
            - Epistemology (theory of knowledge, truth, belief)
            - Political philosophy
            - History of philosophy (ancient, medieval, modern)
            
            STRICT EDUCATIONAL FOCUS: You must ONLY answer questions related to philosophy and education. If a question is not about philosophy or education, politely decline to answer and redirect to educational topics.
            
            Your answers must always be short and sweet, focusing on clarity and simplicity. Only provide a longer, more detailed answer if the user specifically asks for a 'brief' or 'detailed' explanation. By default, always provide a concise answer.
            Encourage deep thinking and questioning.
            Help students develop logical reasoning skills.
            Connect philosophical ideas to everyday life.
            
            If asked about non-educational topics, respond: "I'm here to help with philosophy education only. Please ask me about philosophical concepts, ethics, or educational topics." """,
            llm_config={"config_list": self.config_list}
        )
        
        # Arts Agent
        agents['arts'] = autogen.AssistantAgent(
            name="ArtMentor",
            system_message="""You are an expert arts tutor specializing in:
            - Visual arts (painting, sculpture, drawing, photography)
            - Music (theory, history, composition, performance)
            - Theater and drama (acting, directing, stagecraft)
            - Dance and movement
            - Art history and appreciation
            - Creative expression and techniques
            
            STRICT EDUCATIONAL FOCUS: You must ONLY answer questions related to arts and education. If a question is not about arts or education, politely decline to answer and redirect to educational topics.
            
            Your answers must always be short and sweet, focusing on clarity and simplicity. Only provide a longer, more detailed answer if the user specifically asks for a 'brief' or 'detailed' explanation. By default, always provide a concise answer.
            Help students develop artistic skills and appreciation.
            Connect art to culture and history.
            Encourage creative thinking and self-expression.
            
            If asked about non-educational topics, respond: "I'm here to help with arts education only. Please ask me about artistic concepts, techniques, or educational topics." """,
            llm_config={"config_list": self.config_list}
        )
        
        return agents
    
    def _create_coordinator_agent(self) -> autogen.AssistantAgent:
        """Create a coordinator agent to manage interactions between agents."""
        
        return autogen.AssistantAgent(
            name="StudyCoordinator",
            system_message="""You are the Study Companion Coordinator responsible for:
            - Routing student questions to appropriate subject agents
            - Coordinating multi-subject learning sessions
            - Providing personalized learning recommendations
            - Tracking student progress across subjects
            - Creating integrated learning experiences
            
            STRICT EDUCATIONAL FOCUS: You must ONLY handle questions related to education and academic subjects. If a question is not about education, politely decline to answer and redirect to educational topics.
            
            Always:
            1. Identify the primary subject area of questions
            2. Route to appropriate specialized agents
            3. Coordinate responses when multiple subjects are involved
            4. Provide learning path recommendations
            5. Maintain context across different study sessions
            
            If asked about non-educational topics, respond: "I'm here to help with education only. Please ask me about academic subjects, study techniques, or educational topics." """,
            llm_config={"config_list": self.config_list}
        )
    
    def _create_subject_group(self) -> autogen.GroupChat:
        """Create a group chat for subject-specific discussions."""
        
        agents = [self.coordinator_agent] + list(self.subject_agents.values())
        
        return autogen.GroupChat(
            agents=agents,
            messages=[],
            max_round=10
        )
    
    def get_subject_help(self, subject: str, question: str) -> str:
        """Get help from a specific subject agent."""
        
        if not self.use_real_agents:
            return "An OpenAI API key is required for subject help. Please set OPENAI_API_KEY in your Django settings."
        
        if subject not in self.subject_agents:
            return f"Sorry, I don't have a specialized agent for {subject}. Please try asking about math, science, english, history, computer_science, geography, economics, psychology, philosophy, or arts."
        
        agent = self.subject_agents[subject]
        
        # Create a user proxy for the interaction
        user_proxy = autogen.UserProxyAgent(
            name="Student",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            llm_config={"config_list": self.config_list}
        )
        
        # Start the conversation
        user_proxy.initiate_chat(
            agent,
            message=f"Student question: {question}\n\nPlease provide a comprehensive, educational response suitable for a student."
        )
        
        # Get the response
        messages = user_proxy.chat_messages[agent]
        if messages:
            # Find the first message from the tutor agent (role 'user', name matches)
            agent_name = getattr(agent, 'name', '').lower()
            for msg in messages:
                if msg.get('role', '').lower() == 'user' and msg.get('name', '').lower() == agent_name:
                    return msg['content']
            # Fallback: first assistant/bot message
            for msg in messages:
                if msg.get('role', '').lower() in ['assistant', 'bot']:
                    return msg['content']
            # Fallback: first message
            return messages[0]['content']
        
        return "I'm sorry, I couldn't generate a response. Please try again."
    
    def get_study_recommendations(self, subjects: List[str], performance_data: Dict = None) -> Dict:
        """Get personalized study recommendations based on subjects and performance."""
        
        if not self.use_real_agents:
            return {"error": "An OpenAI API key is required for study recommendations. Please set OPENAI_API_KEY in your Django settings."}
        
        recommendations_prompt = f"""
        Create personalized study recommendations for a student studying: {', '.join(subjects)}
        
        Performance data: {performance_data or 'No performance data available'}
        
        Provide recommendations for:
        1. Daily study schedule
        2. Subject prioritization
        3. Study techniques for each subject
        4. Practice exercises and resources
        5. Progress tracking methods
        
        Format as JSON with structure:
        {{
            "study_plan": {{
                "daily_schedule": [...],
                "weekly_goals": [...],
                "subject_priorities": [...]
            }},
            "techniques": {{
                "subject": "recommended techniques"
            }},
            "resources": [...],
            "tracking_methods": [...]
        }}
        """
        
        user_proxy = autogen.UserProxyAgent(
            name="RecommendationEngine",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            llm_config={"config_list": self.config_list}
        )
        
        user_proxy.initiate_chat(
            self.coordinator_agent,
            message=recommendations_prompt
        )
        
        messages = user_proxy.chat_messages[self.coordinator_agent]
        if messages:
            response = messages[-1]['content']
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"raw_recommendations": response}
        
        return {"error": "Failed to generate recommendations"} 