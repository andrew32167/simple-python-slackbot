
import os
from Bot import Bot, CommandHandler
import re


class MyHandler(CommandHandler):
    _bot = None

    def handle_command(self, command, channel, user):
        command = re.sub(' +', ' ', command)
        if command.startswith('what\'s up'):
            self._bot.post_message(channel=channel, message="@{} all good".format(user))
            question = 'Would you like some coffee?'
            answers = ['yes', 'no']
            answer = self._bot.wait_for_answer_from_user(question, answers, channel, user, new_thread=True)
            if answer == 'yes':
                self._bot.post_message(channel, 'Here you go :coffee:')
            else:
                self._bot.post_message(channel, 'Sure no coffee today')


def main():

    bot = Bot(bot_token=os.environ.get('CLUSTER_BOT_TOKEN'),
              bot_id=os.environ.get('CLUSTER_BOT_ID'),
              command_handler=MyHandler)

    chnl = 'D39TY1ZV2'
    msg = bot.post_message(chnl, 'I\'m here bitchez!!')
    bot.add_reaction(msg, "facepalm", chnl)

    bot.poll(non_stop=False)

main()