import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import settings
from obd_handler import OBDHandler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Инициализация OBD обработчика
obd_handler = OBDHandler()


def format_errors(errors: list) -> str:
    """Форматирование списка ошибок для вывода"""
    if not errors:
        return "✅ Ошибок не обнаружено"
    
    text = "⚠️ Обнаружены ошибки:\n\n"
    for i, error in enumerate(errors, 1):
        text += f"{i}. {error.get('code', 'N/A')}\n"
        if error.get('description'):
            text += f"   {error['description']}\n"
        text += "\n"
    return text


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="📊 Все данные", callback_data="all_data"))
    keyboard.add(InlineKeyboardButton(text="🌡️ Температура", callback_data="temperature"))
    keyboard.add(InlineKeyboardButton(text="⚠️ Ошибки", callback_data="errors"))
    keyboard.add(InlineKeyboardButton(text="🔌 Подключить OBD", callback_data="connect"))
    keyboard.add(InlineKeyboardButton(text="❌ Отключить OBD", callback_data="disconnect"))
    keyboard.adjust(2, 2, 1)
    
    await message.answer(
        "🚗 Добро пожаловать в Mercedes OBD бот!\n\n"
        "Выберите действие:",
        reply_markup=keyboard.as_markup()
    )


@dp.message(Command("connect"))
async def cmd_connect(message: Message):
    """Обработчик команды /connect"""
    await message.answer("⏳ Подключение к OBD адаптеру...")
    
    if obd_handler.connect():
        await message.answer("✅ Успешно подключено к OBD адаптеру!")
    else:
        await message.answer(
            "❌ Не удалось подключиться к OBD адаптеру.\n\n"
            "Проверьте:\n"
            "• Адаптер подключен и включен\n"
            "• Bluetooth соединение установлено\n"
            "• Правильно указан порт в настройках"
        )


@dp.message(Command("disconnect"))
async def cmd_disconnect(message: Message):
    """Обработчик команды /disconnect"""
    obd_handler.disconnect()
    await message.answer("🔌 Отключено от OBD адаптера")


@dp.message(Command("status"))
async def cmd_status(message: Message):
    """Обработчик команды /status"""
    status = "🟢 Подключено" if obd_handler.is_connected else "🔴 Не подключено"
    await message.answer(f"Статус OBD: {status}")


@dp.message(Command("errors"))
async def cmd_errors(message: Message):
    """Обработчик команды /errors"""
    if not obd_handler.is_connected:
        await message.answer("❌ Сначала подключитесь к OBD адаптеру (/connect)")
        return
    
    errors = obd_handler.get_errors()
    await message.answer(format_errors(errors))


@dp.message(Command("clear_errors"))
async def cmd_clear_errors(message: Message):
    """Обработчик команды /clear_errors"""
    if not obd_handler.is_connected:
        await message.answer("❌ Сначала подключитесь к OBD адаптеру (/connect)")
        return
    
    if obd_handler.clear_errors():
        await message.answer("✅ Коды ошибок очищены")
    else:
        await message.answer("❌ Не удалось очистить коды ошибок")


@dp.message(Command("temperature"))
async def cmd_temperature(message: Message):
    """Обработчик команды /temperature"""
    if not obd_handler.is_connected:
        await message.answer("❌ Сначала подключитесь к OBD адаптеру (/connect)")
        return
    
    coolant_temp = obd_handler.get_temperature("coolant")
    intake_temp = obd_handler.get_temperature("intake")
    
    text = "🌡️ Температура:\n\n"
    if coolant_temp is not None:
        text += f"Охлаждающая жидкость: {coolant_temp:.1f}°C\n"
    else:
        text += "Охлаждающая жидкость: N/A\n"
    
    if intake_temp is not None:
        text += f"Впускной воздух: {intake_temp:.1f}°C\n"
    else:
        text += "Впускной воздух: N/A\n"
    
    await message.answer(text)


