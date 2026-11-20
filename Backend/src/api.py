"""ASGI entry point."""
from dotenv import load_dotenv
load_dotenv()
import uvicorn
   

from Api.ApiConfiguration.api_configurations import create_app
app = create_app()

if __name__ == "__main__":

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)


