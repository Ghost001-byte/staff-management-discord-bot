import os
import json
import logging
from datetime import datetime, UTC
import asyncio

import discord
from discord.ext import commands, tasks
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")
DATA_FILE = "bot_data.json"
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

data = {
    "roles": {},
    "blacklist": [],
    "absences": {},
}

def load_data():
    global data
    if os.path.isfile(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logging.error(f"Errore caricamento dati: {e}")
    else:
        save_data()

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Errore salvataggio dati: {e}")

async def log_event(message: str):
    if LOG_CHANNEL_ID:
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(message)


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apri Ticket", style=discord.ButtonStyle.green, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="Tickets")
        if not category:
            category = await guild.create_category("Tickets")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        staff_role = discord.utils.get(guild.roles, name="Staff")
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )
        await channel.send(f"{interaction.user.mention} Benvenuto nel tuo ticket! Spiega il tuo problema e lo staff ti aiuterà.")
        await interaction.response.send_message(f"✅ Ticket creato: {channel.mention}", ephemeral=True)

@tree.command(name="ticketpanel", description="Invia il pannello per aprire ticket")
@app_commands.describe(channel="Canale dove inviare il pannello")
async def ticketpanel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Permesso negato: solo amministratori.", ephemeral=True)
        return
    embed = discord.Embed(
        title="🎫 Apri un Ticket",
        description="Hai bisogno di aiuto? Premi il pulsante qui sotto per aprire un ticket privato con lo staff.",
        color=0x3498db
    )
    await channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message(f"Pannello ticket inviato in {channel.mention}", ephemeral=True)

@tree.command(name="close", description="Chiudi il ticket (solo nei canali ticket)")
async def close(interaction: discord.Interaction):
    channel = interaction.channel
    if channel.category and channel.category.name == "Tickets":
        await interaction.response.send_message("🔒 Ticket chiuso. Il canale verrà eliminato tra pochi secondi.", ephemeral=True)
        await asyncio.sleep(3)
        await channel.delete()
    else:
        await interaction.response.send_message("❌ Questo comando va usato solo nei canali ticket.", ephemeral=True)

@tree.command(name="rename", description="Rinomina il ticket (solo nei canali ticket)")
@app_commands.describe(new_name="Nuovo nome del ticket")
async def rename(interaction: discord.Interaction, new_name: str):
    channel = interaction.channel
    if channel.category and channel.category.name == "Tickets":
        await channel.edit(name=new_name)
        await interaction.response.send_message(f"✅ Ticket rinominato in `{new_name}`.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Questo comando va usato solo nei canali ticket.", ephemeral=True)

@tree.command(name="claim", description="Prendi in carico il ticket (solo nei canali ticket)")
async def claim(interaction: discord.Interaction):
    channel = interaction.channel
    if channel.category and channel.category.name == "Tickets":
        await channel.send(f"🎟️ {interaction.user.mention} ha preso in carico questo ticket!")
        await interaction.response.send_message("Hai preso in carico il ticket.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Questo comando va usato solo nei canali ticket.", ephemeral=True)

