# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import enums, filters, types
from pyrogram.enums import ButtonStyle
from delta import app, db
from delta.helpers import buttons, not_blacklisted


@app.on_message(filters.command(["playlist", "myplaylist"]) & not_blacklisted)
async def playlist_command(_, message: types.Message):
    """Show user's saved playlist."""
    user_id = message.from_user.id
    playlist = await db.get_playlist(user_id)
    
    if not playlist:
        return await message.reply_text(
            "📋 <b>Playlist Kosong</b>\n\n"
            "<blockquote>Kamu belum menyimpan lagu apapun.\n\n"
            "💡 <b>Tips:</b> Klik tombol ➕ Playlist saat lagu diputar untuk menyimpan.</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    
    text = f"📋 <b>Playlist {message.from_user.first_name}</b>\n\n<blockquote>"
    
    emoji_numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, track in enumerate(playlist[:10]):
        num = emoji_numbers[i] if i < 10 else f"{i+1}."
        title = track.get("title", "Unknown")
        duration = track.get("duration", "0:00")
        text += f"{num} 🎵 {title} ({duration})\n"
    
    text += "</blockquote>"
    
    if len(playlist) > 10:
        text += f"\n\n➕ <i>... dan {len(playlist) - 10} lagu lagi</i>"
    
    text += f"\n\n<i>Total: {len(playlist)} lagu tersimpan</i>"
    
    # Create inline buttons
    keyboard = types.InlineKeyboardMarkup([
        [
            types.InlineKeyboardButton(text="▶️ Play All", callback_data=f"pl_playall {user_id}", style=ButtonStyle.SUCCESS),
            types.InlineKeyboardButton(text="🗑 Clear All", callback_data=f"pl_clear {user_id}", style=ButtonStyle.DANGER),
        ]
    ])
    
    await message.reply_text(
        text,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=keyboard
    )


@app.on_callback_query(filters.regex("pl_") & not_blacklisted)
async def playlist_callback(_, query: types.CallbackQuery):
    """Handle playlist callbacks."""
    data = query.data.split()
    action = data[0].replace("pl_", "")
    target_user = int(data[1])
    
    # Only allow the playlist owner to manage it
    if query.from_user.id != target_user:
        return await query.answer("❌ Ini bukan playlist kamu!", show_alert=True)
    
    if action == "playall":
        from delta import queue, anon, yt
        
        playlist = await db.get_playlist(target_user)
        if not playlist:
            return await query.answer("Playlist kosong!", show_alert=True)
        
        chat_id = query.message.chat.id
        
        # Check if in group
        if query.message.chat.type == enums.ChatType.PRIVATE:
            return await query.answer("⚠️ Gunakan di grup untuk memutar!", show_alert=True)
        
        await query.answer("▶️ Memproses playlist...", show_alert=True)
        
        # Add first track and start playing
        first_track = playlist[0]
        await query.edit_message_text(
            f"▶️ <b>Memutar Playlist</b>\n\n<blockquote>Menambahkan {len(playlist)} lagu ke antrian...</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
        
        # Add tracks to queue
        from delta.helpers._dataclass import Track
        for track in playlist:
            t = Track(
                id=track["track_id"],
                channel_name="Playlist",
                duration=track.get("duration", "0:00"),
                duration_sec=0,
                title=track["title"],
                url=track.get("url", ""),
                user=query.from_user.mention
            )
            queue.add(chat_id, t)
        
        await query.edit_message_text(
            f"✅ <b>Playlist Ditambahkan</b>\n\n<blockquote>{len(playlist)} lagu ditambahkan ke antrian!\n\nGunakan /play untuk mulai memutar.</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    
    elif action == "clear":
        await db.clear_playlist(target_user)
        await query.edit_message_text(
            "🗑 <b>Playlist Dihapus</b>\n\n<blockquote>Semua lagu di playlist kamu telah dihapus.</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
