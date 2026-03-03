"""
Economic Calendar Router
=========================
Ekonomik takvim ve kazanç takvimi API endpointleri
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Literal
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import aiohttp

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

DEEP_SEEKR1 = os.getenv("DEEP_SEEKR1", "")

# =============================================================================
# DATA MODELS
# =============================================================================

class EconomicEventDetail(BaseModel):
    id: str
    timestamp: str
    title: str
    title_tr: str
    currency: str
    impact: Literal["High", "Medium", "Low"]
    actual: Optional[str] = None
    forecast: Optional[str] = None
    previous: Optional[str] = None
    
    # AI Analizi
    predicted_direction: Literal["bullish", "bearish", "neutral"]
    affected_symbols: List[str]
    impact_analysis: str
    impact_analysis_tr: str
    
    # Veri açıklaması
    description: str
    description_tr: str
    why_it_matters: str
    why_it_matters_tr: str
    typical_market_reaction: str
    typical_market_reaction_tr: str
    
    # Tarih bilgisi
    is_upcoming: bool
    minutes_until: Optional[int] = None


class EarningsEventDetail(BaseModel):
    id: str
    timestamp: str
    company: str
    ticker: str
    sector: str
    
    # Beklentiler
    eps_forecast: Optional[str] = None
    revenue_forecast: Optional[str] = None
    
    # Önceki çeyrek
    previous_eps: Optional[str] = None
    previous_revenue: Optional[str] = None
    
    # AI Analizi
    predicted_direction: Literal["bullish", "bearish", "neutral"]
    confidence: int  # 1-100
    affected_symbols: List[str]  # NDX, SPY, etc.
    
    # Analiz
    analysis: str
    analysis_tr: str
    key_metrics_to_watch: List[str]
    key_metrics_to_watch_tr: List[str]
    
    # Tarih bilgisi
    is_upcoming: bool
    minutes_until: Optional[int] = None


# =============================================================================
# EKONOMİK VERİLER DATABASE (Simplified - Gerçekte API'den gelecek)
# =============================================================================

ECONOMIC_EVENTS_DB = [
    {
        "id": "nfp_2024_01_05",
        "title": "Non-Farm Payrolls (NFP)",
        "title_tr": "Tarım Dışı İstihdam (NFP)",
        "currency": "USD",
        "impact": "High",
        "description": "Monthly report showing the number of paid workers in the US excluding farm workers, private household employees, and non-profits.",
        "description_tr": "ABD'de çiftlik işçileri, özel hanehalkı çalışanları ve kar amacı gütmeyen kuruluşlar hariç ücretli işçi sayısını gösteren aylık rapor.",
        "why_it_matters": "NFP is the most important employment report. It directly impacts Fed policy decisions and USD strength.",
        "why_it_matters_tr": "NFP en önemli istihdam raporudur. Doğrudan Fed politika kararlarını ve USD gücünü etkiler.",
        "typical_market_reaction": "Better than expected: USD ↑, Gold ↓, Stocks ↑ | Worse: USD ↓, Gold ↑, Stocks ↓",
        "typical_market_reaction_tr": "Beklenenden iyi: USD ↑, Altın ↓, Hisse ↑ | Kötü: USD ↓, Altın ↑, Hisse ↓",
        "affected_symbols": ["DXY", "XAUUSD", "NDX", "USOIL", "VIX"],
        "schedule": "first_friday",  # Ayın ilk Cuma'sı
    },
    {
        "id": "cpi_2024_monthly",
        "title": "Consumer Price Index (CPI)",
        "title_tr": "Tüketici Fiyat Endeksi (TÜFE)",
        "currency": "USD",
        "impact": "High",
        "description": "Monthly measure of the average change in prices over time that consumers pay for a basket of goods and services.",
        "description_tr": "Tüketicilerin bir mal ve hizmet sepeti için ödedikleri fiyatlardaki ortalama değişimin aylık ölçümü.",
        "why_it_matters": "Primary inflation gauge. High CPI = Rate hike expectations = Stronger USD, weaker stocks and gold.",
        "why_it_matters_tr": "Temel enflasyon ölçüsü. Yüksek CPI = Faiz artışı beklentisi = Güçlü USD, zayıf hisse ve altın.",
        "typical_market_reaction": "Higher inflation: USD ↑, Stocks ↓, Gold volatile | Lower: USD ↓, Stocks ↑, Gold stable",
        "typical_market_reaction_tr": "Yüksek enflasyon: USD ↑, Hisse ↓, Altın volatil | Düşük: USD ↓, Hisse ↑, Altın stabil",
        "affected_symbols": ["DXY", "XAUUSD", "NDX", "USOIL", "VIX"],
        "schedule": "monthly_mid",  # Ayın ortası
    },
    {
        "id": "fomc_2024_quarterly",
        "title": "FOMC Interest Rate Decision",
        "title_tr": "FOMC Faiz Kararı",
        "currency": "USD",
        "impact": "High",
        "description": "Federal Open Market Committee decision on the federal funds rate. Includes policy statement and Powell's press conference.",
        "description_tr": "Federal Açık Piyasa Komitesi'nin federal fonlama faizi kararı. Politika açıklaması ve Powell'ın basın toplantısı içerir.",
        "why_it_matters": "Most important event for USD and global markets. Rate decisions cascade through all asset classes.",
        "why_it_matters_tr": "USD ve küresel piyasalar için en önemli olay. Faiz kararları tüm varlık sınıflarına yayılır.",
        "typical_market_reaction": "Hawkish (Rate ↑): USD ↑↑, Stocks ↓↓, Gold ↓ | Dovish: USD ↓, Stocks ↑, Gold ↑",
        "typical_market_reaction_tr": "Şahin (Faiz ↑): USD ↑↑, Hisse ↓↓, Altın ↓ | Güvercin: USD ↓, Hisse ↑, Altın ↑",
        "affected_symbols": ["DXY", "XAUUSD", "NDX", "DAX", "USOIL", "VIX"],
        "schedule": "quarterly",  # 3 ayda bir
    },
    {
        "id": "gdp_2024_quarterly",
        "title": "GDP Growth Rate",
        "title_tr": "GDP Büyüme Oranı",
        "currency": "USD",
        "impact": "High",
        "description": "Quarterly measure of US economic output. Shows whether economy is expanding or contracting.",
        "description_tr": "ABD ekonomik çıktısının çeyreklik ölçümü. Ekonominin genişleyip genişlemediğini gösterir.",
        "why_it_matters": "Broadest measure of economic health. Recession fears drive risk-off flows to USD and gold.",
        "why_it_matters_tr": "Ekonomik sağlığın en kapsamlı ölçüsü. Resesyon korkuları riskten kaçışı USD ve altına yönlendirir.",
        "typical_market_reaction": "Strong GDP: USD ↑, Stocks ↑, Gold ↓ | Weak/Recession: USD ↓, Stocks ↓, Gold ↑",
        "typical_market_reaction_tr": "Güçlü GDP: USD ↑, Hisse ↑, Altın ↓ | Zayıf/Recessiyon: USD ↓, Hisse ↓, Altın ↑",
        "affected_symbols": ["DXY", "XAUUSD", "NDX", "USOIL"],
        "schedule": "quarterly",
    },
    {
        "id": "retail_sales_monthly",
        "title": "Retail Sales",
        "title_tr": "Perakende Satışlar",
        "currency": "USD",
        "impact": "Medium",
        "description": "Monthly measure of consumer spending at retail stores. Key indicator of consumer confidence.",
        "description_tr": "Perakende mağazalardaki tüketici harcamalarının aylık ölçümü. Tüketici güveninin ana göstergesi.",
        "why_it_matters": "Consumer spending drives 70% of US economy. Strong sales = Economic health = Hawkish Fed.",
        "why_it_matters_tr": "Tüketici harcamaları ABD ekonomisinin %70'ini yönlendirir. Güçlü satış = Ekonomik sağlık = Şahin Fed.",
        "typical_market_reaction": "Strong: USD ↑, Stocks ↑ | Weak: USD ↓, Stocks ↓, Gold ↑",
        "typical_market_reaction_tr": "Güçlü: USD ↑, Hisse ↑ | Zayıf: USD ↓, Hisse ↓, Altın ↑",
        "affected_symbols": ["DXY", "NDX", "XAUUSD"],
        "schedule": "monthly",
    },
    {
        "id": "pmi_manufacturing",
        "title": "ISM Manufacturing PMI",
        "title_tr": "ISM Üretim PMI",
        "currency": "USD",
        "impact": "Medium",
        "description": "Monthly survey of purchasing managers in manufacturing. Above 50 = expansion, below 50 = contraction.",
        "description_tr": "Üretim sektörü satın alma yöneticilerinin aylık anketi. 50 üzeri = genişleme, 50 altı = daralma.",
        "why_it_matters": "Leading indicator of economic health. First major data release of each month.",
        "why_it_matters_tr": "Ekonomik sağlığın öncü göstergesi. Her ayın ilk büyük veri açıklaması.",
        "typical_market_reaction": "Above 50: USD ↑, Stocks ↑ | Below 50: USD ↓, Stocks ↓, Gold ↑",
        "typical_market_reaction_tr": "50 üzeri: USD ↑, Hisse ↑ | 50 altı: USD ↓, Hisse ↓, Altın ↑",
        "affected_symbols": ["DXY", "NDX", "USOIL"],
        "schedule": "monthly",
    },
    {
        "id": "jobless_claims_weekly",
        "title": "Initial Jobless Claims",
        "title_tr": "İlk İşsizlik Başvuruları",
        "currency": "USD",
        "impact": "Medium",
        "description": "Weekly count of Americans filing for unemployment benefits. Most timely labor market indicator.",
        "description_tr": "İşsizlik yardımı için başvuran Amerikalıların haftalık sayısı. En güncel işgücü piyasası göstergesi.",
        "why_it_matters": "Weekly frequency makes it important for detecting labor market trends early.",
        "why_it_matters_tr": "Haftalık frekansı, işgücü piyasası trendlerini erken tespit etmeyi önemli kılar.",
        "typical_market_reaction": "Lower claims: USD ↑, Stocks ↑ | Higher claims: USD ↓, Stocks ↓, Gold ↑",
        "typical_market_reaction_tr": "Düşük başvuru: USD ↑, Hisse ↑ | Yüksek başvuru: USD ↓, Hisse ↓, Altın ↑",
        "affected_symbols": ["DXY", "NDX", "XAUUSD"],
        "schedule": "weekly",  # Her Perşembe
    },
    {
        "id": "eia_oil_weekly",
        "title": "EIA Crude Oil Inventories",
        "title_tr": "EIA Ham Petrol Stokları",
        "currency": "USD",
        "impact": "High",
        "description": "Weekly report on US crude oil stockpiles. Major driver of oil prices.",
        "description_tr": "ABD ham petrol stoklarının haftalık raporu. Petrol fiyatlarının ana itici gücü.",
        "why_it_matters": "Supply/demand balance indicator. Higher stocks = Lower oil prices, affects energy stocks and inflation.",
        "why_it_matters_tr": "Arz/talep denge göstergesi. Yüksek stok = Düşük petrol fiyatları, enerji hisselerini ve enflasyonu etkiler.",
        "typical_market_reaction": "Higher stocks: Oil ↓, Energy stocks ↓ | Lower stocks: Oil ↑, Energy stocks ↑",
        "typical_market_reaction_tr": "Yüksek stok: Petrol ↓, Enerji hisseleri ↓ | Düşük stok: Petrol ↑, Enerji hisseleri ↑",
        "affected_symbols": ["USOIL", "NDX", "XAUUSD"],
        "schedule": "weekly_wednesday",  # Her Çarşamba
    },
]


# =============================================================================
# KAZANÇ TAKVİMİ DATABASE
# =============================================================================

EARNINGS_DB = [
    {
        "id": "aapl_q4_2024",
        "company": "Apple Inc.",
        "ticker": "AAPL",
        "sector": "Technology",
        "date": "2024-02-01",
        "time": "after_market",
        "eps_forecast": "$2.18",
        "revenue_forecast": "$118.1B",
        "previous_eps": "$1.88",
        "previous_revenue": "$117.2B",
        "affected_symbols": ["NDX", "QQQ", "SPY"],
        "analysis": "Apple's earnings are critical for tech sector sentiment. Watch iPhone sales and Services revenue growth.",
        "analysis_tr": "Apple'ın kazançları teknoloji sektörü hissiyatı için kritik. iPhone satışları ve Servis gelir büyümesini izleyin.",
        "key_metrics": ["iPhone Revenue", "Services Revenue", "China Sales", "Gross Margin", "Guidance"],
        "key_metrics_tr": ["iPhone Geliri", "Servis Geliri", "Çin Satışları", "Brüt Kar Marjı", "Tahminler"],
    },
    {
        "id": "msft_q2_2024",
        "company": "Microsoft Corporation",
        "ticker": "MSFT",
        "sector": "Technology",
        "date": "2024-01-30",
        "time": "after_market",
        "eps_forecast": "$2.78",
        "revenue_forecast": "$61.1B",
        "previous_eps": "$2.93",
        "previous_revenue": "$62.0B",
        "affected_symbols": ["NDX", "QQQ", "SPY"],
        "analysis": "Azure cloud growth and AI integration key. Leading indicator for enterprise tech spending.",
        "analysis_tr": "Azure bulut büyümesi ve AI entegrasyonu kritik. Kurumsal teknoloji harcamaları için öncü gösterge.",
        "key_metrics": ["Azure Growth", "Cloud Revenue", "AI Revenue", "Office 365 Subscribers"],
        "key_metrics_tr": ["Azure Büyümesi", "Bulut Geliri", "AI Geliri", "Office 365 Aboneleri"],
    },
    {
        "id": "tsla_q4_2024",
        "company": "Tesla Inc.",
        "ticker": "TSLA",
        "sector": "Automotive",
        "date": "2024-01-24",
        "time": "after_market",
        "eps_forecast": "$0.73",
        "revenue_forecast": "$25.9B",
        "previous_eps": "$1.19",
        "previous_revenue": "$24.3B",
        "affected_symbols": ["NDX", "QQQ"],
        "analysis": "High volatility expected. Watch delivery numbers, margins, and FSD progress. Can move entire EV sector.",
        "analysis_tr": "Yüksek volatilite bekleniyor. Teslimat sayıları, kar marjları ve FSD ilerlemesini izleyin. Tüm EV sektörünü hareket ettirebilir.",
        "key_metrics": ["Vehicle Deliveries", "Gross Margin", "FSD Revenue", "Energy Storage", "Cybertruck Updates"],
        "key_metrics_tr": ["Araç Teslimatları", "Brüt Kar Marjı", "FSD Geliri", "Enerji Depolama", "Cybertruck Güncellemeleri"],
    },
    {
        "id": "nvda_q4_2024",
        "company": "NVIDIA Corporation",
        "ticker": "NVDA",
        "sector": "Technology",
        "date": "2024-02-21",
        "time": "after_market",
        "eps_forecast": "$4.56",
        "revenue_forecast": "$20.4B",
        "previous_eps": "$3.71",
        "previous_revenue": "$18.1B",
        "affected_symbols": ["NDX", "QQQ", "SMH", "SOXX"],
        "analysis": "AI chip demand remains the key driver. Most important earnings for AI sector sentiment.",
        "analysis_tr": "AI çip talebi ana itici güç olmaya devam ediyor. AI sektörü hissiyatı için en önemli kazanç.",
        "key_metrics": ["Data Center Revenue", "Gaming Revenue", "AI Chip Demand", "Gross Margin", "Guidance"],
        "key_metrics_tr": ["Veri Merkezi Geliri", "Oyun Geliri", "AI Çip Talebi", "Brüt Kar Marjı", "Tahminler"],
    },
    {
        "id": "amzn_q4_2024",
        "company": "Amazon.com Inc.",
        "ticker": "AMZN",
        "sector": "Consumer Cyclical",
        "date": "2024-02-01",
        "time": "after_market",
        "eps_forecast": "$0.84",
        "revenue_forecast": "$166.2B",
        "previous_eps": "$0.03",
        "previous_revenue": "$149.2B",
        "affected_symbols": ["NDX", "QQQ", "XLY", "SPY"],
        "analysis": "AWS cloud growth and retail margins critical. Good indicator of consumer spending trends.",
        "analysis_tr": "AWS bulut büyümesi ve perakende kar marjları kritik. Tüketici harcama trendlerinin iyi göstergesi.",
        "key_metrics": ["AWS Revenue", "AWS Growth Rate", "Retail Revenue", "Operating Margin", "Prime Subscribers"],
        "key_metrics_tr": ["AWS Geliri", "AWS Büyüme Oranı", "Perakende Geliri", "Faaliyet Kar Marjı", "Prime Aboneleri"],
    },
    {
        "id": "goog_q4_2024",
        "company": "Alphabet Inc.",
        "ticker": "GOOGL",
        "sector": "Technology",
        "date": "2024-01-30",
        "time": "after_market",
        "eps_forecast": "$1.60",
        "revenue_forecast": "$70.8B",
        "previous_eps": "$1.64",
        "previous_revenue": "$76.7B",
        "affected_symbols": ["NDX", "QQQ", "SPY"],
        "analysis": "Search ad revenue and cloud growth key. AI integration with Gemini progress important.",
        "analysis_tr": "Arama reklam geliri ve bulut büyümesi kritik. Gemini ile AI entegrasyonu ilerlemesi önemli.",
        "key_metrics": ["Search Revenue", "YouTube Revenue", "Cloud Revenue", "AI Integration", "Ad Click Rates"],
        "key_metrics_tr": ["Arama Geliri", "YouTube Geliri", "Bulut Geliri", "AI Entegrasyonu", "Reklam Tıklama Oranları"],
    },
    {
        "id": "meta_q4_2024",
        "company": "Meta Platforms Inc.",
        "ticker": "META",
        "sector": "Technology",
        "date": "2024-02-01",
        "time": "after_market",
        "eps_forecast": "$4.96",
        "revenue_forecast": "$39.1B",
        "previous_eps": "$5.33",
        "previous_revenue": "$40.1B",
        "affected_symbols": ["NDX", "QQQ"],
        "analysis": "Ad revenue recovery and Reality Labs losses key. Metaverse spending remains concern.",
        "analysis_tr": "Reklam geliri toparlanması ve Reality Labs kayıpları kritik. Metaverse harcamaları endişe kaynağı olmaya devam ediyor.",
        "key_metrics": ["Ad Revenue", "Daily Active Users", "Reels Revenue", "Reality Labs Loss", "AI Investments"],
        "key_metrics_tr": ["Reklam Geliri", "Günlük Aktif Kullanıcı", "Reels Geliri", "Reality Labs Kaybı", "AI Yatırımları"],
    },
    {
        "id": "jpm_q4_2024",
        "company": "JPMorgan Chase & Co.",
        "ticker": "JPM",
        "sector": "Financials",
        "date": "2024-01-12",
        "time": "before_market",
        "eps_forecast": "$3.68",
        "revenue_forecast": "$39.7B",
        "previous_eps": "$3.04",
        "previous_revenue": "$38.6B",
        "affected_symbols": ["SPY", "XLF"],
        "analysis": "First major bank to report. Sets tone for financial sector. Watch net interest income and loan loss reserves.",
        "analysis_tr": "Rapor veren ilk büyük banka. Finans sektörü için ton belirler. Net faiz geliri ve karşılık ayırmalarını izleyin.",
        "key_metrics": ["Net Interest Income", "Investment Banking", "Loan Loss Reserves", "Trading Revenue", "Deposit Growth"],
        "key_metrics_tr": ["Net Faiz Geliri", "Yatırım Bankacılığı", "Karşılık Ayırmaları", "İşlem Geliri", "Mevduat Büyümesi"],
    },
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_next_event_date(schedule: str, base_date: datetime) -> datetime:
    """Calculate next event date based on schedule pattern"""
    if schedule == "first_friday":
        # Ayın ilk Cuma'sı
        first_day = base_date.replace(day=1)
        weekday = first_day.weekday()
        days_until_friday = (4 - weekday) % 7
        return first_day + timedelta(days=days_until_friday)
    
    elif schedule == "monthly_mid":
        # Ayın ortası (genellikle 10-15 arası)
        return base_date.replace(day=12)
    
    elif schedule == "quarterly":
        # Çeyreklik - yaklaşık tarihler
        month = base_date.month
        if month <= 3:
            return base_date.replace(month=3, day=20)
        elif month <= 6:
            return base_date.replace(month=6, day=19)
        elif month <= 9:
            return base_date.replace(month=9, day=18)
        else:
            return base_date.replace(month=12, day=18)
    
    elif schedule == "weekly":
        # Her Perşembe
        weekday = base_date.weekday()
        days_until_thursday = (3 - weekday) % 7
        return base_date + timedelta(days=days_until_thursday)
    
    elif schedule == "weekly_wednesday":
        # Her Çarşamba
        weekday = base_date.weekday()
        days_until_wednesday = (2 - weekday) % 7
        return base_date + timedelta(days=days_until_wednesday)
    
    return base_date


def generate_upcoming_events(days_ahead: int = 30) -> List[Dict]:
    """Generate upcoming economic events for next X days"""
    events = []
    now = datetime.utcnow()
    
    for event_template in ECONOMIC_EVENTS_DB:
        next_date = get_next_event_date(event_template["schedule"], now)
        
        # Eğer tarih geçmişse, bir sonraki periyoda atla
        if next_date < now:
            if event_template["schedule"] == "first_friday":
                next_date = get_next_event_date(event_template["schedule"], now + timedelta(days=32))
            elif event_template["schedule"].startswith("weekly"):
                next_date = next_date + timedelta(days=7)
            elif event_template["schedule"] == "monthly" or event_template["schedule"] == "monthly_mid":
                next_date = get_next_event_date(event_template["schedule"], now + timedelta(days=32))
            elif event_template["schedule"] == "quarterly":
                next_date = get_next_event_date(event_template["schedule"], now + timedelta(days=95))
        
        # Belirtilen gün aralığında mı?
        if (next_date - now).days <= days_ahead:
            minutes_until = int((next_date - now).total_seconds() / 60)
            
            # Basit bir yön tahmini (gerçekte AI veya analizle yapılmalı)
            predicted_direction = "neutral"
            if event_template["impact"] == "High":
                # Yüksek etkili verilerde volatilite yüksek
                predicted_direction = "volatile"
            
            events.append({
                **event_template,
                "timestamp": next_date.isoformat(),
                "is_upcoming": True,
                "minutes_until": max(0, minutes_until),
                "predicted_direction": predicted_direction,
            })
    
    # Tarihe göre sırala
    events.sort(key=lambda x: x["timestamp"])
    return events


def generate_upcoming_earnings(days_ahead: int = 30) -> List[Dict]:
    """Generate upcoming earnings events"""
    earnings = []
    now = datetime.utcnow()
    
    for earnings_template in EARNINGS_DB:
        # Tarihi parse et
        event_date = datetime.strptime(earnings_template["date"], "%Y-%m-%d")
        event_time = earnings_template["time"]
        
        # Saati ayarla (after_market = 21:00, before_market = 13:30 UTC)
        if event_time == "after_market":
            event_date = event_date.replace(hour=21, minute=0)
        else:
            event_date = event_date.replace(hour=13, minute=30)
        
        # Tarih geçmiş mi kontrol et
        if event_date < now:
            # Çeyreklik kazançları simüle et
            event_date = event_date + timedelta(days=90)
        
        if (event_date - now).days <= days_ahead:
            minutes_until = int((event_date - now).total_seconds() / 60)
            
            # Kazanç tahmini (basit kurallar)
            confidence = 70
            if earnings_template["ticker"] in ["AAPL", "MSFT", "GOOGL"]:
                confidence = 80
            elif earnings_template["ticker"] == "TSLA":
                confidence = 50  # Tesla daha volatil
            
            # EPS tahmin vs önceki
            predicted_direction = "neutral"
            if earnings_template.get("eps_forecast") and earnings_template.get("previous_eps"):
                try:
                    forecast = float(earnings_template["eps_forecast"].replace("$", ""))
                    previous = float(earnings_template["previous_eps"].replace("$", ""))
                    if forecast > previous:
                        predicted_direction = "bullish"
                    elif forecast < previous:
                        predicted_direction = "bearish"
                except:
                    pass
            
            earnings.append({
                **earnings_template,
                "timestamp": event_date.isoformat(),
                "is_upcoming": True,
                "minutes_until": max(0, minutes_until),
                "confidence": confidence,
                "predicted_direction": predicted_direction,
            })
    
    earnings.sort(key=lambda x: x["timestamp"])
    return earnings


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get("/economic")
async def get_economic_calendar(
    days: int = Query(30, ge=1, le=90, description="Days ahead to fetch"),
    currency: Optional[str] = Query(None, description="Filter by currency (USD, EUR, etc.)")
):
    """
    Get upcoming economic calendar events with detailed analysis
    """
    try:
        events = generate_upcoming_events(days_ahead=days)
        
        if currency:
            events = [e for e in events if e["currency"].upper() == currency.upper()]
        
        return {
            "success": True,
            "count": len(events),
            "days_ahead": days,
            "events": events
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/earnings")
async def get_earnings_calendar(
    days: int = Query(30, ge=1, le=90, description="Days ahead to fetch"),
    sector: Optional[str] = Query(None, description="Filter by sector")
):
    """
    Get upcoming earnings calendar with AI analysis
    """
    try:
        earnings = generate_upcoming_earnings(days_ahead=days)
        
        if sector:
            earnings = [e for e in earnings if e["sector"].lower() == sector.lower()]
        
        return {
            "success": True,
            "count": len(earnings),
            "days_ahead": days,
            "earnings": earnings
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/today")
async def get_today_events():
    """
    Get all events happening today
    """
    try:
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0)
        today_end = now.replace(hour=23, minute=59, second=59)
        
        economic = generate_upcoming_events(days_ahead=1)
        earnings = generate_upcoming_earnings(days_ahead=1)
        
        # Sadece bugünküleri filtrele
        economic_today = [
            e for e in economic 
            if today_start <= datetime.fromisoformat(e["timestamp"]) <= today_end
        ]
        
        earnings_today = [
            e for e in earnings
            if today_start <= datetime.fromisoformat(e["timestamp"]) <= today_end
        ]
        
        return {
            "success": True,
            "date": now.strftime("%Y-%m-%d"),
            "economic_count": len(economic_today),
            "earnings_count": len(earnings_today),
            "economic": economic_today,
            "earnings": earnings_today
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/event/{event_id}")
async def get_event_details(event_id: str):
    """
    Get detailed information about a specific economic event with DeepSeek AI analysis
    """
    try:
        # Ekonomik olayları kontrol et
        for template in ECONOMIC_EVENTS_DB:
            if template["id"] == event_id:
                now = datetime.utcnow()
                next_date = get_next_event_date(template["schedule"], now)
                minutes_until = int((next_date - now).total_seconds() / 60)
                
                # DeepSeek AI Analysis
                event_data = {
                    **template,
                    "timestamp": next_date.isoformat(),
                    "is_upcoming": True,
                    "minutes_until": max(0, minutes_until),
                }
                
                ai_analysis = await analyze_economic_event_with_deepseek(event_data)
                
                return {
                    "success": True,
                    "event": {
                        **event_data,
                        **ai_analysis
                    }
                }
        
        # Kazançları kontrol et
        for template in EARNINGS_DB:
            if template["id"] == event_id:
                event_date = datetime.strptime(template["date"], "%Y-%m-%d")
                if template["time"] == "after_market":
                    event_date = event_date.replace(hour=21, minute=0)
                else:
                    event_date = event_date.replace(hour=13, minute=30)
                
                if event_date < datetime.utcnow():
                    event_date = event_date + timedelta(days=90)
                
                minutes_until = int((event_date - datetime.utcnow()).total_seconds() / 60)
                
                # DeepSeek AI Analysis
                event_data = {
                    **template,
                    "timestamp": event_date.isoformat(),
                    "is_upcoming": True,
                    "minutes_until": max(0, minutes_until),
                }
                
                ai_analysis = await analyze_earnings_with_deepseek(event_data)
                
                return {
                    "success": True,
                    "event": {
                        **event_data,
                        **ai_analysis
                    }
                }
        
        raise HTTPException(status_code=404, detail="Event not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# DEEPSEEK AI ANALYSIS
# =============================================================================

async def analyze_economic_event_with_deepseek(event_data: Dict) -> Dict:
    """
    Analyze economic event using DeepSeek-R1
    Returns AI-powered market impact prediction and scenarios
    """
    if not DEEP_SEEKR1:
        # Return fallback analysis if no API key
        return _fallback_economic_analysis(event_data)
    
    prompt = f"""Analyze this economic event and predict market impact scenarios:

