import os
import re
import discord
import subprocess
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()
code_blocks = re.compile(r'```curly(-dev)?\n(.*?)```', re.DOTALL)
ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
timeout = '10'

branches = {
    "dev":"master",
    "master":"master",
    "release":"release",
    "stable":"release",
}

authorized_users = None
with open('.authorised_users', 'r') as f:
    print('uwu')
    authorized_users = f.read().split('\n')


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if '```curly' in message.content:
        dev = False
        print(f'Received message:\n{message.content}')
        matches = code_blocks.findall(message.content)

        result = ''
        for match in matches:
            result += match[1]
            if match[0] == '-dev':
                dev = True
        result = result.strip()

        if result == '':
            return

        if dev:
            print('Dev mode on')
        print(f'Running:\n{result}')

        p = subprocess.run(['timeout', timeout, './curly-binaries/curlyc' + ('-master' if dev else '-release'), 'run', '/dev/stdin'], stdout = subprocess.PIPE, stderr = subprocess.PIPE, input = result, encoding='utf-8')

        print(p.stderr)
        print(p.stdout)
        if p.returncode == 124:
            await message.channel.send(f'Operation timed out:\n```\n{result}\n```')
        elif p.stdout:
            msg = ansi_escape.sub('', p.stdout)
            await message.channel.send(f'Result: ```\n{msg}\n```')
        else:
            err = ansi_escape.sub('', p.stderr)
            await message.channel.send(f'Error: ```\n{err}\n```')
    
    if message.content.startswith("curly-update"):
        if message.content.split(" ")[1] in list(branches.keys()):
            subprocess_command = ['./curly-update.sh', branches[message.content.split(" ")[1]]]
            if len(message.content.split(" ")) == 3:
                if message.content.split(" ")[2] == "--force" or message.content.split(" ")[2] == "-f":
                    if message.author.id in authorized_users:
                        subprocess_command.append("--force")
                    else:
                        await message.channel.send("The `--force` parameter is currently being locked to authorized users only.  Running regular upgrade.")
                else:
                    await message.channel.send("Illegal usage of second parameter.\n Command format follows:```curly-update [branch name] (--force or -f)```")
                    return
                if len(message.content.split(" ")) > 3:
                    await message.channel.send("Too many paraeters passed.\n Command format follows:```curly-update [branch name] (--force or -f)```")
                    return
            await message.channel.send("Running: `" + " ".join(subprocess_command) + "`")
            p = subprocess.run(subprocess_command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, encoding='utf-8')
            msg = ansi_escape.sub('', p.stdout)
            await message.channel.send(f'Result: ```\n{msg}\n```')
        else:
            await message.channel.send("Invalid curly branch!\nValid branches are:\n" + ", ".join(branches.keys()))
            return


client.run(TOKEN)
