import os, uuid
from fastapi import FastAPI, UploadFile, Depends,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pypdf import PdfReader
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import openai
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db import SessionLocal
from app.models import Document
from app.redis_cache import get_cached_answer, set_cached_answer
from authlib.integrations.starlette_client import OAuth
from jose import jwt
from starlette.middleware.sessions import SessionMiddleware
from app.models import User
 
# Load environment variables
load_dotenv()
openai.api_key = "openai-api-key"  # Replace with your OpenAI API key
QDRANT_URL = "quadrant-url"  # Replace with your Qdrant URL
QDRANT_API_KEY = "quadrant-api-key"  # Replace with your Qdrant API key
COLLECTION_NAME = "pdf_chunks"

load_dotenv()
GOOGLE_CLIENT_ID = "google-client-id"
GOOGLE_CLIENT_SECRET = "google-client-secret"
SESSION_SECRET = "session-secret-key"
SERVER_URL =  "server-url"  # e.g., "http://localhost:8000"

SECRET_KEY = "SECRET_KEY"
ALGORITHM = "ALGORITHM"
    
async def init_db():
    return await asyncpg.connect(
        user="storehousedb_owner",
        password="4QWYsjOdfk3E",
        database="storehousedb",
        host="ep-lively-thunder-a5v88os8.us-east-2.aws.neon.tech",
        port="5432",
        ssl="require",
    )
# FastAPI
app = FastAPI()
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# Qdrant client
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
client.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Mock tenant
def get_current_user():
    return {"id": 1, "email": "user1@example.com"}

# Request schema
class QuestionRequest(BaseModel):
    question: str

# text chunking
def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks, start = [], 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks

# embeddings
def embed_text(texts):
    resp = openai.embeddings.create(model="text-embedding-3-small", input=texts)
    return [d.embedding for d in resp.data]

# Upload PDF endpoint
@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    reader = PdfReader(file.file)
    text = "".join([p.extract_text() for p in reader.pages])
    chunks = chunk_text(text)

    # Store metadata in Postgres
    doc = Document(title=file.filename, tenant_id=user["id"])
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Embed + store in Qdrant
    vectors = embed_text(chunks)
    points = [
        PointStruct(id=str(uuid.uuid4()), vector=vectors[i], payload={"text": chunks[i], "doc_id": doc.id})
        for i in range(len(chunks))
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)

    return {"message": f"Uploaded {len(chunks)} chunks from {file.filename}"}

# Ask question endpoint
@app.post("/ask/")
async def ask_question(req: QuestionRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    tenant_id = user["id"]

    #  Check Redis cache
    cached = get_cached_answer(tenant_id, req.question)
    if cached:
        return {"answer": cached, "source": "cache"}

    #  Embed query and search Qdrant
    query_vec = embed_text([req.question])[0]
    results = client.search(collection_name=COLLECTION_NAME, query_vector=query_vec, limit=3)

    # Build citations 
    sources = []
    for r in results:
        doc_id = r.payload.get("doc_id")
        if doc_id:
            doc = db.query(Document).filter_by(id=doc_id, tenant_id=tenant_id).first()
            if doc:
                sources.append({
                    "text": r.payload["text"],
                    "doc_title": doc.title,
                    "doc_id": doc.id
                })

    #  Filter by tenant 
    context_chunks = [r.payload["text"] for r in results if r.payload.get("doc_id") is not None]

    context = "\n\n".join(context_chunks)
    prompt = f"""You are a helpful assistant.
Answer the question in summary based ONLY on this context:

Context:
{context}

Question: {req.question}
Answer:"""

    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    answer_text = resp.choices[0].message.content

    # 4️⃣ Cache answer
    set_cached_answer(tenant_id, req.question, {"answer": answer_text, "sources": context_chunks})

    return {"answer": answer_text, "sources": context_chunks, "source": "fresh"}

# OAuth setup
oauth = OAuth()
CONF_URL = "https://accounts.google.com/.well-known/openid-configuration"
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url=CONF_URL,
    client_kwargs={'scope': 'openid email profile'},
)

# Redirect user to Google login
@app.get("/login")
async def login(request: Request):
    redirect_uri = "http://127.0.0.1:8000/auth/google/secrets"
 
    return await oauth.google.authorize_redirect(request, redirect_uri)

# OAuth callback
@app.get("/auth/google/secrets")
async def auth(request: Request,db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = await oauth.google.userinfo(token=token)  # <-- Fetch user profile
     # Extract details
    email = user_info.get("email")
    name = user_info.get("name")
    picture = user_info.get("picture")

    # Check if user exists
    user = db.query(User).filter_by(email=email).first()
    if not user:
        user = User(email=email, name=name)
        db.add(user)
        db.commit()
        db.refresh(user)

    # Save to session
    request.session["user"] = {"id": user.id, "email": user.email}

    redirect_url = f"http://localhost:3000?email={user.email}&id={user.id}"
    return RedirectResponse(url=redirect_url)

# Get current user from session
@app.get("/me")
async def me(request: Request, db: Session = Depends(get_db)):
    session_user = request.session.get("user")
    if not session_user:
        return {"error": "Not logged in"}

    user = db.query(User).filter_by(id=session_user["id"]).first()
    if not user:
        return {"error": "User not found"}

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        
    }