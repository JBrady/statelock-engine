import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv, dotenv_values
import chromadb
from sentence_transformers import SentenceTransformer
import uuid
from datetime import datetime



# Load environment variables from .env file
# load_dotenv() # Disable automatic loading for now

# --- Configuration --- 
# Load directly into a dictionary for inspection
env_values = dotenv_values(".env") 
print(f"DEBUG: Loaded .env values: {env_values}") # Debug print

CHROMA_DB_PATH = env_values.get("CHROMA_DB_PATH", "./chroma_db")
EMBEDDING_MODEL_NAME = env_values.get("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
print(f"DEBUG: Using Embedding Model Name: '{EMBEDDING_MODEL_NAME}'") # Debug print

# Potentially add OPENAI_API_KEY loading here if needed

# --- Initialize Clients --- 
try:
    # Initialize ChromaDB client (persistent storage)
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    print(f"ChromaDB client initialized. Storage path: {CHROMA_DB_PATH}")

    # Ensure a default collection exists (or create it)
    # Using a fixed name for now, could be configurable
    COLLECTION_NAME = "memory_blocks"
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
    print(f"ChromaDB collection '{COLLECTION_NAME}' loaded/created.")

    # Load the Sentence Transformer model
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    print(f"Sentence Transformer model '{EMBEDDING_MODEL_NAME}' loaded.")
except Exception as e:
    print(f"Error during initialization: {e}")
    # Decide how to handle fatal init errors - maybe exit or raise?
    raise RuntimeError(f"Failed to initialize core components: {e}") from e


app = FastAPI(
    title="Memory Block Assistant API",
    description="API for simulating named memory blocks with semantic retrieval.",
    version="0.1.0",
)

# --- Pydantic Models --- 
class MemoryBlockCreate(BaseModel):
    content: str = Field(..., description="The text content of the memory block.")
    name: str | None = Field(None, description="An optional descriptive name for the memory block.")

class MemoryBlockResponse(BaseModel):
    id: str
    message: str

class MemoryBlockQuery(BaseModel):
    query_text: str
    top_k: int = Field(default=3, gt=0, description="Number of similar blocks to retrieve")

class MemoryBlockQueryResult(BaseModel):
    id: str
    name: str | None # Name might be missing if originally unnamed
    content: str | None # Content might be missing in older blocks
    distance: float # Similarity score (lower is more similar)

class MemoryBlockQueryResponse(BaseModel):
    results: list[MemoryBlockQueryResult]


# --- API Endpoints --- 

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Memory Block Assistant API!"}


@app.post("/memory_blocks/", response_model=MemoryBlockResponse, status_code=201, tags=["Memory Blocks"])
async def add_memory_block(block_data: MemoryBlockCreate):
    """Adds a new memory block to the collection."""
    try:
        block_id = str(uuid.uuid4())
        
        # Generate embedding for the content
        embedding = embedding_model.encode(block_data.content).tolist()
        
        # Prepare metadata - **Include content here**
        metadata = {
            "name": block_data.name if block_data.name else "Unnamed Block",
            "content": block_data.content # Store the original content
        }

        # Add to ChromaDB
        collection.add(
            ids=[block_id],
            embeddings=[embedding],
            metadatas=[metadata]
            # documents=[block_data.content] # Alternatively, store content here - sticking with metadata for now
        )
        
        print(f"Added memory block {block_id} (Name: {metadata['name']})")
        return MemoryBlockResponse(id=block_id, message="Memory block added successfully.")

    except Exception as e:
        print(f"Error adding memory block: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.post("/memory_blocks/query/", response_model=MemoryBlockQueryResponse)
async def query_memory_blocks(query_data: MemoryBlockQuery):
    """Queries the collection for memory blocks semantically similar to the query text."""
    try:
        # Generate embedding for the query text
        query_embedding = embedding_model.encode(query_data.query_text).tolist()

        # Query ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=query_data.top_k,
            include=['metadatas', 'distances'] # Request metadata and distance
        )

        # Process and format results
        formatted_results = []
        if results and results.get('ids') and len(results['ids']) > 0:
            ids = results['ids'][0]
            distances = results['distances'][0]
            metadatas = results['metadatas'][0]
            
            for i in range(len(ids)):
                formatted_results.append(
                    MemoryBlockQueryResult(
                        id=ids[i],
                        name=metadatas[i].get('name'), # Safely get name
                        content=metadatas[i].get('content'), # Safely get content
                        distance=distances[i]
                    )
                )

        return MemoryBlockQueryResponse(results=formatted_results)

    except Exception as e:
        print(f"Error querying memory blocks: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

# Future endpoints for memory block management will go here