@tree.command(name="pex", description="Assegna un ruolo ad un utente (slash command)")
@app_commands.describe(member="Utente", role="Ruolo", reason="Motivazione")
async def pex(interaction: discord.Interaction, member: discord.Member, role: str, reason: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Permesso negato: solo amministratori.", ephemeral=True)
        return
    uid = str(member.id)
    data["roles"][uid] = {
        "role": role,
        "reason": reason,
        "assigned_by": interaction.user.id,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    save_data()
    await interaction.response.send_message(f"✅ {member.mention} assegnato al ruolo **{role}**\nMotivazione: {reason}")
    await log_event(f"[PEX] {member} ➔ {role} by {interaction.user}: {reason}")

@tree.command(name="depex", description="Declassa un utente a user (slash command)")
@app_commands.describe(member="Utente", reason="Motivazione")
async def depex(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Permesso negato: solo amministratori.", ephemeral=True)
        return
    uid = str(member.id)
    data["roles"][uid] = {
        "role": "user",
        "reason": reason,
        "assigned_by": interaction.user.id,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    save_data()
    await interaction.response.send_message(f"✅ {member.mention} declassato a **user**\nMotivazione: {reason}")
    await log_event(f"[DEPEX] {member} ➔ user by {interaction.user}: {reason}")

@tree.command(name="blacklist", description="Aggiungi un utente alla blacklist e lo banna (slash command)")
@app_commands.describe(member="Utente", reason="Motivazione")
async def blacklist(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Permesso negato: solo amministratori.", ephemeral=True)
        return
    uid = str(member.id)
    if uid not in data["blacklist"]:
        data["blacklist"].append(uid)
    data["roles"].pop(uid, None)
    save_data()
    try:
        await member.ban(reason=f"Blacklist: {reason}")
        await interaction.response.send_message(f"⛔️ {member.mention} aggiunto alla blacklist e bannato permanentemente.\nMotivazione: {reason}")
        await log_event(f"[BLACKLIST] {member} bannato by {interaction.user}: {reason}")
    except Exception as e:
        await interaction.response.send_message(f"Errore nel ban: {e}", ephemeral=True)

@tree.command(name="assenza", description="Segna un utente in assenza (slash command)")
@app_commands.describe(member="Utente", date="YYYY-MM-DD", reason="Motivazione")
async def assenza(interaction: discord.Interaction, member: discord.Member, date: str, reason: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Permesso negato: solo amministratori.", ephemeral=True)
        return
    try:
        expires = datetime.fromisoformat(date)
    except ValueError:
        await interaction.response.send_message("❗️ Formato data non valido. Usa YYYY-MM-DD.", ephemeral=True)
        return
    uid = str(member.id)
    data["absences"][uid] = {
        "expires": expires.isoformat(),
        "reason": reason,
        "assigned_by": interaction.user.id,
    }
    save_data()
    await interaction.response.send_message(f"✈️ {member.mention} in assenza fino al {expires.date()}\nMotivazione: {reason}")
    await log_event(f"[ASSENZA] {member} until {expires.date()} by {interaction.user}: {reason}")

@tree.command(name="stafflist", description="Mostra la lista dello staff attivo (slash command)")
async def stafflist(interaction: discord.Interaction):
    now = datetime.now(UTC)
    ROLE_PRIORITY = {"owner":100,"admin":90,"mod":80,"helper":70}
    staff = []
    guild = interaction.guild

    for uid, info in data["roles"].items():
        if info["role"] == "user" or uid in data["blacklist"]:
            continue
        abs_info = data["absences"].get(uid)
        if abs_info and datetime.fromisoformat(abs_info["expires"]) > now:
            continue
        member = guild.get_member(int(uid))
        if member:
            priority = ROLE_PRIORITY.get(info["role"], 0)
            staff.append((priority, member.display_name, info["role"]))

    staff.sort(key=lambda x: -x[0])
    if not staff:
        await interaction.response.send_message("📋 Nessun membro dello staff attivo.")
        return

    lines = [f"{name} — {role}" for _, name, role in staff]
    embed = discord.Embed(
        title="📋 Lista Staff",
        description="\n".join(lines),
        color=0x00ff00
    )
    embed.set_footer(text=f"Totale staff: {len(lines)}")
    await interaction.response.send_message(embed=embed)

@tree.command(name="blacklistlist", description="Mostra la lista degli utenti blacklistati")
async def blacklistlist(interaction: discord.Interaction):
    guild = interaction.guild
    if not data["blacklist"]:
        await interaction.response.send_message("✅ Nessun utente in blacklist.")
        return
    lines = []
    for uid in data["blacklist"]:
        member = guild.get_member(int(uid))
        if member:
            lines.append(f"{member.mention} (`{uid}`)")
        else:
            lines.append(f"Utente ID: `{uid}` (non più nel server)")
    embed = discord.Embed(
        title="⛔️ Blacklist",
        description="\n".join(lines),
        color=0xff0000
    )
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    logging.info(f"Bot connesso come {bot.user}")
    load_data()
    try:
        synced = await tree.sync()
        logging.info(f"Slash commands sincronizzati: {len(synced)}")
    except Exception as e:
        logging.error(f"Errore sync slash commands: {e}")

if not TOKEN:
    raise RuntimeError("Token Discord non trovato. Imposta la variabile d'ambiente DISCORD_TOKEN.")

bot.run(TOKEN)

