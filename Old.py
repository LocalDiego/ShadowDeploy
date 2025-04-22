import os
import sys
import time
import threading
import asyncio
import discord
from discord.ext import commands
import requests

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    LIGHT_GRAY = "\033[90m"
    WHITE = "\033[37m"

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def print_colored(text, color=Colors.WHITE, bold=False, underline=False, big=False):
    style = ""
    if big or bold:
        style += Colors.BOLD
    if underline:
        style += Colors.UNDERLINE
    print(f"{style}{color}{text.upper() if big else text}{Colors.RESET}")

clear()
print_colored("========== ShadowDeploy by LK-GONNA11 ==========", Colors.MAGENTA, bold=True, big=True)
print_colored("Enable PRIVILEGED INTENTS on the Discord Developer Portal:", Colors.YELLOW)
print_colored("1. https://discord.com/developers/applications", Colors.CYAN)
print_colored("2. Select your bot", Colors.CYAN)
print_colored("3. Go to the 'Bot' tab", Colors.CYAN)
print_colored("4. Enable: PRESENCE INTENT + SERVER MEMBERS INTENT", Colors.CYAN)
input(f"\n{Colors.YELLOW}Press Enter when done...{Colors.RESET}")

class BotController:
    def __init__(self, token, name):
        self.token = token
        self.name = name
        self.bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.run_bot)
        self.guilds = []
        self.channels = {}
        self.thread.start()

        @self.bot.event
        async def on_ready():
            self.guilds = self.bot.guilds
            print_colored(f"Bot '{self.name}' is now connected!", Colors.GREEN, bold=True)
            max_display = 10
            for i, guild in enumerate(self.guilds[:max_display]):
                print_colored(f"- {guild.name} (ID: {guild.id})", Colors.CYAN)
                self.channels[guild.id] = guild.text_channels
            if len(self.guilds) > max_display:
                print_colored(f"...and {len(self.guilds) - max_display} more servers not shown", Colors.YELLOW)

    def run_bot(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.bot.start(self.token))
        except Exception as e:
            print_colored(f"[{self.name}] Connection Error: {e}", Colors.RED)

    def send_message_safe(self, channel_id, message):
        asyncio.run_coroutine_threadsafe(self.bot.get_channel(int(channel_id)).send(message), self.bot.loop)

    def get_guild_names_and_ids(self, limit=100):
        return [(g.name, g.id) for g in self.guilds[:limit]]

    def get_channel_names_and_ids_for_guild(self, guild_id):
        return [(c.name, c.id) for c in self.channels.get(guild_id, [])]

    def fetch_logs(self, guild_id, limit=3):
        logs = []
        for channel in self.channels.get(guild_id, []):
            if channel.permissions_for(channel.guild.me).read_message_history:
                try:
                    messages = asyncio.run_coroutine_threadsafe(channel.history(limit=limit).flatten(), self.bot.loop).result()
                    for m in messages:
                        logs.append(f"[{channel.name}] {m.author}: {m.content}")
                except:
                    continue
        return logs

def send_webhook_alert(webhook_url):
    payload = {
        "username": "ShadowDeploy",
        "content": "**ShadowDeploy by LK-GONNA11** has successfully connected."
    }
    try:
        requests.post(webhook_url, json=payload)
    except Exception as e:
        print_colored(f"Webhook error: {e}", Colors.RED)

def interface():
    clear()
    print_colored("========== ShadowDeploy MultiTool ==========", Colors.MAGENTA, bold=True, big=True)
    webhook = input(f"{Colors.YELLOW}Enter webhook URL for alerts (or leave blank): {Colors.RESET}")
    if webhook:
        send_webhook_alert(webhook)

    while True:
        try:
            n = int(input(f"{Colors.YELLOW}How many bots to load? (min: 1): {Colors.RESET}"))
            if n >= 1:
                break
        except:
            print_colored("Invalid number. Try again.", Colors.RED)

    bots = []
    for i in range(n):
        token = input(f"{Colors.YELLOW}Bot Token {i+1}: {Colors.RESET}")
        name = input(f"{Colors.YELLOW}Bot Name {i+1}: {Colors.RESET}")
        with open("tokens.txt", "a") as f:
            f.write(f"{token}|{name}\n")
        bots.append(BotController(token, name))

    while True:
        clear()
        print_colored("========== Control Panel ==========", Colors.MAGENTA, bold=True, big=True)
        print_colored("Select a bot to manage:", Colors.GREEN)
        for i, bot in enumerate(bots):
            print_colored(f"{i+1}. {bot.name}", Colors.CYAN)
        print_colored("0. Exit", Colors.RED)

        try:
            choice = int(input("Your choice: "))
            if choice == 0:
                print_colored("Goodbye!", Colors.GREEN)
                sys.exit()
            elif 1 <= choice <= len(bots):
                sub_menu(bots[choice - 1])
        except:
            print_colored("Invalid input. Try again.", Colors.RED)
            time.sleep(1)

def sub_menu(bot):
    while True:
        clear()
        print_colored(f"========== {bot.name} - Menu ==========", Colors.MAGENTA, bold=True, big=True)
        print_colored("1. Send Message", Colors.CYAN)
        print_colored("2. View Logs", Colors.CYAN)
        print_colored("0. Back", Colors.YELLOW)

        try:
            action = int(input("Action: "))
            if action == 0:
                break
            elif action == 1:
                servers = bot.get_guild_names_and_ids()
                for i, (name, gid) in enumerate(servers):
                    print_colored(f"{i+1}. {name} (ID: {gid})", Colors.CYAN)
                sidx = int(input("Server #: ")) - 1
                if 0 <= sidx < len(servers):
                    channels = bot.get_channel_names_and_ids_for_guild(servers[sidx][1])
                    for i, (cname, cid) in enumerate(channels):
                        print_colored(f"{i+1}. {cname} (ID: {cid})", Colors.CYAN)
                    cidx = int(input("Channel #: ")) - 1
                    if 0 <= cidx < len(channels):
                        msg = input("Message to send: ")
                        bot.send_message_safe(channels[cidx][1], msg)
                        print_colored("Message sent successfully!", Colors.GREEN)
                input("Press Enter to continue...")
            elif action == 2:
                servers = bot.get_guild_names_and_ids()
                for i, (name, gid) in enumerate(servers):
                    print_colored(f"{i+1}. {name} (ID: {gid})", Colors.CYAN)
                sidx = int(input("Server #: ")) - 1
                if 0 <= sidx < len(servers):
                    logs = bot.fetch_logs(servers[sidx][1])
                    print_colored("=== RECENT LOGS ===", Colors.YELLOW, bold=True)
                    if logs:
                        for log in logs:
                            print_colored(log, Colors.LIGHT_GRAY)
                    else:
                        print_colored("No logs available or permission denied.", Colors.RED)
                input("\nPress Enter to return...")
        except:
            print_colored("Error. Returning to menu...", Colors.RED)
            time.sleep(1)

if __name__ == "__main__":
    interface()
