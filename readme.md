# RAG Knowledge Retrieval System

## Overview

This project is a **Retrieval-Augmented Generation (RAG) system** that allows users to upload documents, store their content in a vector database, and ask questions about the documents. Answers are generated using a large language model (LLM) grounded in the document content, with citations included.  

The system demonstrates a **full end-to-end workflow** from document ingestion to answer generation with caching and multi-tenant support.

---

## Features

- **Document Ingestion:** Upload PDFs or provide URLs. Extracts text and stores metadata in Postgres.  
- **Vector Indexing:** Generates embeddings for document chunks and stores them in Qdrant.  
- **Query & Retrieval:** Searches Qdrant for relevant document chunks based on user queries.  
- **Answer Generation:** Uses an LLM (OpenAI GPT or Claude) to answer questions grounded in retrieved documents.  
- **Caching:** Redis caches frequent queries and generated answers for faster performance.  
- **Authentication & Multi-Tenancy:** Users log in via Google OAuth. Data is scoped per tenant.  
- **Minimal Frontend:** Web interface for document upload and chat-style querying.  
- **Production-Ready Setup:** Docker Compose configuration for all services.

---

## Tech Stack

- **Backend:** FastAPI  
- **Database:** PostgreSQL + SQLAlchemy + Alembic  
- **Caching:** Redis  
- **Vector Database:** Qdrant (or alternative)  
- **Authentication:** Google OAuth 2.0  
- **LLM Integration:** OpenAI / Claude  
- **Frontend:** Minimal (React/Next.js or any stack)  
- **Containerization:** Docker + Docker Compose  

---

## Architecture

