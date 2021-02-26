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
    "dev":"main",
    "main":"main",
    "release":"release",
    "stable":"release",
}

with open('.authorised_users', 'r') as f:
    print('uwu')
    authorized_users = [int(i.strip()) for i in f.read().split('\n') if i.strip() != '']

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

        subprocess_command = ['./curly-binaries/curlyc' + ('-main' if dev else '-release'), 'build', '/dev/stdin']
        comp = subprocess.run(['./curly-binaries/curlyc' + ('-main' if dev else '-release'), 'build', '/dev/stdin'], stdout = subprocess.PIPE, stderr = subprocess.PIPE, input = result, encoding='utf-8')

        print(comp.stderr)
        print(comp.stdout)

        if comp.stderr:
            err = ansi_escape.sub('', comp.stderr)
            err_mess = f'Error: ```ocaml\n{err}'
            trunc_err_mess = ''
            TRUNCATION_MESSAGE = 'Error truncated because of 2000 character limit.'
            
            if len(err_mess + '\n```') > 2000:
                for line in err_mess.split("\n"):
                    if 2000 - len(trunc_err_mess + "\n" + line) >= len(f'\n{TRUNCATION_MESSAGE}\n```'):
                        trunc_err_mess += "\n"
                        trunc_err_mess += line
                trunc_err_mess += f'\n{TRUNCATION_MESSAGE}'
            else:
                trunc_err_mess = err_mess
            trunc_err_mess += '\n```'

            await message.channel.send(trunc_err_mess)
            return
        
        temp_timeout = timeout
        subprocess_command = ['./.build/main']

        if message.content.startswith("timeout"):
            try:
                timeout_value = message.content.split(" ")[1].split("`")[0]
                if timeout_value:
                    if message.author.id in authorized_users:
                        try:
                            if(float(timeout_value) != 0.0):
                                await message.channel.send(f'Timeout set to {timeout_value}.')
                            else:
                                await message.channel.send('No timeout set.  This could potentially run forever.')
                            temp_timeout = str(float(timeout_value))
                        except:
                            await message.channel.send(f'"{timeout_value}" is not a number.  Using default timeout of {timeout} instead.')
                    else:
                        await message.channel.send(f'Unauthorized user, default timeout of {timeout} used.')
            except:
                if message.author.id in authorized_users:
                    await message.channel.send('"timeout" used without a parameter!\nTimeout works like:\n\ntimeout [number] ```\n[code here]```')
                else:
                    await message.channel.send(f'Unauthorized user, default timeout of {timeout} used.')
        
        subprocess_command = ['timeout', temp_timeout] + subprocess_command
        
        p = subprocess.run(subprocess_command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, input = result, encoding='utf-8')
        
        
        print(p.stderr)
        print(p.stdout)
        if p.returncode == 124:
            await message.channel.send(f'Operation timed out:\n```ocaml\n{result}\n```')
        elif p.stdout:
            msg = ansi_escape.sub('', p.stdout)
            await message.channel.send(f'Result: ```\n{msg}\n```')
        elif p.stderr:
            err = ansi_escape.sub('', p.stderr)
            err_mess = f'Error: ```ocaml\n{err}'
            trunc_err_mess = ''
            TRUNCATION_MESSAGE = 'Error truncated because of 2000 character limit.'

            if len(err_mess + '\n```') > 2000:
                for line in err_mess.split("\n"):
                    if 2000 - len(trunc_err_mess + "\n" + line) >= len(f'\n{TRUNCATION_MESSAGE}\n```'):
                        trunc_err_mess += "\n"
                        trunc_err_mess += line
                trunc_err_mess += f'\n{TRUNCATION_MESSAGE}'
            else:
                trunc_err_mess = err_mess
            trunc_err_mess += '\n```'

            await message.channel.send(trunc_err_mess)
        else:
            await message.channel.send(f'Operation executed successfully:\n```ocaml\n{result}\n```')
    
    if message.content.startswith("curly-update"):
        if len(message.content.split(" ")) < 2:
            await message.channel.send('Invalid curly branch!\nValid branches are:\n' + ", ".join(branches.keys()))
        elif message.content.split(" ")[1] in list(branches.keys()):
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
    
    if message.content == "curly-restart":
        if message.author.id in authorized_users:
            await message.channel.send("Restarting...")
            await client.logout()
        else:
            await message.channel.send("Unauthorized user, cancelling restart.")


client.run(TOKEN)
