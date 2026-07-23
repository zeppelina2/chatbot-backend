from ollama import AsyncClient
from app.schemas import MessageSchema


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

    
    async def generate_async(self, messages: list[MessageSchema | dict]) -> dict:
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
        
        print("messages", messages)
        
        try:
            response = await self.async_client.chat(
                model=self.ollama_model,
                messages=messages
            )

            print("response", response)

            return response
        except Exception as e:
            raise Exception(f"Ошибка при запросе к Ollama: {str(e)}") from e
