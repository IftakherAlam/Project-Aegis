# src/api/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
from .admin_routes import router as admin_router


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Project Aegis API",
    description="Open-Source AI Security Proxy",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)
# Pydantic models
class SecurityCheckRequest(BaseModel):
    content: str
    source_type: str = "unknown"
    metadata: Dict[str, Any] = {}

class SecurityCheckResponse(BaseModel):
    request_id: str
    is_safe: bool
    confidence_score: float
    detected_threats: List[str]
    sanitized_content: str
    processing_time: float

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    components: Dict[str, str]


# Add performance tracker dependency
def get_performance_tracker():
    from src.monitoring.performance_tracker import PerformanceTracker
    return PerformanceTracker()
# Dependency injection
def get_security_proxy():
    try:
        from src.core.security_proxy import AegisSecurityProxy
        from src.core.config import load_config
        config = load_config()
        return AegisSecurityProxy(config)
    except ImportError as e:
        logger.error(f"Import error in security proxy: {e}")
        raise HTTPException(status_code=500, detail=f"Service configuration error: {e}")
    except Exception as e:
        logger.error(f"Error initializing security proxy: {e}")
        raise HTTPException(status_code=500, detail="Service initialization failed")

# Mock implementation for testing
class MockSecurityProxy:
    """Mock security proxy for testing when real components aren't available"""
    def process_input(self, content: str, source_type: str):
        from src.core.security_proxy import SecurityResult
        return SecurityResult(
            content=content,
            is_safe=True,
            confidence_score=0.9,
            detected_threats=[],
            sanitized_content=content
        )

def get_fallback_proxy():
    """Fallback dependency for when main proxy fails"""
    try:
        return get_security_proxy()
    except:
        logger.warning("Using mock security proxy - some features may be limited")
        return MockSecurityProxy()

# API Routes
@app.post("/v1/analyze", response_model=SecurityCheckResponse)
async def analyze_content(
    request: SecurityCheckRequest,
    proxy: Any = Depends(get_fallback_proxy)
):
    """Main endpoint for content security analysis"""
    import time
    start_time = time.time()
    
    try:
        result = await proxy.process_input(request.content, request.source_type)
        processing_time = time.time() - start_time
        
        return SecurityCheckResponse(
            request_id=f"req_{int(time.time())}",
            is_safe=result.is_safe,
            confidence_score=result.confidence_score,
            detected_threats=result.detected_threats,
            sanitized_content=result.sanitized_content,
            processing_time=processing_time
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.get("/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    components = {
        "security_proxy": "operational",
        "api": "operational", 
        "database": "not_implemented",
        "connectors": "limited"
    }
    
    # Test basic functionality
    try:
        from src.core.security_proxy import AegisSecurityProxy
        components["security_proxy"] = "operational"
    except ImportError:
        components["security_proxy"] = "degraded"
    
    return HealthResponse(
        status="healthy",
        service="Project Aegis",
        version="1.0.0",
        components=components
    )

@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "message": "Project Aegis AI Security Proxy",
        "version": "1.0.0",
        "endpoints": {
            "health": "/v1/health",
            "analyze": "/v1/analyze",
            "docs": "/docs"
        }
    }
    
    

@app.get("/demo")
async def launch_demo():
    """Redirect to executive demo"""
    return {"message": "Demo available at /executive-demo"}

@app.get("/executive-demo")
async def executive_demo():
    """Serve the executive demo"""
    import subprocess
    import os
    
    demo_path = os.path.join(os.path.dirname(__file__), '../demo/executive_demo.py')
    subprocess.Popen([f"streamlit run {demo_path} --server.port 8502"], shell=True)
    return {"status": "Demo launching on port 8502"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")