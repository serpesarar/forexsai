from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timezone
import logging

from database.supabase_client import get_supabase_client, is_db_available

router = APIRouter(prefix="/api/admin", tags=["Admin & Feedback"])
logger = logging.getLogger(__name__)

# Models
class FeedbackReport(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    type: str # 'bug', 'feature', 'other'
    message: str
    metadata: Optional[Dict[str, Any]] = None

class AdminStats(BaseModel):
    total_users: int
    active_users_24h: int
    total_reports: int
    pending_reports: int

# Endpoints

@router.post("/report")
async def submit_report(report: FeedbackReport):
    """
    Kullanıcıdan gelen sorun/öneri bildirimini kaydeder.
    """
    if not is_db_available():
        return {"success": False, "error": "Database unavailable"}
    
    client = get_supabase_client()
    try:
        data = {
            "type": report.type,
            "message": report.message,
            "metadata": report.metadata or {},
            "status": "pending", # pending, in_progress, resolved
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        if report.user_id:
            data["user_id"] = report.user_id
        if report.email:
            data["email"] = report.email
            
        # 'user_reports' tablosu olmalı
        client.table("user_reports").insert(data).execute()
        return {"success": True, "message": "Report submitted successfully"}
    except Exception as e:
        logger.error(f"Failed to submit report: {e}")
        # Tablo yoksa bile frontend'e hata döndürmeyelim ki kullanıcı üzülmesin, loglayalım.
        # Gerçek senaryoda tabloyu oluşturmak gerekir.
        return {"success": False, "error": str(e)}

@router.get("/reports")
async def get_reports(limit: int = 50, status: str = "pending"):
    """
    Admin paneli için raporları listeler.
    """
    if not is_db_available():
        return []
    
    client = get_supabase_client()
    try:
        query = client.table("user_reports").select("*").order("created_at", desc=True).limit(limit)
        if status != "all":
            query = query.eq("status", status)
        
        result = query.execute()
        return result.data
    except Exception as e:
        logger.error(f"Failed to fetch reports: {e}")
        return []

@router.get("/metrics")
async def get_admin_metrics():
    """
    Admin paneli istatistikleri.
    """
    if not is_db_available():
        return AdminStats(total_users=0, active_users_24h=0, total_reports=0, pending_reports=0)
    
    client = get_supabase_client()
    try:
        # Mock/Real data fetch
        # Supabase auth users tablosuna erişim kısıtlı olabilir, public tablolardan sayım yapmaya çalışacağız
        # Veya basitçe users tablosunu sayacağız
        
        # 1. Total Users (users tablosundan)
        total_users = 0
        try:
            r = client.table("users").select("id", count="exact").execute()
            total_users = r.count or 0
        except:
            pass # users tablosu olmayabilir
            
        # 2. Total Reports
        total_reports = 0
        pending_reports = 0
        try:
            r = client.table("user_reports").select("id", count="exact").execute()
            total_reports = r.count or 0
            
            p = client.table("user_reports").select("id", count="exact").eq("status", "pending").execute()
            pending_reports = p.count or 0
        except:
            pass
            
        return AdminStats(
            total_users=total_users,
            active_users_24h=0, # Loglama olmadan zor, şimdilik 0
            total_reports=total_reports,
            pending_reports=pending_reports
        )
            
    except Exception as e:
        logger.error(f"Failed to fetch metrics: {e}")
        return AdminStats(total_users=0, active_users_24h=0, total_reports=0, pending_reports=0)
