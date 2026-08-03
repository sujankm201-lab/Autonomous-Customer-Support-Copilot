#!/usr/bin/env python3
"""Simplified end-to-end test for RAG components without heavy ML models."""
import sys
import os
from pathlib import Path
import tempfile

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Test imports without triggering heavy ML loads
def test_imports():
    """Test that all RAG modules can be imported."""
    print("=" * 80)
    print("TESTING RAG MODULE IMPORTS")
    print("=" * 80)
    
    try:
        print("\n1. Testing document_loader import...")
        from app.rag.document_loader import DocumentLoader, Document
        print("   ✓ document_loader imported successfully")
        
        print("\n2. Testing text_chunker import...")
        from app.rag.text_chunker import TextChunker, Chunk
        print("   ✓ text_chunker imported successfully")
        
        print("\n3. Testing prompts import...")
        from app.rag.prompts import get_prompt, AVAILABLE_PROMPTS
        print(f"   ✓ prompts imported successfully ({len(AVAILABLE_PROMPTS)} templates)")
        
        print("\n4. Testing llm_service import...")
        from app.rag.llm_service import LLMService, MockLLM
        print("   ✓ llm_service imported successfully")
        
        print("\n5. Testing config import...")
        from app.rag.config import CHUNK_SIZE, COLLECTION_NAME
        print(f"   ✓ config imported successfully (chunk_size={CHUNK_SIZE})")
        
        return True
    except ImportError as e:
        print(f"   ✗ Import error: {str(e)}")
        return False


def test_text_chunking():
    """Test text chunking without ML models."""
    print("\n" + "=" * 80)
    print("TESTING TEXT CHUNKING")
    print("=" * 80)
    
    try:
        from app.rag.text_chunker import TextChunker
        
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        text = "This is a test document. " * 10
        chunks = chunker.chunk_text(text)
        
        print(f"\n✓ Created {len(chunks)} chunks from text")
        print(f"  - First chunk: {chunks[0].text[:50]}...")
        print(f"  - Chunk size range: {min(len(c.text) for c in chunks)} - {max(len(c.text) for c in chunks)} chars")
        
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_mock_llm():
    """Test Mock LLM without API keys."""
    print("\n" + "=" * 80)
    print("TESTING MOCK LLM SERVICE")
    print("=" * 80)
    
    try:
        from app.rag.llm_service import MockLLM
        
        llm = MockLLM("mock-model", 0.7, 1000)
        
        # Test simple response
        response1 = llm.predict("What is the answer to the question?")
        print(f"\n✓ Simple response: {response1[:60]}...")
        
        # Test confidence scoring
        response2 = llm.predict("confidence")
        print(f"✓ Confidence response: {response2[:60]}...")
        
        # Test follow-up generation
        response3 = llm.predict("follow-up questions")
        print(f"✓ Follow-up response: {response3[:60]}...")
        
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_document_loader():
    """Test document loading."""
    print("\n" + "=" * 80)
    print("TESTING DOCUMENT LOADER")
    print("=" * 80)
    
    try:
        from app.rag.document_loader import DocumentLoader, Document
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("This is a test document content.")
            
            # Test loading
            loader = DocumentLoader()
            doc = loader.load_file(str(test_file))
            
            if doc:
                print(f"\n✓ Loaded document from {test_file.name}")
                print(f"  - Content length: {len(doc.content)} chars")
                print(f"  - Metadata: {doc.metadata}")
            else:
                print(f"\n✗ Failed to load document")
                return False
            
            # Test loading directory
            docs = loader.load_directory(tmpdir, file_types=['.txt'])
            print(f"✓ Loaded {len(docs)} documents from directory")
            
            return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_prompts():
    """Test prompt templates."""
    print("\n" + "=" * 80)
    print("TESTING PROMPT TEMPLATES")
    print("=" * 80)
    
    try:
        from app.rag.prompts import get_prompt, AVAILABLE_PROMPTS
        
        print(f"\n✓ Available prompts: {list(AVAILABLE_PROMPTS.keys())}")
        
        # Test fetching prompts
        qa_prompt = get_prompt("qa")
        detailed_qa = get_prompt("detailed_qa")
        
        print(f"✓ QA Prompt variables: {qa_prompt.input_variables}")
        print(f"✓ Detailed QA Prompt variables: {detailed_qa.input_variables}")
        
        # Test invalid prompt
        try:
            get_prompt("invalid_prompt")
            print("✗ Should have raised ValueError for invalid prompt")
            return False
        except ValueError:
            print("✓ Correctly raised ValueError for invalid prompt")
        
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_rag_components():
    """Test individual RAG components without full pipeline."""
    print("\n" + "=" * 80)
    print("TESTING RAG COMPONENTS")
    print("=" * 80)
    
    try:
        from app.rag.document_loader import Document
        from app.rag.text_chunker import TextChunker
        from app.rag.prompts import get_prompt
        from app.rag.llm_service import MockLLM
        
        # Create sample documents
        docs = [
            Document(
                content="Python is a programming language",
                metadata={"source": "python.txt"}
            ),
            Document(
                content="Machine Learning is AI technology",
                metadata={"source": "ml.txt"}
            ),
        ]
        
        # Chunk documents
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        chunks = chunker.chunk_documents(docs)
        print(f"\n✓ Created {len(chunks)} chunks from {len(docs)} documents")
        
        # Test LLM
        llm = MockLLM("test", 0.7, 1000)
        answer = llm.predict("What is Python?")
        print(f"✓ LLM generated response: {answer[:50]}...")
        
        # Test prompts
        qa_prompt = get_prompt("qa")
        formatted = qa_prompt.format(context="Test context", question="Test question?")
        print(f"✓ Formatted prompt template (length: {len(formatted)} chars)")
        
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    tests = [
        ("Module Imports", test_imports),
        ("Text Chunking", test_text_chunking),
        ("Mock LLM", test_mock_llm),
        ("Document Loader", test_document_loader),
        ("Prompt Templates", test_prompts),
        ("RAG Components", test_rag_components),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' failed with exception: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 80)
    
    return all(result for _, result in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