EVENT: {event_data.get('title', 'Unknown')}
CURRENCY: {event_data.get('currency', 'USD')}
IMPACT LEVEL: {event_data.get('impact', 'Medium')}
PREVIOUS: {event_data.get('previous', 'N/A')}
FORECAST: {event_data.get('forecast', 'N/A')}
AFFECTED SYMBOLS: {', '.join(event_data.get('affected_symbols', []))}

Provide analysis in JSON format:
{{
    "predicted_direction": "bullish|bearish|neutral|volatile",
    "confidence": 0-100,
    "impact_analysis": "Detailed impact analysis in English",
    "impact_analysis_tr": "Detaylı etki analizi Türkçe",
    "scenarios": {{
        "better_than_expected": {{
            "direction": "bullish|bearish",
            "first_5min": "Expected price movement",
            "first_hour": "Expected price movement", 
            "day_close": "Expected price movement",
            "next_day": "Expected price movement",
            "impacts": [
                {{"symbol": "DXY", "direction": "bullish|bearish", "magnitude": "+0.3%"}},
                {{"symbol": "XAUUSD", "direction": "bullish|bearish", "magnitude": "-$8"}},
                {{"symbol": "NDX", "direction": "bullish|bearish", "magnitude": "+0.4%"}}
            ]
        }},
        "worse_than_expected": {{
            "direction": "bullish|bearish",
            "first_5min": "Expected price movement",
            "first_hour": "Expected price movement",
            "day_close": "Expected price movement",
            "next_day": "Expected price movement",
            "impacts": [
                {{"symbol": "DXY", "direction": "bullish|bearish", "magnitude": "-0.3%"}},
                {{"symbol": "XAUUSD", "direction": "bullish|bearish", "magnitude": "+$10"}},
                {{"symbol": "NDX", "direction": "bullish|bearish", "magnitude": "-0.5%"}}
            ]
        }},
        "as_expected": {{
            "direction": "neutral",
            "first_5min": "Expected price movement",
            "first_hour": "Expected price movement",
            "day_close": "Expected price movement",
            "impacts": []
        }}
    }},
    "trading_tips": "Key trading strategy tips"
}}

