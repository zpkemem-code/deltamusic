# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import os
import re
import yt_dlp
import random
import asyncio
import aiohttp
from pathlib import Path

from py_yt import Playlist, VideosSearch

from delta import logger
from delta.helpers import Track, utils


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.cookies = []
        self.checked = False
        self.cookie_dir = "delta/cookies"
        self.warned = False
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )

    def get_cookies(self):
        if not self.checked:
            for file in os.listdir(self.cookie_dir):
                if file.endswith(".txt"):
                    self.cookies.append(f"{self.cookie_dir}/{file}")
            self.checked = True
        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("Cookies are missing; downloads might fail.")
            return None
        return random.choice(self.cookies)

    async def save_cookies(self, urls: list[str]) -> None:
        logger.info("Saving cookies from urls...")
        async with aiohttp.ClientSession() as session:
            for i, url in enumerate(urls):
                path = f"{self.cookie_dir}/cookie_{i}.txt"
                link = "https://batbin.me/api/v2/paste/" + url.split("/")[-1]
                async with session.get(link) as resp:
                    resp.raise_for_status()
                    with open(path, "wb") as fw:
                        fw.write(await resp.read())
        logger.info(f"Cookies saved in {self.cookie_dir}.")

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    def extract_video_id(self, url: str) -> str | None:
        """Extract video ID from YouTube URL (including YouTube Music)."""
        # Pattern for watch?v= format
        match = re.search(r'[?&]v=([A-Za-z0-9_-]{11})', url)
        if match:
            return match.group(1)
        # Pattern for youtu.be format
        match = re.search(r'youtu\.be/([A-Za-z0-9_-]{11})', url)
        if match:
            return match.group(1)
        return None

    async def get_video_info(self, video_id: str, m_id: int, video: bool = False, user_id: int = 0) -> Track | None:
        """Get video info directly using yt_dlp."""
        url = self.base + video_id
        try:
            def _get_info():
                opts = {"quiet": True, "no_warnings": True}
                cookie = self.get_cookies()
                if cookie:
                    opts["cookiefile"] = cookie
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return info
            
            info = await asyncio.to_thread(_get_info)
            if not info:
                return None
            
            duration_sec = info.get("duration", 0)
            minutes = duration_sec // 60
            seconds = duration_sec % 60
            duration = f"{minutes}:{seconds:02d}"
            
            return Track(
                id=info.get("id"),
                channel_name=info.get("channel", info.get("uploader", "")),
                duration=duration,
                duration_sec=duration_sec,
                message_id=m_id,
                title=info.get("title"),
                thumbnail=info.get("thumbnail", ""),
                url=info.get("webpage_url", url),
                view_count=str(info.get("view_count", "")),
                video=video,
                user_id=user_id,
            )
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return None

    async def search(self, query: str, m_id: int, video: bool = False, user_id: int = 0) -> Track | None:
        # Check if query is a URL - extract video ID and get info directly
        if "youtube.com" in query or "youtu.be" in query or "music.youtube.com" in query:
            video_id = self.extract_video_id(query)
            if video_id:
                return await self.get_video_info(video_id, m_id, video, user_id)
        
        # Regular search
        try:
            _search = VideosSearch(query, limit=1, with_live=False)
            results = await _search.next()
        except:
             return None
             
        if results and results["result"]:
            data = results["result"][0]
            return Track(
                id=data.get("id"),
                channel_name=data.get("channel", {}).get("name"),
                duration=data.get("duration"),
                duration_sec=utils.to_seconds(data.get("duration")),
                message_id=m_id,
                title=data.get("title"),
                thumbnail=data.get("thumbnails", [{}])[-1].get("url").split("?")[0],
                url=data.get("link"),
                view_count=data.get("viewCount", {}).get("short"),
                video=video,
                user_id=user_id,
            )
        return None

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> list[Track | None]:
        tracks = []
        try:
            plist = await Playlist.get(url)
            for data in plist["videos"][:limit]:
                track = Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnails")[-1].get("url").split("?")[0],
                    url=data.get("link").split("&list=")[0],
                    user=user,
                    view_count="",
                    video=video,
                    user_id=0  # Playlist user_id handling can be improved later if needed
                )
                tracks.append(track)
        except:
            pass
        return tracks

    async def formats(self, video_id: str, lyrics: bool = False):
        """Get available formats for a YouTube video."""
        url = self.base + video_id
        try:
            def _get_formats():
                with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return info.get("formats", []), url
            
            return await asyncio.to_thread(_get_formats)
        except Exception as e:
            logger.error(f"Failed to get formats: {e}")
            return [], url

    async def download(self, video_id: str, video: bool = False) -> str | None:
        url = self.base + video_id
        ext = "mp4" if video else "webm"
        filename = f"downloads/{video_id}.{ext}"

        if Path(filename).exists():
            return filename

        cookie = self.get_cookies()
        base_opts = {
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "quiet": True,
            "noplaylist": True,
            "geo_bypass": True,
            "no_warnings": True,
            "overwrites": False,
            "nocheckcertificate": True,
            "cookiefile": cookie,
        }

        if video:
            ydl_opts = {
                **base_opts,
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio)",
                "merge_output_format": "mp4",
            }
        else:
            ydl_opts = {
                **base_opts,
                "format": "bestaudio[ext=webm][acodec=opus]",
            }

        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([url])
                except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError):
                    if cookie: self.cookies.remove(cookie)
                    return None
                except Exception as ex:
                    logger.warning("Download failed: %s", ex)
                    return None
            return filename

        return await asyncio.to_thread(_download)
