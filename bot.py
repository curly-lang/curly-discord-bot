import os
import re
import discord
import subprocess
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()
code_blocks = re.compile(r'```([^\n]*)\n(.*?)```', re.DOTALL)
ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
timeout = '10'

branches = {
    "dev":"main",
    "main":"main",
    "release":"release",
    "stable":"release",
}

with open('curly-args.txt', 'r') as f:
    print('owo?')
    curly_args = [i.strip() for i in f.read().split('\n') if i.strip() != '']
    print('curly args: %s' % curly_args)

with open('.authorised_users', 'r') as f:
    print('uwu')
    authorized_users = [int(i.strip()) for i in f.read().split('\n') if i.strip() != '']

async def send_msg(message, content):
    try:
        message.reply(content)
    except:
        message.channel.send(content)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("!curly"):
        dev = message.content.startswith('!curly-dev')
        print(f'Received message:\n{message.content}')
        matches = code_blocks.findall(message.content)

        result = ''
        for match in matches:
            result += match[1]
        result = result.strip()

        if result == '':
            return

        if dev:
            print('Dev mode on')
        print(f'Running:\n{result}')

        comp = subprocess.run(['./curly-binaries/curlyc' + ('-main' if dev else '-release'), 'build', '/dev/stdin'] + curly_args, stdout = subprocess.PIPE, stderr = subprocess.PIPE, input = result, encoding='utf-8')

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

            await send_msg(message, trunc_err_mess)
            return

        temp_timeout = timeout
        subprocess_command = ['./.build/main']

        if '!timeout' in message.content:
            try:
                timeout_value = message.content[message.content.find('!timeout'):].split(" ")[1].split("`")[0]
                if timeout_value:
                    if message.author.id in authorized_users:
                        try:
                            if(float(timeout_value) != 0.0):
                                await send_msg(message, f'Timeout set to {timeout_value}.')
                            else:
                                await send_msg(message, 'No timeout set.  This could potentially run forever.')
                            temp_timeout = str(float(timeout_value))
                        except:
                            await send_msg(message, f'"{timeout_value}" is not a number.  Using default timeout of {timeout} instead.')
                    else:
                        await send_msg(message, f'Unauthorized user, default timeout of {timeout} used.')
            except:
                if message.author.id in authorized_users:
                    await send_msg(message, '"timeout" used without a parameter!\nTimeout works like:\n\ntimeout [number] ```\n[code here]```')
                else:
                    await send_msg(message, f'Unauthorized user, default timeout of {timeout} used.')

        subprocess_command = ['timeout', temp_timeout] + subprocess_command

        p = subprocess.run(subprocess_command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, input = result, encoding='utf-8')


        print(p.stderr)
        print(p.stdout)
        if p.returncode == 124:
            await send_msg(message, f'Operation timed out:\n```ocaml\n{result}\n```')
        elif p.stdout:
            msg = ansi_escape.sub('', p.stdout)
            await send_msg(message, f'Result: ```\n{msg}\n```')
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

            await send_msg(message, trunc_err_mess)
        else:
            await send_msg(message, f'Operation executed successfully:\n```ocaml\n{result}\n```')

    if message.content.startswith("curly-update"):
        if len(message.content.split(" ")) < 2:
            await send_msg(message, 'Invalid curly branch!\nValid branches are:\n' + ", ".join(branches.keys()))
        elif message.content.split(" ")[1] in list(branches.keys()):
            subprocess_command = ['./curly-update.sh', branches[message.content.split(" ")[1]]]
            if len(message.content.split(" ")) == 3:
                if message.content.split(" ")[2] == "--force" or message.content.split(" ")[2] == "-f":
                    if message.author.id in authorized_users:
                        subprocess_command.append("--force")
                    else:
                        await send_msg(message, "The `--force` parameter is currently being locked to authorized users only.  Running regular upgrade.")
                else:
                    await send_msg(message, "Illegal usage of second parameter.\n Command format follows:```curly-update [branch name] (--force or -f)```")
                    return
                if len(message.content.split(" ")) > 3:
                    await send_msg(message, "Too many paraeters passed.\n Command format follows:```curly-update [branch name] (--force or -f)```")
                    return
            await send_msg(message, "Running: `" + " ".join(subprocess_command) + "`")
            p = subprocess.run(subprocess_command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, encoding='utf-8')
            msg = ansi_escape.sub('', p.stdout)
            await send_msg(message, f'Result: ```\n{msg}\n```')
        else:
            await send_msg(message, "Invalid curly branch!\nValid branches are:\n" + ", ".join(branches.keys()))
            return

    if message.content == "curly-restart":
        if message.author.id in authorized_users:
            await send_msg(message, "Restarting...")
            await client.logout()
        else:
            await send_msg(message, "Unauthorized user, cancelling restart.")


client.run(TOKEN)
