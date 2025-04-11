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

CHROMA_DB_PATH = env_values.get("CHROMA_DB_PATH", "./chroma_db")
EMBEDDING_MODEL_NAME = env_values.get("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

# Potentially add OPENAI_API_KEY loading here if needed

# --- Initialize Clients --- 
try:
    # Initialize ChromaDB client (persistent storage)
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    # Ensure a default collection exists (or create it)
    # Using a fixed name for now, could be configurable
    COLLECTION_NAME = "memory_blocks"
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    # Load the Sentence Transformer model
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
except Exception as e:
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

class MemoryBlockListItem(BaseModel):
    """Schema for items in the list view."""
    id: str
    name: str | None
    content: str

class MemoryBlockBulkDeleteRequest(BaseModel):
    """Schema for bulk delete request."""
    ids: list[str]

class MemoryBlockBulkDeleteResponse(BaseModel):
    """Schema for bulk delete response."""
    message: str
    deleted_count: int

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
        
        # Prepare metadata - **Remove content from here**
        metadata = {
            "name": block_data.name if block_data.name else "Unnamed Block"
            # "content": block_data.content # Store the original content - moving to documents
        }

        # Add to ChromaDB
        collection.add(
            ids=[block_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[block_data.content] # Store content in the documents field
        )
        
        return MemoryBlockResponse(id=block_id, message="Memory block added successfully.")

    except Exception as e:
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
            include=['metadatas', 'distances', 'documents'] # Request metadata, distance, and documents
        )

        # Process and format results
        formatted_results = []
        if results and results.get('ids') and len(results['ids']) > 0:
            ids = results['ids'][0]
            distances = results['distances'][0]
            metadatas = results['metadatas'][0]
            documents = results['documents'][0] # Get the documents list
            
            for i in range(len(ids)):
                formatted_results.append(
                    MemoryBlockQueryResult(
                        id=ids[i],
                        name=metadatas[i].get('name'), # Safely get name
                        content=documents[i], # Get content from documents list
                        distance=distances[i]
                    )
                )

        return MemoryBlockQueryResponse(results=formatted_results)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying memory blocks: {e}")

# --- NEW ENDPOINT --- 
@app.get("/memory_blocks/", response_model=list[MemoryBlockListItem], tags=["Memory Blocks"])
async def list_memory_blocks():
    """Lists all memory blocks currently stored (ID and Name only)."""
    try:
        # Get all items, specifically requesting metadata
        # ChromaDB's get() returns a dict with keys like 'ids', 'embeddings', 'metadatas', etc.
        results = collection.get(include=['metadatas', 'documents'])
        
        block_list = []
        ids = results.get('ids', [])
        metadatas = results.get('metadatas', [])
        documents = results.get('documents', [])

        # Ensure we have the same number of ids and metadatas
        if len(ids) != len(metadatas) or len(ids) != len(documents):
            raise HTTPException(status_code=500, detail="Internal data inconsistency.")

        for block_id, metadata, content in zip(ids, metadatas, documents):
            # Metadata should contain 'name' and 'content' based on our add logic
            block_list.append(MemoryBlockListItem(
                id=block_id,
                name=metadata.get('name'), # Use .get() for safety in case 'name' is missing
                content=content
            ))
        
        return block_list

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error while listing blocks.")

# --- NEW BULK DELETE ENDPOINT ---
@app.delete("/memory_blocks/bulk", response_model=MemoryBlockBulkDeleteResponse, tags=["Memory Blocks"])
async def delete_memory_blocks_bulk(delete_request: MemoryBlockBulkDeleteRequest):
    """Deletes multiple memory blocks based on a list of IDs."""
    if not delete_request.ids:
        raise HTTPException(status_code=400, detail="No IDs provided for deletion.")
    
    try:
        # ChromaDB's delete method takes a list of IDs
        # It doesn't explicitly return the count of deleted items, 
        # but it will raise an error if something goes wrong.
        # We assume success means all requested valid IDs were processed.
        collection.delete(ids=delete_request.ids)
        
        # Note: ChromaDB delete doesn't fail if some IDs don't exist. 
        # We return the count of IDs *requested* for deletion.
        deleted_count = len(delete_request.ids)
        return MemoryBlockBulkDeleteResponse(
            message=f"Bulk delete request processed for {deleted_count} ID(s).",
            deleted_count=deleted_count
        )
    except Exception as e:
        # Log the exception for debugging
        print(f"Error during bulk delete: {e}") 
        raise HTTPException(status_code=500, detail=f"Internal server error during bulk delete: {e}")

# --- NEW DELETE ENDPOINT ---
@app.delete("/memory_blocks/{block_id}", status_code=200, tags=["Memory Blocks"], response_model=dict)
async def delete_memory_block(block_id: str):
    """Deletes a specific memory block by its unique ID."""
    try:
        collection.delete(ids=[block_id])
        return {"message": f"Memory block {block_id} marked for deletion (if it existed)."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error while attempting to delete block {block_id}.")

# Future endpoints for memory block management will go here
