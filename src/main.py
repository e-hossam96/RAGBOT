"""Implementation of the main FastAPI application.

In this file we will define the main fastapi app and connect it \
with the different routes of the system.
"""

import wandb
import weave
from fastapi import FastAPI
from routes.base import base_router
from routes.data import data_router
from routes.index import index_router
from routes.rag import rag_router
from routes.eval import eval_router
from configs import VectorDBProviderConfig
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from qdrant_client import AsyncQdrantClient
from openai import AsyncOpenAI
from helpers import get_settings, Settings


def connect_mongo_client(
    app: FastAPI,
    app_settinigs: Settings,
) -> FastAPI:
    # get mongo connection and db client
    app.db_connection = AsyncIOMotorClient(
        host=app_settinigs.MONGODB_HOST, port=app_settinigs.MONGODB_PORT
    )
    app.db_client = app.db_connection[app_settinigs.MONGODB_DATABASE_NAME]
    return app


def connect_vectordb_client(
    app: FastAPI,
    app_settinigs: Settings,
) -> FastAPI:
    app.vectordb_client = None
    if app_settinigs.VECTORDB_PROVIDER == VectorDBProviderConfig.QDRANT.value:
        app.vectordb_client = AsyncQdrantClient(
            host=app_settinigs.VECTORDB_HOST, port=app_settinigs.VECTORDB_PORT
        )
    return app


def connect_generation_client(
    app: FastAPI,
    app_settinigs: Settings,
) -> FastAPI:
    app.generation_client = AsyncOpenAI(
        api_key=app_settinigs.OPENAI_API_KEY,
        base_url=app_settinigs.GENERATION_LLM_BASE_URL,
    )
    return app


def connect_evaluation_client(
    app: FastAPI,
    app_settinigs: Settings,
) -> FastAPI:
    app.evaluation_client = AsyncOpenAI(
        api_key=app_settinigs.OPENAI_API_KEY,
        base_url=app_settinigs.EVAL_LLM_BASE_URL,
    )
    return app


def connect_embedding_client(
    app: FastAPI,
    app_settinigs: Settings,
) -> FastAPI:
    app.embedding_client = AsyncOpenAI(
        api_key=app_settinigs.OPENAI_API_KEY,
        base_url=app_settinigs.EMBEDDING_LLM_BASE_URL,
    )
    return app


def connect_tracer_client(
    app: FastAPI,
    app_settinigs: Settings,
) -> FastAPI:
    _ = wandb.login(key=app_settinigs.WANDB_API_KEY)
    app.tracer_client = weave.init(project_name=app_settinigs.WEAVE_PROJECT_NAME)
    return app


@asynccontextmanager
async def connect_lifespan_clients(app: FastAPI):
    settings = get_settings()
    app = connect_mongo_client(app, settings)
    app = connect_vectordb_client(app, settings)
    app = connect_generation_client(app, settings)
    app = connect_embedding_client(app, settings)
    app = connect_tracer_client(app, settings)
    app = connect_evaluation_client(app, settings)
    yield
    app.db_connection.close()
    app.db_client = None
    app.vectordb_client = None
    app.generation_client = None
    app.evaluation_client = None
    app.embedding_client = None
    app.tracer_client = None


app = FastAPI(lifespan=connect_lifespan_clients)
app.include_router(base_router)
app.include_router(data_router)
app.include_router(index_router)
app.include_router(rag_router)
app.include_router(eval_router)
