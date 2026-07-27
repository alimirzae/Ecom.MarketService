from fastapi import FastAPI

from api.v1.market import router as market_router

app = FastAPI(
    title="Ecom Market Service",
    version="1.0.0"
)

# Include API v1 routers
app.include_router(market_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "service": "Ecom Market Service",
        "status": "Running"
    }


@app.get("/health")
async def health():
    return {
        "status": "Healthy"
    }
