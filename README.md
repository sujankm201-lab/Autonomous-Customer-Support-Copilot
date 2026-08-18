# Autonomous Customer Support Copilot

An AI-powered customer support system that combines Retrieval-Augmented Generation (RAG), intelligent ticket management, intent detection, smart ticket routing, and human escalation to provide efficient customer support.

## Project Overview

The Autonomous Customer Support Copilot is designed to help organizations automate customer support operations.

Users can ask questions using a natural-language AI chat interface. The system searches the company's knowledge base using semantic search and generates relevant answers using Retrieval-Augmented Generation (RAG).

If a customer issue cannot be resolved automatically, the system can create and route a support ticket to the appropriate department.

## Key Features

- User Registration and Login
- JWT Authentication
- AI Customer Support Chat
- Retrieval-Augmented Generation (RAG)
- Company Knowledge Base
- Document Indexing
- PDF, TXT and Markdown Document Support
- Sentence Transformer Embeddings
- ChromaDB Vector Database
- AI Answer Generation
- Confidence Scoring
- Source Document Display
- Conversation History
- Intent Detection
- Smart Ticket Routing
- Human Escalation
- Complete Ticket Management
- Screenshot/PDF Attachment Support
- Feedback Learning Loop
- Dashboard
- Knowledge Base Management
- RAG Status Monitoring

## System Architecture

```text
User
  |
  v
React Frontend
  |
  v
FastAPI Backend
  |
  +----------------------+
  |                      |
  v                      v
MongoDB               RAG Pipeline
                          |
                          v
                    Document Loader
                          |
                          v
                     Text Chunker
                          |
                          v
                 Sentence Transformers
                          |
                          v
                      ChromaDB
                          |
                          v
                    Relevant Context
                          |
                          v
                       LLM
                          |
                          v
                  AI Generated Answer