IMPORTANT: Include "impacts" array with affected symbols, their direction (bullish/bearish), and magnitude (e.g., "+0.3%", "-$8", "+0.4%"). Focus on DXY, XAUUSD, NDX, USOIL, VIX.
"""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEP_SEEKR1}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-reasoner",
                    "messages": [
                        {"role": "system", "content": "You are an expert financial analyst specializing in macroeconomic events and market impact prediction. Always respond in valid JSON format."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1500
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    print(f"[EconomicAI] DeepSeek error: {response.status}")
                    return _fallback_economic_analysis(event_data)
                
                data = await response.json()
                content = data["choices"][0]["message"]["content"]
                
                # Extract JSON from response
                try:
                    # Try to find JSON in the response
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = content[json_start:json_end]
                        ai_result = json.loads(json_str)
                        ai_result["ai_analyzed"] = True
                        ai_result["ai_model"] = "deepseek-reasoner"
                        return ai_result
                    else:
                        return _fallback_economic_analysis(event_data)
                except json.JSONDecodeError:
                    print(f"[EconomicAI] JSON parse error")
                    return _fallback_economic_analysis(event_data)
                    
    except Exception as e:
        print(f"[EconomicAI] Error: {e}")
        return _fallback_economic_analysis(event_data)


def _fallback_economic_analysis(event_data: Dict) -> Dict:
    """Fallback analysis when DeepSeek is unavailable"""
    impact = event_data.get('impact', 'Medium')
    currency = event_data.get('currency', 'USD')
    
    # Default scenarios based on impact level
    if impact == "High":
        return {
            "predicted_direction": "volatile",
            "confidence": 75,
            "impact_analysis": "High-impact event expected to cause significant market volatility. Multiple asset classes will be affected.",
            "impact_analysis_tr": "Yüksek etkili olay önemli piyasa volatilitesine neden olması bekleniyor. Birden fazla varlık sınıfı etkilenecek.",
            "scenarios": {
                "better_than_expected": {
                    "direction": "bullish" if currency == "USD" else "mixed",
                    "first_5min": f"{currency} +0.3% • XAUUSD -$8 • NDX +0.4%",
                    "first_hour": f"{currency} +0.5% momentum continues",
                    "day_close": "Trend extends, watch for profit-taking",
                    "next_day": "Possible reversal, monitor closely"
                },
                "worse_than_expected": {
                    "direction": "bearish" if currency == "USD" else "mixed",
                    "first_5min": f"{currency} -0.3% • XAUUSD +$10 • NDX -0.5%",
                    "first_hour": f"{currency} -0.6% as risk-off takes hold",
                    "day_close": "Extended move, consider counter-trend",
                    "next_day": "Mean reversion possible"
                },
                "as_expected": {
                    "direction": "neutral",
                    "first_5min": "Minimal movement ±0.1%",
                    "first_hour": "Range-bound consolidation",
                    "day_close": "Focus shifts to other catalysts"
                }
            },
            "trading_tips": "Use limit orders. Wait 5min post-release for volatility to settle. Watch for reversals after first hour.",
            "ai_analyzed": False,
            "ai_model": "fallback"
        }
    else:
        return {
            "predicted_direction": "neutral",
            "confidence": 60,
            "impact_analysis": "Medium-impact event with limited market reaction expected.",
            "impact_analysis_tr": "Sınırlı piyasa reaksiyonu beklenen orta etkili olay.",
            "scenarios": {
                "better_than_expected": {
                    "direction": "slightly_bullish",
                    "first_5min": f"{currency} +0.1% • Minor moves",
                    "first_hour": "Momentum fades quickly",
                    "day_close": "Little lasting impact",
                    "next_day": "Back to technicals"
                },
                "worse_than_expected": {
                    "direction": "slightly_bearish",
                    "first_5min": f"{currency} -0.1% • Minor moves",
                    "first_hour": "Quickly absorbed by market",
                    "day_close": "Negligible impact",
                    "next_day": "Normal trading resumes"
                },
                "as_expected": {
                    "direction": "neutral",
                    "first_5min": "No significant movement",
                    "first_hour": "Range-bound",
                    "day_close": "Minimal effect"
                }
            },
            "trading_tips": "Focus on technical levels. This event unlikely to change trend direction.",
            "ai_analyzed": False,
            "ai_model": "fallback"
        }


async def analyze_earnings_with_deepseek(event_data: Dict) -> Dict:
    """
    Analyze earnings event using DeepSeek-R1
    Returns AI-powered earnings prediction and scenarios
    """
    if not DEEP_SEEKR1:
        return _fallback_earnings_analysis(event_data)
    
    prompt = f"""Analyze this earnings report and predict stock and market impact:

