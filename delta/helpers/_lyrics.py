# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import logging
import re
from typing import Optional

import aiohttp

# Use direct logging to avoid circular import
logger = logging.getLogger(__name__)


class LyricsSearcher:
    """Search and fetch song lyrics from multiple sources"""
    
    def __init__(self):
        self.session = None
        self.genius_token = None  # Optional: Add Genius API token for better results
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self) -> None:
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def clean_title(self, title: str) -> str:
        """Clean song title for better search results"""
        # Remove common patterns
        patterns = [
            r'\(.*?[Oo]fficial.*?\)',
            r'\[.*?[Oo]fficial.*?\]',
            r'\(.*?[Vv]ideo.*?\)',
            r'\[.*?[Vv]ideo.*?\]',
            r'\(.*?[Ll]yrics.*?\)',
            r'\[.*?[Ll]yrics.*?\]',
            r'\(.*?[Aa]udio.*?\)',
            r'\[.*?[Aa]udio.*?\]',
            r'[\(\[].*?HD.*?[\)\]]',
            r'[\(\[].*?4K.*?[\)\]]',
            r'[\(\[].*?MV.*?[\)\]]',
        ]
        
        cleaned = title
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        # Clean up extra spaces
        cleaned = ' '.join(cleaned.split())
        return cleaned.strip()
    
    async def search_lyrics_api(self, title: str) -> Optional[dict]:
        """
        Search lyrics using lyrics.ovh API
        
        Returns:
            dict with 'title', 'artist', 'lyrics' or None
        """
        try:
            # Try to extract artist and song name
            cleaned_title = self.clean_title(title)
            
            # Common patterns: "Artist - Song" or "Song - Artist"
            if ' - ' in cleaned_title:
                parts = cleaned_title.split(' - ', 1)
                artist, song = parts[0].strip(), parts[1].strip()
            else:
                # Fallback: use whole title as song name
                artist = "Unknown"
                song = cleaned_title
            
            session = await self._get_session()
            
            # Try lyrics.ovh
            url = f"https://api.lyrics.ovh/v1/{artist}/{song}"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'lyrics' in data and data['lyrics']:
                        return {
                            'title': song,
                            'artist': artist,
                            'lyrics': data['lyrics'].strip()
                        }
        
        except Exception as e:
            logger.debug(f"lyrics.ovh search failed: {e}")
        
        return None
    
    async def search_lyrics_genius(self, title: str) -> Optional[dict]:
        """
        Search lyrics using Genius API (if token provided)
        
        Note: Requires GENIUS_API_TOKEN in environment
        """
        if not self.genius_token:
            return None
        
        try:
            cleaned_title = self.clean_title(title)
            session = await self._get_session()
            
            headers = {"Authorization": f"Bearer {self.genius_token}"}
            
            # Search for song
            search_url = "https://api.genius.com/search"
            params = {"q": cleaned_title}
            
            async with session.get(search_url, headers=headers, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['response']['hits']:
                        hit = data['response']['hits'][0]['result']
                        return {
                            'title': hit['title'],
                            'artist': hit['primary_artist']['name'],
                            'url': hit['url'],
                            'lyrics': None  # Genius API doesn't provide lyrics directly
                        }
        
        except Exception as e:
            logger.debug(f"Genius search failed: {e}")
        
        return None
    
    async def search(self, title: str) -> Optional[dict]:
        """
        Search lyrics from multiple sources
        
        Args:
            title: Song title to search
        
        Returns:
            dict with lyrics info or None if not found
        """
        logger.info(f"Searching lyrics for: {title}")
        
        # Try multiple sources in order
        result = await self.search_lyrics_api(title)
        
        if not result and self.genius_token:
            result = await self.search_lyrics_genius(title)
        
        if result:
            logger.info(f"Lyrics found: {result['title']} - {result['artist']}")
        else:
            logger.info(f"Lyrics not found for: {title}")
        
        return result
    
    def format_lyrics(self, lyrics_data: dict, max_length: int = 4000) -> str:
        """
        Format lyrics for Telegram message
        
        Args:
            lyrics_data: Dictionary with lyrics info
            max_length: Maximum message length
        
        Returns:
            Formatted lyrics text
        """
        title = lyrics_data.get('title', 'Unknown')
        artist = lyrics_data.get('artist', 'Unknown')
        lyrics = lyrics_data.get('lyrics', '')
        
        if not lyrics:
            return (
                f"🎵 <b>{title}</b>\n"
                f"👤 <i>{artist}</i>\n\n"
                f"<blockquote>Lirik tidak tersedia. "
                f"Kunjungi: {lyrics_data.get('url', '')}</blockquote>"
            )
        
        # Format header
        formatted = (
            f"🎤 <b>Lirik Lagu</b>\n\n"
            f"🎵 <b>{title}</b>\n"
            f"👤 <i>{artist}</i>\n\n"
            f"<blockquote expandable>\n"
        )
        
        # Add lyrics (truncate if too long)
        remaining_space = max_length - len(formatted) - 20  # 20 for closing tags
        if len(lyrics) > remaining_space:
            lyrics = lyrics[:remaining_space] + "...\n\n[Lirik terlalu panjang, sebagian dipotong]"
        
        formatted += lyrics
        formatted += "\n</blockquote>"
        
        return formatted


# Global instance
lyrics_searcher = LyricsSearcher()
