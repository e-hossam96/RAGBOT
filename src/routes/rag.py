import json
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from .route_schemas import RagQueryConfig
from configs import ResponseConfig, OpenAIRoleConfig
from models.data_schemas import Vector
from models import QdrantVectorModel, OpenAILLMModel
from controllers import OpenAILLMController
from helpers import get_settings
import logging

rag_router = APIRouter(prefix="/rag", tags=["rag"])


@rag_router.post("/query")
async def chat(request: Request, rag_config: RagQueryConfig) -> JSONResponse:
    # almost same as search index at start
    app_settings = get_settings()
    vectordb_model = QdrantVectorModel(request.app.vectordb_client)
    embedding_model = OpenAILLMModel(embedding_client=request.app.embedding_client)
    generation_model = OpenAILLMModel(generation_client=request.app.generation_client)
    generation_controller = OpenAILLMController()

    prompt = generation_controller.process_prompt_text(
        rag_config.text,
        app_settings.GENERATION_LLM_MAX_PROMPT_TOKENS,
        app_settings.GENERATION_LLM_SPECIAL_TOKENS,
    )
    messages = generation_controller.construct_user_query(
        prompt=prompt, chat_history=rag_config.chat_history
    )
    ans = await generation_model.generate_text(
        model_name=app_settings.GENERATION_LLM_MODEL_NAME,
        messages=messages,
        max_output_tokens=app_settings.GENERATION_LLM_MAX_OUTPUT_TOKENS,
        temperature=app_settings.GENERATION_LLM_TEMPERATURE,
        tools=generation_controller.get_tools(),
    )

    if ans is None:
        return JSONResponse(
            content={"message": ResponseConfig.RAG_ANS_GENERATION_FAILED.value},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # handle function call responses
    while ans.choices[0].finish_reason == "tool_calls":
        tool_call = ans.choices[0].message.tool_calls[0].function
        tool_name = tool_call.name
        args = json.loads(tool_call.arguments)
        # get tool input parameters
        if "text" in args and tool_name == "search_knowledge_base":
            args["text"] = generation_controller.process_prompt_text(
                prompt_text=args["text"],
                max_tokens=app_settings.EMBEDDING_LLM_MAX_PROMPT_TOKENS,
                special_tokens=app_settings.EMBEDDING_LLM_SPECIAL_TOKENS,
            )
            vector = Vector(**args)
        else:
            return JSONResponse(
                content={"message": ResponseConfig.RAG_ANS_GENERATION_FAILED.value},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        # embed the text
        resp = await embedding_model.embed_text(
            vector.text, app_settings.EMBEDDING_LLM_MODEL_NAME
        )
        vector.vector = resp.data[0].embedding if resp is not None else resp
        if vector.vector is None:
            return JSONResponse(
                content={"message": ResponseConfig.EMBEDDING_FAILED.value},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        augmenttions = await vectordb_model.search_by_vector(vector, rag_config.limit)
        if len(augmenttions) == 0:
            return JSONResponse(
                content={"message": ResponseConfig.VECTORDB_SEARCH_FAILED.value},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        augmenttions = [aug.text for aug in augmenttions]
        augmenttions = generation_controller.process_augmentations(augmenttions)

        tool_call_result_message = {
            "role": OpenAIRoleConfig.TOOL.value,
            "content": json.dumps(
                {
                    "text": vector.text,
                    "relevant_knowledge": augmenttions,
                }
            ),
            "tool_call_id": ans.choices[0].message.tool_calls[0].id,
        }
        tool_messsage = ans.choices[0].message.to_dict()
        messages.extend([tool_messsage, tool_call_result_message])
        ans = await generation_model.generate_text(
            model_name=app_settings.GENERATION_LLM_MODEL_NAME,
            messages=messages,
            max_output_tokens=app_settings.GENERATION_LLM_MAX_OUTPUT_TOKENS,
            temperature=app_settings.GENERATION_LLM_TEMPERATURE,
            tools=generation_controller.get_tools(),
        )

    # finialize chat history and return
    messages.append(
        {
            "role": OpenAIRoleConfig.ASSISTANT.value,
            "content": ans.choices[0].message.content,
        }
    )
    messages = generation_controller.finalize_messages(messages)
    return JSONResponse(
        content={
            "message": ResponseConfig.RAG_ANS_GENERATION_SUCCEEDED.value,
            "response": ans.choices[0].message.content,
            "chat_history": messages,
        },
        status_code=status.HTTP_200_OK,
    )
