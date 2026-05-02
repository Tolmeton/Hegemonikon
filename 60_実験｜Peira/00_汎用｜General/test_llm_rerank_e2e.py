import asyncio
import logging
from mekhane.periskope.engine import PeriskopeEngine
import yaml
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("test_rerank")

async def test():
    with open("mekhane/periskope/config.yaml") as f:
        config = yaml.safe_load(f)
    
    # Force enable both
    config["llm_rerank"]["enabled"] = True
    config["llm_rerank"]["cohere"]["enabled"] = False  # Let's test standard LLM rerank first
    
    engine = PeriskopeEngine(config)
    
    logger.info("Starting quick E2E search for 'Free Energy Principle'...")
    # research returns a single ResearchReport object
    report = await engine.research(
        query="Free Energy Principle active inference",
        sources=["vertex_search", "searxng"],
        depth=1,  # Keep it quick (L1), depth controls LLM Reranker stage depth too (1=Flash only)
    )
    
    logger.info("=== Output Results ===")
    if not report.summary:
        logger.warning("No summary generated.")
        
    logger.info("Done.")

if __name__ == "__main__":
    asyncio.run(test())
