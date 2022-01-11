from datetime import datetime, timedelta

from apscheduler.triggers.cron import CronTrigger
from discord import Embed, Colour
from discord.ext.commands import Cog
from discord.ext.commands import command
from ..database import database
from ..cogs.exp import Exp, check_lvl_rewards


async def find_invite_by_code(invite_list, code):
    for inv in invite_list:
        if inv.code == code:
            return inv.uses


async def get_uses_by_code(all_invites, invite_code):
    """Get uses of an invite code."""
    for invite in all_invites:
        if invite.code == invite_code.code:
            return invite.uses


class Invite(Cog):
    def __init__(self, bot):
        self.bot = bot
        # bot.scheduler.add_job(self.set, CronTrigger(second=0))

    @command(name="invite", description="Get a unique invite link for the server.",
             brief="Get a unique invite link for xp rewards.")
    async def invite(self, ctx):
        """
        Create an invite link for the guild.
        """
        guild = ctx.guild
        # if guild.chunked:
        #     await ctx.send("The server is too large to generate an invite link.")
        # else:
        url = await self.generate_unique_invite_url()
        print(url)
        embed = Embed(
            title="Your invite link has been generated.",
            description=f"Bring 5 friends over, receive XP and get "
                        "whitelist advantage.",

            color=Colour.green()
        )

        embed.add_field(name="Invite Link", value=url, inline=True)
        await ctx.send(embed=embed)
        # Add the invite link to the database
        database.execute(
            "INSERT INTO invites (InviteLink, CreatorID, Code) VALUES (?, ?, ?)",
            url.url, ctx.author.id, url.code
        )
        database.commit()

    async def generate_unique_invite_url(self):
        channel = self.bot.get_channel(912697602120757338)
        invite = await channel.create_invite(max_age=0, unique=True)
        return invite

    @Cog.listener()
    async def on_member_join(self, member):

        invites_before_join = self.invites  # Codes
        invites_after_join = await member.guild.invites()

        for invite in invites_before_join:
            if get_uses_by_code(await member.guild.invites(), invite) < find_invite_by_code(invites_after_join, invite):
                database.execute("UPDATE invite SET CreatorID = ?, Uses = ? WHERE InviteLink = ?",
                                 (member.id, invite.uses, invite.url))

                await self.ranks_channel.send(embed=Embed(
                    title="Unique Invite Link",
                    description=f"{member.mention} has joined the server and has used a unique invite link."
                                f"<@{invite.inviter.id}> has received XP and whitelist advantage.",
                    color=Colour.green(),
                ))
                self.invites = invites_after_join
                await self.invite_xp_reward(invite.inviter)

                return

    async def invite_xp_reward(self, member):
        xp, lvl, xplock = database.record("SELECT XP, Level, XPLock FROM exp WHERE UserID = ?", member.id)
        new_lvl = int(((xp + 150) // 42) ** 0.55)
        database.execute("UPDATE exp SET XP = XP + ?, Level = ?, XPLock = ? WHERE UserID = ?",
                         150, new_lvl, (datetime.utcnow() + timedelta(seconds=60)).isoformat(), member.id)
        if new_lvl > lvl:
            await self.ranks_channel.send(f"Congrats {member.mention} - you reached level {new_lvl:,}!")
            await check_lvl_rewards(member, new_lvl)

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.ranks_channel = self.bot.get_channel(929369474853920858)
            self.invites = database.column("SELECT Code FROM invites")
            self.bot.cogs_ready.ready_up("invite")


def setup(bot):
    bot.add_cog(Invite(bot))
