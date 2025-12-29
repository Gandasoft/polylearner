#!/usr/bin/env python3
"""
Test script for vector embeddings and calendar integration features
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_embeddings():
    """Test the embeddings endpoint"""
    print("🧪 Testing embeddings endpoint...")
    
    response = requests.get(f"{BASE_URL}/analytics/embeddings")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Embeddings generated for {data['total_tasks']} tasks")
        print(f"✅ Embedding dimension: {data['embedding_dimension']}")
        
        if data['embeddings']:
            first_task = list(data['embeddings'].keys())[0]
            sample = data['embeddings'][first_task]
            print(f"✅ Sample embedding (task {first_task}):")
            print(f"   - Dimension: {sample['dimension']}")
            print(f"   - First 5 values: {sample['vector'][:5]}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False

def test_intelligent_schedule():
    """Test intelligent schedule with embeddings"""
    print("\n🧪 Testing intelligent schedule with embeddings...")
    
    response = requests.get(
        f"{BASE_URL}/analytics/schedule/intelligent",
        params={"include_embeddings": True}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Schedule generated with {data['total_blocks']} blocks")
        print(f"✅ Total hours: {data['total_hours']}")
        print(f"✅ Embeddings generated: {data['embeddings_generated']}")
        print(f"✅ Embedding dimension: {data['embedding_dimension']}")
        print(f"✅ Cognitive tax score: {data['cognitive_metrics']['cognitive_tax_score']}")
        
        if data['schedule'] and len(data['schedule']) > 0:
            first_block = data['schedule'][0]
            if 'embedding_sample' in first_block:
                print(f"✅ Sample schedule block includes embedding sample:")
                print(f"   - Task: {first_block['task_title']}")
                print(f"   - Embedding sample: {first_block['embedding_sample']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False

def test_endpoints_exist():
    """Verify new endpoints are registered"""
    print("\n🧪 Checking endpoint registration...")
    
    response = requests.get(f"{BASE_URL}/openapi.json")
    if response.status_code == 200:
        openapi = response.json()
        paths = openapi.get('paths', {})
        
        required_endpoints = [
            "/analytics/embeddings",
            "/analytics/schedule/intelligent/create-events"
        ]
        
        for endpoint in required_endpoints:
            if endpoint in paths:
                print(f"✅ Endpoint registered: {endpoint}")
            else:
                print(f"❌ Endpoint missing: {endpoint}")
                return False
        return True
    else:
        print(f"❌ Failed to fetch OpenAPI spec")
        return False

def main():
    print("=" * 60)
    print("Vector Embeddings & Calendar Integration Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Endpoint registration
    results.append(("Endpoint Registration", test_endpoints_exist()))
    
    # Test 2: Embeddings
    results.append(("Vector Embeddings", test_embeddings()))
    
    # Test 3: Intelligent Schedule
    results.append(("Intelligent Schedule", test_intelligent_schedule()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    exit(main())
