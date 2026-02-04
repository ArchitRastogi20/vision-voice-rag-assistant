from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import httpx
import base64
import PyPDF2
from io import BytesIO
from typing import List, Dict
from pymongo import MongoClient
from bm25 import BM25
import os
from datetime import datetime
import uuid
from openai import OpenAI
import re
import time
import csv

app = FastAPI()

# CORS setup for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # vocal-rag-frontend
        "http://localhost:8080",   # landing-page
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Service URLs
ASR_SERVICE = os.getenv("ASR_SERVICE", "http://asr-service:8001")
TTS_SERVICE = os.getenv("TTS_SERVICE", "http://tts-service:8000")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://mongodb:27017/")

# MongoDB setup
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client["multimodal_rag"]
users_collection = db["users"]
documents_collection = db["documents"]
chunks_collection = db["chunks"]
conversations_collection = db["conversations"]

# OpenAI setup
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

# In-memory session store (simple)
sessions = {}


def log_latency(component: str, latency_ms: float):
    """Log latency to a CSV file"""
    # Create directory if it doesn't exist
    log_dir = "benchmark_data"
    os.makedirs(log_dir, exist_ok=True)
    
    filename = os.path.join(log_dir, f"{component}_latency.csv")
    file_exists = os.path.isfile(filename)
    
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['timestamp', 'latency_ms'])
        
        writer.writerow([datetime.utcnow().isoformat(), latency_ms])


# ============= UTILITY FUNCTIONS =============
def clean_markdown(text: str) -> str:
    """Remove markdown formatting and special characters, keep only . ? !"""
    # Remove bold/italic markers
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
    text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__
    text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_
    
    # Remove headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    
    # Replace multiple dashes with period
    text = re.sub(r'\s*-{2,}\s*', '. ', text)
    
    # Replace single dash between words with comma
    text = re.sub(r'\s+-\s+', ', ', text)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Clean up multiple periods
    text = re.sub(r'\.{2,}', '.', text)
    
    return text.strip()


# ============= AUTHENTICATION =============
@app.post("/api/login")
async def login(username: str = Form(...)):
    """Simple username-based login"""
    if not username or len(username.strip()) == 0:
        raise HTTPException(status_code=400, detail="Username required")
    
    # Find or create user
    user = users_collection.find_one({"username": username})
    if not user:
        user = {
            "username": username,
            "created_at": datetime.utcnow(),
        }
        users_collection.insert_one(user)
    
    # Create session
    session_id = str(uuid.uuid4())
    sessions[session_id] = username
    
    return JSONResponse({
        "session_id": session_id,
        "username": username,
        "message": "Login successful"
    })


@app.post("/api/logout")
async def logout(session_id: str = Form(...)):
    """Logout user"""
    if session_id in sessions:
        del sessions[session_id]
    return JSONResponse({"message": "Logged out successfully"})


