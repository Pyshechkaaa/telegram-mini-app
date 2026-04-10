import random
import datetime
import asyncio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
import uvicorn

TOKEN = "8667775358:AAEGTOTAoEmZsuQLE54eA60OQXqTCIbLTTM"
WEBAPP_URL = "https://safeguard-strongman-phony.ngrok-free.dev"

app = FastAPI()

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ====== БАЗА (пока в памяти) ======
users = {}

# ====== HTML прямо внутри ======
html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
body {
    background: #0f172a;
    color: white;
    font-family: Arial;
    text-align: center;
}
.btn {
    padding: 15px;
    margin: 10px;
    border-radius: 10px;
    cursor: pointer;
    background: #1e293b;
    color: white;
}
</style>
</head>

<body>

<h1>📈 Crypto Signals</h1>

<button class="btn" onclick="getSignal()">Получить сигнал</button>

<div id="result"></div>

<script>
const tg = window.Telegram.WebApp;
tg.expand();

function getSignal() {
    fetch(`/signal/${tg.initDataUnsafe.user.id}`)
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            document.getElementById("result").innerHTML = data.error;
            return;
        }

        let color = data.direction === "UP" ? "green" : "red";

        document.getElementById("result").innerHTML = `
            <h2>${data.pair}</h2>
            <h2 style="color:${color}">
                ${data.direction}
            </h2>
            <p>Confidence: ${data.confidence}%</p>
        `;
    });
}
</script>

</body>
</html>
"""

# ====== API ======

@app.get("/")
def home():
    return HTMLResponse(html)

@app.get("/signal/{user_id}")
def get_signal(user_id: int):
    if user_id not in users:
        users[user_id] = {
            "free_used": False,
            "sub_until": None,
            "referrer": None,
            "balance": 0
        }

    user = users[user_id]
    now = datetime.datetime.now()

    # подписка
    if user["sub_until"] and now < user["sub_until"]:
        return generate_signal()

    # бесплатный сигнал
    if not user["free_used"]:
        user["free_used"] = True
        return generate_signal()

    return {"error": "Нужна подписка"}

def generate_signal():
    return {
        "pair": "BTC/USDT",
        "direction": random.choice(["UP", "DOWN"]),
        "confidence": random.randint(60, 95)
    }

# ====== БОТ ======

@dp.message(lambda msg: msg.text == "/start")
async def start(msg: types.Message):
    user_id = msg.from_user.id

    if user_id not in users:
        users[user_id] = {
            "free_used": False,
            "sub_until": None,
            "referrer": None,
            "balance": 0
        }

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text="🚀 Открыть приложение",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )]
        ],
        resize_keyboard=True
    )

    await msg.answer("Жми кнопку 👇", reply_markup=kb)

# ====== ЗАПУСК ВСЕГО ======

async def main():
    # запускаем API
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)

    # запускаем всё параллельно
    await asyncio.gather(
        server.serve(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Выход")