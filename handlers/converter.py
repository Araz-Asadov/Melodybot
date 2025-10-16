# handlers/converter.py – Audio format converter
import os
import logging
from aiogram import Router, types, F
from pydub import AudioSegment

logger = logging.getLogger(__name__)
router = Router()

CONVERT_PATH = "converted"
os.makedirs(CONVERT_PATH, exist_ok=True)

@router.message(F.content_type == "audio")
async def convert_audio(message: types.Message):
    """İstifadəçi MP3/WAV göndərdikdə avtomatik çevirmə"""
    file_name = message.audio.file_name
    user_id = message.from_user.id

    # Fayl formatını tap
    ext = os.path.splitext(file_name)[1].lower()
    if ext not in [".mp3", ".wav"]:
        await message.reply("❌ Yalnız MP3 və WAV formatları çevrilə bilər.")
        return

    # Faylı endir
    file = await message.bot.get_file(message.audio.file_id)
    src_path = os.path.join(CONVERT_PATH, file_name)
    await message.bot.download_file(file.file_path, src_path)

    # Yeni formatı seç (MP3 ↔ WAV)
    if ext == ".mp3":
        new_name = file_name.replace(".mp3", ".wav")
        dst_path = os.path.join(CONVERT_PATH, new_name)
        sound = AudioSegment.from_mp3(src_path)
        sound.export(dst_path, format="wav")
        new_format = "WAV"
    else:
        new_name = file_name.replace(".wav", ".mp3")
        dst_path = os.path.join(CONVERT_PATH, new_name)
        sound = AudioSegment.from_wav(src_path)
        sound.export(dst_path, format="mp3")
        new_format = "MP3"

    # Çevrilmiş faylı göndər
    await message.reply_document(types.FSInputFile(dst_path),
                                 caption=f"✅ Fayl {new_format} formatına çevrildi.")
    logger.info(f"User {user_id} converted {file_name} -> {new_name}")
