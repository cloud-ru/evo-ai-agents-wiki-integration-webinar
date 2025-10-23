import logging
import os
from typing import Any
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.agent_base_url = os.getenv('AGENT_BASE_URL')
        self.agent_auth_token = os.getenv('AGENT_AUTH_TOKEN')
        
        if not all([self.bot_token, self.agent_base_url, self.agent_auth_token]):
            raise ValueError("Missing required environment variables. Please check your .env file.")
        
        self.application = Application.builder().token(self.bot_token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup command and message handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Message handler for all text messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = (
            "🤖 Привет! Я бот, который работает с AI-агентом.\n\n"
            "Просто отправь мне сообщение, и я передам его агенту для обработки.\n\n"
            "Используй /help для получения дополнительной информации."
        )
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = (
            "📋 Доступные команды:\n\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать это сообщение\n\n"
            "💬 Просто отправь любое текстовое сообщение, и я передам его AI-агенту для обработки."
        )
        await update.message.reply_text(help_message)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages"""
        user_message = update.message.text
        user_id = update.effective_user.id
        
        logger.info(f"Received message from user {user_id}: {user_message}")
        
        # Send "typing" indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Get response from agent
            agent_response = await self.get_agent_response(user_message)
            
            if agent_response:
                await update.message.reply_text(agent_response)
            else:
                await update.message.reply_text("Извините, не удалось получить ответ от агента. Попробуйте еще раз.")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await update.message.reply_text("Произошла ошибка при обработке вашего сообщения. Попробуйте еще раз.")
    
    async def get_agent_response(self, message: str) -> str:
        """Get response from the AI agent"""
        timeout_config = httpx.Timeout(5 * 60.0)
        
        async with httpx.AsyncClient(timeout=timeout_config) as httpx_client:
            httpx_client.headers["Authorization"] = f"Bearer {self.agent_auth_token}"
            
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=self.agent_base_url,
            )
            
            try:
                public_card = await resolver.get_agent_card()
                client = A2AClient(
                    httpx_client=httpx_client,
                    agent_card=public_card,
                )
                
                send_message_payload: dict[str, Any] = {
                    "message": {
                        "role": "user",
                        "parts": [{"kind": "text", "text": message}],
                        "messageId": uuid4().hex,
                    },
                }
                
                request = SendMessageRequest(
                    id=str(uuid4()), 
                    params=MessageSendParams(**send_message_payload)
                )
                
                response = await client.send_message(request)
                
                # Extract the LLM answer from the response
                result = response.model_dump(mode="json", exclude_none=True)
                
                if (
                    "result" in result
                    and "status" in result["result"]
                    and "message" in result["result"]["status"]
                ):
                    status_message = result["result"]["status"]["message"]
                    if "parts" in status_message:
                        for part in status_message["parts"]:
                            if part.get("kind") == "text":
                                return part["text"]
                
                return "Не удалось получить ответ от агента."
                
            except Exception as e:
                logger.error(f"Error communicating with agent: {e}")
                raise
    

def main():
    """Main function to run the bot"""
    try:
        bot = TelegramBot()
        bot.application.run_polling()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()
