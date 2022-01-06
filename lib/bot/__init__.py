from asyncio import sleep

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord import Intents, Embed, Forbidden, DMChannel
from discord.ext.commands import Bot as BotOrigin, CommandNotFound, Context, BadArgument, MissingRequiredArgument, \
    CommandOnCooldown
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
IGNORE_EXC = (CommandNotFound, BadArgument, MissingRequiredArgument)


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

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=Context)

        if ctx.command is not None and ctx.guild is not None:
            if self.ready:
                await self.invoke(ctx)
            else:
                pass  # Bot is not ready

    async def on_connect(self):
        print("[*] Bot is running...")

    async def on_disconnect(self):
        print("[-] Bot is disconnected...")
        # await self.log_channel.send("🔒 Bot is down for development...")

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

    def update_db(self):
        db.multiexec("INSERT OR IGNORE INTO guilds (GuildID) VALUES (?)",
                     ((guild.id,) for guild in self.guilds))

        db.multiexec("INSERT OR IGNORE INTO exp (UserID) VALUES (?)",
                     ((member.id,) for member in self.guild.members if not member.bot))

        to_remove = []
        stored_members = db.column("SELECT UserID FROM exp")
        for id_ in stored_members:
            if not self.guild.get_member(id_):
                to_remove.append(id_)

        db.multiexec("DELETE FROM exp WHERE UserID = ?",
                     ((id_,) for id_ in to_remove))

        db.commit()

    async def on_message(self, message):
        if not message.author.bot:
            if isinstance(message.channel, DMChannel):
                if len(message.content) < 50:
                    await message.channel.send("Hi there :wave: Your message should be at least 50 characters in "
                                               "length.")

                else:
                    member = self.guild.get_member(message.author.id)
                    embed = Embed(title="Mod Mails",
                                  colour=member.colour,
                                  timestamp=datetime.utcnow())

                    embed.set_thumbnail(url=member.avatar_url)

                    fields = [("Member", member.display_name, False),
                              ("Message", message.content, False)]

                    for name, value, inline in fields:
                        embed.add_field(name=name, value=value, inline=inline)

                    mod = self.get_cog("Mod")
                    await mod.log_channel.send(embed=embed)
                    await message.channel.send("Message relayed to moderators.")

            else:
                await self.process_commands(message)

    async def on_command_error(self, ctx, exc):
        if any([isinstance(exc, error) for error in IGNORE_EXC]):
            pass

        elif isinstance(exc, MissingRequiredArgument):
            await ctx.send("One or more required arguments are missing.")

        elif isinstance(exc, CommandOnCooldown):
            await ctx.send(
                f"That command is on {str(exc.cooldown.type).split('.')[-1]} cooldown. Try again in {exc.retry_after:,.2f} secs.")

        elif hasattr(exc, "original"):
            # if isinstance(exc.original, HTTPException):
            # 	await ctx.send("Unable to send message.")

            if isinstance(exc.original, Forbidden):
                await ctx.send("I am sorry, I do not have permission to do that.")

            else:
                raise exc.original

        else:
            raise exc

    async def on_error(self, event_method, *args, **kwargs):

        if event_method == "on_command_error":
            await args[0].send("👷 Something went wrong, reporting...")
            print("[-] Error:"
                  f"\n\t{event_method}"
                  f"\n\t{args}"
                  f"\n\t{kwargs} ")

        else:
            await self.log_channel.send("❗ Error occurred, reporting to log...")
            print(f"[-] Error: {event_method} ({datetime.utcnow()}")


bot = Bot()
