import uvicorn
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


if __name__ == '__main__':
    uvicorn.run('routers:app', reload=True)
