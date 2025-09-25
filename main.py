import fastapi
from fastapi import FastAPI

app = FastAPI()


@app.get('/home')
async def home_greetings():
    return {'message' : 'this is the backend ulr'}