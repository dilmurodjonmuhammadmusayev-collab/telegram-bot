import asyncio
import logging
import gspread

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from google.oauth2.service_account import Credentials

# ================= LOGGING =================
logging.basicConfig(level=logging.INFO)

# ================= TOKEN + ADMIN =================
TOKEN = "8422029302:AAFBGSnIzv1J0EFW-rk55eHm-u2n7-nD8V0"
ADMIN_ID = 8476112476

# ================= GOOGLE SHEETS =================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "credentials.json",
    scopes=scope
)

client = gspread.authorize(creds)

# Spreadsheet ochish
sheet = client.open_by_key(
    "1oXPXRDJDZtoDJE3qKvznVXoCoKTEcv1tXjxTpzYEhKw"
).sheet1

# ================= HEADER CHECK =================
headers = sheet.row_values(1)

if not headers:
    sheet.append_row(["product", "code", "price", "stock", "image"])

# ================= BOT =================
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# ================= FSM =================
class AddProduct(StatesGroup):
    name = State()
    code = State()
    price = State()
    stock = State()
    image = State()

# ================= START =================
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "📦 Mahsulot qidiring.\n\n"
        "Masalan: <b>lampa</b>\n\n"
        "Admin uchun: /add"
    )

# ================= ADMIN ADD =================
@dp.message(Command("add"))
async def add_product(message: types.Message, state: FSMContext):

    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Siz admin emassiz")
        return

    await state.clear()

    await message.answer("📦 Mahsulot nomini yuboring:")
    await state.set_state(AddProduct.name)

# ================= STEP 1 =================
@dp.message(AddProduct.name)
async def product_name(message: types.Message, state: FSMContext):

    if not message.text:
        await message.answer("❌ Text yuboring")
        return

    await state.update_data(name=message.text.strip())

    await message.answer("🔢 Mahsulot kodini yuboring:")
    await state.set_state(AddProduct.code)

# ================= STEP 2 =================
@dp.message(AddProduct.code)
async def product_code(message: types.Message, state: FSMContext):

    if not message.text:
        await message.answer("❌ Kod yuboring")
        return

    await state.update_data(code=message.text.strip())

    await message.answer("💰 Narxini yuboring:")
    await state.set_state(AddProduct.price)

# ================= STEP 3 =================
@dp.message(AddProduct.price)
async def product_price(message: types.Message, state: FSMContext):

    if not message.text:
        await message.answer("❌ Narx yuboring")
        return

    await state.update_data(price=message.text.strip())

    await message.answer("📦 Soni nechta?")
    await state.set_state(AddProduct.stock)

# ================= STEP 4 =================
@dp.message(AddProduct.stock)
async def product_stock(message: types.Message, state: FSMContext):

    if not message.text:
        await message.answer("❌ Son yuboring")
        return

    await state.update_data(stock=message.text.strip())

    await message.answer("📸 Endi mahsulot rasmini yuboring:")
    await state.set_state(AddProduct.image)

# ================= STEP 5 SAVE =================
@dp.message(AddProduct.image, F.photo)
async def product_image(message: types.Message, state: FSMContext):

    file_id = message.photo[-1].file_id

    data = await state.get_data()

    try:
        sheet.append_row([
            data["name"],
            data["code"],
            data["price"],
            data["stock"],
            file_id
        ])

        await message.answer("✅ Mahsulot saqlandi")

    except Exception as e:
        await message.answer(f"❌ Xatolik:\n{e}")

    await state.clear()

# ================= IMAGE REQUIRED =================
@dp.message(AddProduct.image)
async def image_required(message: types.Message):
    await message.answer("❌ Iltimos rasm yuboring")

# ================= SEARCH =================
@dp.message(F.text & ~F.text.startswith("/"))
async def search_product(message: types.Message):

    text = message.text.strip().lower()

    try:
        data = sheet.get_all_records()

    except Exception as e:
        await message.answer(f"❌ Google Sheet xatosi:\n{e}")
        return

    found = False

    for row in data:

        product_name = str(row.get("product", "")).strip().lower()

        # PARTIAL SEARCH
        if text in product_name:

            caption = (
                f"📦 <b>Mahsulot:</b> {row.get('product')}\n"
                f"🔢 <b>Kod:</b> {row.get('code')}\n"
                f"💰 <b>Narx:</b> {row.get('price')}\n"
                f"📦 <b>Soni:</b> {row.get('stock')}"
            )

            file_id = row.get("image")

            try:
                if file_id:
                    await message.answer_photo(
                        photo=file_id,
                        caption=caption
                    )
                else:
                    await message.answer(caption)

            except Exception:
                await message.answer(caption)

            found = True

    if not found:
        await message.answer("❌ Mahsulot topilmadi")

# ================= MAIN =================
async def main():

    print("🚀 BOT ISHGA TUSHDI")

    await dp.start_polling(bot)

# ================= RUN =================
if __name__ == "__main__":
    asyncio.run(main())
