from aiogram import types, Router, F
from aiogram.filters import Command
from app.services.deepseek_service import get_deepseek_response
from app.config import get_api_key

router = Router()

# Обработчик приветствия новых участников группы


@router.message(F.new_chat_members)
async def greet_new_member(message: types.Message):
    """
    Приветствует новых участников, когда они присоединяются к группе.
    """
    for user in message.new_chat_members:
        await message.reply(
            f"👋 Привет, {user.full_name}!\n"
            "Добро пожаловать в наш финансовый чат! "
            "Я могу помочь вам с вопросами о финансах. "
            "Просто отметьте меня в сообщении или напишите в личные сообщения."
        )

# Обработчик сообщений с тегом бота в группах


@router.message(F.chat.type.in_(["group", "supergroup"]))
async def answer_tagged(message: types.Message, bot):
    """
    Отвечает только на те сообщения, где бот был явно упомянут через @username или text_mention.
    """
    bot_user = await bot.me()
    bot_username = f"@{bot_user.username}"

    print(f"Received message in group: {message.text}")
    print(f"Bot username: {bot_username}")
    print(f"Message entities: {message.entities}")

    # Проверяем, был ли бот упомянут в сообщении
    mentioned = False
    if message.entities:
        for e in message.entities:
            print(f"Checking entity: {e.type}")
            if e.type == "mention":
                mention_text = message.text[e.offset:e.offset + e.length]
                print(f"Found mention: {mention_text}")
                if mention_text.lower() == bot_username.lower():
                    mentioned = True
                    print("Bot was mentioned!")
                    break
            elif e.type == "text_mention" and e.user and e.user.id == bot_user.id:
                mentioned = True
                print("Bot was text_mentioned!")
                break

    if not mentioned:
        print("Bot was not mentioned, ignoring message")
        return  # Не отвечаем, если бот не был упомянут

    # Удаляем тег бота из вопроса
    question = message.text
    for entity in message.entities:
        if entity.type == "mention":
            mention_text = message.text[entity.offset:entity.offset + entity.length]
            if mention_text.lower() == bot_username.lower():
                question = question.replace(mention_text, "").strip()
        elif entity.type == "text_mention" and entity.user and entity.user.id == bot_user.id:
            question = question.replace(
                message.text[entity.offset:entity.offset + entity.length], "").strip()

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
        # Обрабатываем ответ
        if "error" in response:
            await message.reply("Извините, произошла ошибка при обработке вашего запроса.")
        else:
            await message.reply(response["message"])
    except Exception as e:
        print(f"Error in group handler: {str(e)}")
        await message.reply("Извините, произошла ошибка при обработке вашего запроса.")

# Обработчик команды /help в группе


@router.message(Command("help"))
async def help_command(message: types.Message):
    """
    Отправляет справку по использованию бота в группе.
    """
    help_text = (
        "🤖 Я финансовый бот!\n\n"
        "Как использовать:\n"
        "1. Отметьте меня в сообщении с вопросом\n"
        "2. Или напишите мне в личные сообщения\n\n"
        "Я постараюсь дать краткий и полезный ответ на ваш финансовый вопрос."
    )
    await message.reply(help_text)
