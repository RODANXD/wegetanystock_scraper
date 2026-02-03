import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi import Path as FastAPIPath  # ✅ Rename to avoid conflict

sys.path.insert(0, str(Path(__file__).parent.parent))


from scraper.bestwayScraper import BestwayScraper
from scraper.laxmiScraper import LakshmiGroceryScraper
from cleaner.cleaner_intergated import IntegratedProductCleaner


class ScrapeRequest(BaseModel):
    """Request model for scraping"""
    target_products: int = Field(default=100, description="Number of products to scrape", ge=1, le=10000)
    source: str = Field(default="bestway", description="Source to scrape: 'bestway' or 'laxmi'")

class ScrapeResponse(BaseModel):
    """Response model for scraping"""
    job_id: str
    status: str
    source: str
    target_products: int
    timestamp: str
    message: str

class JobStatus(BaseModel):
    """Job status response"""
    job_id: str
    status: str  # running, completed, failed
    source: str
    raw_count: int
    cleaned_count: int
    timestamp: str
    error: Optional[str] = None
    
    
class ProductListResponse(BaseModel):
    """Response for product list"""
    total_count: int
    source: str
    products: List[dict]

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str
    
    
app = FastAPI(
    title="Product Scraping API",
    description="REST API for web scraping and cleaning e-commerce products",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


jobs = {}
data_dir = Path(__file__).parent / "data"
data_dir.mkdir(exist_ok=True, parents=True)


@app.get("/", tags=["Info"])
async def root():
    """Root endpoint - API information"""
    return {
        "api": "Product Scraping API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "GET /health",
            "scrape": "POST /api/scrape",
            "job_status": "GET /api/jobs/{job_id}",
            "raw_products": "GET /api/products/raw/{source}",
            "cleaned_products": "GET /api/products/cleaned/{source}"
        }
    }
    
@app.get("/health", response_model=HealthResponse, tags=["Info"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
    

@app.post("/api/scrape", response_model=ScrapeResponse, tags=["Scrape"])
async def start_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Start a new scraping job
    """
    
    if request.source.lower() not in ["bestway", "laxmi"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source '{request.source}'. Must be 'bestway' or 'laxmi'"
        )
    
    job_id = f"{request.source}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    jobs[job_id] = {
        "status": "queued",
        "source": request.source.lower(),
        "target_products": request.target_products,
        "created_at": datetime.now().isoformat(),
        "raw_count": 0,
        "cleaned_count": 0,
        "error": None
    }
    
    background_tasks.add_task(
        run_scraping_job,
        job_id=job_id,
        source=request.source.lower(),
        target_products=request.target_products
    )
    
    return ScrapeResponse(
        job_id=job_id,
        status="queued",
        source=request.source,
        target_products=request.target_products,
        timestamp=datetime.now().isoformat(),
        message=f"Scraping job '{job_id}' queued. Check status with GET /api/jobs/{job_id}"
    )

@app.get("/api/jobs/{job_id}", response_model=JobStatus, tags=["Jobs"])
async def get_job_status(job_id: str):
    """Get the status of a scraping job"""
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    
    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        source=job["source"],
        raw_count=job["raw_count"],
        cleaned_count=job["cleaned_count"],
        timestamp=job["created_at"],
        error=job.get("error")
    )

@app.get("/api/jobs", tags=["Jobs"])
async def list_jobs():
    """List all scraping jobs"""
    return {
        "total_jobs": len(jobs),
        "jobs": {
            job_id: {
                "status": job["status"],
                "source": job["source"],
                "created_at": job["created_at"],
                "raw_count": job["raw_count"],
                "cleaned_count": job["cleaned_count"]
            }
            for job_id, job in jobs.items()
        }
    }
    
@app.get("/api/products/cleaned/{source}", tags=["Products"])
async def get_cleaned_products(
    source: str = FastAPIPath(..., description="Source: 'bestway' or 'laxmi'"),  # ✅ Use renamed import
    limit: Optional[int] = Query(None, description="Limit number of results"),
    skip: Optional[int] = Query(0, description="Skip first N results")
):
    """Get cleaned and normalized products from a source"""
    
    source = source.lower()
    
    if source == "bestway":
        cleaned_file = data_dir / "bestway_cleaned_products.json"
    elif source == "laxmi":
        cleaned_file = data_dir / "laxmi_cleaned_products.json"
    else:
        raise HTTPException(status_code=400, detail=f"Invalid source '{source}'")
    
    if not cleaned_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No cleaned products found for source '{source}'"
        )
    
    with open(cleaned_file, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    total = len(products)
    products = products[skip:]
    if limit:
        products = products[:limit]
    
    return {
        "source": source,
        "total_count": total,
        "returned_count": len(products),
        "skip": skip,
        "limit": limit,
        "products": products
    }


def run_scraping_job(job_id: str, source: str, target_products: int):
    """Background task to run scraping"""
    
    try:
        jobs[job_id]["status"] = "running"
        
        if source == "bestway":
            scraper = BestwayScraper(target_products=target_products, output_dir=str(data_dir))
            all_products, cleaned_products = scraper.run_full_pipeline()
            
            jobs[job_id]["raw_count"] = len(all_products) if all_products else 0
            jobs[job_id]["cleaned_count"] = len(cleaned_products) if cleaned_products else 0
            jobs[job_id]["status"] = "completed"
        
        elif source == "laxmi":
            scraper = LakshmiGroceryScraper(target_products=target_products, output_dir=str(data_dir))
            all_products, cleaned_products = scraper.run_full_pipeline()
            
            jobs[job_id]["raw_count"] = len(all_products) if all_products else 0
            jobs[job_id]["cleaned_count"] = len(cleaned_products) if cleaned_products else 0
            jobs[job_id]["status"] = "completed"
        
    except Exception as e:
        print(f"❌ Error in job {job_id}: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 STARTING PRODUCT SCRAPING API SERVER")
    print("="*80)
    print(f"📍 Swagger UI: http://localhost:8000/docs")
    print(f"📍 ReDoc: http://localhost:8000/redoc")
    print("="*80 + "\n")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )