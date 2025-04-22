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

class BotController:
    def __init__(self, token, name, op_mode=False):
        self.token = token
        self.name = name
        self.op_mode = op_mode
        self.bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.run_bot)
        self.guilds = []
        self.channels = {}
        self.auto_reply = False
        self.auto_spam = False
        self.reply_message = "Automated Reply!"
        self.thread.start()

        @self.bot.event
        async def on_ready():
            self.guilds = self.bot.guilds
            print_colored(f"Bot '{self.name}' is now connected!", Colors.GREEN, bold=True)
            for guild in self.guilds:
                self.channels[guild.id] = guild.text_channels

        if self.op_mode:
            @self.bot.event
            async def on_message(msg):
                if self.auto_reply and msg.author != self.bot.user:
                    await msg.channel.send(self.reply_message)
                await self.bot.process_commands(msg)

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

    def toggle_reply(self):
        self.auto_reply = not self.auto_reply
        return self.auto_reply

    def toggle_spam(self, channel_id, message):
        if not self.auto_spam:
            self.auto_spam = True
            threading.Thread(target=self._spam_loop, args=(channel_id, message)).start()
        else:
            self.auto_spam = False

    def _spam_loop(self, channel_id, message):
        while self.auto_spam:
            self.send_message_safe(channel_id, message)
            time.sleep(1)

    def add_custom_command(self, command_name, response):
        @self.bot.command(name=command_name)
        async def custom_command(ctx):
            await ctx.send(response)

    def set_auto_reply_message(self, message):
        self.reply_message = message

def send_webhook_alert(webhook_url):
    payload = {"username": "ShadowDeploy", "content": "**ShadowDeploy by LK-GONNA11** has successfully connected."}
    try:
        requests.post(webhook_url, json=payload)
    except Exception as e:
        print_colored(f"Webhook error: {e}", Colors.RED)

def sub_menu(bot):
    while True:
        clear()
        print_colored(f"========== {bot.name} - Menu ==========", Colors.MAGENTA, bold=True, big=True)
        print_colored("1. Send Message", Colors.CYAN)
        print_colored("2. View Logs", Colors.CYAN)
        if bot.op_mode:
            print_colored("3. Toggle Auto-Reply", Colors.CYAN)
            print_colored("4. Toggle Auto-Spam", Colors.CYAN)
            print_colored("5. Add Custom Command", Colors.CYAN)
            print_colored("6. Execute Command", Colors.CYAN)
            print_colored("7. Set Auto-Reply Message", Colors.CYAN)
            print_colored(f"{Colors.RED}8. Stop Auto-Reply{Colors.RESET}", Colors.RED)
            print_colored(f"{Colors.RED}9. Stop Spam{Colors.RESET}", Colors.RED)
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
                channels = bot.get_channel_names_and_ids_for_guild(servers[sidx][1])
                for i, (cname, cid) in enumerate(channels):
                    print_colored(f"{i+1}. {cname} (ID: {cid})", Colors.CYAN)
                cidx = int(input("Channel #: ")) - 1
                msg = input("Message to send: ")
                bot.send_message_safe(channels[cidx][1], msg)
                print_colored("Message sent!", Colors.GREEN)
                input("Enter to continue...")
            elif action == 2:
                servers = bot.get_guild_names_and_ids()
                for i, (name, gid) in enumerate(servers):
                    print_colored(f"{i+1}. {name} (ID: {gid})", Colors.CYAN)
                sidx = int(input("Server #: ")) - 1
                logs = bot.fetch_logs(servers[sidx][1])
                for log in logs:
                    print_colored(log, Colors.LIGHT_GRAY)
                input("Enter to return...")
            elif action == 3 and bot.op_mode:
                status = bot.toggle_reply()
                print_colored(f"Auto-Reply {'enabled' if status else 'disabled'}", Colors.YELLOW)
                input("Enter to continue...")
            elif action == 4 and bot.op_mode:
                servers = bot.get_guild_names_and_ids()
                for i, (name, gid) in enumerate(servers):
                    print_colored(f"{i+1}. {name} (ID: {gid})", Colors.CYAN)
                sidx = int(input("Server #: ")) - 1
                channels = bot.get_channel_names_and_ids_for_guild(servers[sidx][1])
                for i, (cname, cid) in enumerate(channels):
                    print_colored(f"{i+1}. {cname} (ID: {cid})", Colors.CYAN)
                cidx = int(input("Channel #: ")) - 1
                msg = input("Spam message: ")
                bot.toggle_spam(channels[cidx][1], msg)
                print_colored("Toggled spam mode.", Colors.YELLOW)
                input("Enter to continue...")
            elif action == 5 and bot.op_mode:
                cmd_name = input("Enter custom command name: ")
                response = input("Enter response for the command: ")
                bot.add_custom_command(cmd_name, response)
                print_colored(f"Custom command '{cmd_name}' added.", Colors.GREEN)
                input("Enter to continue...")
            elif action == 6 and bot.op_mode:
                command = input("Enter the command to execute: ")
                try:
                    exec(command)
                    print_colored(f"Executed: {command}", Colors.GREEN)
                except Exception as e:
                    print_colored(f"Error: {e}", Colors.RED)
                input("Enter to continue...")
            elif action == 7 and bot.op_mode:
                new_message = input("Enter new auto-reply message: ")
                bot.set_auto_reply_message(new_message)
                print_colored(f"Auto-reply message set to: {new_message}", Colors.GREEN)
                input("Enter to continue...")
            elif action == 8 and bot.op_mode:
                bot.toggle_reply()
                print_colored("Auto-Reply deactivated.", Colors.RED)
                input("Enter to continue...")
            elif action == 9 and bot.op_mode:
                bot.auto_spam = False
                print_colored("Spam mode deactivated.", Colors.RED)
                input("Enter to continue...")
        except:
            print_colored("Invalid input", Colors.RED)
            time.sleep(1)

def interface(op_mode=False):
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
        bots.append(BotController(token, name, op_mode=op_mode))

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

if __name__ == "__main__":
    clear()
    print_colored("========== ShadowDeploy by LK-GONNA11 ==========", Colors.MAGENTA, bold=True, big=True)
    print_colored("1. Launch CLASSIC version", Colors.CYAN)
    print_colored("2. Launch OP version", Colors.YELLOW)
    choice = input("Your choice (1/2): ")
    if choice == "2":
        interface(op_mode=True)
    else:
        interface(op_mode=False)
        
