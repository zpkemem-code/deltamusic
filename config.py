from os import getenv
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self.API_ID = int(getenv("API_ID", 0))
        self.API_HASH = getenv("API_HASH")

        self.BOT_TOKEN = getenv("BOT_TOKEN")
        self.MONGO_URL = getenv("MONGO_URL")
        self.DB_NAME = getenv("DB_NAME", "StreamingMusic")

        self.LOGGER_ID = int(getenv("LOGGER_ID", 0))
        self.OWNER_ID = int(getenv("OWNER_ID", 0))

        self.DURATION_LIMIT = int(getenv("DURATION_LIMIT", 60)) * 60
        self.QUEUE_LIMIT = int(getenv("QUEUE_LIMIT", 20))
        self.PLAYLIST_LIMIT = int(getenv("PLAYLIST_LIMIT", 20))
        self.FILE_SIZE_LIMIT = int(getenv("FILE_SIZE_LIMIT", 200)) * 1024 * 1024
        self.API_URL = getenv("API_URL")

        self.SESSION1 = getenv("SESSION", None)
        self.SESSION2 = getenv("SESSION2", None)
        self.SESSION3 = getenv("SESSION3", None)

        self.DONATE_QR_IMAGE = getenv("DONATE_QR_IMAGE", "https://files.catbox.moe/2d927j.jpg")

        self.AUTO_END: bool = getenv("AUTO_END", False)
        self.AUTO_LEAVE: bool = getenv("AUTO_LEAVE", False)
        self.AUTO_DELETE_COMMANDS: bool = getenv("AUTO_DELETE_COMMANDS", "True").lower() == "true"
        self.AUTO_DELETE_TIME: int = int(getenv("AUTO_DELETE_TIME", 15))
        self.ANTI_PM_ENABLED: bool = getenv("ANTI_PM_ENABLED", True)
        self.PM_WARN_COUNT: int = int(getenv("PM_WARN_COUNT", 3))
        self.VIDEO_PLAY: bool = getenv("VIDEO_PLAY", True)
        self.COOKIES_URL = [
            url for url in getenv("COOKIES_URL", "").split(" ")
            if url and "batbin.me" in url
        ]
        
        self.DEFAULT_THUMB = getenv("DEFAULT_THUMB", "https://te.legra.ph/file/3e40a408286d4eda24191.jpg")
        self.PING_IMG = getenv("PING_IMG", "https://files.catbox.moe/haagg2.png")
        self.STATS_IMG_URL = getenv("STATS_IMG_URL", "https://telegra.ph/file/6213d2673486beca02967.jpg")
        self.GLOBAL_IMG_URL = getenv("GLOBAL_IMG_URL", "https://telegra.ph/file/6213d2673486beca02967.jpg")
        self.START_IMG = getenv("START_IMG", "https://files.catbox.moe/zvziwk.jpg")


    def check(self):
        missing = [
            var
            for var in ["API_ID", "API_HASH", "BOT_TOKEN", "MONGO_URL", "LOGGER_ID", "OWNER_ID", "SESSION1"]
            if not getattr(self, var)
        ]
        if missing:
            raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")
