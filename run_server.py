import uvicorn
from pie.config import settings

if __name__ == "__main__":
    print(f"Starting PIE FastAPI Server at http://{settings.HOST}:{settings.PORT}")
    print("API docs available at: http://127.0.0.1:8004/docs")
    uvicorn.run(
        "pie.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
