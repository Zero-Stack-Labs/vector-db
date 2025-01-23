import os

from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")