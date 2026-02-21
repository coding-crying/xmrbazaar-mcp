#!/usr/bin/env python3
"""
NexusAI MCP Server - Multi-Tool Architecture
==============================================
A research-focused shopping assistant that gives LLMs tools to deeply evaluate products.

Tools:
1. search_market  - Broad search to find initial listings
2. get_item_details - Deep dive into specific product pages
3. get_vendor_rating - Verify seller trust/reputation

This architecture allows the LLM to chain tools together for human-like research.
"""

import asyncio
import os
import re
import json
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class Config:
    """NexusAI MCP Server configuration."""
    
    # Target marketplaces (XMR Bazaars, etc.)
    MARKETS: list[str] = None
    
    # Browser settings
    HEADLESS: bool = True
    TIMEOUT: int = 30000
    
    # Cache settings
    CACHE_DIR: Path = Path.home() / ".cache" / "nexusai"
    CACHE_TTL: int = 3600  # seconds
    
    def __post_init__(self):
        if self.MARKETS is None:
            self.MARKETS = [
                "xmr.bazaar",
                # Add more markets here
            ]
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)


config = Config()


# ============================================================================
# Cache Utilities
# ============================================================================

def get_cache_path(key: str) -> Path:
    """Get cache file path for a given key."""
    safe_key = re.sub(r'[^a-zA-Z0-9_-]', '_', key)
    return config.CACHE_DIR / f"{safe_key}.json"


def get_cached(key: str) -> Optional[dict]:
    """Get cached data if fresh."""
    cache_path = get_cache_path(key)
    if not cache_path.exists():
        return None
    
    import time
    age = time.time() - cache_path.stat().st_mtime
    if age > config.CACHE_TTL:
        return None
    
    try:
        return json.loads(cache_path.read_text())
    except:
        return None


def set_cached(key: str, data: dict) -> None:
    """Store data in cache."""
    cache_path = get_cache_path(key)
    cache_path.write_text(json.dumps(data, indent=2))


# ============================================================================
# Tool 1: Broad Search
# ============================================================================

async def search_market(
    query: str,
    marketplace: str = "xmrbazaar.com",
    max_results: int = 15
) -> dict:
    """
    Search the marketplace for listings matching a keyword.
    
    WHEN TO USE:
    - User asks about products in a category (e.g., "any ThinkPads for sale?")
    - Initial research phase to discover what's available
    - User provides a general interest area
    
    HOW TO USE:
    - Start with broad search terms matching user's interest
    - Review returned titles and prices to identify candidates
    - Call get_item_details on promising listings
    
    Returns: List of items with title, price, URL, and thumbnail.
    """
    cache_key = f"search_{marketplace}_{query}"
    cached = get_cached(cache_key)
    if cached:
        print(f"[CACHE] Returning cached search for: {query}")
        return cached
    
    print(f"[SEARCH] Querying {marketplace} for: {query}")
    
    # Build search URL based on marketplace
    if marketplace == "xmrbazaar.com":
        # XMRBazaar uses /search/ with query param
        search_url = f"https://{marketplace}/search/?q={query}"
    elif marketplace == "xmr.bazaar":
        search_url = f"https://xmr.bazaar/?q={query}&sort=price_asc"
    else:
        search_url = f"https://{marketplace}/search?q={query}"
    
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=config.HEADLESS)
        page = await browser.new_page()
        
        try:
            await page.goto(search_url, timeout=config.TIMEOUT)
            await page.wait_for_load_state("networkidle", timeout=15000)
            
            # Extract listings - XMRBazaar specific selectors
            listings = await page.query_selector_all(".listings-product")
            
            for listing in listings[:max_results]:
                try:
                    # XMRBazaar selectors
                    title_elem = await listing.query_selector(".listing-title-text")
                    title = await title_elem.inner_text() if title_elem else None
                    
                    price_elem = await listing.query_selector(".listings-product-price-value")
                    price = await price_elem.inner_text() if price_elem else "N/A"
                    
                    link = await listing.query_selector("a")
                    url = await link.get_attribute("href") if link else ""
                    
                    # Get thumbnail
                    img = await listing.query_selector(".listings-product-img img")
                    thumbnail = await img.get_attribute("src") if img else None
                    
                    if title and url:
                        results.append({
                            "title": title.strip(),
                            "price": price.strip() if price else "N/A",
                            "url": f"https://{marketplace}{url}" if url.startswith("/") else url,
                            "marketplace": marketplace,
                            "thumbnail": thumbnail
                        })
                except Exception as e:
                    print(f"[WARN] Skipped listing: {e}")
                    continue
                    
        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
        finally:
            await browser.close()
    
    output = {
        "query": query,
        "marketplace": marketplace,
        "count": len(results),
        "results": results
    }
    
    set_cached(cache_key, output)
    return output


