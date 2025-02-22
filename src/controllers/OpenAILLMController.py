import json
from .BaseController import BaseController
from locales import rag_templates
from configs import OpenAIRoleConfig


class OpenAILLMController(BaseController):
    def __init__(self) -> None:
        super().__init__()

        self.tools = [  # one tool to search the vector db
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge_base",
                    "description": "search the knowledge base for texts similar to the input.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "the text used to search knowledge base",
                            },
                        },
                        "required": ["text"],
                        "additionalProperties": False,
                    },
                },
            }
        ]

    def get_tools(self) -> list[dict]:
        return self.tools

    def get_tools_aspects(self) -> list[str]:
        # return name and param names of tools
        tools_aspects = []
        for tool in self.tools:
            tool_aspects = {}
            tools_aspects["name"] = tool["function"]["name"]
            tool_aspects["param_names"] = tool["function"]["parameters"].keys()
            tools_aspects.append(tool_aspects)
        return tools_aspects

    def process_prompt_text(
        self,
        prompt_text: str,
        max_tokens: int = 1024,
        special_tokens: list[str] | None = None,
    ):
        prompt_tokens = prompt_text.split()
        if special_tokens is not None:
            for st in special_tokens:
                while st in prompt_tokens:
                    prompt_tokens.remove(st)
        prompt_tokens = prompt_tokens[:max_tokens]
        return " ".join(prompt_tokens).strip()

    def construct_user_query(
        self,
        prompt: str,
        chat_history: list[dict] | None = None,
    ) -> list[dict]:
        # to be used at the beginning of "rag/query" endpoint
        if chat_history is None:
            system_msg = rag_templates.system_prompt.substitute({})
            chat_history = [
                {"role": OpenAIRoleConfig.SYSTEM.value, "content": system_msg}
            ]
        # ensure all contents are json strings or strings
        # also, ensure function args for tool calls are json strings
        for m in chat_history:
            if "content" in m and isinstance(m["content"], dict):
                m["content"] = json.dumps(m["content"])
            elif "content" not in m:
                for tool in m["tool_calls"]:
                    tool["function"]["arguments"] = json.dumps(
                        tool["function"]["arguments"]
                    )
        chat_history.append(
            {
                "role": OpenAIRoleConfig.USER.value,
                "content": f"{prompt}",
            }
        )
        return chat_history

    def process_augmentations(self, augmentations: list[str]) -> str:
        augmentations = [
            rag_templates.document_prompt.substitute(
                {"doc_num": i + 1, "chunk_text": aug}
            )
            for i, aug in enumerate(augmentations)
        ]
        augmentations = "\n\n".join(augmentations)
        return augmentations

    def finalize_messages(self, messages: list[dict]) -> list[dict]:
        for message in messages:
            if "tool_calls" in message:
                message.pop("content", None)
                message.pop("refusal", None)
                for tool in message["tool_calls"]:
                    tool["function"]["arguments"] = json.loads(
                        tool["function"]["arguments"]
                    )
            elif message["role"] == "tool":
                message["content"] = json.loads(message["content"])
        return messages
