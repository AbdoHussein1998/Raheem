"""ASGI entry point."""
from dotenv import load_dotenv
load_dotenv()
from Api.ApiConfiguration.api_configurations import create_app
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