# ============= PDF PROCESSING =============
def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes"""
    pdf_file = BytesIO(pdf_bytes)
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    """Split text into chunks"""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks


@app.post("/api/upload-pdf")
async def upload_pdf(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload and process PDF"""
    # Validate session
    if session_id not in sessions:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    username = sessions[session_id]
    
    # Validate PDF
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    # Read PDF
    pdf_bytes = await file.read()
    
    # Extract text
    try:
        text = extract_text_from_pdf(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF parsing failed: {str(e)}")
    
    # Chunk text
    chunks = chunk_text(text)
    
    # Create document record
    doc_id = str(uuid.uuid4())
    document = {
        "doc_id": doc_id,
        "username": username,
        "filename": file.filename,
        "text": text,
        "num_chunks": len(chunks),
        "uploaded_at": datetime.utcnow()
    }
    documents_collection.insert_one(document)
    
    # Store chunks with BM25-ready format
    chunk_records = []
    for idx, chunk in enumerate(chunks):
        chunk_record = {
            "doc_id": doc_id,
            "chunk_id": idx,
            "text": chunk,
            "username": username
        }
        chunk_records.append(chunk_record)
    
    if chunk_records:
        chunks_collection.insert_many(chunk_records)
    
    return JSONResponse({
        "doc_id": doc_id,
        "filename": file.filename,
        "num_chunks": len(chunks),
        "message": "PDF processed successfully"
    })


# ============= BM25 RETRIEVAL =============
def get_user_chunks(username: str) -> List[Dict]:
    """Get all chunks for a user"""
    return list(chunks_collection.find({"username": username}))


def bm25_search(query: str, username: str, top_k: int = 8) -> List[str]:
    """Perform BM25 search on user's documents"""
    # Get user's chunks
    chunks = get_user_chunks(username)
    
    if not chunks:
        return []
    
    # Extract text from chunks
    corpus = [chunk["text"] for chunk in chunks]
    
    # Create BM25 index
    bm25 = BM25(corpus)
    
    # Search
    query_tokens = query.lower().split()
    scores = bm25.get_scores(query_tokens)
    
    # Get top-k
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    
    return [corpus[i] for i in top_indices]


# ============= RAG PIPELINE =============
async def rag_pipeline(query: str, username: str) -> str:
    """Execute RAG pipeline: retrieve chunks + generate answer"""
    # BM25 retrieval
    start_time = time.time()
    relevant_chunks = bm25_search(query, username, top_k=8)
    end_time = time.time()
    log_latency("bm25", (end_time - start_time) * 1000)
    
    if not relevant_chunks:
        return "I don't have any documents to answer your question. Please upload a PDF first."
    
    # Create context
    context = "\n\n".join(f"[Chunk {i+1}]: {chunk}" for i, chunk in enumerate(relevant_chunks))
    
    # Create prompt
    prompt = f"""You are a helpful assistant. Answer the user's question based on the following context from their documents.

Context:
{context}

Question: {query}

Answer: """
    
    # Call ChatGPT
    try:
        start_time = time.time()
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        end_time = time.time()
        log_latency("gpt", (end_time - start_time) * 1000)

        answer = response.choices[0].message.content.strip()
        
        # Clean markdown formatting
        answer = clean_markdown(answer)
        
        return answer
    except Exception as e:
        return f"Error generating answer: {str(e)}"


# ============= VOICE QUERY =============
@app.post("/api/voice-query")
async def voice_query(
    session_id: str = Form(...),
    audio: UploadFile = File(...)
):
    """Handle voice query: ASR -> RAG -> TTS"""
    # Validate session
    if session_id not in sessions:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    username = sessions[session_id]
    
    # Step 1: ASR - transcribe audio
    async with httpx.AsyncClient(timeout=30.0) as client:
        files = {"audio": (audio.filename, await audio.read(), audio.content_type)}
        try:
            start_time = time.time()
            asr_response = await client.post(f"{ASR_SERVICE}/asr", files=files)
            end_time = time.time()
            log_latency("asr", (end_time - start_time) * 1000)
            
            asr_data = asr_response.json()
            query_text = asr_data.get("text", "")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ASR failed: {str(e)}")
    
    if not query_text:
        raise HTTPException(status_code=400, detail="Could not transcribe audio")
    
    # Step 2: RAG - get answer
    answer = await rag_pipeline(query_text, username)
    
    # Step 3: TTS - convert answer to speech
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            start_time = time.time()
            tts_response = await client.post(
                f"{TTS_SERVICE}/tts",
                data={"text": answer}
            )
            end_time = time.time()
            log_latency("tts", (end_time - start_time) * 1000)
            
            audio_content = tts_response.content
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")
    
    # Convert audio to base64
    audio_base64 = base64.b64encode(audio_content).decode('utf-8')
    
    # Save conversation to database
    conversation = {
        "username": username,
        "query": query_text,
        "answer": answer,
        "audio": audio_base64,
        "timestamp": datetime.utcnow()
    }
    conversations_collection.insert_one(conversation)
    
    # Return JSON response with all data
    return JSONResponse({
        "query": query_text,
        "answer": answer,
        "audio": audio_base64,
        "timestamp": datetime.utcnow().isoformat()
    })


# ============= CONVERSATION HISTORY =============
@app.get("/api/conversations")
async def get_conversations(session_id: str):
    """Get user's conversation history"""
    if session_id not in sessions:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    username = sessions[session_id]
    
    # Get conversations sorted by timestamp
    conversations = list(conversations_collection.find(
        {"username": username},
        {"_id": 0}
    ).sort("timestamp", 1))
    
    # Convert datetime to string
    for conv in conversations:
        if "timestamp" in conv:
            conv["timestamp"] = conv["timestamp"].isoformat()
    
    return JSONResponse({"conversations": conversations})


# ============= UTILITY ENDPOINTS =============
@app.get("/api/documents")
async def get_documents(session_id: str):
    """Get user's documents"""
    if session_id not in sessions:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    username = sessions[session_id]
    docs = list(documents_collection.find(
        {"username": username},
        {"_id": 0, "text": 0}
    ))
    
    # Convert datetime to string
    for doc in docs:
        if "uploaded_at" in doc:
            doc["uploaded_at"] = doc["uploaded_at"].isoformat()
        if "created_at" in doc:
            doc["created_at"] = doc["created_at"].isoformat()
    
    return JSONResponse({"documents": docs})


@app.get("/")
async def health():
    return {"status": "Orchestrator service running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)