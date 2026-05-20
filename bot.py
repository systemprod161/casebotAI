import asyncio
import json
import os
import random
import websockets

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# =======================
# CONFIG
# =======================

BOT_TOKEN = os.getenv("8701511595:AAFr8dOEvt2O3nP3LqqbahuTvci5tX0jYkM")

WS_URL = "wss://ws3.gamecontent.io/"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# память статистики
stats = {
    "total_drops": 0,
    "high_value": 0,
    "low_value": 0,
    "history": []
}

subscribers = set()

# =======================
# WS ANALYZER
# =======================

def analyze_drop(drop):
    """простая логика анализа"""
    price = drop.get("price", 0)

    stats["total_drops"] += 1
    stats["history"].append(price)

    if price >= 100:
        stats["high_value"] += 1
    else:
        stats["low_value"] += 1


def get_advice(budget: float):
    """простые советы"""
    if stats["total_drops"] < 10:
        return "⚠️ Недостаточно данных для анализа"

    avg = sum(stats["history"]) / len(stats["history"])

    risk = stats["high_value"] / stats["total_drops"]

    if budget < 10:
        return "❌ Бюджет слишком маленький, риск высокий"

    if risk > 0.4:
        return "🔥 Сайт сейчас 'жирный', можно пробовать средние кейсы"

    if avg < 50:
        return "⚠️ Сейчас слабая отдача, лучше не рисковать"

    return "🟡 Ситуация средняя, играй аккуратно, не ставь больше 10–20% банка"


# =======================
# WS LOOP
# =======================

async def ws_worker():
    while True:
        try:
            async with websockets.connect(WS_URL) as ws:
                print("WS CONNECTED")

                while True:
                    msg = await ws.recv()

                    try:
                        data = json.loads(msg)
                    except:
                        continue

                    # если пришёл дроп
                    if isinstance(data, dict):
                        analyze_drop(data)

                        text = f"🎁 Дроп: {data.get('price', 0)}"

                        # отправка всем подписчикам
                        for uid in subscribers:
                            try:
                                await bot.send_message(uid, text)
                            except:
                                pass

        except Exception as e:
            print("WS ERROR:", e)
            await asyncio.sleep(5)


# =======================
# TELEGRAM COMMANDS
# =======================

@dp.message(Command("start"))
async def start(msg: types.Message):
    subscribers.add(msg.chat.id)

    await msg.answer(
        "🤖 Бот запущен\n\n"
        "Команды:\n"
        "/stats - статистика\n"
        "/advice <budget> - совет по бюджету\n"
    )


@dp.message(Command("stats"))
async def get_stats(msg: types.Message):
    if stats["total_drops"] == 0:
        await msg.answer("Нет данных")
        return

    avg = sum(stats["history"]) / len(stats["history"])

    await msg.answer(
        f"📊 Статистика:\n"
        f"Всего дропов: {stats['total_drops']}\n"
        f"Высоких: {stats['high_value']}\n"
        f"Низких: {stats['low_value']}\n"
        f"Среднее: {round(avg, 2)}"
    )


@dp.message(Command("advice"))
async def advice(msg: types.Message):
    try:
        budget = float(msg.text.split()[1])
    except:
        await msg.answer("Используй: /advice 100")
        return

    await msg.answer(get_advice(budget))


# =======================
# MAIN
# =======================

async def main():
    asyncio.create_task(ws_worker())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())