COMPANY: {event_data.get('company', 'Unknown')}
TICKER: {event_data.get('ticker', 'UNKNOWN')}
SECTOR: {event_data.get('sector', 'Technology')}
EPS FORECAST: {event_data.get('eps_forecast', 'N/A')}
REVENUE FORECAST: {event_data.get('revenue_forecast', 'N/A')}
PREVIOUS EPS: {event_data.get('previous_eps', 'N/A')}
AFFECTED SYMBOLS: {', '.join(event_data.get('affected_symbols', []))}

Provide analysis in JSON format:
{{
    "predicted_direction": "bullish|bearish|neutral",
    "confidence": 0-100,
    "analysis": "Detailed analysis in English",
    "analysis_tr": "Detaylı analiz Türkçe",
    "scenarios": {{
        "beat": {{
            "direction": "bullish",
            "pre_market": "Expected stock move",
            "open": "Opening bell reaction",
            "first_hour": "First hour behavior",
            "sector_effect": "Impact on sector peers",
            "impacts": [
                {{"symbol": "{event_data.get('ticker', 'STOCK')}", "direction": "bullish", "magnitude": "+4%"}},
                {{"symbol": "NDX", "direction": "bullish", "magnitude": "+0.5%"}},
                {{"symbol": "VIX", "direction": "bearish", "magnitude": "-5%"}}
            ]
        }},
        "miss": {{
            "direction": "bearish",
            "pre_market": "Expected stock move",
            "open": "Opening bell reaction",
            "first_hour": "First hour behavior",
            "sector_effect": "Impact on sector peers",
            "impacts": [
                {{"symbol": "{event_data.get('ticker', 'STOCK')}", "direction": "bearish", "magnitude": "-6%"}},
                {{"symbol": "NDX", "direction": "bearish", "magnitude": "-0.4%"}},
                {{"symbol": "VIX", "direction": "bullish", "magnitude": "+8%"}}
            ]
        }},
        "mixed": {{
            "direction": "volatile",
            "pre_market": "Expected stock move",
            "guidance_importance": "Why guidance matters",
            "trading_approach": "How to trade mixed results",
            "impacts": [
                {{"symbol": "{event_data.get('ticker', 'STOCK')}", "direction": "volatile", "magnitude": "±2%"}},
                {{"symbol": "NDX", "direction": "neutral", "magnitude": "±0.2%"}}
            ]
        }},
        "inline": {{
            "direction": "neutral",
            "pre_market": "Expected stock move",
            "guidance_focus": "What to watch for",
            "impacts": [
                {{"symbol": "{event_data.get('ticker', 'STOCK')}", "direction": "neutral", "magnitude": "±1%"}}
            ]
        }}
    }},
    "key_metrics": ["Most important metrics to watch"],
    "trading_tips": "Key trading strategy tips"
}}

