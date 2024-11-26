"""
MIT License

Copyright (c) 2021-present vertyco

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
# pyinstaller.exe --clean app.spec

import asyncio
import importlib
import importlib.util
import logging
import os
import random
from datetime import datetime, timedelta
from itertools import cycle
from pathlib import Path

import discord
from dotenv import load_dotenv

from common.db import DB, IS_EXE, ROOT_DIR
from common.logger import init_logging, init_sentry
from common.version import VERSION


class Config:
    enabled: bool
    channel_id: int
    cooldown_minutes: int
    title: str
    tags: list[int]


class SelfBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bg_task: asyncio.Task = None
        self.bg_task2: asyncio.Task = None

    async def setup_hook(self) -> None:
        if dsn := os.getenv("SENTRY_DSN"):
            log.info("Initializing Sentry")
            init_sentry(dsn, VERSION)

    async def on_ready(self):
        log.info(f"Logged in as {self.user}")
        self.bg_task = self.loop.create_task(self.ad_loop())
        if IS_EXE:
            self.bg_task2 = self.loop.create_task(self.status_bar())

    async def on_message(self, message: discord.Message):
        if message.author.id == self.user.id:
            return

    async def ad_loop(self):
        await self.wait_until_ready()
        while not self.is_closed():
            await self.check_ads()
            await asyncio.sleep(120)

    async def check_ads(self):
        ad_dirs = ROOT_DIR / "ads"
        ad_dirs.mkdir(exist_ok=True)
        # If there are no ad dirs, throw error
        if not list(ad_dirs.iterdir()):
            log.error("No ad directories found")
            return

        for ad_dir in ad_dirs.iterdir():
            try:
                await self.maybe_send_ad(ad_dir)
            except Exception as e:
                log.error(f"Error sending ad from {ad_dir.stem}", exc_info=e)

    async def status_bar(self):
        BAR = [
            "▱▱▱▱▱▱▱",
            "▰▱▱▱▱▱▱",
            "▰▰▱▱▱▱▱",
            "▰▰▰▱▱▱▱",
            "▰▰▰▰▱▱▱",
            "▰▰▰▰▰▱▱",
            "▰▰▰▰▰▰▱",
            "▰▰▰▰▰▰▰",
            "▱▰▰▰▰▰▰",
            "▱▱▰▰▰▰▰",
            "▱▱▱▰▰▰▰",
            "▱▱▱▱▰▰▰",
            "▱▱▱▱▱▰▰",
            "▱▱▱▱▱▱▰",
        ]
        bar_cycle = cycle(BAR)
        while not self.is_closed():
            cmd = "title SelfBot Poster " + next(bar_cycle)
            os.system(cmd)
            await asyncio.sleep(0.15)

    async def maybe_send_ad(self, ad_dir: Path):
        ad_content_path = ad_dir / "content.txt"
        if not ad_content_path.exists():
            log.error(f"Missing ad content file in {ad_dir.stem}")
            return
        config_module = ad_dir / "config.py"
        if not config_module.exists():
            log.error(f"Missing config file in {ad_dir.stem}")
            return

        # Import the module
        spec = importlib.util.spec_from_file_location(config_module.stem, config_module)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        config: Config = module

        if not config.enabled:
            return
        channel = self.get_channel(config.channel_id)
        if not channel:
            log.error(f"Channel {config.channel_id} not found for ad for {ad_dir.stem}")
            return

        global db
        if config.channel_id in db.sent_messages:
            last_sent = db.sent_messages[config.channel_id]
            now = datetime.now()
            if now - last_sent < timedelta(minutes=config.cooldown_minutes):
                # Not ready yet
                return

        # Set the last sent time to a random time in the future to give some variance
        next_send = datetime.now() + timedelta(minutes=random.randint(5, 60))
        db.sent_messages[config.channel_id] = next_send
        db.save()

        ad_content = ad_content_path.read_bytes().decode("utf-8")
        # Get any png, jpg, jpeg, or gif files in the ad directory
        image_paths = (
            list(ad_dir.glob("*.png"))
            + list(ad_dir.glob("*.jpg"))
            + list(ad_dir.glob("*.jpeg"))
            + list(ad_dir.glob("*.gif"))
        )
        if image_paths:
            image_paths.sort(key=lambda p: p.stem)

        files = []
        for image_path in image_paths:
            files.append(discord.File(image_path))

        if isinstance(channel, discord.ForumChannel):
            kwargs = {"name": config.title, "content": ad_content}
            if files:
                kwargs["files"] = files
            if config.tags:
                found = [i for i in channel.available_tags if i.id in config.tags]
                if found:
                    kwargs["applied_tags"] = found
                else:
                    log.warning(
                        f"Could not find tags {config.tags} in {channel.available_tags}"
                    )
            await channel.create_thread(**kwargs)
        else:
            kwargs = {"content": ad_content}
            if files:
                kwargs["files"] = files
            await channel.send(**kwargs)

        logtxt = f"Posted message to {channel} from {ad_dir.stem}"
        if files:
            logtxt += f" with {len(files)} image(s)"
        log.info(logtxt)

        # If we made it here lets wait for a bit
        await asyncio.sleep(15)


load_dotenv()
client = SelfBot(chunk_guilds_at_startup=True)
init_logging()
log = logging.getLogger("selfbot")
db: DB = DB.load()

if __name__ == "__main__":
    if IS_EXE:
        os.system("title SelfBot Poster [Iniializing...]")
    try:
        client.run(token=os.getenv("TOKEN"), log_handler=None)
    finally:
        db.save()
