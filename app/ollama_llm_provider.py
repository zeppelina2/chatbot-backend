from ollama import AsyncClient
from uuid import UUID, uuid4

from app.schemas import MessageListSchema, MessageSchema


class OllamaLLMProvider:
    """
    Провайдер для работы с Ollama LLM.
    
    Обеспечивает асинхронные методы для генерации ответов
    через локально запущенный Ollama сервер
    """
    
    def __init__(self, ollama_url, ollama_model, ollama_timeout):
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.ollama_timeout = ollama_timeout
        
        # Асинхронный клиент
        self.async_client = AsyncClient(
            host=ollama_url,
            timeout=ollama_timeout
        )

    
    async def generate_async(self, messages: MessageListSchema) -> MessageSchema:
        """
        Асинхронная генерация ответа от LLM.
        
        Args:
            messages: История сообщений диалога
            model: Имя модели
            
        Returns:
            Словарь с ответом LLM
        
        Raises:
            Exception: Если запрос не удалось выполнить
        """
        
        format_messages = [{ "content": "/no_think", "role": "system" }] + [
            {"content": message.content, "role": message.role} for message in messages.messages
        ]
        
        try:
            response = await self.async_client.chat(
                model=self.ollama_model,
                messages=format_messages
            )

            print("response", response)
            
            message_from_llm = MessageSchema(
                message_id = str(uuid4()),
                content = response.message.content,
                created_at=response.created_at,
                updated_at=response.created_at,
                role = "assistant"
            )

            return message_from_llm
        except Exception as e:
            raise Exception(f"Ошибка при запросе к Ollama: {str(e)}") from e
