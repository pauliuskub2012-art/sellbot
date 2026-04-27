import discord
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive

TOKEN = "MTQ5ODI3NTY1MDAyNzUyNDI3Nw.G6bK54.MlgA4tH6knguiMkraNw237sNPr6IEkSpUX8JHw"
ALLOWED_ROLE_ID =   # change this
LEAGUES_ROLE_ID =  # change this
ALLOWED_ROLE_ID_GUIDE = 
GUILD_ID = 

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

def get_clan_role(member: discord.Member):
    # Assumes clan owner has ONLY 1 clan role (recommended)
    for role in member.roles:
        if role.name not in ["@everyone"]:
            return role
    return None

class ClanInviteView(discord.ui.View):
    def __init__(self, role, target):
        super().__init__(timeout=60)
        self.role = role
        self.target = target

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            return await interaction.response.send_message("Not your invite.", ephemeral=True)

        await interaction.user.add_roles(self.role)
        await interaction.response.edit_message(content="You joined the clan!", view=None)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            return await interaction.response.send_message("Not your invite.", ephemeral=True)

        await interaction.response.edit_message(content="Invite declined.", view=None)
        
# =========================
# JOIN VIEW (MAIN SYSTEM)
# =========================
# In your main setup View (the one with the 'Create League' button)
class JoinLeagueView(discord.ui.View):
    def __init__(self, thread_id, total_slots, host_user, region, l_type, perks):
        super().__init__(timeout=None)
        self.thread_id = thread_id
        self.total_slots = int(total_slots)
        self.joined_count = 1
        self.host_user = host_user
        self.host_name = host_user.name
        self.region = region
        self.l_type = l_type
        self.perks = perks
        self.joined_users = {host_user.id}

    def create_embed(self, is_full=False):
        remaining = self.total_slots - self.joined_count

        if is_full:
            status_text = "🔒 Lobby Full"
            color = 0xff0000
            for item in self.children:
                item.disabled = True
        else:
            status_text = f"Hosting a game. Need **{remaining}** more player{'s' if remaining != 1 else ''} to join."
            color = 0x5865F2

        embed = discord.Embed(
            title=f"{self.perks} - {self.l_type} ({self.region})",
            description=status_text,
            color=color
        )

        embed.add_field(name="Hosted by", value=f"`{self.host_name}`", inline=True)
        embed.set_footer(
            text=f"Game ID: {self.thread_id} • {discord.utils.format_dt(discord.utils.utcnow(), style='t')}"
        )

        return embed  # Ši eilutė turi būti viename lygyje su 'remaining = ...'

    @discord.ui.button(label="Join Game", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.joined_users:
            return await interaction.response.send_message(
                "You're already in the league!",
                ephemeral=True
            )

        if self.joined_count >= self.total_slots:
            return await interaction.response.send_message(
                "League is full!",
                ephemeral=True
            )

        thread = interaction.guild.get_thread(self.thread_id)
        if not thread:
            return await interaction.response.send_message(
                "Thread not found.",
                ephemeral=True
            )

        await thread.add_user(interaction.user)
        self.joined_users.add(interaction.user.id)
        self.joined_count += 1

        is_full = self.joined_count >= self.total_slots

        await interaction.response.edit_message(
            embed=self.create_embed(is_full),
            view=self
        )

        await interaction.followup.send(
            "You joined the league!",
            ephemeral=True
        )

        if is_full:
            try:
                await thread.edit(name="League: Full", archived=True, locked=True)
            except:
                pass
            
@bot.tree.command(
    name="guidelines",
    description="Post server guidelines"
)
@app_commands.checks.has_role(ALLOWED_ROLE_ID_GUIDE)
async def guidelines(interaction: discord.Interaction):

    embed = discord.Embed(
        title="📜 SERVER GUIDELINES",
        description="We’re committed to maintaining a welcoming and respectful environment for everyone.\n\nAny toxic or harmful behavior will not be tolerated. Staff will take appropriate action to ensure community standards are upheld.",
        color=0x2f3136
    )

    embed.add_field(
        name="📖 General Rules",
        value="Follow Discord Terms of Service and Community Guidelines at all times.\nIf you're new, take a moment to read and understand them.",
        inline=False
    )

    embed.add_field(
        name="⚠️ Harassment & Toxicity",
        value="Hate speech, racism, or targeted harassment is strictly forbidden.\nToxic behavior will result in mutes, kicks, or bans.\nRespecting others is mandatory.",
        inline=False
    )

    embed.add_field(
        name="🔒 Privacy & Identity Protection",
        value="Sharing private or real-world information is strictly prohibited.\nDoxxing or leaking content will result in a permanent blacklist.",
        inline=False
    )

    embed.add_field(
        name="🚫 NSFW & Legal Compliance",
        value="NSFW or illegal content is not allowed.\nViolators will be removed and reported without warning.",
        inline=False
    )

    embed.add_field(
        name="🛡️ System Integrity",
        value="Exploits, scripts, or abuse of bot systems are forbidden.\nAny attempt to bypass rules will result in permanent removal.",
        inline=False
    )

    embed.set_footer(text="RCD • Rogue Competitive Division")

    await interaction.response.send_message(embed=embed)

# =========================
# SETUP VIEW
# =========================
class LeagueSetupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.values = {}

    @discord.ui.select(placeholder="1. Perks?", options=[
        discord.SelectOption(label="Perks", value="Perks"),
        discord.SelectOption(label="No Perks", value="No Perks")
    ])
    async def perks_s(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.values['perks'] = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(placeholder="2. Region", options=[
        discord.SelectOption(label="EU", value="EU"),
        discord.SelectOption(label="Asia", value="Asia"),
        discord.SelectOption(label="NA", value="NA"),
        discord.SelectOption(label="South America", value="South America"),
        discord.SelectOption(label="North America", value="North America"),
        discord.SelectOption(label="Oceania", value="Oceania"),
        discord.SelectOption(label="Africa", value="Africa")
    ])
    async def region_s(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.values['region'] = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(placeholder="3. Type", options=[
        discord.SelectOption(label="Swift", value="Swift"),
        discord.SelectOption(label="War", value="War")
    ])
    async def type_s(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.values['type'] = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(placeholder="4. Amount", options=[
        discord.SelectOption(label="1v1", value="2"),
        discord.SelectOption(label="2v2", value="4"),
        discord.SelectOption(label="3v3", value="6"),
        discord.SelectOption(label="4v4", value="8")
    ])
    async def amount_s(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.values['slots'] = int(select.values[0])
        await interaction.response.defer()

    @discord.ui.button(label="🚀 Create League", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.values) < 4:
            return await interaction.response.send_message("Complete all fields!", ephemeral=True)

        # Create thread
        thread = await interaction.channel.create_thread(
            name=f"RCD: {self.values['type']}",
            type=discord.ChannelType.private_thread
        )

        await thread.add_user(interaction.user)

        # Create join system
        view = JoinLeagueView(
            thread.id,
            self.values['slots'],
            interaction.user.name,
            self.values['region'],
            self.values['type'],
            self.values['perks']
        )

        role_mention = f"<@&{LEAGUES_ROLE_ID}>"

        # Send main message
        await interaction.response.send_message(
            content=f"{role_mention} League Hosted!",
            embed=view.create_embed(),
            view=view,
            allowed_mentions=discord.AllowedMentions(roles=True)
        )


# =========================
# COMMANDS
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot is online: {bot.user}")


@bot.tree.command(name="league", description="Host a session")
@app_commands.checks.has_any_role(ALLOWED_ROLE_ID)
async def league(interaction: discord.Interaction):
    await interaction.response.send_message(
        "League Setup:",
        view=LeagueSetupView(),
        ephemeral=True
    )
@bot.tree.command(name="promote", description="Create a clan and assign an owner")
async def promote(interaction: discord.Interaction, clan_name: str, clan_owner: discord.Member):

    # Optional: restrict to admin or yourself
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message(
            "You need administrator permissions.",
            ephemeral=True
        )

    # Create role
    role = await interaction.guild.create_role(name=clan_name)

    # Give role to owner
    await clan_owner.add_roles(role)

    await interaction.response.send_message(
        f"{clan_owner.mention} is now the owner of clan **{clan_name}**!"
    )
@bot.tree.command(name="offer", description="Invite a member to your clan")
async def offer(interaction: discord.Interaction, member: discord.Member):

    clan_role = get_clan_role(interaction.user)

    if not clan_role:
        return await interaction.response.send_message(
            "You are not a clan owner.",
            ephemeral=True
        )

    view = ClanInviteView(clan_role, member)

    await interaction.response.send_message(
        f"{member.mention}, you got invited to **{clan_role.name}**",
        view=view
    )
@bot.tree.command(name="remove", description="Remove a member from your clan")
async def remove(interaction: discord.Interaction, member: discord.Member):

    clan_role = get_clan_role(interaction.user)

    if not clan_role:
        return await interaction.response.send_message(
            "You are not a clan owner.",
            ephemeral=True
        )

    if clan_role not in member.roles:
        return await interaction.response.send_message(
            "That user is not in your clan.",
            ephemeral=True
        )

    await member.remove_roles(clan_role)

    await interaction.response.send_message(
        f"{member.mention} was removed from **{clan_role.name}**."
    )
    
@bot.tree.command(name="end", description="End session immediately")
@app_commands.checks.has_any_role(ALLOWED_ROLE_ID)
async def end(interaction: discord.Interaction):
    if isinstance(interaction.channel, discord.Thread):
        await interaction.response.send_message("League session closed.")
        await interaction.channel.edit(name="League: Ended", archived=True, locked=True)
    else:
        await interaction.response.send_message(
            "Use this command inside the league thread!",
            ephemeral=True
        )
@bot.event
async def on_ready():
    await bot.tree.sync()

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Leagues"
        )
    )

keep_alive()
bot.run(TOKEN)