@dp.message(Command("data"))
async def cmd_data(message: Message):
    """Обработчик команды /data - все данные"""
    if not obd_handler.is_connected:
        await message.answer("❌ Сначала подключитесь к OBD адаптеру (/connect)")
        return
    
    data = obd_handler.get_all_data()
    
    text = "📊 Данные OBD:\n\n"
    text += f"🔌 Статус: {'🟢 Подключено' if data['connected'] else '🔴 Не подключено'}\n\n"
    
    if data['rpm'] is not None:
        text += f"⚙️ Обороты: {data['rpm']:.0f} об/мин\n"
    if data['speed'] is not None:
        text += f"🚗 Скорость: {data['speed']:.0f} км/ч\n"
    if data['coolant_temp'] is not None:
        text += f"🌡️ Температура охлаждающей жидкости: {data['coolant_temp']:.1f}°C\n"
    if data['intake_temp'] is not None:
        text += f"🌡️ Температура впускного воздуха: {data['intake_temp']:.1f}°C\n"
    if data['fuel_level'] is not None:
        text += f"⛽ Уровень топлива: {data['fuel_level']:.1f}%\n"
    if data['engine_load'] is not None:
        text += f"⚡ Нагрузка двигателя: {data['engine_load']:.1f}%\n"
    
    text += "\n" + format_errors(data['errors'])
    
    await message.answer(text)


@dp.callback_query(F.data)
async def process_callback(callback: types.CallbackQuery):
    """Обработчик callback кнопок"""
    await callback.answer()
    
    if callback.data == "connect":
        await callback.message.answer("⏳ Подключение к OBD адаптеру...")
        if obd_handler.connect():
            await callback.message.answer("✅ Успешно подключено к OBD адаптеру!")
        else:
            await callback.message.answer("❌ Не удалось подключиться к OBD адаптеру.")
    
    elif callback.data == "disconnect":
        obd_handler.disconnect()
        await callback.message.answer("🔌 Отключено от OBD адаптера")
    
    elif callback.data == "errors":
        if not obd_handler.is_connected:
            await callback.message.answer("❌ Сначала подключитесь к OBD адаптеру")
            return
        errors = obd_handler.get_errors()
        await callback.message.answer(format_errors(errors))
    
    elif callback.data == "temperature":
        if not obd_handler.is_connected:
            await callback.message.answer("❌ Сначала подключитесь к OBD адаптеру")
            return
        coolant_temp = obd_handler.get_temperature("coolant")
        intake_temp = obd_handler.get_temperature("intake")
        text = "🌡️ Температура:\n\n"
        if coolant_temp is not None:
            text += f"Охлаждающая жидкость: {coolant_temp:.1f}°C\n"
        if intake_temp is not None:
            text += f"Впускной воздух: {intake_temp:.1f}°C\n"
        await callback.message.answer(text)
    
    elif callback.data == "all_data":
        if not obd_handler.is_connected:
            await callback.message.answer("❌ Сначала подключитесь к OBD адаптеру")
            return
        data = obd_handler.get_all_data()
        text = "📊 Данные OBD:\n\n"
        if data['rpm'] is not None:
            text += f"⚙️ Обороты: {data['rpm']:.0f} об/мин\n"
        if data['speed'] is not None:
            text += f"🚗 Скорость: {data['speed']:.0f} км/ч\n"
        if data['coolant_temp'] is not None:
            text += f"🌡️ Температура охлаждающей жидкости: {data['coolant_temp']:.1f}°C\n"
        if data['intake_temp'] is not None:
            text += f"🌡️ Температура впускного воздуха: {data['intake_temp']:.1f}°C\n"
        if data['fuel_level'] is not None:
            text += f"⛽ Уровень топлива: {data['fuel_level']:.1f}%\n"
        if data['engine_load'] is not None:
            text += f"⚡ Нагрузка двигателя: {data['engine_load']:.1f}%\n"
        text += "\n" + format_errors(data['errors'])
        await callback.message.answer(text)


async def main():
    """Главная функция запуска бота"""
    logger.info("Запуск бота...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        obd_handler.disconnect()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

