import aiosqlite
from config import DB_PATH

CREATE_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS group_settings (
  chat_id INTEGER PRIMARY KEY,
  required_adds INTEGER NOT NULL DEFAULT 1,
  force_text TEXT DEFAULT 'Guruhda yozish uchun avval odam qo‘shing!',
  force_text_delete_after INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS members (
  chat_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  added_count INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (chat_id, user_id)
);

CREATE TABLE IF NOT EXISTS privileged (
  chat_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  PRIMARY KEY (chat_id, user_id)
);

CREATE TABLE IF NOT EXISTS linked_channels (
  chat_id INTEGER NOT NULL,
  channel_username TEXT NOT NULL,
  PRIMARY KEY (chat_id, channel_username)
);
"""

class DB:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        self.conn: aiosqlite.Connection | None = None

    async def init(self):
        self.conn = await aiosqlite.connect(self.path)
        await self.conn.execute("PRAGMA foreign_keys=ON;")
        await self.conn.executescript(CREATE_SQL)
        await self.conn.commit()

    async def close(self):
        if self.conn:
            await self.conn.close()
            self.conn = None

    async def ensure_group(self, chat_id: int):
        await self.conn.execute(
            "INSERT OR IGNORE INTO group_settings(chat_id) VALUES(?)",
            (chat_id,)
        )
        await self.conn.commit()

    async def get_settings(self, chat_id: int) -> dict:
        await self.ensure_group(chat_id)
        cur = await self.conn.execute(
            "SELECT required_adds, force_text, force_text_delete_after "
            "FROM group_settings WHERE chat_id=?",
            (chat_id,)
        )
        row = await cur.fetchone()
        return {
            "required_adds": int(row[0]),
            "force_text": row[1],
            "force_text_delete_after": int(row[2]),
        }

    async def set_required_adds(self, chat_id: int, n: int):
        await self.ensure_group(chat_id)
        await self.conn.execute(
            "UPDATE group_settings SET required_adds=? WHERE chat_id=?",
            (int(n), chat_id)
        )
        await self.conn.commit()

    async def set_force_text(self, chat_id: int, text: str):
        await self.ensure_group(chat_id)
        await self.conn.execute(
            "UPDATE group_settings SET force_text=? WHERE chat_id=?",
            (text, chat_id)
        )
        await self.conn.commit()

    async def set_force_text_delete_after(self, chat_id: int, sec: int):
        await self.ensure_group(chat_id)
        await self.conn.execute(
            "UPDATE group_settings SET force_text_delete_after=? WHERE chat_id=?",
            (int(sec), chat_id)
        )
        await self.conn.commit()

    async def inc_added(self, chat_id: int, inviter_id: int, by: int = 1):
        await self.ensure_group(chat_id)
        await self.conn.execute(
            "INSERT OR IGNORE INTO members(chat_id,user_id,added_count) VALUES(?,?,0)",
            (chat_id, inviter_id)
        )
        await self.conn.execute(
            "UPDATE members SET added_count = added_count + ? "
            "WHERE chat_id=? AND user_id=?",
            (int(by), chat_id, inviter_id)
        )
        await self.conn.commit()

    async def get_added(self, chat_id: int, user_id: int) -> int:
        await self.ensure_group(chat_id)
        cur = await self.conn.execute(
            "SELECT added_count FROM members WHERE chat_id=? AND user_id=?",
            (chat_id, user_id)
        )
        row = await cur.fetchone()
        return int(row[0]) if row else 0

    async def reset_added_for(self, chat_id: int, user_id: int):
        await self.ensure_group(chat_id)
        await self.conn.execute(
            "INSERT OR IGNORE INTO members(chat_id,user_id,added_count) VALUES(?,?,0)",
            (chat_id, user_id)
        )
        await self.conn.execute(
            "UPDATE members SET added_count=0 WHERE chat_id=? AND user_id=?",
            (chat_id, user_id)
        )
        await self.conn.commit()

    async def reset_all_added(self, chat_id: int):
        await self.ensure_group(chat_id)
        await self.conn.execute("DELETE FROM members WHERE chat_id=?", (chat_id,))
        await self.conn.commit()

    async def top10(self, chat_id: int):
        await self.ensure_group(chat_id)
        cur = await self.conn.execute(
            "SELECT user_id, added_count FROM members "
            "WHERE chat_id=? ORDER BY added_count DESC LIMIT 10",
            (chat_id,)
        )
        return await cur.fetchall()

    async def add_priv(self, chat_id: int, user_id: int):
        await self.ensure_group(chat_id)
        await self.conn.execute(
            "INSERT OR IGNORE INTO privileged(chat_id, user_id) VALUES(?, ?)",
            (chat_id, user_id)
        )
        await self.conn.commit()

    async def del_priv(self, chat_id: int, user_id: int):
        await self.conn.execute(
            "DELETE FROM privileged WHERE chat_id=? AND user_id=?",
            (chat_id, user_id)
        )
        await self.conn.commit()

    async def is_priv(self, chat_id: int, user_id: int) -> bool:
        cur = await self.conn.execute(
            "SELECT 1 FROM privileged WHERE chat_id=? AND user_id=?",
            (chat_id, user_id)
        )
        row = await cur.fetchone()
        return bool(row)

    async def list_priv(self, chat_id: int):
        cur = await self.conn.execute(
            "SELECT user_id FROM privileged WHERE chat_id=?",
            (chat_id,)
        )
        rows = await cur.fetchall()
        return [int(r[0]) for r in rows]

    def _clean_username(self, username: str) -> str:
        u = (username or "").strip()
        if u.startswith("@"):
            u = u[1:]
        return u.lower()

    async def add_channel(self, chat_id: int, username: str):
        u = self._clean_username(username)
        if not u:
            return
        await self.ensure_group(chat_id)
        await self.conn.execute(
            "INSERT OR IGNORE INTO linked_channels(chat_id, channel_username) VALUES(?, ?)",
            (chat_id, u)
        )
        await self.conn.commit()

    async def remove_channel(self, chat_id: int, username: str):
        u = self._clean_username(username)
        if not u:
            return
        await self.conn.execute(
            "DELETE FROM linked_channels WHERE chat_id=? AND channel_username=?",
            (chat_id, u)
        )
        await self.conn.commit()

    async def get_channels(self, chat_id: int):
        cur = await self.conn.execute(
            "SELECT channel_username FROM linked_channels WHERE chat_id=?",
            (chat_id,)
        )
        rows = await cur.fetchall()
        return [r[0] for r in rows]
