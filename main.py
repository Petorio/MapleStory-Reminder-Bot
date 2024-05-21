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
        """Reminds the user to refresh EXP."""
        buttons = [
            discord.ui.Button(style=discord.ButtonStyle.primary, label="15 minutes", custom_id="exp_15"),
            discord.ui.Button(style=discord.ButtonStyle.primary, label="30 minutes", custom_id="exp_30"),
            discord.ui.Button(style=discord.ButtonStyle.primary, label="60 minutes", custom_id="exp_60"),
            discord.ui.Button(style=discord.ButtonStyle.danger, label="Quit Bot", custom_id="quit")
        ]
        view = discord.ui.View()
        for button in buttons:
            view.add_item(button)

        await ctx.author.send("Set a reminder for EXP:", view=view)

    @bot.command()
    async def legion(ctx):
        """Reminds the user to refresh Legion Wealth."""
        buttons = [
            discord.ui.Button(style=discord.ButtonStyle.primary, label="10 minutes", custom_id="legion_10"),
            discord.ui.Button(style=discord.ButtonStyle.primary, label="20 minutes", custom_id="legion_20"),
            discord.ui.Button(style=discord.ButtonStyle.primary, label="30 minutes", custom_id="legion_30"),
            discord.ui.Button(style=discord.ButtonStyle.danger, label="Quit Bot", custom_id="quit")
        ]
        view = discord.ui.View()
        for button in buttons:
            view.add_item(button)

        await ctx.author.send("Set a reminder for Legion Wealth:", view=view)

    @bot.command()
    async def botinfo(ctx):
        """Displays bot commands and information regarding those commands."""
        embed = discord.Embed(title="Bot Commands", color=discord.Color.blue())
        embed.add_field(name="r!exp", value="Reminds the user to refresh EXP.", inline=False)
        embed.add_field(name="r!legion", value="Reminds the user to refresh Legion Wealth.", inline=False)
        embed.add_field(name="r!botinfo", value="Displays bot commands and information regarding those commands.", inline=False)
        await ctx.send(embed=embed)

    async def send_reminder_menu(channel, is_legion=False):
        if is_legion:
            buttons = [
                discord.ui.Button(style=discord.ButtonStyle.primary, label="10 minutes", custom_id="legion_10"),
                discord.ui.Button(style=discord.ButtonStyle.primary, label="20 minutes", custom_id="legion_20"),
                discord.ui.Button(style=discord.ButtonStyle.primary, label="30 minutes", custom_id="legion_30"),
                discord.ui.Button(style=discord.ButtonStyle.danger, label="Quit Bot", custom_id="quit")
            ]
        else:
            buttons = [
                discord.ui.Button(style=discord.ButtonStyle.primary, label="15 minutes", custom_id="exp_15"),
                discord.ui.Button(style=discord.ButtonStyle.primary, label="30 minutes", custom_id="exp_30"),
                discord.ui.Button(style=discord.ButtonStyle.primary, label="60 minutes", custom_id="exp_60"),
                discord.ui.Button(style=discord.ButtonStyle.danger, label="Quit Bot", custom_id="quit")
            ]
        view = discord.ui.View()
        for button in buttons:
            view.add_item(button)
        
        if is_legion:
            await channel.send("Set a reminder for LEGION:", view=view)
        else:
            await channel.send("Set a reminder for EXP:", view=view)

    @bot.event
    async def on_interaction(interaction):
        if interaction.type != discord.InteractionType.component:
            return

        user_id = interaction.user.id
        custom_id = interaction.data["custom_id"]

        logger.info(f"User: {interaction.user} (ID: {user_id}) using {custom_id} button")
        logger.info(f"Current reminder_tasks: {reminder_tasks}")

        if custom_id == "quit":
            await interaction.response.send_message("Bot has been quit.")
            await interaction.message.delete()
            return

        if custom_id == "cancel":
            task_key_prefix = f"{user_id}_"
            task_key = next((key for key in reminder_tasks if key.startswith(task_key_prefix)), None)
            if task_key and task_key in reminder_tasks:
                reminder_type = reminder_tasks[task_key]["type"]
                reminder_tasks[task_key]["task"].cancel()
                del reminder_tasks[task_key]
                await interaction.response.send_message("Reminder canceled.")
                await send_reminder_menu(interaction.channel, is_legion=(reminder_type == "legion"))  # Send the appropriate reminder menu again after canceling
                logger.info(f"Updated reminder_tasks: {reminder_tasks}")
            return

        if custom_id.startswith("exp_"):
            wait_time = int(custom_id.split("_")[1]) * 60
            reminder_type = "exp"
        elif custom_id.startswith("legion_"):
            wait_time = int(custom_id.split("_")[1]) * 60
            reminder_type = "legion"
        else:
            return

        # Remove all buttons except cancel after clicking a time button
        cancel_button = discord.ui.Button(style=discord.ButtonStyle.danger, label="Cancel", custom_id="cancel")
        view = discord.ui.View()
        view.add_item(cancel_button)
        await interaction.response.edit_message(content=f"Reminder set for {reminder_type.upper()}, {custom_id.split('_')[1]} minutes. Waiting...", view=view)

        async def reminder_task():
            try:
                await asyncio.sleep(wait_time)
                await interaction.channel.send(f"{interaction.user.mention}, Refresh your {reminder_type.upper()}!")
                # Remove the interaction message with buttons
                await interaction.message.delete()
                await send_reminder_menu(interaction.channel, is_legion=(reminder_type == "legion"))  # Send the reminder menu again after reminder
            except asyncio.CancelledError:
                await interaction.message.delete()

        # Start the reminder task and store it in the dictionary
        task_key = f"{user_id}_{custom_id}"
        task = bot.loop.create_task(reminder_task())
        reminder_tasks[task_key] = {"task": task, "type": reminder_type}
        logger.info(f"Added task {task_key} to reminder_tasks")

    bot.run(settings.DISCORD_SECRET, root_logger=True)

if __name__ == "__main__":
    run()