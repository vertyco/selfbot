"""
Compile with the following:

pyinstaller.exe --clean app.spec
"""

import asyncio
import importlib
import importlib.util
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import discord
from dotenv import load_dotenv

from common.db import DB, ROOT_DIR
from common.logger import init_logging, init_sentry

load_dotenv()
log = init_logging()

if dsn := os.getenv("SENTRY_DSN"):
    log.info("Initializing Sentry")
    init_sentry(dsn)

token = os.getenv("TOKEN")
error_channel = os.getenv("ERROR_CHANNEL")

db: DB = DB.load()


class Config:
    enabled: bool
    channel_id: int
    cooldown_minutes: int
    title: str
    tags: list[int]


class SelfBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def setup_hook(self) -> None:
        self.bg_task = self.loop.create_task(self.ad_loop())

    async def on_ready(self):
        log.info(f"Logged in as {self.user}")

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
            log.info(f"Found {len(image_paths)} images in {ad_dir.stem}")

        files = []
        for image_path in image_paths:
            files.append(discord.File(image_path))

        log.info(f"Sending ad to {channel} from {ad_dir.stem}")
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
        log.info(f"Sent ad to {channel} from {ad_dir.stem}")

        # If we made it here lets wait for a bit
        await asyncio.sleep(15)


if __name__ == "__main__":
    try:
        client = SelfBot(chunk_guilds_at_startup=True, log_handler=None)
        client.run(token)
    finally:
        db.save()
