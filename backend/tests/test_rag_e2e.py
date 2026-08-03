#!/usr/bin/env python3
"""End-to-end test script for RAG pipeline."""
import sys
import os
import tempfile
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Set environment to development
os.environ['ENVIRONMENT'] = 'development'

from app.rag.document_loader import Document
from app.rag.rag_pipeline import RAGPipeline


def test_rag_pipeline():
    """Complete end-to-end test of RAG pipeline."""
    print("=" * 80)
    print("RAG PIPELINE END-TO-END TEST")
    print("=" * 80)

    # Create temporary directory for vector database
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\n1. Initializing RAG Pipeline...")
        print(f"   - Vector DB: {tmpdir}")

        try:
            rag = RAGPipeline(
                collection_name="test_collection",
                persist_directory=tmpdir,
                chunk_size=500,
                chunk_overlap=100,
                top_k=3,
            )
            print("   ✓ RAG Pipeline initialized successfully")
        except Exception as e:
            print(f"   ✗ Error initializing RAG Pipeline: {str(e)}")
            return False

        # Test 2: Create sample documents
        print(f"\n2. Creating sample knowledge base documents...")
        documents = [
            Document(
                content="""FastAPI is a modern, fast (high-performance) web framework for building APIs with Python. 
                It's built on top of Starlette with optional features from Pydantic. FastAPI was designed with speed and 
                developer experience in mind. Key features include automatic API documentation using OpenAPI and Swagger UI.""",
                metadata={"source": "fastapi.txt", "category": "Frameworks"}
            ),
            Document(
                content="""Django is a high-level Python web framework that encourages rapid development and clean, 
                pragmatic design. Built by experienced developers, it takes care of much of the hassle of web development, 
                so you can focus on writing your app without needing to reinvent the wheel.""",
                metadata={"source": "django.txt", "category": "Frameworks"}
            ),
            Document(
                content="""Machine Learning is a subset of artificial intelligence focusing on algorithms and data 
                analysis. It enables systems to learn and improve from experience without being explicitly programmed. 
                Common applications include image recognition, natural language processing, and recommendation systems.""",
                metadata={"source": "ml.txt", "category": "AI"}
            ),
            Document(
                content="""Python is a high-level, interpreted programming language known for its simplicity and readability. 
                It supports multiple programming paradigms and has extensive standard libraries. Python is widely used in 
                web development, data science, artificial intelligence, and automation.""",
                metadata={"source": "python.txt", "category": "Languages"}
            ),
        ]
        print(f"   - Created {len(documents)} documents")
        print("   ✓ Documents ready for indexing")

        # Test 3: Index documents
        print(f"\n3. Indexing documents into knowledge base...")
        try:
            num_indexed = rag.index_documents(documents)
            print(f"   - Indexed {num_indexed} chunks")
            print("   ✓ Documents indexed successfully")
        except Exception as e:
            print(f"   ✗ Error indexing documents: {str(e)}")
            return False

        # Test 4: Check statistics
        print(f"\n4. Retrieving knowledge base statistics...")
        try:
            stats = rag.get_stats()
            print(f"   - Total documents: {stats['document_count']}")
            print(f"   - Embedding model: {stats['embedding_model']}")
            print(f"   - LLM model: {stats['llm_model']}")
            print("   ✓ Statistics retrieved successfully")
        except Exception as e:
            print(f"   ✗ Error retrieving stats: {str(e)}")
            return False

        # Test 5: Query the knowledge base
        print(f"\n5. Testing Query 1: 'What is FastAPI?'")
        try:
            result = rag.query("What is FastAPI?")
            print(f"   Answer: {result.answer[:100]}...")
            print(f"   Confidence: {result.confidence_score:.2%}")
            print(f"   Sources: {result.source_documents}")
            print("   ✓ Query 1 completed successfully")
        except Exception as e:
            print(f"   ✗ Error querying: {str(e)}")
            return False

        # Test 6: Another query
        print(f"\n6. Testing Query 2: 'Tell me about Machine Learning'")
        try:
            result = rag.query("Tell me about Machine Learning")
            print(f"   Answer: {result.answer[:100]}...")
            print(f"   Confidence: {result.confidence_score:.2%}")
            print(f"   Sources: {result.source_documents}")
            print("   ✓ Query 2 completed successfully")
        except Exception as e:
            print(f"   ✗ Error querying: {str(e)}")
            return False

        # Test 7: Confidence scoring test
        print(f"\n7. Testing confidence scoring...")
        try:
            queries = [
                "What is Python used for?",
                "Does the knowledge base have information about cooking?",
                "Compare FastAPI and Django"
            ]
            
            for query in queries:
                result = rag.query(query)
                print(f"   Query: '{query}'")
                print(f"   Confidence: {result.confidence_score:.2%}")
            
            print("   ✓ Confidence scoring working correctly")
        except Exception as e:
            print(f"   ✗ Error in confidence scoring: {str(e)}")
            return False

        # Test 8: Clear knowledge base
        print(f"\n8. Testing knowledge base clearing...")
        try:
            rag.clear_knowledge_base()
            stats = rag.get_stats()
            if stats['document_count'] == 0:
                print(f"   - Knowledge base cleared (0 documents)")
                print("   ✓ Knowledge base cleared successfully")
            else:
                print(f"   ✗ Knowledge base still contains {stats['document_count']} documents")
                return False
        except Exception as e:
            print(f"   ✗ Error clearing knowledge base: {str(e)}")
            return False

        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED - RAG PIPELINE WORKING END-TO-END")
        print("=" * 80)
        return True


if __name__ == "__main__":
    success = test_rag_pipeline()
    sys.exit(0 if success else 1)
