from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord import Intents, Embed
from discord.ext.commands import Bot as BotOrigin, CommandNotFound
from datetime import datetime
PREFIX = "$"
OWNER_IDS = [797858811142340660,
             383641902441824259,
             905033119156023306,
             905039535354810418,
             912678787999731773,
             415389907523993601,
             453262739318767616]


def read_changelog():
    with open('./lib/bot/changelog.txt', 'r') as file:
        data = file.read()
    return data


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
        await self.log_channel.send("🔒 Bot is down for development...")

    async def on_ready(self):
        if not self.ready:
            self.ready = True
            self.guild = self.get_guild(905040652251852820)
            print("[*] Bot is ready to operate...")
            self.log_channel = self.get_channel(922903725809471518)
            # await self.log_channel.send("🔓 Bot is up from development...")

            embed = Embed(title="Bot is online", description="Mate is currently running", timestamp=datetime.utcnow())
            embed.add_field(name="Change-log", value=read_changelog(), inline=True)

            user = self.get_user(383641902441824259)
            profilePicture = user.avatar_url
            embed.set_author(name="@Timski", icon_url=profilePicture)
            await self.log_channel.send(embed=embed)
        else:
            print("[*] Bot has just reconnected")

    async def on_message(self, message):
        pass

    async def on_command_error(self, context, exception):
        if not isinstance(exception, CommandNotFound):
            await context.send("👷 This command is still in development, coming soon...")

    async def on_error(self, event_method, *args, **kwargs):
        if event_method == "on_command_error":
            await args[0].send("👷 Something went wrong, reporting...")
        raise

bot = Bot()
