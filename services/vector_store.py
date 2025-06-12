from typing import List, Dict, Optional
from supabase import Client
import openai
from config.config import OPENAI_API_KEY

class VectorStore:
    def __init__(self, supabase_url: str, supabase_key: str):
        """Initialize vector store with Supabase client."""
        self.supabase = Client(supabase_url, supabase_key)
        self.table = "documents"  # Changed to match the actual table name
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.model = "text-embedding-3-small"  # Using the latest embedding model

    def search(self, query: str, limit: int = 3) -> List[Dict]:
        """
        Search the vector store for relevant documentation.
        
        Args:
            query: The search query from the parent
            limit: Maximum number of results to return
            
        Returns:
            List of relevant documentation entries with their content and metadata
        """
        try:
            # Generate embedding for the query
            query_embedding = self._generate_embedding(query)
            
            # Perform vector similarity search in Supabase
            response = self.supabase.rpc(
                'match_documents',
                {
                    'filter': {},  # Empty filter to search all documents
                    'match_count': limit,
                    'query_embedding': query_embedding
                }
            ).execute()
            
            # Process and return results
            results = []
            for doc in response.data:
                results.append({
                    'content': doc.get('content'),
                    'metadata': doc.get('metadata', {}),
                    'similarity': doc.get('similarity', 0)
                })
            
            return results

        except Exception as e:
            print(f"Error searching vector store: {str(e)}")
            return []

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI's API."""
        try:
            response = self.openai_client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            return []

    def get_relevant_context(self, query: str) -> str:
        """
        Get formatted context from vector store for LLM.
        
        Args:
            query: The parent's question
            
        Returns:
            Formatted string with relevant documentation
        """
        results = self.search(query)
        
        if not results:
            return "No relevant documentation found."
        
        # Format results for LLM context
        context = "Relevant TeachPro Documentation:\n\n"
        for i, result in enumerate(results, 1):
            context += f"{i}. {result['content']}\n"
            if result['metadata']:
                context += f"   Source: {result['metadata'].get('source', 'Unknown')}\n"
            context += "\n"
        
        return context 