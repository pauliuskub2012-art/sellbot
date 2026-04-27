import discord
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive

# --- KONFIGŪRACIJA ---
ALLOWED_ROLE_ID = 1496172112715579586  # Įklijuok savo Role ID
TOKEN = "MTQ5NDMyNDIxNDg0NzYzOTY2Mg.GULOIt.itaJMRIR7cvkRDHwyIjcWHoJ1J6RKnedg-mI4Y"              # Įklijuok savo Bot Token

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- 1. Mygtuko vaizdas (Join Button) ---
class JoinLeagueView(discord.ui.View):
    def __init__(self, thread_id, total_slots, host_name, region, l_type, perks):
        super().__init__(timeout=None)
        self.thread_id, self.total_slots, self.joined_count = thread_id, total_slots, 1
        self.region, self.l_type, self.perks, self.host_name = region, l_type, perks, host_name

    def create_embed(self, is_full=False):
        color = 0xff0000 if is_full else 0x2f3136
        slots_text = f"**Open Slots:** {max(0, self.total_slots - self.joined_count)}" if not is_full else "🔒 **LOBBY FULL**"
        
        embed = discord.Embed(title="🏆 FCD League Session", color=color)
        embed.description = f"Click **Join League** to enter.\n{slots_text}"
        embed.add_field(name="Perks", value=self.perks, inline=True)
        embed.add_field(name="Type", value=self.l_type, inline=True)
        embed.add_field(name="Region", value=self.region, inline=True)
        embed.set_footer(text=f"FCD | Fair Competitive Division | Hosted by {self.host_name}")
        return embed

    @discord.ui.button(label="Join League", style=discord.ButtonStyle.green, custom_id="join_btn")
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        thread = interaction.guild.get_thread(self.thread_id)
        if not thread or self.joined_count >= self.total_slots:
            return await interaction.response.send_message("Lobby is full or closed.", ephemeral=True)
        
        await thread.add_user(interaction.user)
        self.joined_count += 1
        await thread.send(f"✅ {interaction.user.mention} joined!")
        
        if self.joined_count >= self.total_slots:
            button.disabled = True
            await interaction.response.edit_message(embed=self.create_embed(is_full=True), view=self)
        else:
            await interaction.response.edit_message(embed=self.create_embed(), view=self)

# --- 2. Sąrankos klausimai (Setup) ---
class LeagueSetupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.values = {}

    @discord.ui.select(placeholder="1. Perks?", options=[
        discord.SelectOption(label="Perks Enabled", value="Perks"),
        discord.SelectOption(label="No Perks", value="No Perks")
    ])
    async def perks_s(self, interaction, select):
        self.values['perks'] = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(placeholder="2. Region", options=[
        discord.SelectOption(label="EU", value="EU"),
        discord.SelectOption(label="Asia", value="Asia"),
        discord.SelectOption(label="NA", value="NA"),
        discord.SelectOption(label="America", value="America"),
        discord.SelectOption(label="Africa", value="Africa")
    ])
    async def region_s(self, interaction, select):
        self.values['region'] = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(placeholder="3. Type", options=[
        discord.SelectOption(label="Swift", value="Swift"),
        discord.SelectOption(label="War", value="War")
    ])
    async def type_s(self, interaction, select):
        self.values['type'] = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(placeholder="4. Amount", options=[
        discord.SelectOption(label="1v1", value="2"),
        discord.SelectOption(label="2v2", value="4"),
        discord.SelectOption(label="3v3", value="6"),
        discord.SelectOption(label="4v4", value="8")
    ])
    async def amount_s(self, interaction, select):
        self.values['slots'] = int(select.values[0])
        await interaction.response.defer()

    @discord.ui.button(label="🚀 Create League", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.values) < 4:
            return await interaction.response.send_message("Complete all fields!", ephemeral=True)
        
        thread = await interaction.channel.create_thread(
            name=f"FCD: {self.values['type']}",
            type=discord.ChannelType.private_thread
        )
        await thread.add_user(interaction.user)

        view = JoinLeagueView(thread.id, self.values['slots'], interaction.user.name, self.values['region'], self.values['type'], self.values['perks'])
        await interaction.response.send_message(content="@everyone League Live!", embed=view.create_embed(), view=view)

# --- 3. Komandos ---
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Botas aktyvus: {bot.user}")

@bot.tree.command(name="league", description="Host a session")
@app_commands.checks.has_any_role(ALLOWED_ROLE_ID)
async def league(interaction: discord.Interaction):
    await interaction.response.send_message("League Setup:", view=LeagueSetupView(), ephemeral=True)

@bot.tree.command(name="end", description="End session immediately")
@app_commands.checks.has_any_role(ALLOWED_ROLE_ID)
async def end(interaction: discord.Interaction):
    if isinstance(interaction.channel, discord.Thread):
        thread = interaction.channel
        await interaction.response.send_message("League session closed.")
        # Tik pervadiname ir uždarome, jokių klausimų
        await thread.edit(name="League: Ended", archived=True, locked=True)
    else:
        await interaction.response.send_message("Use this inside the league thread!", ephemeral=True)

keep_alive()
bot.run(TOKEN)
