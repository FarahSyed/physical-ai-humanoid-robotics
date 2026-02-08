import os
import time
from dotenv import load_dotenv
from qdrant_client import QdrantClient
import cohere

# Load environment variables
load_dotenv()

# Initialize clients with the same configuration as main.py
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "humanoid-robotics-book")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

print("Initializing clients...")
qdrant_client = QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY)
co = cohere.Client(COHERE_API_KEY)

print(f"Connected to Qdrant collection: {QDRANT_COLLECTION_NAME}")

# Check collection info
collection_info = qdrant_client.get_collection(QDRANT_COLLECTION_NAME)
print(f"Collection vectors count: {collection_info.points_count}")

# Test search function manually
def test_search(query_text):
    print(f"\nTesting search for: '{query_text}'")

    try:
        # Generate embedding for the query using the same parameters as the pipeline
        response = co.embed(
            texts=[query_text],
            model="embed-english-v3.0",
            input_type="classification",  # Same as pipeline
            truncate="END"
        )
        query_embedding = response.embeddings[0]
        print(f"Query embedding dimension: {len(query_embedding)}")

        # Search in Qdrant
        results = qdrant_client.search(
            collection_name=QDRANT_COLLECTION_NAME,
            query_vector=query_embedding,
            limit=3,
            query_filter=None,
            search_params={"hnsw_ef": 128, "exact": False}
        )

        print(f"Search returned {len(results)} results:")
        for i, hit in enumerate(results):
            payload = hit.payload or {}
            print(f"  {i+1}. ID: {hit.id}")
            print(f"     Score: {hit.score}")
            print(f"     Content preview: {payload.get('content_preview', 'N/A')[:100]}...")
            print(f"     Keys in payload: {list(payload.keys())}")
            print()

        return results
    except Exception as e:
        print(f"Error during search: {e}")
        if "rate" in str(e).lower() or "429" in str(e):
            print("Rate limit hit, waiting before retry...")
            time.sleep(10)  # Wait before retrying
        return []

# Test with a single query first to avoid rate limits
test_query = "ROS 2 Architecture for Humanoids"
print(f"\nTesting single query to avoid rate limits: '{test_query}'")
results = test_search(test_query)

if results:
    print("SUCCESS: Found matching embeddings!")
else:
    print("No results found for this query.")

    # Let's try to see a sample of what's in the collection
    print("\nLet's look at a sample of what's in the collection:")
    try:
        # Use scroll with proper return format for Qdrant
        scroll_result = qdrant_client.scroll(
            collection_name=QDRANT_COLLECTION_NAME,
            limit=3
        )
        # The scroll function returns points and next_page_offset
        points = scroll_result[0] if isinstance(scroll_result, tuple) else scroll_result
        print("Sample points from collection:")
        for i, point in enumerate(points):
            payload = point.payload or {}
            print(f"  {i+1}. ID: {point.id}")
            print(f"     Content preview: {payload.get('content_preview', 'N/A')[:100]}...")
            print(f"     Keys in payload: {list(payload.keys())}")
            print()
    except Exception as e:
        print(f"Error retrieving sample: {e}")
        # Alternative way to get collection info
        try:
            # Get a count of points with specific conditions
            count_result = qdrant_client.count(
                collection_name=QDRANT_COLLECTION_NAME
            )
            print(f"Total points in collection: {count_result.count}")
        except Exception as e2:
            print(f"Error getting count: {e2}")