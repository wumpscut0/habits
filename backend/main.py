import uvicorn
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


if __name__ == '__main__':
    from backend.routers import app
    uvicorn.run(app)