# ============================================================================
# Tool 2: Deep Dive - Item Details
# ============================================================================

async def get_item_details(url: str) -> dict:
    """
    Scrape full details from a specific product page.
    
    WHEN TO USE:
    - After search_market returns promising candidates
    - User asks about a specific listing ("what's the condition?")
    - Need to verify specs, condition, shipping before recommending
    - User expresses interest in a specific item
    
    HOW TO USE:
    - Pass the URL from a search result
    - Review description, condition, seller info
    - Check vendor rating if available
    
    Returns: Complete product info including title, price, description, specs, condition, shipping, seller.
    """
    cache_key = f"details_{hash(url)}"
    cached = get_cached(cache_key)
    if cached:
        print(f"[CACHE] Returning cached details for: {url}")
        return cached
    
    print(f"[DETAILS] Fetching: {url}")
    
    details = {
        "url": url,
        "title": None,
        "price": None,
        "description": None,
        "specs": {},
        "condition": None,
        "shipping": None,
        "vendor": None,
        "vendor_url": None,
        "images": []
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=config.HEADLESS)
        page = await browser.new_page()
        
        try:
            await page.goto(url, timeout=config.TIMEOUT)
            await page.wait_for_load_state("networkidle", timeout=15000)
            
            # Extract title - XMRBazaar specific
            title_elem = await page.query_selector(".listings-product-title, h1, [class*='title']")
            if title_elem:
                details["title"] = await title_elem.inner_text()
            
            # Extract price - XMRBazaar specific
            price_elem = await page.query_selector(".listings-product-price-value, [class*='price']")
            if price_elem:
                details["price"] = await price_elem.inner_text()
            
            # Extract description - XMRBazaar specific
            desc_elem = await page.query_selector(".listing-description, [class*='description'], .content")
            if desc_elem:
                details["description"] = await desc_elem.inner_text()
            
            # Extract specs (key-value pairs) - XMRBazaar uses categories
            cat_elem = await page.query_selector(".listing-category, [class*='category']")
            if cat_elem:
                details["specs"]["Category"] = await cat_elem.inner_text()
            
            # Extract condition
            cond_elem = await page.query_selector(".listing-condition, [class*='condition']")
            if cond_elem:
                details["condition"] = await cond_elem.inner_text()
            
            # Extract shipping/delivery
            delivery_elem = await page.query_selector(".listing-delivery, [class*='delivery'], .listing-location")
            if delivery_elem:
                details["shipping"] = await delivery_elem.inner_text()
            
            # Extract vendor info - XMRBazaar specific
            vendor_elem = await page.query_selector(".listings-product-username, [class*='username'], .seller-name")
            if vendor_elem:
                details["vendor"] = await vendor_elem.inner_text()
                vendor_link = await vendor_elem.get_attribute("href")
                if vendor_link:
                    details["vendor_url"] = f"https://xmrbazaar.com{vendor_link}" if vendor_link.startswith("/") else vendor_link
            
            # Extract images
            img_elems = await page.query_selector_all("img[class*='product'], .gallery img")
            for img in img_elems[:10]:
                src = await img.get_attribute("src")
                if src:
                    details["images"].append(src)
                    
        except Exception as e:
            print(f"[ERROR] Details fetch failed: {e}")
            details["error"] = str(e)
        finally:
            await browser.close()
    
    set_cached(cache_key, details)
    return details


