import logging
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from nlp_model import predict_issue_by_merk
from keep_alive import keep_alive  # <- Tambahan agar Replit selalu hidup

# Token Bot Telegram
TOKEN = '7739754258:AAEtT6m0gWenQOoE7AXa7bPhLOeKh47YtEc'

# Logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Data pengguna disimpan sementara di memori
USER_DATA = {}

# Alamat dan jam buka
ALAMAT = "TRIA KURNIA CELL, Jl. Dewi Sartika No.7 Blok A, RT.003/RW.007, Margahayu Timur, Kec. Bekasi Timur, Kota Bekasi, Jawa Barat 17113"
JAM_BUKA = (
    "\n\u23F0 *Jam Operasional:*",
    "- Senin - Minggu: 08.00 - 23.00 WIB"
)

# Simpan data ke Google Sheet
def simpan_ke_google_sheet(nama, merk_hp, keluhan, kerusakan, estimasi, kode):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("triakurniabot-8a15dd568380.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("TriaKurniaData").sheet1
    sheet.append_row([nama, merk_hp, keluhan, kerusakan, f"Rp{estimasi}", kode])

# Mulai percakapan
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Sebelum kita mulai, bisa sebutkan nama Anda?")
    USER_DATA[update.message.chat.id] = {'stage': 'nama'}

# Handle input pesan dari pengguna
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    user_input = update.message.text.strip()

    if chat_id not in USER_DATA:
        return

    stage = USER_DATA[chat_id]['stage']

    if stage == 'nama':
        USER_DATA[chat_id]['nama'] = user_input
        USER_DATA[chat_id]['stage'] = 'merk_hp'

        keyboard = [
            [InlineKeyboardButton("Samsung", callback_data='samsung')],
            [InlineKeyboardButton("Xiaomi", callback_data='xiaomi')],
            [InlineKeyboardButton("Apple", callback_data='apple')],
            [InlineKeyboardButton("Lainnya", callback_data='other')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Sekarang, bisa pilih merk HP Anda:", reply_markup=reply_markup)

# Handle tombol-tombol (Inline Keyboard)
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat.id
    await query.answer()

    if chat_id not in USER_DATA:
        return

    choice = query.data
    stage = USER_DATA[chat_id].get('stage')

    if stage == 'merk_hp' and choice in ['samsung', 'xiaomi', 'apple', 'other']:
        USER_DATA[chat_id]['merk_hp'] = choice
        USER_DATA[chat_id]['stage'] = 'keluhan'

        keyboard = [
            [InlineKeyboardButton("Layar rusak", callback_data='layar')],
            [InlineKeyboardButton("Baterai cepat habis", callback_data='baterai')],
            [InlineKeyboardButton("Kamera rusak", callback_data='kamera')],
            [InlineKeyboardButton("Mati total", callback_data='mati_total')],
            [InlineKeyboardButton("Lainnya", callback_data='lainnya')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"Sekarang, bisa pilih keluhan pada HP {choice}:", reply_markup=reply_markup)

    elif stage == 'keluhan' and choice in ['layar', 'baterai', 'kamera', 'mati_total', 'lainnya']:
        USER_DATA[chat_id]['keluhan'] = choice
        merk_hp = USER_DATA[chat_id]['merk_hp']
        kerusakan, estimasi = predict_issue_by_merk(merk_hp, choice)
        USER_DATA[chat_id]['kerusakan'] = kerusakan
        USER_DATA[chat_id]['estimasi'] = estimasi
        USER_DATA[chat_id]['stage'] = 'service_choice'

        response = (
            f"\U0001F527 Perkiraan kerusakan: *{kerusakan}*\n"
            f"\U0001F4B0 Estimasi biaya: *Rp{estimasi}*"
        )
        keyboard = [
            [InlineKeyboardButton("Service di tempat kami", callback_data='service')],
            [InlineKeyboardButton("Tidak ingin service", callback_data='no_service')],
            [InlineKeyboardButton("Lihat solusi lainnya", callback_data='solutions')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(response + "\n\nApakah Anda ingin service di tempat kami?", reply_markup=reply_markup, parse_mode='Markdown')

    elif choice == 'service':
        kode = random.randint(10000, 99999)
        USER_DATA[chat_id]['kode'] = kode
        data = USER_DATA[chat_id]

        simpan_ke_google_sheet(
            data['nama'],
            data['merk_hp'],
            data['keluhan'],
            data['kerusakan'],
            data['estimasi'],
            kode
        )

        await query.edit_message_text(
            f"Terima kasih telah memilih layanan kami.\n"
            f"Silakan kirim HP Anda ke alamat berikut:\n\n{ALAMAT}\n\n"
            f"Kode Pendaftaran Anda: *{kode}*\n\n"
            f"Untuk pembayaran silakan transfer ke rekening 123-456-7890 atas nama TRIA KURNIA SERVICE."
            f"{''.join(JAM_BUKA)}",
            parse_mode='Markdown'
        )
        USER_DATA[chat_id]['stage'] = 'selesai'

    elif choice == 'no_service':
        await query.edit_message_text("Terima kasih! Jika Anda berubah pikiran, kami siap membantu kapan saja.")
        del USER_DATA[chat_id]

    elif choice == 'solutions':
        solutions = (
            "Berikut solusi umum:\n"
            "1. Layar pecah: Ganti LCD berkualitas tinggi.\n"
            "2. Baterai boros: Ganti baterai baru.\n"
            "3. Kamera rusak: Ganti modul kamera."
        )
        await query.edit_message_text(solutions)

# Fungsi utama
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button))

    try:
        app.run_polling()
    except Exception as e:
        logger.error(f"Error in main loop: {e}")

# Jalankan bot + keep alive server
if __name__ == '__main__':
    keep_alive()
    main()
