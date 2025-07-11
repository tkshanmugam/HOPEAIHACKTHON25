import os
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import openai
from .models import CustomLearningMaterial, DocumentChunk, RAGQuery

logger = logging.getLogger(__name__)

class RAGService:
        
    def __init__(self):
        self.client = openai.OpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', None))
        self.chunk_size = 1000  # Characters per chunk
        self.chunk_overlap = 200  # Overlap between chunks
        self.max_chunks = 5  # Maximum chunks to retrieve for context
        
    def process_document(self, material: CustomLearningMaterial) -> bool:
        try:
            material.processing_status = 'processing'
            material.save()
            
            # For now, we'll create a simple text extraction
            # In a full implementation, you would extract text from PDF/DOC files
            text_content = self._extract_text_from_file(material.file.path, material.document_type)
            if not text_content:
                material.processing_status = 'failed'
                material.save()
                return False
            
            # Split text into chunks
            chunks = self._create_chunks(text_content)
            
            # Create document chunks
            for i, chunk_text in enumerate(chunks):
                # Generate embedding for chunk
                embedding = self._generate_embedding(chunk_text)
                
                # Create DocumentChunk
                DocumentChunk.objects.create(
                    material=material,
                    chunk_index=i,
                    content=chunk_text,
                    embedding=embedding,
                    metadata={'chunk_size': len(chunk_text)}
                )
            
            material.is_processed = True
            material.processing_status = 'completed'
            material.save()
            
            logger.info(f"Successfully processed document: {material.title}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing document {material.title}: {e}")
            material.processing_status = 'failed'
            material.save()
            return False
    
    def _extract_text_from_file(self, file_path: str, document_type: str) -> Optional[str]:
        try:
            if document_type == 'txt':
                return self._extract_text_from_txt(file_path)
            else:
                # For now, return a placeholder for PDF/DOC files
                # In production, you would implement proper text extraction
                logger.warning(f"Text extraction for {document_type} not yet implemented")
                return f"Document content for {document_type} file. This is a placeholder for the actual content extraction."
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return None
    
    def _extract_text_from_txt(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error reading TXT {file_path}: {e}")
            return ""
    
    def _create_chunks(self, text: str) -> List[str]:
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # If this isn't the last chunk, try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start + self.chunk_size - 100, start), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _generate_embedding(self, text: str) -> List[float]:
        try:
            if not self.client:
                logger.error("OpenAI client not initialized")
                return []
            
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []
    
    def search_documents(self, user, query: str, material_id: Optional[int] = None) -> List[DocumentChunk]:
        try:
            # Generate embedding for query
            query_embedding = self._generate_embedding(query)
            if not query_embedding:
                return []
            
            # Get user's materials
            if material_id:
                materials = CustomLearningMaterial.objects.filter(
                    user=user, 
                    id=material_id,
                    is_processed=True
                )
            else:
                materials = CustomLearningMaterial.objects.filter(
                    user=user, 
                    is_processed=True
                )
            
            if not materials.exists():
                return []
            
            # Get all chunks from user's materials
            chunks = DocumentChunk.objects.filter(
                material__in=materials,
                embedding__isnull=False
            )
            
            # Calculate similarity scores
            chunk_scores = []
            for chunk in chunks:
                if chunk.embedding:
                    similarity = self._calculate_cosine_similarity(query_embedding, chunk.embedding)
                    chunk_scores.append((chunk, similarity))
            
            # Sort by similarity and return top chunks
            chunk_scores.sort(key=lambda x: x[1], reverse=True)
            top_chunks = [chunk for chunk, score in chunk_scores[:self.max_chunks]]
            
            return top_chunks
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def _calculate_cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def generate_rag_response(self, user, query: str, material_id: Optional[int] = None) -> Tuple[str, float, List[DocumentChunk]]:
        try:
            # Search for relevant chunks
            relevant_chunks = self.search_documents(user, query, material_id)
            
            if not relevant_chunks:
                return "I couldn't find any relevant information in your uploaded documents to answer this question. Please try rephrasing your question or upload relevant study materials.", 0.0, []
            
            # Prepare context from chunks
            context = "\n\n".join([chunk.content for chunk in relevant_chunks])
            
            # Generate response using OpenAI
            if not self.client:
                return "Sorry, I'm unable to generate responses at the moment. Please try again later.", 0.0, relevant_chunks
            
            prompt = f"""You are an educational assistant helping a student with their uploaded study materials. 
                        Context from the student's documents:
                        {context}
                        Student's question: {query}
                        Please provide a helpful, educational response based on the context provided. If the context doesn't contain enough information to fully answer the question, acknowledge this and provide what you can from the available information.
                        Your response should be:
                        1. Educational and informative
                        2. Based on the provided context
                        3. Clear and well-structured
                        4. Helpful for learning and understanding
                        Response:"""
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            ) 
            ai_response = response.choices[0].message.content.strip()
            confidence = min(0.9, len(relevant_chunks) / self.max_chunks) if relevant_chunks else 0.0
            return ai_response, confidence, relevant_chunks
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            return "Sorry, I encountered an error while processing your question. Please try again.", 0.0, []
    
    def save_rag_query(self, user, material: CustomLearningMaterial, query: str, response: str, relevant_chunks: List[DocumentChunk], confidence: float) -> RAGQuery:
        """Save RAG query for analytics and improvement."""
        try:
            rag_query = RAGQuery.objects.create(
                user=user,
                material=material,
                query=query,
                response=response,
                confidence_score=confidence
            )
            rag_query.relevant_chunks.set(relevant_chunks)
            return rag_query
        except Exception as e:
            logger.error(f"Error saving RAG query: {e}")
            return None 