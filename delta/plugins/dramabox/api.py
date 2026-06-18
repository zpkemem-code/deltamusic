# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

"""
DramaBox API Client

Wrapper untuk mengakses DramaBox API dari Sansekai.
API Dokumentasi: https://dramabox.sansekai.my.id/
"""

import aiohttp
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from delta import logger


# Base URL API
BASE_URL = "https://drama.sansekai.my.id"


@dataclass
class Drama:
    """Representasi data drama dari API."""
    book_id: str
    title: str
    cover: str
    chapter_count: int
    introduction: str
    tags: List[str]
    protagonist: str
    hot_code: str = ""
    
    @classmethod
    def from_dict(cls, data: dict) -> "Drama":
        return cls(
            book_id=data.get("bookId", ""),
            title=data.get("bookName", ""),
            cover=data.get("coverWap", data.get("cover", "")),
            chapter_count=data.get("chapterCount", 0),
            introduction=data.get("introduction", ""),
            tags=data.get("tags", data.get("tagNames", [])),
            protagonist=data.get("protagonist", ""),
            hot_code=data.get("rankVo", {}).get("hotCode", "") if isinstance(data.get("rankVo"), dict) else "",
        )


@dataclass  
class Episode:
    """Representasi episode/chapter dari drama."""
    chapter_id: str
    chapter_index: int
    chapter_name: str
    thumbnail: str
    is_paid: bool
    video_urls: Dict[str, str]  # quality -> url
    
    @classmethod
    def from_dict(cls, data: dict) -> "Episode":
        video_urls = {}
        cdn_list = data.get("cdnList", [])
        if cdn_list:
            # Ambil dari CDN pertama (default)
            for cdn in cdn_list:
                if cdn.get("isDefault", 0) == 1:
                    for video in cdn.get("videoPathList", []):
                        quality = str(video.get("quality", ""))
                        url = video.get("videoPath", "")
                        if quality and url:
                            video_urls[f"{quality}p"] = url
                    break
            
            # Fallback ke CDN pertama jika tidak ada default
            if not video_urls and cdn_list:
                for video in cdn_list[0].get("videoPathList", []):
                    quality = str(video.get("quality", ""))
                    url = video.get("videoPath", "")
                    if quality and url:
                        video_urls[f"{quality}p"] = url
        
        return cls(
            chapter_id=data.get("chapterId", ""),
            chapter_index=data.get("chapterIndex", 0),
            chapter_name=data.get("chapterName", ""),
            thumbnail=data.get("chapterImg", ""),
            is_paid=data.get("isCharge", 0) == 1,
            video_urls=video_urls,
        )


class DramaBoxAPI:
    """Client untuk mengakses DramaBox API."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
    
    async def _request(self, endpoint: str, params: dict = None) -> Optional[Any]:
        """Melakukan HTTP request ke API."""
        url = f"{BASE_URL}/{endpoint}"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.error(f"DramaBox API Error: {e}")
            return None
    
    async def get_trending(self) -> List[Drama]:
        """Mendapatkan daftar drama trending."""
        data = await self._request("trending")
        if data and isinstance(data, list):
            return [Drama.from_dict(d) for d in data]
        return []
    
    async def get_latest(self) -> List[Drama]:
        """Mendapatkan daftar drama terbaru."""
        data = await self._request("latest")
        if data and isinstance(data, list):
            return [Drama.from_dict(d) for d in data]
        return []
    
    async def get_foryou(self) -> List[Drama]:
        """Mendapatkan drama rekomendasi."""
        data = await self._request("foryou")
        if data and isinstance(data, list):
            return [Drama.from_dict(d) for d in data]
        return []
    
    async def search(self, query: str) -> List[Drama]:
        """Mencari drama berdasarkan query."""
        data = await self._request("search", {"query": query})
        if data and isinstance(data, list):
            return [Drama.from_dict(d) for d in data]
        return []
    
    async def get_popular_search(self) -> List[str]:
        """Mendapatkan kata kunci pencarian populer."""
        data = await self._request("populersearch")
        if data and isinstance(data, list):
            return data
        return []
    
    async def get_random_drama(self) -> Optional[Dict]:
        """Mendapatkan drama acak (video pendek)."""
        return await self._request("randomdrama")
    
    async def get_all_episodes(self, book_id: str) -> List[Episode]:
        """
        Mendapatkan semua episode dari drama.
        
        Args:
            book_id: ID buku/drama
            
        Returns:
            List dari Episode dengan link streaming
        """
        data = await self._request("allepisode", {"bookId": book_id})
        if data and isinstance(data, list):
            return [Episode.from_dict(d) for d in data]
        return []


# Singleton instance
dramabox = DramaBoxAPI()
