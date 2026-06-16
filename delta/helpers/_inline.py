# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import types
from pyrogram.enums import ButtonStyle

# Note: 'app' and 'config' are imported lazily where needed to avoid circular imports


class Inline:
    def __init__(self):
        self.ikm = types.InlineKeyboardMarkup
        self.ikb = types.InlineKeyboardButton

    def cancel_dl(self, text) -> types.InlineKeyboardMarkup:
        return self.ikm([[self.ikb(text=text, callback_data=f"cancel_dl")]])

    def controls(
        self,
        chat_id: int,
        status: str = None,
        timer: str = None,
        remove: bool = False,
    ) -> types.InlineKeyboardMarkup:
        keyboard = []
        if status:
            keyboard.append(
                [self.ikb(text=status, callback_data=f"controls status {chat_id}", style=ButtonStyle.PRIMARY)]
            )
        elif timer:
            keyboard.append(
                [self.ikb(text=timer, callback_data=f"controls status {chat_id}", style=ButtonStyle.PRIMARY)]
            )

        if not remove:
            keyboard.append(
                [
                    self.ikb(text="⏹", callback_data=f"controls stop {chat_id}"),
                    self.ikb(text="⏸", callback_data=f"controls pause {chat_id}"),
                    self.ikb(text="▶️", callback_data=f"controls resume {chat_id}"),
                    self.ikb(text="⏭", callback_data=f"controls skip {chat_id}"),
                ]
            )
            keyboard.append(
                [
                    self.ikb(text="➕ Playlist", callback_data=f"controls playlist {chat_id}", style=ButtonStyle.SUCCESS),
                    self.ikb(text="✖ Close", callback_data=f"controls close {chat_id}", style=ButtonStyle.DANGER),
                ]
            )
        return self.ikm(keyboard)

    def stats_buttons(self, _lang=None, is_sudo: bool = False) -> types.InlineKeyboardMarkup:
        """Main stats menu buttons."""
        keyboard = [
            [
                self.ikb(text="🎵 Top Tracks (Here)", callback_data="GetStatsNow Here"),
                self.ikb(text="👤 Top Users (Here)", callback_data="GetStatsNow UsersHere"),
            ],
            [
                self.ikb(text="🌍 Top Tracks (Global)", callback_data="GetStatsNow Tracks"),
                self.ikb(text="📢 Top Groups (Global)", callback_data="GetStatsNow Chats"),
            ],
            [
                self.ikb(text="🤖 Bot Info", callback_data="TopOverall s"),
            ],
        ]
        if is_sudo:
            keyboard.append([
                self.ikb(text="⚙️ System Info", callback_data="bot_stats_sudo s"),
            ])
        keyboard.append([
            self.ikb(text="✖ Close", callback_data="stats_close", style=ButtonStyle.DANGER),
        ])
        return self.ikm(keyboard)

    def back_stats_markup(self, _lang=None) -> types.InlineKeyboardMarkup:
        """Back button for stats."""
        return self.ikm([
            [self.ikb(text="« Kembali", callback_data="stats_back")],
            [self.ikb(text="✖ Close", callback_data="stats_close", style=ButtonStyle.DANGER)]
        ])

    def overall_stats_markup(self, _lang=None, main: bool = False) -> types.InlineKeyboardMarkup:
        """Overall stats navigation."""
        if main:
            return self.ikm([[self.ikb(text="« Kembali", callback_data="stats_back")]])
        return self.ikm([[
            self.ikb(text="« Kembali", callback_data="TopOverall s")
        ]])

    def help_markup(
        self, _lang=None, back: bool = False
    ) -> types.InlineKeyboardMarkup:
        if back:
            rows = [
                [
                    self.ikb(text="Kembali", callback_data="help back"),
                    self.ikb(text="Tutup", callback_data="help close", style=ButtonStyle.DANGER),
                ]
            ]
        else:
            # Manual mapping with hardcoded Indonesian labels
            help_map = [
                ("admins", "help_0", "👮 Admin"),
                ("auth", "help_1", "🔐 Auth"),
                ("blist", "help_2", "🚫 Blacklist"),
                # help_3 (Bahasa) - SKIPPED
                ("ping", "help_4", "🏓 Ping"),
                ("play", "help_5", "▶️ Play"),
                ("queue", "help_6", "📝 Queue"),
                ("stats", "help_7", "📊 Stats"),
                ("sudo", "help_8", "⚙️ Sudoers"),
                ("drama", "help_9", "🎬 Drama"),
            ]
            buttons = [
                self.ikb(text=label, callback_data=f"help {cb}")
                for cb, help_key, label in help_map
            ]
            rows = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]

        return self.ikm(rows)

    def ping_markup(self, text: str) -> types.InlineKeyboardMarkup:
        from delta import config
        return self.ikm([[self.ikb(text=text, url=f"tg://user?id={config.OWNER_ID}")]])

    def play_queued(
        self, chat_id: int, item_id: str, _text: str
    ) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text=_text, callback_data=f"controls force {chat_id} {item_id}"
                    )
                ]
            ]
        )

    def queue_markup(
        self, chat_id: int, _text: str, playing: bool, page: int = 0, total_pages: int = 1
    ) -> types.InlineKeyboardMarkup:
        _action = "pause" if playing else "resume"
        buttons = [
            [self.ikb(text=_text, callback_data=f"controls {_action} {chat_id} q")]
        ]
        
        # Add pagination if needed
        if total_pages > 1:
            nav_row = []
            if page > 0:
                nav_row.append(self.ikb(text="◀️", callback_data=f"controls page {chat_id} {page-1}"))
            
            nav_row.append(self.ikb(text=f"📄 {page+1}/{total_pages}", callback_data="noop"))
            
            if page < total_pages - 1:
                nav_row.append(self.ikb(text="▶️", callback_data=f"controls page {chat_id} {page+1}"))
            
            buttons.append(nav_row)
            
        return self.ikm(buttons)

    def player_settings_markup(
        self, loop_mode="normal", admin_only=True, cmd_delete=True, video_mode=True, video_quality="720p", drama_mode=False, chat_id=0
    ) -> types.InlineKeyboardMarkup:
        """Player settings panel with loop mode and video mode."""
        # Loop mode button text
        loop_text = {
            "normal": "▶️ Normal",
            "loop_all": "🔁 Loop All",
            "loop_one": "🔂 Loop One"
        }.get(loop_mode, "▶️ Normal")
        
        return self.ikm(
            [
                [
                    self.ikb(
                        text="🔁 Loop Mode ➜",
                        callback_data="noop",
                    ),
                    self.ikb(text=loop_text, callback_data="player_settings loop"),
                ],
                [
                    self.ikb(
                        text="📹 Video Mode ➜",
                        callback_data="noop",
                    ),
                    self.ikb(text="✅ Aktif" if video_mode else "❌ Nonaktif", callback_data="player_settings video"),
                ],
                [
                    self.ikb(
                        text="🎬 Kualitas ➜",
                        callback_data="noop",
                    ),
                    self.ikb(text=f"📺 {video_quality}", callback_data="player_settings quality"),
                ],
                [
                    self.ikb(
                        text="👮 Admin Only ➜",
                        callback_data="noop",
                    ),
                    self.ikb(text="✅ Aktif" if admin_only else "❌ Nonaktif", callback_data="player_settings admin"),
                ],
                [
                    self.ikb(
                        text="🗑 Auto Delete ➜",
                        callback_data="noop",
                    ),
                    self.ikb(text="✅ Aktif" if cmd_delete else "❌ Nonaktif", callback_data="player_settings delete"),
                ],
                [
                    self.ikb(
                        text="🎭 Drama (Admin) ➜",
                        callback_data="noop",
                    ),
                    self.ikb(text="✅ Aktif" if drama_mode else "❌ Nonaktif", callback_data="player_settings drama"),
                ],
                [
                    self.ikb(text="✖ Close", callback_data="player_settings close"),
                ],
            ]
        )

    def start_key(
        self, lang=None, private: bool = False
    ) -> types.InlineKeyboardMarkup:
        from delta import app, config
        rows = [
            [
                self.ikb(
                    text="➕ Tambahkan saya ke grup Anda",
                    url=f"https://t.me/{app.username}?startgroup=true",
                )
            ],
            [self.ikb(text="❓ Bantuan", callback_data="help")],
            [
                self.ikb(text="Owner", url=f"https://t.me/959792624119"),
                self.ikb(text="💰 Donate", callback_data="donate"),
            ],
        ]
        return self.ikm(rows)

    def yt_key(self, link: str) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(text="❐", copy_text=link),
                    self.ikb(text="Youtube", url=link),
                ],
            ]
        )