# ============================================================================
# Tool 3: Trust Check - Vendor Rating
# ============================================================================

async def get_vendor_rating(vendor_url: str) -> dict:
    """
    Verify seller reputation from their profile page.
    
    WHEN TO USE:
    - Before recommending any listing to user
    - User asks "is this seller trustworthy?"
    - Large purchase amounts or first-time transaction
    - Any time you want to verify seller credibility
    
    HOW TO USE:
    - Pass the vendor_url from get_item_details
    - Check rating (4+ stars is good)
    - Verify trade count (more = more experienced)
    - Review trust level indicators
    
    Returns: Rating, completed trades, reviews, trust score.
    """
    cache_key = f"vendor_{hash(vendor_url)}"
    cached = get_cached(cache_key)
    if cached:
        print(f"[CACHE] Returning cached vendor for: {vendor_url}")
        return cached
    
    print(f"[VENDOR] Checking: {vendor_url}")
    
    vendor_info = {
        "url": vendor_url,
        "username": None,
        "rating": None,
        "total_trades": None,
        "member_since": None,
        "reviews": [],
        "trust_level": None
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=config.HEADLESS)
        page = await browser.new_page()
        
        try:
            await page.goto(vendor_url, timeout=config.TIMEOUT)
            await page.wait_for_load_state("networkidle", timeout=15000)
            
            # Username
            user_elem = await page.query_selector("h1, [class*='username'], .profile-name")
            if user_elem:
                vendor_info["username"] = await user_elem.inner_text()
            
            # Rating stars
            stars_elem = await page.query_selector("[class*='rating'], .stars")
            if stars_elem:
                vendor_info["rating"] = await stars_elem.inner_text()
            
            # Total trades
            trades_elem = await page.query_selector("[class*='trades'], .completed")
            if trades_elem:
                vendor_info["total_trades"] = await trades_elem.inner_text()
            
            # Member since
            since_elem = await page.query_selector("[class*='joined'], .member-since")
            if since_elem:
                vendor_info["member_since"] = await since_elem.inner_text()
            
            # Recent reviews
            review_elems = await page.query_selector_all("[class*='review']")[:5]
            for review in review_elems:
                review_text = await review.inner_text()
                if review_text:
                    vendor_info["reviews"].append(review_text)
            
            # Calculate trust level
            if vendor_info["total_trades"]:
                try:
                    trades = int(re.search(r'\d+', vendor_info["total_trades"]).group())
                    if trades > 100:
                        vendor_info["trust_level"] = "HIGH"
                    elif trades > 20:
                        vendor_info["trust_level"] = "MEDIUM"
                    else:
                        vendor_info["trust_level"] = "LOW"
                except:
                    pass
                    
        except Exception as e:
            print(f"[ERROR] Vendor check failed: {e}")
            vendor_info["error"] = str(e)
        finally:
            await browser.close()
    
    set_cached(cache_key, vendor_info)
    return vendor_info


# ============================================================================
# Tool 4: Match Analysis - Evaluate listing vs user needs
# ============================================================================

