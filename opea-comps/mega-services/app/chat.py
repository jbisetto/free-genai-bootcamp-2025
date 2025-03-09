from comps import MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceRoleType, ServiceType
from comps.cores.mega.utils import handle_message
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo,
)
from fastapi import Request

class Chat:
    def __init__(self):
        print("Chat service initialized")
        self.megaservice = ServiceOrchestrator()
        self.endpoint = "/v1/chat/bootcamp"
        self.host = "0.0.0.0"
        self.port = 8888

    def add_remote_service(self):
        print("Adding remote service")

    def start(self):
        print("Starting chat service")  

        self.service = MicroService(
            self.__class__.__name__,
            service_role=ServiceRoleType.MEGASERVICE,
            host=self.host,
            port=self.port,
            endpoint=self.endpoint,
            input_datatype=ChatCompletionRequest,
            output_datatype=ChatCompletionResponse,
        )

        self.service.add_route(self.endpoint, self.handle_request, methods=["POST"])

        self.service.start()

    def handle_request(self, request):
        print("Handling chat request")
        return ChatCompletionResponse(
            id="1234567890",
            object="chat.completion",
            created=1677662400,
            model="gpt-3.5-turbo",
            choices=[
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello, how can I help you today?"
                    }
                }
            ],
            usage=UsageInfo(
                prompt_tokens=100,
                completion_tokens=100,
                total_tokens=200
            )
        )

if __name__ == "__main__":
    chat = Chat()
    chat.add_remote_service()
    chat.start()    