from asyncio import sleep
from datetime import datetime, timedelta
from re import search
from typing import Optional
from discord_components import DiscordComponents, ComponentsBot, Button, SelectOption, Select
from better_profanity import profanity
from discord import Embed, Member, NotFound, Object, utils, Colour
from discord.utils import find
from discord import Embed, Member, NotFound, Object, Colour
from discord.utils import find, get
from discord.ext.commands import Cog, Greedy, Converter
from discord.ext.commands import CheckFailure, BadArgument
from discord.ext.commands import command, has_permissions, bot_has_permissions

from ..database import database

profanity.load_censor_words_from_file("./data/profanity.txt")


class BannedUser(Converter):
    async def convert(self, ctx, arg):
        if ctx.guild.me.guild_permissions.ban_members:
            if arg.isdigit():
                try:
                    return (await ctx.guild.fetch_ban(Object(id=int(arg)))).user
                except NotFound:
                    raise BadArgument

        banned = [e.user for e in await ctx.guild.bans()]
        if banned:
            if (user := find(lambda u: str(u) == arg, banned)) is not None:
                return user
            else:
                raise BadArgument


class Mod(Cog):
    def __init__(self, bot):
        self.bot = bot
        DiscordComponents(self.bot)
        self.url_regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        self.links_allowed = (759432499221889034,)
        self.images_allowed = (759432499221889034,)

    async def kick_members(self, message, targets, reason):
        for target in targets:
            if (message.guild.me.top_role.position > target.top_role.position
                    and not target.guild_permissions.administrator):
                await target.kick(reason=reason)

                embed = Embed(title="Member kicked",
                              colour=0xDD2222,
                              timestamp=datetime.utcnow())

                embed.set_thumbnail(url=target.avatar_url)

                fields = [("Member", f"{target.name} a.k.a. {target.display_name}", False),
                          ("Actioned by", message.author.display_name, False),
                          ("Reason", reason, False)]

                for name, value, inline in fields:
                    embed.add_field(name=name, value=value, inline=inline)

                await self.log_channel.send(embed=embed)

    @command(name="kick")
    @bot_has_permissions(kick_members=True)
    @has_permissions(kick_members=True)
    async def kick_command(self, ctx, targets: Greedy[Member], *, reason: Optional[str] = "No reason provided."):
        if not len(targets):
            await ctx.send("One or more required arguments are missing.")

        else:
            await self.kick_members(ctx.message, targets, reason)
            await ctx.send("Action complete.")

    @kick_command.error
    async def kick_command_error(self, ctx, exc):
        if isinstance(exc, CheckFailure):
            await ctx.send("Insufficient permissions to perform that task.")

    async def ban_members(self, message, targets, reason):
        for target in targets:
            if (message.guild.me.top_role.position > target.top_role.position
                    and not target.guild_permissions.administrator):
                await target.ban(reason=reason)

                embed = Embed(title="Member banned",
                              colour=0xDD2222,
                              timestamp=datetime.utcnow())

                embed.set_thumbnail(url=target.avatar_url)

                fields = [("Member", f"{target.name} a.k.a. {target.display_name}", False),
                          ("Actioned by", message.author.display_name, False),
                          ("Reason", reason, False)]

                for name, value, inline in fields:
                    embed.add_field(name=name, value=value, inline=inline)

                await self.log_channel.send(embed=embed)

    @command(name="ban")
    @bot_has_permissions(ban_members=True)
    @has_permissions(ban_members=True)
    async def ban_command(self, ctx, targets: Greedy[Member], *, reason: Optional[str] = "No reason provided."):
        if not len(targets):
            await ctx.send("One or more required arguments are missing.")

        else:
            await self.ban_members(ctx.message, targets, reason)
            await ctx.send("Action complete.")

    @ban_command.error
    async def ban_command_error(self, ctx, exc):
        if isinstance(exc, CheckFailure):
            await ctx.send("Insufficient permissions to perform that task.")

    @command(name="unban")
    @bot_has_permissions(ban_members=True)
    @has_permissions(ban_members=True)
    async def unban_command(self, ctx, targets: Greedy[BannedUser], *, reason: Optional[str] = "No reason provided."):
        if not len(targets):
            await ctx.send("One or more required arguments are missing.")

        else:
            for target in targets:
                await ctx.guild.unban(target, reason=reason)

                embed = Embed(title="Member unbanned",
                              colour=0xDD2222,
                              timestamp=datetime.utcnow())

                embed.set_thumbnail(url=target.avatar_url)

                fields = [("Member", target.name, False),
                          ("Actioned by", ctx.author.display_name, False),
                          ("Reason", reason, False)]

                for name, value, inline in fields:
                    embed.add_field(name=name, value=value, inline=inline)

                await self.log_channel.send(embed=embed)

            await ctx.send("Action complete.")

    @command(name="clear", aliases=["purge"])
    @bot_has_permissions(manage_messages=True)
    @has_permissions(manage_messages=True)
    async def clear_messages(self, ctx, targets: Greedy[Member], limit: Optional[int] = 1):
        def _check(message):
            return not len(targets) or message.author in targets

        if 0 < limit <= 100:
            with ctx.channel.typing():
                await ctx.message.delete()
                deleted = await ctx.channel.purge(limit=limit, after=datetime.utcnow() - timedelta(days=14),
                                                  check=_check)

                await ctx.send(f"Deleted {len(deleted):,} messages.", delete_after=5)

        else:
            await ctx.send("The limit provided is not within acceptable bounds.")

    @clear_messages.error
    async def clear_messages_error(self, ctx, exception):
        print("Clear error:"
              f"\n\tException: {exception}")

    async def mute_members(self, message, targets, hours, reason):
        unmutes = []

        for target in targets:
            if not self.mute_role in target.roles:
                if message.guild.me.top_role.position > target.top_role.position:
                    try:
                        role_ids = ",".join([str(r.id) for r in target.roles])
                    except AttributeError:
                        role_ids = ""
                    print(f"roles: {role_ids}")
                    end_time = datetime.utcnow() + timedelta(seconds=hours) if hours else None
                    print(f"end time: {end_time}")
                    database.execute("INSERT INTO mutes VALUES (?, ?, ?)",
                                     target.id, role_ids, getattr(end_time, "isoformat", lambda: None)())
                    await target.edit(roles=[self.mute_role])

                    embed = Embed(title="Member muted",
                                  colour=0xDD2222,
                                  timestamp=datetime.utcnow())

                    embed.set_thumbnail(url=target.avatar_url)

                    fields = [("Member", target.display_name, False),
                              ("Actioned by", message.author.display_name, False),
                              ("Duration", f"{hours:,} hour(s)" if hours else "Indefinite", False),
                              ("Reason", reason, False)]

                    for name, value, inline in fields:
                        embed.add_field(name=name, value=value, inline=inline)

                    await self.log_channel.send(embed=embed)

                    if hours:
                        unmutes.append(target)

        return unmutes

    @command(name="mute")
    @bot_has_permissions(manage_roles=True)
    @has_permissions(manage_roles=True, manage_guild=True)
    async def mute_command(self, ctx, targets: Greedy[Member], hours: Optional[int], *,
                           reason: Optional[str] = "No reason provided."):
        if not len(targets):
            await ctx.send("One or more required arguments are missing.")

        else:
            unmutes = await self.mute_members(ctx.message, targets, hours, reason)
            await ctx.send("Action complete.")

            if len(unmutes):
                await sleep(hours)
                await self.unmute_members(ctx.guild, targets)
        # guild = ctx.guild
        # mutedRole = utils.get(guild.roles, name="Muted")
        #
        # if not mutedRole:
        #     mutedRole = await guild.create_role(name="Muted")
        #
        #     for channel in guild.channels:
        #         await channel.set_permissions(mutedRole, speak=False, send_messages=False,
        #                                       read_message_history=True, read_messages=False)
        # embed = Embed(title="User Muted", description=f"{targets.mention} was muted ",
        #               colour=Colour.light_gray())
        # embed.add_field(name="Reason:", value=reason, inline=False)
        # await ctx.send(embed=embed)
        # await targets.add_roles(mutedRole, reason=reason)
        # await targets.send(f"Heya! You have been muted in {guild.name} (Reason: {reason})")

    @mute_command.error
    async def mute_error(self, ctx, exception):
        await ctx.send("Oops. Seems like last command did not work well. Try again... ")
        print("[-] Error occurred with the mute command.\n"
              f"\tCall: {ctx.message}\n"
              f"\tException: {exception}")

    @mute_command.error
    async def mute_command_error(self, ctx, exc):
        if isinstance(exc, CheckFailure):
            await ctx.send("Insufficient permissions to perform that task.")

    async def unmute_members(self, guild, targets, *, reason="Mute time expired."):
        for target in targets:
            if self.mute_role in target.roles:
                role_ids = database.field("SELECT RoleIDs FROM mutes WHERE UserID = ?", target.id)
                roles = [guild.get_role(int(id_)) for id_ in role_ids.split(",") if len(id_)]

                database.execute("DELETE FROM mutes WHERE UserID = ?", target.id)

                await target.edit(roles=roles)

                embed = Embed(title="Member unmuted",
                              colour=0xDD2222,
                              timestamp=datetime.utcnow())

                embed.set_thumbnail(url=target.avatar_url)

                fields = [("Member", target.display_name, False),
                          ("Reason", reason, False)]

                for name, value, inline in fields:
                    embed.add_field(name=name, value=value, inline=inline)

                await self.log_channel.send(embed=embed)

    @command(name="unmute")
    @bot_has_permissions(manage_roles=True)
    @has_permissions(manage_roles=True, manage_guild=True)
    async def unmute_command(self, ctx, targets: Greedy[Member], *, reason: Optional[str] = "No reason provided."):
        if not len(targets):
            await ctx.send("One or more required arguments is missing.")

        else:
            await self.unmute_members(ctx.guild, targets, reason=reason)

    @command(name="addprofanity", aliases=["addswears", "addcurses"])
    @has_permissions(manage_guild=True)
    async def add_profanity(self, ctx, *words):
        with open("./data/profanity.txt", "a", encoding="utf-8") as f:
            f.write("".join([f"{w}\n" for w in words]))

        profanity.load_censor_words_from_file("./data/profanity.txt")
        await ctx.send("Action complete.")

    @command(name="delprofanity", aliases=["delswears", "delcurses"])
    @has_permissions(manage_guild=True)
    async def remove_profanity(self, ctx, *words):
        with open("./data/profanity.txt", "r", encoding="utf-8") as f:
            stored = [w.strip() for w in f.readlines()]

        with open("./data/profanity.txt", "w", encoding="utf-8") as f:
            f.write("".join([f"{w}\n" for w in stored if w not in words]))

        profanity.load_censor_words_from_file("./data/profanity.txt")
        await ctx.send("Action complete.")

    @command(name="verify")
    @has_permissions(manage_guild=True)
    async def verify(self, ctx, *words):
        await ctx.send("React with the <:space_verify:> emoji to access the server.", components=[
            [Button(label="Join", style=3, emoji=self.bot.get_emoji(927540434513821717), custom_id="button1")]
        ])
        while True:
            interaction = await self.bot.wait_for("button_click", check=lambda i: i.custom_id == "button1")
            await interaction.send(content="Button clicked!", ephemeral=False)

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.log_channel = self.bot.get_channel(922914186009383012)
            self.mute_role = self.bot.guild.get_role(927478816463523860)

            self.bot.cogs_ready.ready_up("mod")

            # embed = Embed(
            #     description=f"React with the <:space_verify:927540434513821717> emoji to access the server.",
            #     colour=Colour.blue()
            # )
            # verif = await self.bot.get_channel(912697602120757338).send(embed=embed)
            # emoji_id = self.bot.get_emoji(927540434513821717)
            # await verif.add_reaction(emoji_id)

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        user = self.bot.get_user(payload.user_id)
        roles = self.bot.get_guild(payload.guild_id).roles
        if user != self.bot.user:
            try:
                role = find(lambda r: r.name == 'Member', roles)
                if role not in payload.member.roles and str(payload.emoji) == "<:space_verify:927540434513821717>":
                    # and payload.member.id not in self.bot.owner_ids
                    role_to_add = get(roles, name="Member")
                    # memberToRemoveRole = get(reaction.guild.members, name=user.display_name)
                    await payload.member.add_roles(role_to_add)



            except Exception as e:
                print(f"Didnt work ({e})")

    @Cog.listener()
    async def on_message(self, message):
        def _check(m):
            return (m.author == message.author
                    and len(m.mentions)
                    and (datetime.utcnow() - m.created_at).seconds < 60)

        if not message.author.bot:
            if len(list(filter(lambda m: _check(m), self.bot.cached_messages))) >= 3:
                await message.channel.send("Don't spam mentions!", delete_after=10)
                unmutes = await self.mute_members(message, [message.author], 5, reason="Mention spam")

                if len(unmutes):
                    await sleep(5)
                    await self.unmute_members(message.guild, [message.author])

            elif not self.is_admin(message.author) and profanity.contains_profanity(message.content):
                await message.delete()
                await message.channel.send("You can't use that word here.", delete_after=10)

        # XX commented out so it doesn't interfere with the rest of the server while recording
        # elif message.channel.id not in self.links_allowed and search(self.url_regex, message.content):
        # 	await message.delete()
        # 	await message.channel.send("You can't send links in this channel.", delete_after=10)

        # elif (message.channel.id not in self.images_allowed
        # 	and any([hasattr(a, "width") for a in message.attachments])):
        # 	await message.delete()
        # 	await message.channel.send("You can't send images here.", delete_after=10)
    def is_admin(self, member):
        """Checks if a member is an admin"""
        return member.guild_permissions.administrator or member.id in self.bot.owner_ids

def setup(bot):
    bot.add_cog(Mod(bot))
