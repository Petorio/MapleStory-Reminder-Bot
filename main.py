import settings
import discord
from discord.ext import commands
import asyncio

logger = settings.logging.getLogger("bot")

def run():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    reminder_tasks = {}

    bot = commands.Bot(command_prefix='r!', intents=intents)

    @bot.event
    async def on_ready():
        logger.info(f"Bot: {bot.user} (Bot ID: {bot.user.id})")

    @bot.command()
    async def exp(ctx):
        buttons = [
            discord.ui.Button(style=discord.ButtonStyle.primary, label="15 minutes", custom_id="15"),
            discord.ui.Button(style=discord.ButtonStyle.primary, label="30 minutes", custom_id="30"),
            discord.ui.Button(style=discord.ButtonStyle.primary, label="60 minutes", custom_id="60"),
            discord.ui.Button(style=discord.ButtonStyle.danger, label="Quit Bot", custom_id="quit")
        ]
        view = discord.ui.View()
        for button in buttons:
            view.add_item(button)

        await ctx.author.send("Set a reminder for:", view=view)

    async def send_reminder_menu(channel):
        buttons = [
            discord.ui.Button(style=discord.ButtonStyle.primary, label="15 minutes", custom_id="15"),
            discord.ui.Button(style=discord.ButtonStyle.primary, label="30 minutes", custom_id="30"),
            discord.ui.Button(style=discord.ButtonStyle.primary, label="60 minutes", custom_id="60"),
            discord.ui.Button(style=discord.ButtonStyle.danger, label="Quit Bot", custom_id="quit")
        ]
        view = discord.ui.View()
        for button in buttons:
            view.add_item(button)

        await channel.send("Set a reminder for:", view=view)

    @bot.event
    async def on_interaction(interaction):
        if interaction.type != discord.InteractionType.component:
            return

        user_id = interaction.user.id

        logger.info(f"User: {interaction.user} (ID: {user_id}) using {interaction.data["custom_id"]} button")

        if interaction.data["custom_id"] == "quit":
            await interaction.response.send_message("Bot has been quit.")
            await interaction.message.delete()
            return

        if interaction.data["custom_id"] == "cancel":
            if user_id in reminder_tasks:
                reminder_tasks[user_id].cancel()
                del reminder_tasks[user_id]
                await interaction.response.send_message("Reminder canceled.")
                await send_reminder_menu(interaction.channel)  # Send the reminder menu again after canceling
                return
            else:
                await interaction.message.delete()
                return

        time_mapping = {
            "15": 15 * 60,
            "30": 30 * 60,
            "60": 60 * 60
        }
        wait_time = time_mapping.get(interaction.data["custom_id"], 0)

        # Remove all buttons except cancel after clicking a time button
        cancel_button = discord.ui.Button(style=discord.ButtonStyle.danger, label="Cancel", custom_id="cancel")
        view = discord.ui.View()
        view.add_item(cancel_button)
        await interaction.response.edit_message(content=f"Reminder set for {interaction.data['custom_id']} minutes. Waiting...", view=view)

        async def reminder_task():
            try:
                await asyncio.sleep(wait_time)
                await interaction.channel.send(f"{interaction.user.mention}, Refresh your EXP!")
                # Remove the interaction message with buttons
                await interaction.message.delete()
                await send_reminder_menu(interaction.channel)  # Send the reminder menu again after reminder
            except asyncio.CancelledError:
                await interaction.message.delete()

        # Start the reminder task and store it in the dictionary
        task = bot.loop.create_task(reminder_task())
        reminder_tasks[user_id] = task

    bot.run(settings.DISCORD_SECRET, root_logger=True)


if __name__ == "__main__":
    run()