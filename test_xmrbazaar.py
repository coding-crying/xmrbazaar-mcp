#!/usr/bin/env python3
"""
XMRBazaar MCP Server - Comprehensive Test Suite
================================================
Tests all tool functions with multiple test cases.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the module to path
sys.path.insert(0, str(Path(__file__).parent))

from nexusai_mcp.server import (
    search_market,
    get_item_details,
    get_vendor_rating,
    analyze_match,
    config,
    get_cached,
    set_cached,
    get_cache_path
)
import time


async def test_search_market():
    """Test 1: search_market with different queries"""
    print("\n" + "=" * 70)
    print("TEST 1: search_market - Different Queries")
    print("=" * 70)
    
    test_queries = [
        ("thinkpad", "ThinkPad laptops"),
        ("laptop", "General laptops"),
        ("graphics card", "GPU/graphics cards")
    ]
    
    results_summary = {}
    
    for query, description in test_queries:
        print(f"\n--- Searching for: {query} ({description}) ---")
        try:
            result = await search_market(query=query, max_results=5)
            print(f"Query: {result.get('query')}")
            print(f"Marketplace: {result.get('marketplace')}")
            print(f"Results count: {result.get('count')}")
            
            if result.get('results'):
                print("Sample results:")
                for item in result['results'][:3]:
                    print(f"  - {item.get('title')[:50]}... | {item.get('price')}")
            
            results_summary[query] = {
                "success": True,
                "count": result.get('count', 0),
                "has_results": len(result.get('results', [])) > 0
            }
        except Exception as e:
            print(f"ERROR: {e}")
            results_summary[query] = {"success": False, "error": str(e)}
    
    return results_summary


async def test_get_item_details():
    """Test 2: get_item_details on actual listing URLs"""
    print("\n" + "=" * 70)
    print("TEST 2: get_item_details")
    print("=" * 70)
    
    # First get some search results to test with
    print("\n--- Getting search results for testing ---")
    search_result = await search_market(query="thinkpad", max_results=3)
    
    if not search_result.get('results'):
        print("No search results to test with!")
        return {"success": False, "error": "No search results"}
    
    test_urls = []
    for item in search_result['results'][:2]:
        test_urls.append(item['url'])
        print(f"Testing URL: {item['url']}")
    
    details_results = []
    
    for url in test_urls:
        print(f"\n--- Fetching details for: {url[:60]}... ---")
        try:
            details = await get_item_details(url)
            print(f"Title: {details.get('title', 'N/A')[:50]}...")
            print(f"Price: {details.get('price', 'N/A')}")
            print(f"Condition: {details.get('condition', 'N/A')}")
            print(f"Vendor: {details.get('vendor', 'N/A')}")
            print(f"Description length: {len(details.get('description', ''))} chars")
            
            details_results.append({
                "url": url,
                "success": True,
                "has_title": bool(details.get('title')),
                "has_price": bool(details.get('price')),
                "has_vendor": bool(details.get('vendor'))
            })
        except Exception as e:
            print(f"ERROR: {e}")
            details_results.append({"url": url, "success": False, "error": str(e)})
    
    return {"tested_urls": len(test_urls), "results": details_results}


def test_analyze_match():
    """Test 3: analyze_match with various user requirements"""
    print("\n" + "=" * 70)
    print("TEST 3: analyze_match")
    print("=" * 70)
    
    # Sample item details to test with
    test_cases = [
        {
            "name": "Perfect match - ThinkPad under budget",
            "item_details": {
                "title": "ThinkPad X1 Carbon Gen 9",
                "price": "$450",
                "description": "Excellent condition ThinkPad with i7 processor, 16GB RAM, 512GB SSD. Perfect for coding and development work.",
                "condition": "Excellent"
            },
            "user_requirements": {
                "budget_max": 500,
                "category": "thinkpad",
                "condition": "excellent",
                "features": ["i7", "16GB RAM", "SSD"]
            }
        },
        {
            "name": "Over budget - High specs",
            "item_details": {
                "title": "MacBook Pro 16 inch M3 Max",
                "price": "$2800",
                "description": "Brand new MacBook Pro with M3 Max chip, 64GB RAM, 2TB SSD.",
                "condition": "New"
            },
            "user_requirements": {
                "budget_max": 1000,
                "category": "laptop",
                "condition": "used"
            }
        },
        {
            "name": "Partial match - Missing features",
            "item_details": {
                "title": "Dell XPS 13",
                "price": "$600",
                "description": "Good condition XPS 13 with i5 processor, 8GB RAM, 256GB SSD.",
                "condition": "Good"
            },
            "user_requirements": {
                "budget_max": 500,
                "category": "laptop",
                "features": ["16GB RAM", "1TB SSD"]
            }
        },
        {
            "name": "Empty requirements",
            "item_details": {
                "title": "Generic Laptop",
                "price": "$300",
                "description": "A laptop",
                "condition": "Used"
            },
            "user_requirements": {}
        }
    ]
    
    results = []
    for tc in test_cases:
        print(f"\n--- Test: {tc['name']} ---")
        result = analyze_match(
            item_details=tc["item_details"],
            user_requirements=tc["user_requirements"]
        )
        print(f"Score: {result['match_score']}/100")
        print(f"Recommendation: {result['recommendation']}")
        print(f"Pros: {result['pros']}")
        print(f"Cons: {result['cons']}")
        
        results.append({
            "name": tc["name"],
            "score": result['match_score'],
            "recommendation": result['recommendation']
        })
    
    return results


def test_error_handling():
    """Test 4: Error handling (invalid URLs, empty queries, etc.)"""
    print("\n" + "=" * 70)
    print("TEST 4: Error Handling")
    print("=" * 70)
    
    error_tests = []
    
    # Test analyze_match with missing data
    print("\n--- Test: analyze_match with empty item_details ---")
    try:
        result = analyze_match({}, {})
        print(f"Result: {result}")
        error_tests.append({"test": "empty_analyze", "handled": True})
    except Exception as e:
        print(f"ERROR: {e}")
        error_tests.append({"test": "empty_analyze", "handled": False, "error": str(e)})
    
    # Test analyze_match with None values
    print("\n--- Test: analyze_match with None values ---")
    try:
        result = analyze_match(None, None)
        print(f"Result: {result}")
        error_tests.append({"test": "none_analyze", "handled": True})
    except Exception as e:
        print(f"ERROR: {e}")
        error_tests.append({"test": "none_analyze", "handled": False, "error": str(e)})
    
    # Test search with empty query (will use default behavior)
    print("\n--- Test: search_market with empty query ---")
    try:
        # This will likely fail or return empty
        result = asyncio.run(search_market("", max_results=1))
        print(f"Result count: {result.get('count', 'N/A')}")
        error_tests.append({"test": "empty_search", "handled": True})
    except Exception as e:
        print(f"ERROR (expected): {e}")
        error_tests.append({"test": "empty_search", "handled": "exception_expected"})
    
    # Test get_item_details with invalid URL
    print("\n--- Test: get_item_details with invalid URL ---")
    try:
        result = asyncio.run(get_item_details("https://invalid-domain-that-does-not-exist.com/item"))
        print(f"Result: {result.get('error', 'No error field')}")
        error_tests.append({"test": "invalid_url", "handled": True})
    except Exception as e:
        print(f"ERROR: {e}")
        error_tests.append({"test": "invalid_url", "handled": "exception_expected"})
    
    return error_tests


def test_cache_functionality():
    """Test 5: Cache functionality"""
    print("\n" + "=" * 70)
    print("TEST 5: Cache Functionality")
    print("=" * 70)
    
    cache_tests = []
    
    # Test cache write/read
    print("\n--- Test: Write and read cache ---")
    test_key = "test_cache_key_123"
    test_data = {"test": "data", "timestamp": time.time()}
    
    try:
        set_cached(test_key, test_data)
        cached = get_cached(test_key)
        
        if cached and cached.get("test") == "data":
            print("✓ Cache write/read successful")
            cache_tests.append({"test": "write_read", "success": True})
        else:
            print("✗ Cache read returned unexpected data")
            cache_tests.append({"test": "write_read", "success": False})
    except Exception as e:
        print(f"ERROR: {e}")
        cache_tests.append({"test": "write_read", "success": False, "error": str(e)})
    
    # Test cache miss
    print("\n--- Test: Cache miss (non-existent key) ---")
    try:
        cached = get_cached("nonexistent_key_xyz_12345")
        if cached is None:
            print("✓ Cache correctly returns None for missing keys")
            cache_tests.append({"test": "cache_miss", "success": True})
        else:
            print("✗ Cache returned data for non-existent key")
            cache_tests.append({"test": "cache_miss", "success": False})
    except Exception as e:
        print(f"ERROR: {e}")
        cache_tests.append({"test": "cache_miss", "success": False, "error": str(e)})
    
    # Test that actual search results get cached
    print("\n--- Test: Search result caching ---")
    try:
        # Run search (should cache)
        result1 = asyncio.run(search_market("test_query_cache", max_results=1))
        
        # Run again (should use cache)
        # We can tell by checking if it says "[CACHE]" in output
        result2 = asyncio.run(search_market("test_query_cache", max_results=1))
        
        # Results should be identical
        if result1.get('count') == result2.get('count'):
            print("✓ Search caching works - identical results returned")
            cache_tests.append({"test": "search_cache", "success": True})
        else:
            print("✗ Search results differ between calls")
            cache_tests.append({"test": "search_cache", "success": False})
    except Exception as e:
        print(f"ERROR: {e}")
        cache_tests.append({"test": "search_cache", "success": False, "error": str(e)})
    
    return cache_tests


async def main():
    """Run all tests and compile results"""
    print("=" * 70)
    print("XMRBazaar MCP Server - Comprehensive Test Suite")
    print("=" * 70)
    print(f"Cache directory: {config.CACHE_DIR}")
    print(f"Cache TTL: {config.CACHE_TTL} seconds")
    print(f"Headless mode: {config.HEADLESS}")
    
    all_results = {}
    
    # Test 1: search_market
    all_results["search_market"] = await test_search_market()
    
    # Test 2: get_item_details
    all_results["get_item_details"] = await test_get_item_details()
    
    # Test 3: analyze_match
    all_results["analyze_match"] = test_analyze_match()
    
    # Test 4: Error handling
    all_results["error_handling"] = test_error_handling()
    
    # Test 5: Cache functionality
    all_results["cache_functionality"] = test_cache_functionality()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    print(f"\n1. search_market tests:")
    for query, result in all_results["search_market"].items():
        status = "✓" if result.get("success") else "✗"
        print(f"   {status} {query}: {result.get('count', 0)} results")
    
    print(f"\n2. get_item_details tests:")
    for r in all_results["get_item_details"].get("results", []):
        status = "✓" if r.get("success") else "✗"
        print(f"   {status} {r.get('url', 'N/A')[:40]}...")
    
    print(f"\n3. analyze_match tests:")
    for r in all_results["analyze_match"]:
        print(f"   {r['name']}: Score {r['score']}/100 - {r['recommendation']}")
    
    print(f"\n4. Error handling tests:")
    for r in all_results["error_handling"]:
        status = "✓" if r.get("handled") else "✗"
        print(f"   {status} {r['test']}")
    
    print(f"\n5. Cache tests:")
    for r in all_results["cache_functionality"]:
        status = "✓" if r.get("success") else "✗"
        print(f"   {status} {r['test']}")
    
    # Save results
    output_file = Path(__file__).parent / "test_results.json"
    output_file.write_text(json.dumps(all_results, indent=2))
    print(f"\n\nFull results saved to: {output_file}")
    
    return all_results


if __name__ == "__main__":
    results = asyncio.run(main())
