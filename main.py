from fastapi import FastAPI
from routes.route import router
import os

os.makedirs("data", exist_ok=True)

app = FastAPI()

app.include_router(router)

