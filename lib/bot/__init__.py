from asyncio import sleep

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord import Intents, Embed
from discord.ext.commands import Bot as BotOrigin, CommandNotFound
from datetime import datetime
from ..database import database as db
from glob import glob

PREFIX = "$"
OWNER_IDS = [797858811142340660,
             383641902441824259,
             905033119156023306,
             905039535354810418,
             912678787999731773,
             415389907523993601,
             453262739318767616]
COGS = [path.split("\\")[-1][:-3] for path in glob("./lib/cogs/*.py")]


class Ready(object):
    def __init__(self):
        for cog in COGS:
            setattr(self, cog, False)

    def ready_up(self, cog):
        setattr(self, cog, True)
        print(f"\t[*] {cog} cog is ready.")

    def all_ready(self):
        return all([getattr(self, cog) for cog in COGS])


def read_changelog():
    with open('./lib/bot/changelog.txt', 'r') as file:
        data = file.read()
    return data


class Bot(BotOrigin):
    def __init__(self):
        self.PREFIX = PREFIX
        self.ready = False
        self.cogs_ready = Ready()
        self.guild = None

        self.scheduler = AsyncIOScheduler()
        db.autosave(self.scheduler)

        super().__init__(command_prefix=PREFIX, owner_ids=OWNER_IDS, intents=Intents.all())

    def setup(self):
        for cog in COGS:
            self.load_extension(f"lib.cogs.{cog}")

    def run(self, version):
        self.VERSION = version
        self.setup()
        with open("./lib/bot/token.0", encoding="utf-8") as my_token:
            self.TOKEN = my_token.read()

        print("[+] Starting bot...")
        super().run(self.TOKEN, reconnect=True)

    async def on_connect(self):
        print("[*] Bot is running...")

    async def on_disconnect(self):
        print("[-] Bot is disconnected...")
        await self.log_channel.send("🔒 Bot is down for development...")

    async def on_ready(self):
        if not self.ready:

            self.guild = self.get_guild(905040652251852820)
            self.scheduler.start()

            while not self.cogs_ready.all_ready():
                await sleep(0.5)
            print("[*] Bot is ready to operate...")
            self.log_channel = self.get_channel(922903725809471518)
            self.ready = True

        else:
            print("[*] Bot has just reconnected")

    async def on_message(self, message):

        if not message.author.bot:
            await self.process_commands(message)

    async def on_command_error(self, context, exception):
        if not isinstance(exception, CommandNotFound):
            await context.send("👷 This command is still in development, coming soon...")

    async def on_error(self, event_method, *args, **kwargs):

        if event_method == "on_command_error":
            await args[0].send("👷 Something went wrong, reporting...")
        else:
            await self.log_channel.send("❗ Error occurred, reporting to log...")
            print(f"[-] Error: {event_method} ({datetime.utcnow()}")


bot = Bot()
