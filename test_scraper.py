import asyncio
import json
from scraper import scrape_civic_sources_ai

async def run_test():
    # Production-grade target test matrix focusing on high-frequency civic discussions
    test_urls = [
        "https://www.reddit.com/r/hyderabad/search/?q=pothole&restrict_sr=1&sort=new",
        "https://www.reddit.com/r/hyderabad/search/?q=sewage&restrict_sr=1&sort=new"
    ]
    
    print("======================================================================")
    print("🚀 STARTING CIVIC PULSE SCRAPER LIVE RUN INTEGRATION TEST")
    print("======================================================================\n")
    
    results = await scrape_civic_sources_ai(test_urls)
    
    print("\n======================================================================")
    print(f"📊 LIVE INGESTION SUMMARY: TRIPPED {len(results)} RAW COMPLAINTS")
    print("======================================================================\n")
    
    if not results:
        print("❌ No items crossed the Hyderabad keyword matrix filter blocks.")
        print("💡 Tip: Try expanding keywords or verifying that the network isn't hitting hard login-walls.")
        return

    # Iterate and print every single captured data object with clean terminal separation
    for index, grievance in enumerate(results, start=1):
        print(f"--- [RECORD {index} / {len(results)}] ------------------------------------")
        print(f"🌐 Platform:    {grievance['source_platform'].upper()}")
        print(f"🔗 Target Node: {grievance['source_url']}")
        print(f"🛠️ Method:      {grievance['extraction_method']}")
        print(f"📁 Metadata Pipeline Block:")
        print(json.dumps(grievance['metadata'], indent=4))
        print(f"\n📝 Captured Text Output:")
        print("-" * 60)
        print(grievance['raw_extracted_text'])
        print("-" * 60)
        print("\n")
        
    print("======================================================================")
    print("🏁 TEST SCENARIO TERMINATED CLEANLY")
    print("======================================================================")

if __name__ == "__main__":
    # Initialize the local event loop
    asyncio.run(run_test())