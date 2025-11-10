from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional

# --- Import core backend systems ---
from src.core.autonomous_integration import AutonomousIntegrationManager
from src.monitoring.performance_tracker import PerformanceTracker
from src.core.config import load_config

# Initialize shared backend dependencies
_config = load_config()
_integration_manager = AutonomousIntegrationManager(_config)
_performance_tracker = PerformanceTracker()

# --- Dependency Providers ---
async def get_security_proxy():
    """
    Dependency for accessing the autonomous security integration system.
    Returns the shared instance of AutonomousIntegrationManager.
    """
    return _integration_manager

async def get_performance_tracker():
    """
    Dependency for accessing system performance metrics.
    Returns the shared instance of PerformanceTracker.
    """
    return _performance_tracker

# --- Router Initialization ---
router = APIRouter(prefix="/admin", tags=["administration"])


# --- Pydantic Models ---
class SystemConfigUpdate(BaseModel):
    autonomous_percentage: Optional[float] = None
    enable_feature: Optional[str] = None
    disable_feature: Optional[str] = None


class LearningStatusResponse(BaseModel):
    autonomous_rollout: float
    performance_metrics: Dict[str, Any]
    feature_flags: Dict[str, bool]
    learning_progress: Dict[str, Any]


# --- Route Handlers ---
@router.get("/status", response_model=LearningStatusResponse)
async def get_system_status(proxy = Depends(get_security_proxy)):
    """Get current autonomous learning system status"""
    status = proxy.get_system_status()
    return LearningStatusResponse(**status)


@router.post("/config")
async def update_system_config(config: SystemConfigUpdate, proxy = Depends(get_security_proxy)):
    """Update system configuration"""
    if config.autonomous_percentage is not None:
        proxy.set_autonomous_percentage(config.autonomous_percentage)
    
    if config.enable_feature:
        proxy.enable_autonomous_feature(config.enable_feature)
    
    return {
        "message": "Configuration updated successfully",
        "config": config.dict()
    }


@router.get("/performance")
async def get_performance_metrics(time_window: str = "1h", tracker = Depends(get_performance_tracker)):
    """Get performance metrics"""
    metrics = tracker.get_performance_metrics()
    return metrics


@router.get("/learning-progress")
async def get_learning_progress(tracker = Depends(get_performance_tracker)):
    """Get learning progress over time"""
    if hasattr(tracker, "get_learning_progress"):
        progress = tracker.get_learning_progress()
        return progress
    return {"message": "Learning progress tracking not implemented"}


@router.post("/force-learn")
async def force_learning_cycle(proxy = Depends(get_security_proxy)):
    """Force a learning cycle to occur immediately"""
    # Trigger deep learning in the autonomous system
    if hasattr(proxy, "force_learning_cycle"):
        proxy.force_learning_cycle()
        return {"message": "Learning cycle triggered", "status": "processing"}
    return {"message": "Manual learning trigger not implemented", "status": "unavailable"}
