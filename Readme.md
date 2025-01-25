# Vector Database API with FastAPI

This project provides a FastAPI-based API to manage vector database operations, including creating indexes, inserting (upserting) data, and performing similarity or ID-based searches. Currently, it supports **Pinecone** as the vector database provider.

## Features

- Create vector indexes in Pinecone.
- Upsert (insert or update) data into the vector database.
- Search for similar vectors or specific IDs with metadata filtering.

## Requirements

- Python 3.12
- FastAPI == 0.109.1
- Pinecone Client == 3.0.0
- Pydantic == 2.5.2
- Uvicorn == 0.24.0
- python-dotenv
- Docker (opcional)

## Instalación y Ejecución

### Usando Docker

1. Construir la imagen:
```bash
docker build -t vector-db-api .
```

2. Ejecutar el contenedor:
```bash
docker run -d -p 9000:9000 --name vector-db-container vector-db-api
```

3. Verificar que está funcionando:
- La API estará disponible en: http://localhost:9000/docs

4. Comandos útiles de Docker:
```bash
# Ver logs del contenedor
docker logs vector-db-container

# Detener el contenedor
docker stop vector-db-container

# Eliminar el contenedor
docker rm vector-db-container
```

### Instalación Local

Install the dependencies using:

```bash
pip install -r requirements.txt
```

## Environment Variables

The following environment variables are required:

- `PINECONE_API_KEY`: Your Pinecone API key.
- `MODEL_NAME`: Name of the embedding model to use.

## Usage

### 1. Start the Server

Run the FastAPI server using Uvicorn:

```bash
uvicorn main:app --reload
```

### 2. API Endpoints

#### Postman Collection
Para probar los endpoints más fácilmente, puedes usar nuestra colección de Postman:
[Vector DB API Collection](https://sumer-07062021.postman.co/workspace/SUMER~148b538f-9145-4526-8806-bb1cc611d3bd/collection/16642082-01b51a02-01f6-4a39-959e-d1f4675e4bd2?action=share&creator=16642082&active-environment=16640760-5fde9fd8-7328-4098-8d82-c9d5fa254624)

#### Create Index

Creates a vector index in Pinecone.

```bash
curl --location 'http://localhost:8000/vector-db/create_index/pinecone' \
--header 'Content-Type: application/json' \
--data '{
    "index_name": "startup",
    "dimension": 1024,
    "metric": "cosine",
    "cloud": "aws",
    "region": "us-east-1"
}'
```

#### Upsert Data

Upserts (inserts or updates) data into the specified namespace of a Pinecone index.

```bash
curl --location 'http://localhost:8000/vector-db/upsert_data/pinecone/startup' \
--header 'Content-Type: application/json' \
--data '{
    "namespace": "products",
    "records": [
        {
            "id": "pc1",
            "data": {"name": "computadora mac", "price": 213131.03131},
            "metadata": {"tags": ["mac"], "category": "tech", "price": 2000,  "id": "pc1"}
        },
        {
            "id": "pc2",
            "data": {"name": "computadora linux", "price": 200.03131},
            "metadata": {"tags": ["linux"], "category": "tech", "price": 1000,  "id": "pc2"}
        }
    ]
}'
```

#### Search

Performs a similarity search with optional metadata filters.

```bash
curl --location 'http://localhost:8000/vector-db/search/pinecone/startup' \
--header 'Content-Type: application/json' \
--data '{
    "query": "quiero comprar un pc",
    "top_k": 2,
    "ids": ["pc1", "pc2"],
    "namespace": "products",
    "metadata_filter": {
        "category": {
            "$eq": "tech"
        },
        "price": {
            "$gt": 200
        },
        "id": {
            "$eq": "pc1"
        }
    }
}'
```

## License

This project is licensed under the MIT License.
