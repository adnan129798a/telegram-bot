import os
from pathlib import Path

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import yt_dlp


TOKEN = os.getenv("BOT_TOKEN")


if not TOKEN:
    raise ValueError("BOT_TOKEN is missing. Please add it in Railway Variables.")


DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


def is_valid_url(text: str) -> bool:
    text = text.strip()
    return text.startswith("http://") or text.startswith("https://")


async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()

    if not is_valid_url(url):
        await update.message.reply_text("Please send a valid video link.")
        return

    await update.message.reply_text("Downloading video...")

    output_template = str(DOWNLOAD_DIR / "%(title).80s.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "mp4/bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
    }

    downloaded_file = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            if "requested_downloads" in info and info["requested_downloads"]:
                possible_path = ydl.prepare_filename(info)
            else:
                possible_path = ydl.prepare_filename(info)

        base_path = Path(possible_path)
        mp4_path = base_path.with_suffix(".mp4")

        if mp4_path.exists():
            downloaded_file = mp4_path
        elif base_path.exists():
            downloaded_file = base_path
        else:
            files = sorted(DOWNLOAD_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
            if files:
                downloaded_file = files[0]

        if not downloaded_file or not downloaded_file.exists():
            await update.message.reply_text("Download failed. File was not found.")
            return

        with downloaded_file.open("rb") as video_file:
            await update.message.reply_video(video=video_file)

    except Exception:
        await update.message.reply_text("Failed to download this link.")
    finally:
        try:
            if downloaded_file and downloaded_file.exists():
                downloaded_file.unlink()
        except Exception:
            pass


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))
    app.run_polling()


if __name__ == "__main__":
    main()
