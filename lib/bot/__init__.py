from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord import Intents
from discord.ext.commands import Bot as BotOrigin

PREFIX = "$"
OWNER_IDS = []


class Bot(BotOrigin):
    def __init__(self):
        self.PREFIX = PREFIX
        self.ready = False
        self.guild = None
        self.scheduler = AsyncIOScheduler()

        super().__init__(command_prefix=PREFIX, owner_ids=OWNER_IDS, intents=Intents.all())

    def run(self, version):
        self.VERSION = version

        with open("./lib/bot/token.0", encoding="utf-8") as my_token:
            self.TOKEN = my_token.read()

        print("[+] Starting bot...")
        super().run(self.TOKEN, reconnect=True)

    async def on_connect(self):
        print("[*] Bot is running...")

    async def on_disconnect(self):
        print("[-] Bot is disconnected...")

    async def on_ready(self):
        if not self.ready:
            self.ready = True
            self.guild = self.get_guild(905040652251852820)
            print("[*] Bot is ready to operate...")
        else:
            print("[*] Bot has just reconnected")
    async def on_message(self, message):
        pass

bot = Bot()