def analyze_match(item_details: dict, user_requirements: dict) -> dict:
    """
    Analyze how well a listing matches user requirements.
    
    WHEN TO USE:
    - After getting item details, before presenting to user
    - User has specific needs (budget, condition, features)
    - Multiple candidates exist and you need to rank/filter
    - User asks "which is best for me?"
    
    HOW TO USE:
    - Call search_market to find candidates
    - Call get_item_details on promising ones
    - Call this to score each against user needs
    - Present ranked results with match reasoning
    
    INPUT:
    - item_details: Output from get_item_details
    - user_requirements: Dict with keys like:
      - budget_max: Maximum price user will pay
      - category: What they're looking for
      - condition: Preferred condition (new, like new, used)
      - features: List of required features
    
    Returns: Match score (0-100), pros, cons, recommendation.
    """
    
    # Handle None inputs
    if item_details is None:
        item_details = {}
    if user_requirements is None:
        user_requirements = {}
    
    score = 0
    max_score = 100
    pros = []
    cons = []
    
    title = item_details.get("title", "") or ""
    price = item_details.get("price", "0") or "0"
    description = item_details.get("description", "") or ""
    
    # Extract price value
    price_match = re.search(r'\$?([\d,]+)', str(price))
    price_value = int(price_match.group(1).replace(",", "")) if price_match else 0
    
    # Budget check (40 points)
    budget_max = user_requirements.get("budget_max")
    if budget_max:
        if price_value <= budget_max:
            score += 40
            pros.append(f"Within budget (${price_value} <= ${budget_max})")
        else:
            score -= 20
            cons.append(f"Over budget (${price_value} > ${budget_max})")
    else:
        score += 20  # No budget specified = neutral
    
    # Category/keyword match (30 points)
    category = user_requirements.get("category", "").lower()
    if category:
        if category in title or category in description:
            score += 30
            pros.append(f"Matches category: {category}")
        else:
            score -= 10
            cons.append(f"May not match category: {category}")
    
    # Condition check (20 points)
    preferred_condition = user_requirements.get("condition", "").lower()
    if preferred_condition:
        condition = item_details.get("condition", "").lower()
        if condition and preferred_condition in condition:
            score += 20
            pros.append(f"Condition matches: {condition}")
        # Not a hard penalty if no condition info
    
    # Feature matching (10 points)
    features = user_requirements.get("features", [])
    if features:
        matched_features = [f for f in features if f.lower() in description or f.lower() in title]
        if matched_features:
            feature_score = (len(matched_features) / len(features)) * 10
            score += feature_score
            pros.append(f"Has features: {', '.join(matched_features)}")
        else:
            cons.append(f"Missing features: {', '.join(features)}")
    
    # Clamp score
    score = max(0, min(100, score))
    
    # Build recommendation
    if score >= 80:
        recommendation = "Highly recommended"
    elif score >= 60:
        recommendation = "Good match"
    elif score >= 40:
        recommendation = "Partial match - review carefully"
    else:
        recommendation = "May not meet needs"
    
    return {
        "match_score": score,
        "pros": pros,
        "cons": cons,
        "recommendation": recommendation,
        "price_value": price_value,
        "title": item_details.get("title")
    }


# ============================================================================
# MCP Server Protocol
# ============================================================================

async def handle_tool_call(tool_name: str, arguments: dict) -> dict:
    """Route tool calls to appropriate handler."""
    
    handlers = {
        "search_market": lambda: search_market(
            query=arguments.get("query", ""),
            marketplace=arguments.get("marketplace", "xmrbazaar.com"),
            max_results=arguments.get("max_results", 15)
        ),
        "get_item_details": lambda: get_item_details(
            url=arguments.get("url", "")
        ),
        "get_vendor_rating": lambda: get_vendor_rating(
            vendor_url=arguments.get("vendor_url", "")
        ),
        "analyze_match": lambda: analyze_match(
            item_details=arguments.get("item_details", {}),
            user_requirements=arguments.get("user_requirements", {})
        )
    }
    
    handler = handlers.get(tool_name)
    if handler:
        return await handler()
    return {"error": f"Unknown tool: {tool_name}"}


# ============================================================================
# Main Entry Point (for testing)
# ============================================================================

if __name__ == "__main__":
    import sys
    
    async def test():
        # Test search
        print("=" * 60)
        print("TEST 1: search_market")
        print("=" * 60)
        results = await search_market("thinkpad")
        print(json.dumps(results, indent=2)[:500])
        
        if results.get("results"):
            # Test details on first result
            first_url = results["results"][0]["url"]
            print("\n" + "=" * 60)
            print("TEST 2: get_item_details")
            print("=" * 60)
            details = await get_item_details(first_url)
            print(json.dumps(details, indent=2)[:800])
    
    asyncio.run(test())
