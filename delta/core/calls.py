# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from ntgcalls import (ConnectionNotFound, TelegramServerError,
                      RTMPStreamingUnsupported)
from pyrogram import enums, errors, types
from pyrogram.errors import MessageIdInvalid
from pyrogram.types import InputMediaPhoto, Message
from pytgcalls import PyTgCalls, exceptions, types
from pytgcalls.pytgcalls_session import PyTgCallsSession

from delta import app, config, db, logger, queue, userbot, yt
from delta.helpers import Media, Track, buttons, thumb


class TgCall(PyTgCalls):
    def __init__(self):
        self.clients = []

    async def pause(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=True)
        return await client.pause(chat_id)

    async def resume(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=False)
        return await client.resume(chat_id)

    async def seek(self, chat_id: int, seconds: int) -> bool:
        """Seek forward (+) or backward (-) by the specified number of seconds."""
        client = await db.get_assistant(chat_id)
        try:
            # Get current playback time
            current_time = await client.get_active_call(chat_id)
            if not current_time:
                return False
            
            # Calculate new position (in milliseconds)
            new_time = max(0, current_time.time + (seconds * 1000))
            
            # Seek to new position
            await client.seeked(chat_id, new_time)
            return True
        except Exception as e:
            logger.error(f"Seek error: {e}")
            return False

    async def stop(self, chat_id: int) -> None:
        client = await db.get_assistant(chat_id)
        try:
            queue.clear(chat_id)
            await db.remove_call(chat_id)
        except:
            pass

        try:
            await client.leave_call(chat_id, close=False)
        except:
            pass


    async def play_media(
        self,
        chat_id: int,
        message: Message,
        media: Media | Track,
        seek_time: int = 0,
    ) -> None:
        client = await db.get_assistant(chat_id)
        _thumb = (
            await thumb.generate(media)
            if isinstance(media, Track)
            else config.DEFAULT_THUMB
        )

        if not media.file_path:
            return await message.edit_text(f"File tidak ditemukan. Hubungi <a href='tg://user?id={config.OWNER_ID}'>owner</a>", parse_mode=enums.ParseMode.HTML)

        stream = types.MediaStream(
            media_path=media.file_path,
            audio_parameters=types.AudioQuality.HIGH,
            video_parameters=types.VideoQuality.HD_720p,
            audio_flags=types.MediaStream.Flags.REQUIRED,
            video_flags=(
                types.MediaStream.Flags.AUTO_DETECT
                if media.video
                else types.MediaStream.Flags.IGNORE
            ),
            ffmpeg_parameters=f"-ss {seek_time}" if seek_time > 1 else None,
        )
        try:
            await client.play(
                chat_id=chat_id,
                stream=stream,
                config=types.GroupCallConfig(auto_start=False),
            )
            if not seek_time:
                media.time = 1
                await db.add_call(chat_id)
                
                # Track stats
                try:
                    stream_type = "file"
                    if isinstance(media, Track):
                        stream_type = "music"
                        if media.duration in ["Unknown", "Live"] or "Stream" in media.duration:
                             stream_type = "live"

                    await db.add_stats(
                        track_id=media.id,
                        title=media.title,
                        duration=media.duration,
                        user_id=media.user_id or message.from_user.id,
                        chat_id=chat_id,
                        thumbnail=media.thumbnail if hasattr(media, 'thumbnail') else None,
                        stream_type=stream_type
                    )
                    await db.increment_queries()
                except:
                    pass
                
                
                # Enhanced now playing message
                text = f"""🎵 <b>Sedang Memutar</b>

📌 <a href='{media.url}'>{media.title}</a>
⏱ <b>Durasi:</b> {media.duration}
👁‍🗨 <b>Diminta oleh:</b> {media.user}"""
                keyboard = buttons.controls(chat_id)
                try:
                    await message.edit_media(
                        media=InputMediaPhoto(
                            media=_thumb,
                            caption=text,
                        ),
                        reply_markup=keyboard,
                    )
                except MessageIdInvalid:
                    media.message_id = (await app.send_photo(
                        chat_id=chat_id,
                        photo=_thumb,
                        caption=text,
                        reply_markup=keyboard,
                    )).id
        except FileNotFoundError:
            await message.edit_text(f"File tidak ditemukan. Hubungi <a href='tg://user?id={config.OWNER_ID}'>owner</a>", parse_mode=enums.ParseMode.HTML)
            await self.play_next(chat_id)
        except exceptions.NoActiveGroupCall:
            await self.stop(chat_id)
            await message.edit_text("Tidak ada panggilan video aktif.")
        except exceptions.NoAudioSourceFound:
            await message.edit_text("Sumber audio tidak ditemukan.")
            await self.play_next(chat_id)
        except (ConnectionNotFound, TelegramServerError):
            await self.stop(chat_id)
            await message.edit_text("Error server Telegram.")
        except RTMPStreamingUnsupported:
            await self.stop(chat_id)
            await message.edit_text("Format streaming RTMP tidak didukung.")


    async def replay(self, chat_id: int) -> None:
        if not await db.get_call(chat_id):
            return

        media = queue.get_current(chat_id)
        msg = await app.send_message(chat_id=chat_id, text="Memutar ulang...")
        await self.play_media(chat_id, msg, media)


    async def play_next(self, chat_id: int) -> None:
        if not await db.get_call(chat_id):
            return

        old_media = queue.get_current(chat_id)
        if old_media and old_media.message_id:
            try:
                await app.delete_messages(chat_id, old_media.message_id)
            except:
                pass


        # Check loop mode
        loop_mode = await db.get_loop_mode(chat_id)
        
        if loop_mode == "loop_one":
            # Replay current track
            if old_media:
                msg = await app.send_message(chat_id=chat_id, text="🔂 Memutar ulang...")
                await self.play_media(chat_id, msg, old_media)
                return
        elif loop_mode == "loop_all":
            # Add current track to end of queue
            if old_media:
                queue.add(chat_id, old_media)

        media = queue.get_next(chat_id)
        try:
            if media.message_id:
                await app.delete_messages(
                    chat_id=chat_id,
                    message_ids=media.message_id,
                    revoke=True,
                )
                media.message_id = 0
        except:
            pass

        if not media:
            return await self.stop(chat_id)

        msg_text = "Memutar lagu selanjutnya..."
        if media.user_id:
            try:
                user = await app.get_users(media.user_id)
                msg_text += f"\nRequest dari: {user.mention}"
            except:
                pass

        msg = await app.send_message(chat_id=chat_id, text=msg_text)
        if not media.file_path:
            media.file_path = await yt.download(media.id, video=media.video)
            if not media.file_path:
                await self.stop(chat_id)
                return await msg.edit_text(
                    f"File tidak ditemukan. Hubungi <a href='tg://user?id={config.OWNER_ID}'>owner</a>",
                    parse_mode=enums.ParseMode.HTML
                )

        media.message_id = msg.id
        await self.play_media(chat_id, msg, media)


    async def ping(self) -> float:
        pings = [client.ping for client in self.clients]
        return round(sum(pings) / len(pings), 2)


    async def decorators(self, client: PyTgCalls) -> None:
        for client in self.clients:

            @client.on_update()
            async def update_handler(_, update: types.Update) -> None:
                if isinstance(update, types.StreamEnded):
                    if update.stream_type == types.StreamEnded.Type.AUDIO:
                        await self.play_next(update.chat_id)
                elif isinstance(update, types.ChatUpdate):
                    if update.status in [
                        types.ChatUpdate.Status.KICKED,
                        types.ChatUpdate.Status.LEFT_GROUP,
                        types.ChatUpdate.Status.CLOSED_VOICE_CHAT,
                    ]:
                        await self.stop(update.chat_id)


    async def boot(self) -> None:
        PyTgCallsSession.notice_displayed = True
        for ub in userbot.clients:
            client = PyTgCalls(ub, cache_duration=100)
            await client.start()
            self.clients.append(client)
            await self.decorators(client)
        logger.info("PyTgCalls client(s) started.")
