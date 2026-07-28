"""Market API endpoints for price data."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.database.database import SessionLocal
from app.dto.market_price_dto import MarketPriceDto
from app.services.market_service import MarketService
from app.repository.market_repository import MarketRepository


router = APIRouter(prefix="/market", tags=["Market"])


# ============================================================
# Pydantic Models for Request/Response
# ============================================================


class LatestPriceResponse(BaseModel):
    """Response model for latest prices endpoint."""

    success: bool = Field(..., description="Whether the request was successful")
    items: list[MarketPriceDto] = Field(..., description="List of latest prices")
    retrieved_at: datetime = Field(
        ..., description="Timestamp when data was retrieved"
    )


class RefreshRequest(BaseModel):
    """Request model for refresh endpoint."""

    provider: str = Field(default="navasan", description="Provider name")
    codes: list[str] = Field(
        default_factory=list, description="List of item codes to refresh"
    )


class RefreshResponse(BaseModel):
    """Response model for refresh endpoint."""

    success: bool = Field(..., description="Whether the refresh was successful")
    items: list[MarketPriceDto] = Field(
        ..., description="List of refreshed prices"
    )
    message: str = Field(..., description="Status message")


class HistoryRequest(BaseModel):
    """Request model for history endpoint."""

    code: Optional[str] = Field(None, description="Item code filter")
    from_date: Optional[datetime] = Field(
        None, description="Start date (inclusive)", alias="from"
    )
    to_date: Optional[datetime] = Field(
        None, description="End date (inclusive)", alias="to"
    )
    limit: int = Field(default=100, description="Maximum records per item")


class HistoryResponse(BaseModel):
    """Response model for history endpoint."""

    success: bool = Field(..., description="Whether the request was successful")
    items: list[MarketPriceDto] = Field(..., description="List of historical prices")
    total_count: int = Field(..., description="Total number of records")


# ============================================================
# Dependency Injection
# ============================================================


def get_db_session():
    """Get database session with proper cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_market_service(db=Depends(get_db_session)) -> MarketService:
    """Get MarketService instance with dependencies."""
    repository = MarketRepository(db)
    return MarketService(repository)


# ============================================================
# API Endpoints
# ============================================================


@router.get("/latest", response_model=LatestPriceResponse)
async def get_latest_prices(
    codes: Optional[str] = Query(
        None,
        description="Comma-separated list of item codes (e.g., 'usd,18ayar,sekkeh')",
        example="usd,18ayar",
    ),
    service: MarketService = Depends(get_market_service),
) -> LatestPriceResponse:
    """
    Get latest market prices.

    Returns cached data if valid, automatically refreshes if cache expired.

    - **codes**: Optional comma-separated list of item codes. If omitted, returns all active items.
    - Returns cached prices if not expired.
    - Automatically refreshes from provider if cache is stale.

    Raises:
        HTTPException 400: Invalid provider or codes
        HTTPException 502: Provider unavailable
        HTTPException 500: Repository error
    """
    try:
        # Parse codes from comma-separated string
        code_list: list[str] | None = None
        if codes:
            code_list = [c.strip() for c in codes.split(",") if c.strip()]

        # Call service (async)
        prices = await service.get_latest_prices(codes=code_list)

        return LatestPriceResponse(
            success=True,
            items=prices,
            retrieved_at=datetime.now(),
        )

    except ValueError as e:
        # Validation error (e.g., invalid provider)
        raise HTTPException(status_code=400, detail=str(e))

    except RuntimeError as e:
        # Provider error
        raise HTTPException(status_code=502, detail=f"Provider error: {str(e)}")

    except Exception as e:
        # Repository or other errors
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_prices(
    request: RefreshRequest,
    service: MarketService = Depends(get_market_service),
) -> RefreshResponse:
    """
    Force refresh prices from external provider.

    Ignores cache and always fetches fresh data from the provider.

    - **provider**: Name of the provider (default: "navasan")
    - **codes**: List of item codes to refresh. If empty, refreshes all active items.

    Raises:
        HTTPException 400: Invalid provider or codes
        HTTPException 502: Provider unavailable
        HTTPException 500: Repository error
    """
    try:
        # Call service with force=True (async)
        prices = await service.force_refresh(
            codes=request.codes if request.codes else None,
            provider_name=request.provider,
        )

        return RefreshResponse(
            success=True,
            items=prices,
            message=f"Successfully refreshed {len(prices)} prices from {request.provider}",
        )

    except ValueError as e:
        # Validation error (e.g., invalid provider)
        raise HTTPException(status_code=400, detail=str(e))

    except RuntimeError as e:
        # Provider error
        raise HTTPException(status_code=502, detail=f"Provider error: {str(e)}")

    except Exception as e:
        # Repository or other errors
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/history", response_model=HistoryResponse)
async def get_price_history(
    code: Optional[str] = Query(None, description="Item code filter"),
    from_date: Optional[datetime] = Query(
        None, description="Start date (inclusive)", alias="from"
    ),
    to_date: Optional[datetime] = Query(
        None, description="End date (inclusive)", alias="to"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records per item"),
    service: MarketService = Depends(get_market_service),
) -> HistoryResponse:
    """
    Get historical price data.

    Returns historical prices for specified items and date range.

    - **code**: Optional item code filter. If omitted, returns all items.
    - **from**: Optional start date (inclusive).
    - **to**: Optional end date (inclusive).
    - **limit**: Maximum number of records per item (default: 100, max: 1000).

    Raises:
        HTTPException 400: Invalid parameters
        HTTPException 500: Repository error
    """
    try:
        # Build code list
        code_list: list[str] | None = None
        if code:
            code_list = [c.strip() for c in code.split(",") if c.strip()]

        # Call service (get_price_history is sync)
        prices = service.get_price_history(
            codes=code_list,
            limit=limit,
        )

        return HistoryResponse(
            success=True,
            items=prices,
            total_count=len(prices),
        )

    except ValueError as e:
        # Validation error
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Repository or other errors
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
