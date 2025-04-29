from aiogram import types, Router, F
from aiogram.filters import Command
from app.services.deepseek_service import get_deepseek_response
from app.config import get_api_key

router = Router()

# Обработчик команды /start в личных сообщениях


@router.message(Command("start"))
async def start_command(message: types.Message):
    """
    Отправляет приветственное сообщение при старте диалога с ботом в личке.
    """
    welcome_text = (
        "👋 Привет! Я финансовый бот.\n\n"
        "Я могу помочь вам с вопросами о финансах. "
        "Просто напишите ваш вопрос, и я постараюсь дать краткий и полезный ответ.\n\n"
        "Используйте /help для получения дополнительной информации."
    )
    await message.answer(welcome_text)

# Обработчик команды /help в личных сообщениях


@router.message(Command("help"))
async def help_command(message: types.Message):
    """
    Отправляет справку по использованию бота в личных сообщениях.
    """
    help_text = (
        "🤖 Я финансовый бот!\n\n"
        "Как использовать:\n"
        "1. Просто напишите ваш вопрос\n"
        "2. Я постараюсь дать краткий и полезный ответ\n\n"
        "Примеры вопросов:\n"
        "- Как начать инвестировать?\n"
        "- Что такое диверсификация?\n"
        "- Как составить бюджет?"
    )
    await message.answer(help_text)

# Обработчик всех остальных сообщений в личных сообщениях


@router.message(F.chat.type == "private")
async def answer_private(message: types.Message):
    """
    Обрабатывает любые сообщения в личке и отправляет их в DeepSeek для получения ответа.
    """
    question = message.text
    try:
        # Получаем API-ключ (для проверки наличия)
        api_key = get_api_key("ProAI_Test_20241219")
        # Получаем ответ от DeepSeek
        response = get_deepseek_response(
            provider_id="ProAI_Test_20241219",
            assistant_name="FinanceBot",
            user_message=question,
            prompt="Отвечай кратко и по существу на финансовые вопросы. И отвечай без выделения текста."
        )
        print(response)  # Для отладки
        # Обрабатываем ответ
        if "error" in response:
            await message.answer("Извините, произошла ошибка при обработке вашего запроса.")
        else:
            await message.answer(response["message"])
    except Exception as e:
        print(f"Error in private handler: {str(e)}")
        await message.answer("Извините, произошла ошибка при обработке вашего запроса.")
