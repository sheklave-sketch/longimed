"""
Set BotFather commands programmatically on startup.
Called from post_init in bot/main.py.
"""


async def set_bot_commands(app):
    from telegram import BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats

    # Private chat commands (full menu)
    private_commands = [
        BotCommand("start", "Start or restart the bot"),
        BotCommand("menu", "Show your menu"),
        BotCommand("help", "Show available commands"),
        BotCommand("end", "End your active consultation session"),
        BotCommand("search", "Search Q&A or doctors"),
    ]
    await app.bot.set_my_commands(private_commands, scope=BotCommandScopeAllPrivateChats())

    # Group chat commands (only /end)
    group_commands = [
        BotCommand("end", "End this consultation session"),
    ]
    await app.bot.set_my_commands(group_commands, scope=BotCommandScopeAllGroupChats())
