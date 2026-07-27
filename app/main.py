from fastapi import FastAPI

app = FastAPI(
    title="Ecom Market Service",
    version="1.0.0"
)

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