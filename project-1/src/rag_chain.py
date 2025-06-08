import os
import logging
import re
from typing import Dict, List, Any

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from src.config import (
    VECTOR_DB_PATH, EMBEDDING_MODEL, LLM_MODEL
)
from src.config_loader import get_app_config, get_prompt_config
from src.prompt_utils import create_rag_prompt

# Configure logging
logger = logging.getLogger(__name__)

class RAGChain:
    def __init__(self, 
                 use_memory: bool = True, 
                 use_reasoning: bool = True, 
                 reasoning_strategy: str = "CoT",
                 prompt_template: str = None):
        """Initialize the RAG chain.
        
        Args:
            use_memory: Whether to use conversation memory
            use_reasoning: Whether to use intermediate reasoning steps
            reasoning_strategy: The reasoning strategy to use ('CoT', 'ReAct', or 'Self-Ask')
            prompt_template: The prompt template configuration to use
        """
        self.use_memory = use_memory
        self.use_reasoning = use_reasoning
        self.reasoning_strategy = reasoning_strategy if use_reasoning else None
        
        # Load app configuration
        self.app_config = get_app_config()
        
        # Get default prompt template if not specified
        if prompt_template is None:
            prompt_template = self.app_config.get("default_prompt_template", "rag_prompt_default")
        
        self.prompt_template = prompt_template
        
        # Check if we should only answer abortion-related questions
        self.only_answer_abortion_topics = self.app_config.get("only_answer_abortion_topics", False)
        
        # Set up abortion-related keywords for filtering
        self.abortion_keywords = [
            'abortion', 'reproductive', 'pregnancy', 'termination', 'pro-choice', 
            'pro-life', 'unborn', 'fetus', 'womb', 'trimester', 'contraception', 
            'planned parenthood', 'women\'s health', 'reproductive rights',
            'medical procedure', 'healthcare access', 'roe v wade'
        ]
        
        # Load prompt configuration
        try:
            self.prompt_config = get_prompt_config(prompt_template)
            logger.info(f"Using prompt template: {prompt_template}")
        except KeyError:
            logger.warning(f"Prompt template '{prompt_template}' not found. Using default.")
            self.prompt_config = get_prompt_config("rag_prompt_default")
        
        # Load vector store
        self._load_vector_store()
        
        # Initialize LLM
        self.llm = ChatOpenAI(model_name=LLM_MODEL, temperature=0.2)
        
        # Initialize memory if needed
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        ) if use_memory else None
        
        # Build the chain
        self._build_chain()
    
    def _is_abortion_related(self, query: str) -> bool:
        """Check if a query is related to abortion awareness.
        
        Args:
            query: The query to check
            
        Returns:
            True if the query is related to abortion awareness, False otherwise
        """
        # Convert to lowercase for case-insensitive matching
        query_lower = query.lower()
        
        # Check for keyword matches
        for keyword in self.abortion_keywords:
            if keyword.lower() in query_lower:
                return True
        
        # If we don't find any keywords, check with the retriever
        docs = self.retriever.get_relevant_documents(query)
        if docs:
            # If we have relevant documents, the query is likely abortion-related
            return True
        
        return False
    
    def _load_vector_store(self):
        """Load the vector store."""
        if not os.path.exists(VECTOR_DB_PATH):
            raise ValueError(f"Vector store not found at {VECTOR_DB_PATH}. Run ingest.py first.")
        
        logger.info(f"Loading vector store from {VECTOR_DB_PATH}")
        embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        self.vector_store = FAISS.load_local(VECTOR_DB_PATH, embeddings, allow_dangerous_deserialization=True)
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}
        )
    
    def _build_chain(self):
        """Build the RAG chain."""
        # Create a placeholder prompt - actual prompt will be constructed dynamically
        prompt = PromptTemplate(
            template="{context}\n\n{question}",
            input_variables=["context", "question"]
        )
        
        # Create the chain
        chain_type = "stuff"  # Use "stuff" method to input all retrieved docs into prompt
        
        chain_kwargs = {
            "prompt": prompt,
            "verbose": True
        }
        
        if self.use_memory:
            chain_kwargs["memory"] = self.memory
        
        self.chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type=chain_type,
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs=chain_kwargs
        )
    
    def query(self, question: str) -> Dict[str, Any]:
        """Query the RAG chain with a question.
        
        Args:
            question: The question to ask
            
        Returns:
            Dict containing the answer and source documents
        """
        logger.info(f"Query: {question}")
        
        # Check if we should only answer abortion-related questions
        if self.only_answer_abortion_topics and not self._is_abortion_related(question):
            # Return a polite refusal for non-abortion-related questions
            refusal_message = (
                "I'm a specialized educational assistant focused only on abortion awareness and reproductive health. "
                "I'm not able to answer questions outside of this specific focus area. "
                "Please feel free to ask me about abortion procedures, reproductive health information, "
                "or related women's health topics, and I'll be happy to provide factual, educational information."
            )
            
            logger.info(f"Refusing to answer non-abortion-related query: {question}")
            return {
                "query": question,
                "answer": refusal_message,
                "source_documents": []
            }
        
        # Get retrieved documents
        docs = self.retriever.get_relevant_documents(question)
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Construct the prompt using prompt_utils
        prompt_str = create_rag_prompt(
            self.prompt_config,
            context,
            question,
            self.app_config,
            self.reasoning_strategy if self.use_reasoning else None
        )
        
        # Execute the LLM with the constructed prompt
        result = self.llm.invoke(prompt_str)
        
        # Format the response
        response = {
            "query": question,
            "answer": result.content,
            "source_documents": [
                {"content": doc.page_content, "source": doc.metadata.get("source", "unknown")}
                for doc in docs
            ]
        }
        
        logger.info(f"Answer: {response['answer']}")
        return response 