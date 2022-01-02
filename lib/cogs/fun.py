from os import getcwd

from discord import Embed, Colour, Member, File
from discord.ext.commands import Cog, command, MissingRequiredArgument
from aiohttp import request
import wikipedia


class Fun(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command()
    async def ping(self, ctx):
        await ctx.send('Hi There! The ping is {0}'.format(self.bot.latency))

    @command(name="say", aliases=["announce"])
    async def announce(self, ctx, *, announcement):
        await ctx.message.delete()
        await ctx.send(announcement)

    @announce.error
    async def announce_error(self, ctx, exception):
        if exception.original == MissingRequiredArgument:
            await ctx.send(f"This command's argument is missing ($say something)")
        else:
            await ctx.send("Oops. Seems like last command did not work well. Try again... ")
            print("[-] Error occurred with the announce error.\n"
                  f"\tCall: {ctx.message}\n"
                  f"\tException: {exception}")

    @command(name="define", aliases=["whatis"])
    async def get_definition(self, ctx, *, x):
        embed = Embed(title=f"Definition for {x}",
                      description=f"{wikipedia.summary(x, sentences=2)}",
                      colour=Colour.blue()
                      )
        embed.set_footer(text=f"Requested by {ctx.author.name}")
        embed.set_author(name="WikiMate", icon_url=self.bot.get_user(906195422224199732).avatar_url)
        await ctx.send(embed=embed)

    @get_definition.error
    async def define_error(self, ctx, exception):
        print("[-] Error occurred with define command:"
              f"\n\tCall: {ctx.message}"
              f"\n\tException: {exception}")

    @command(name="comrade")
    async def comrade(self, ctx, member: Member):
        URL = "https://some-random-api.ml/canvas/comrade"
        # resp = get(URL)
        async with request("GET", URL, headers={"avatar": member.avatar_url_as(format="png")}) as resp:
            if resp.status == 200:
                data = await resp.json()

                open('image.png', 'wb').write(data)
                print(f'File saved in {getcwd()}/image.png')
                await ctx.send(file=File("image.png"))
            elif resp.status != 200:
                jsonresp = await resp.json()
                print(f"[-] Image request returned with code: {resp.status} ({jsonresp})")

    @comrade.error
    async def comrade_error(self, ctx, exception):
        print("[-] Error occurred with comrade command:"
              f"\n\tCall: {ctx.message}"
              f"\n\tException: {exception}")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("fun")


def setup(bot):
    bot.add_cog(Fun(bot))
