# AI Study Companion

AI Study Companion web application with chatbot functionality, conversation history, and advanced RAG (Retrieval-Augmented Generation) capabilities for personalized learning.

## Features

### 🤖 AI Chatbot
- **Multi-subject AI Agents**: Specialized agents for Math, Science, English, History, Computer Science, and more
- **Automatic Subject Detection**: The AI agent automatically detects the subject of each question—no manual selection needed
- **Educational Focus**: Strictly educational responses, refusing off-topic questions
- **Conversation Management**: Save, view, and manage chat conversations
- **Modern, Responsive Chat UI**: Clean, mobile-friendly chat interface with clear user/AI message display and typing indicators (no streaming/SSE)

### 📚 Custom Learning Materials (RAG)
- **Document Upload**: Upload PDF, DOC, DOCX, and TXT files (up to 15MB)
- **RAG Processing**: Automatic document chunking and embedding generation
- **Semantic Search**: Find relevant content in your uploaded materials
- **Personalized Responses**: Get AI answers based on your specific study materials
- **Material Management**: Organize, view, and delete uploaded documents

### 🎯 Study Features
- **Study Sessions**: Track study time and progress
- **Conversation History**: View and search past conversations
- **Subject Tracking**: Automatic subject detection and categorization
- **User Profiles**: Personalized study preferences and goals

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd aistudycompanion
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your-secret-key
   DEBUG=True
   OPENAI_API_KEY=your-openai-api-key
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## Usage

### Getting Started
1. Visit `http://localhost:8000`
2. Register an account or sign in
3. Start chatting with the AI Study Companion

### Using Custom Learning Materials
1. Go to "Learning Materials" in the navigation
2. Upload your study documents (PDF, DOC, DOCX, TXT)
3. Wait for processing to complete
4. Return to chat and select a material from the sidebar
5. Ask questions about your uploaded content

### Chat Experience
- **User and AI messages** are displayed in a modern, responsive chat panel.
- **Typing indicators** show when the AI is processing your question.
- **No streaming/SSE:** The AI response appears after processing is complete (not word-by-word).
- **Automatic subject detection:** The AI agent determines the subject of your question—no manual selection required.

### Troubleshooting
- If user messages do not appear in the chat area, try refreshing the page.
- For other UI issues, clear your browser cache and reload.

### RAG Functionality
- **Document Processing**: Files are automatically chunked and embedded
- **Semantic Search**: Find relevant content using natural language queries
- **Context-Aware Responses**: AI answers based on your specific materials
- **Confidence Scoring**: See how confident the AI is in its responses

## AutoGen Library

This project uses the [AutoGen](https://github.com/microsoft/autogen) library to enable multi-agent AI orchestration for subject-specific tutoring.

AutoGen is an open-source framework for building applications with multiple AI agents that can collaborate, coordinate, and solve complex tasks together. In this project, AutoGen powers the creation and management of specialized agents for different subjects, allowing them to work together to provide accurate and context-aware educational assistance.

## Technical Details

### Architecture
- **Backend**: Django 4.2.7
- **AI**: OpenAI GPT-3.5-turbo and text-embedding-ada-002
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript with Tailwind CSS styling

### Models
- `UserProfile`: Extended user information
- `Conversation`: Chat conversation sessions
- `ChatMessage`: Individual messages
- `StudySession`: Study tracking
- `CustomLearningMaterial`: Uploaded documents
- `DocumentChunk`: Processed document chunks
- `RAGQuery`: RAG query tracking

### RAG Implementation
1. **Document Upload**: Files stored in media directory
2. **Text Extraction**: Content extracted from documents
3. **Chunking**: Text split into overlapping chunks
4. **Embedding**: OpenAI embeddings generated for each chunk
5. **Storage**: Chunks and embeddings stored in database
6. **Retrieval**: Semantic search using cosine similarity
7. **Generation**: Context-aware responses using retrieved chunks

## File Structure
```
aistudycompanion/
├── apps/aistudycompanion/
│   ├── models.py          # Database models
│   ├── views.py           # View functions
│   ├── urls.py            # URL routing
│   ├── agents.py          # AI agent implementations
│   ├── rag_service.py     # RAG functionality
│   ├── admin.py           # Admin interface
│   └── templates/         # HTML templates
├── media/                 # Uploaded files
├── static/                # Static files
├── requirements.txt       # Python dependencies
└── manage.py             # Django management
```

## Configuration

### OpenAI API
Set your OpenAI API key in the `.env` file:
```env
OPENAI_API_KEY=sk-your-api-key-here
```

### File Upload Limits
- Maximum file size: 15MB
- Supported formats: PDF, DOC, DOCX, TXT
- Storage location: `media/learning_materials/`

### RAG Settings
- Chunk size: 1000 characters
- Chunk overlap: 200 characters
- Max chunks per query: 5
- Embedding model: text-embedding-ada-002

## Development

### Adding New Subjects
1. Update the subject detection in `views.py`
2. Add subject-specific agents in `agents.py`
3. Update the frontend subject detection if needed

### Extending RAG
1. Add new document processors in `rag_service.py`
2. Update the `_extract_text_from_file` method
3. Add new file type support in models

### Customizing AI Responses
1. Modify agent prompts in `agents.py`
2. Update RAG prompts in `rag_service.py`
3. Adjust response formatting in views

## Production Deployment

### Requirements
- Python 3.8+
- PostgreSQL (recommended)
- Redis (for caching)
- Web server (Nginx/Apache)

### Environment Variables
```env
DEBUG=False
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:pass@host:port/db
OPENAI_API_KEY=your-openai-api-key
ALLOWED_HOSTS=your-domain.com
```

### Static Files
```bash
python manage.py collectstatic
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue on GitHub. 