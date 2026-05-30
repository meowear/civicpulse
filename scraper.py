import asyncio
import os
import json
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.async_configs import BrowserConfig

# Define the production Pydantic data schema for the incoming CivicPulse dashboard stream
class CivicGrievanceData(BaseModel):
    location: str = Field(
        description="The exact neighborhood, colony, landmark, or street in Hyderabad mentioned (e.g., Ameerpet, Kukatpally, Gachibowli). Default to 'Hyderabad' if unspecified but verified regional context."
    )
    category: str = Field(
        description="The core infrastructure issue category. Must strictly map to one of: 'Road Infrastructure', 'Water Supply & Sewage', 'Garbage Disposal', 'Street Lighting', or 'Traffic & Public Safety'."
    )
    urgency_level: str = Field(
        description="Calculated urgency profile based on text severity. Must strictly be: 'Critical', 'High', 'Medium', or 'Low'."
    )
    raw_complaint_summary: str = Field(
        description="A concise, factual summary of the specific user complaint, filtering out generic conversational fluff or political arguments."
    )
    engagement_count: int = Field(
        default=0,
        description="Approximate metric value indicating post visibility or traction (upvotes, likes, or comments mentioned in structural text blocks)."
    )

async def scrape_civic_sources_ai(urls: List[str]) -> List[Dict[str, Any]]:
    """
    Production AI-based crawling engine utilizing Gemini via Crawl4AI 
    to extract fully structured civic grievance items from raw browser page contexts.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: 'GEMINI_API_KEY' environment variable is missing. AI scraping cannot initialize.")
        return []

    print(f"Deploying AI-driven semantic harvest engine across {len(urls)} entry points...")
    all_extracted_grievances = []

    # Hardened anti-fingerprinting browser configuration layer
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        text_mode=False,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
    )

    # Automated viewport scroll block to trigger client-side infinite loading buckets
    js_scroll_script = """
    (async () => {
        await new Promise(resolve => setTimeout(resolve, 4000));
        for (let i = 0; i < 4; i++) {
            window.scrollTo(0, document.body.scrollHeight);
            await new Promise(resolve => setTimeout(resolve, 1800));
        }
    })();
    """

    # Instantiate the semantic LLM extraction strategy targeting the exact Pydantic schema shape
    ai_strategy = LLMExtractionStrategy(
        provider="google/gemini-2.5-flash",
        api_key=api_key,
        schema=CivicGrievanceData,
        instruction=(
            "Analyze the social media content, post timelines, or comment feeds provided. "
            "Identify and extract user-submitted posts that describe traditional civic grievances, "
            "infrastructure problems, or utility issues strictly within the city of Hyderabad, India. "
            "Ignore all global news, general political rants without specific infrastructure targets, "
            "advertisements, and normal platform navigation buttons. Return a clean, arrayed schema match."
        )
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for url in urls:
            if "reddit.com" in url:
                platform = "reddit"
            elif "instagram.com" in url:
                platform = "instagram"
            elif "facebook.com" in url:
                platform = "facebook"
            else:
                platform = "web_node"

            print(f"\n🤖 Deploying AI Vision Model to live stream node [{platform.upper()}]: {url}")

            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                js_code=js_scroll_script,
                extraction_strategy=ai_strategy
            )

            try:
                result = await crawler.arun(url=url, config=run_config)
                
                if result.success and result.extracted_content:
                    # Crawl4AI applies the schema and returns standard JSON string data
                    parsed_ai_output = json.loads(result.extracted_content)
                    
                    # Ensure unified structure mapping if model returned a single object dictionary block instead of list wrapper
                    if isinstance(parsed_ai_output, dict):
                        # Some versions or model parsing profiles pack results under a root array key
                        if "items" in parsed_ai_output:
                            parsed_ai_output = parsed_ai_output["items"]
                        elif any(isinstance(v, list) for v in parsed_ai_output.values()):
                            # Grab the first list container found inside the object context
                            parsed_ai_output = next(v for v in parsed_ai_output.values() if isinstance(v, list))
                        else:
                            parsed_ai_output = [parsed_ai_output]

                    print(f"✔ AI Extraction confirmed. Generated {len(parsed_ai_output)} validated data profiles from raw canvas.")
                    
                    for data_block in parsed_ai_output:
                        all_extracted_grievances.append({
                            "source_platform": platform,
                            "source_url": url,
                            "extraction_method": "ai_llm_semantic_strategy",
                            "raw_extracted_text": data_block.get("raw_complaint_summary", ""),
                            "metadata": data_block
                        })
                else:
                    print(f"⚠ AI processing was unable to parse data arrays from {url}: {result.error_message}")
                    
            except Exception as e:
                print(f"Exception encountered during AI ingestion pass on {url}: {str(e)}")
                continue

    print(f"\n✨ Ingestion Complete. AI mapped and cataloged {len(all_extracted_grievances)} clean regional issues.")
    return all_extracted_grievances

if __name__ == "__main__":
    # Update target paths for live pipeline execution
    live_nodes = [
        "https://www.reddit.com/r/hyderabad/search/?q=pothole&restrict_sr=1&sort=new"
    ]
    
    # Simple self-contained fallback execution test runner
    if not os.getenv("GEMINI_API_KEY"):
        print("Set your GEMINI_API_KEY environment variable before running.")
    else:
        output = asyncio.run(scrape_civic_sources_ai(live_nodes))
        print(json.dumps(output, indent=2))