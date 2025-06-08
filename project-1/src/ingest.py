import os
import sys
import logging
from datetime import datetime
from typing import List
import pickle

from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
    PyPDFLoader,
    CSVLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Import project config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import DATA_DIR, VECTOR_DB_PATH, EMBEDDING_MODEL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure pickle to use a safer protocol
pickle.HIGHEST_PROTOCOL = 4

def load_documents():
    """Load documents from the data directory."""
    logger.info(f"Loading documents from {DATA_DIR}")
    
    # Configure loaders for different file types
    loaders = {
        ".txt": (DirectoryLoader, {"loader_cls": TextLoader}),
        ".pdf": (DirectoryLoader, {"loader_cls": PyPDFLoader}),
        ".csv": (DirectoryLoader, {"loader_cls": CSVLoader})
    }
    
    documents = []
    for ext, (loader_cls, loader_args) in loaders.items():
        if loader_args.get("loader_cls"):
            loader = loader_cls(
                path=DATA_DIR,
                glob=f"**/*{ext}",
                loader_cls=loader_args["loader_cls"]
            )
        else:
            loader = loader_cls(path=DATA_DIR, glob=f"**/*{ext}")
            
        try:
            ext_documents = loader.load()
            logger.info(f"Loaded {len(ext_documents)} documents with extension {ext}")
            documents.extend(ext_documents)
        except Exception as e:
            logger.warning(f"Error loading {ext} documents: {e}")
    
    return documents

def split_documents(documents):
    """Split documents into chunks."""
    logger.info("Splitting documents into chunks")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    return text_splitter.split_documents(documents)

def create_vector_store(documents):
    """Create a FAISS vector store from the documents."""
    logger.info("Creating vector store")
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    
    # Create vector store directory if it doesn't exist
    os.makedirs(os.path.dirname(VECTOR_DB_PATH), exist_ok=True)
    
    # Create and save the vector store
    vector_store = FAISS.from_documents(documents, embeddings)
    vector_store.save_local(VECTOR_DB_PATH)
    logger.info(f"Vector store saved to {VECTOR_DB_PATH}")
    
    return vector_store

def main():
    """Main function to ingest documents and create vector store."""
    try:
        start_time = datetime.now()
        logger.info("Starting document ingestion")
        
        # Load documents
        documents = load_documents()
        if not documents:
            logger.warning(f"No documents found in {DATA_DIR}. Please add some documents first.")
            return
        
        logger.info(f"Loaded {len(documents)} documents in total")
        
        # Split documents
        splits = split_documents(documents)
        logger.info(f"Split into {len(splits)} chunks")
        
        # Create vector store
        create_vector_store(splits)
        
        end_time = datetime.now()
        logger.info(f"Ingestion completed in {end_time - start_time}")
        
    except Exception as e:
        logger.error(f"Error during document ingestion: {e}")
        raise

if __name__ == "__main__":
    main() 