Consider: Company weight in indices, sector correlations, market sentiment, options implied moves.
"""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEP_SEEKR1}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-reasoner",
                    "messages": [
                        {"role": "system", "content": "You are an expert equity analyst specializing in earnings analysis and market impact prediction. Always respond in valid JSON format."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1500
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    return _fallback_earnings_analysis(event_data)
                
                data = await response.json()
                content = data["choices"][0]["message"]["content"]
                
                try:
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = content[json_start:json_end]
                        ai_result = json.loads(json_str)
                        ai_result["ai_analyzed"] = True
                        ai_result["ai_model"] = "deepseek-reasoner"
                        return ai_result
                    else:
                        return _fallback_earnings_analysis(event_data)
                except json.JSONDecodeError:
                    return _fallback_earnings_analysis(event_data)
                    
    except Exception as e:
        print(f"[EarningsAI] Error: {e}")
        return _fallback_earnings_analysis(event_data)


def _fallback_earnings_analysis(event_data: Dict) -> Dict:
    """Fallback analysis when DeepSeek is unavailable"""
    ticker = event_data.get('ticker', 'UNKNOWN')
    sector = event_data.get('sector', 'Technology')
    
    return {
        "predicted_direction": "neutral",
        "confidence": 70,
        "analysis": f"Standard earnings analysis for {ticker}. Watch for EPS and revenue surprises vs estimates.",
        "analysis_tr": f"{ticker} için standart kazanç analizi. EPS ve gelir tahminlere karşı sürprizleri izleyin.",
        "scenarios": {
            "beat": {
                "direction": "bullish",
                "pre_market": f"{ticker} +3-5% • Calls spike",
                "open": "Gap up, momentum buyers enter",
                "first_hour": "Watch for profit taking at highs",
                "sector_effect": f"{sector} peers likely rally"
            },
            "miss": {
                "direction": "bearish",
                "pre_market": f"{ticker} -4-7% • Put volume surges",
                "open": "Gap down, stop losses trigger",
                "first_hour": "Dead cat bounce possible, then fade",
                "sector_effect": f"{sector} peers may decline"
            },
            "mixed": {
                "direction": "volatile",
                "pre_market": f"{ticker} ±2% • Direction unclear",
                "guidance_importance": "Forward guidance becomes key driver",
                "trading_approach": "Wait for conference call clarity"
            },
            "inline": {
                "direction": "neutral",
                "pre_market": f"{ticker} ±1% • IV crush likely",
                "guidance_focus": "Stock direction depends on forward outlook"
            }
        },
        "key_metrics": ["EPS vs Estimate", "Revenue vs Estimate", "Forward Guidance", "Gross Margin"],
        "trading_tips": f"For {event_data.get('time', 'after-hours')} earnings, liquidity is lower. Consider waiting for regular session open.",
        "ai_analyzed": False,
        "ai_model": "fallback"
    }
