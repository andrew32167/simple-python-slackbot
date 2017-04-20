#!/usr/bin/python
# -*- coding: utf-8 -*-
from slackclient import SlackClient
import time
import re
from utils.time_limit import time_limit, TimeoutException
import utils.logger as logger


class CommandHandler(object):
    _bot = None

    def __init__(self, bot):
        self._bot = bot

    def handle_command(self, command, channel, user):
        command = re.sub(' +', ' ', command)
        print '@{user} said `{command}` at {channel} channel,' \
              ' but I don\'t know what to do with that'.format(user=user, command=command, channel=channel)
        self._bot.send_message(channel=channel, message="Have no idea what to answer you ¯\_(ツ)_/¯".format(user))


class SlackBotException(Exception):
    pass


class Bot(object):
    _slack_client = None
    _bot_id = 0
    _bot_token = None
    _bot_name = None
    _bot_at = None
    _READ_WEBSOCKET_DELAY = 1  # 1 second delay between reading
    _command_handler = None

    def __init__(self, bot_token, bot_id=0, command_handler=None, bot_name="Nameless bot"):
        self._slack_client = SlackClient(bot_token)
        self._bot_id = bot_id
        self._bot_token = bot_token
        self._bot_name = self.get_username_by_id(self._bot_id)

        if self._bot_name is None:
            self._bot_name = bot_name

        self._bot_at = "<@{}>".format(self._bot_id)

        if command_handler is not None:
            self._command_handler = command_handler(self)
        else:
            self._command_handler = CommandHandler(self)

        if self._slack_client is None or self._bot_id is None or self._bot_name is None:
            raise ValueError("Not enough data to start Bot")

        logger.log('{} bot is online'.format(self._bot_name))

    def get_bot_info(self):
        return self.get_user_by_id(self._bot_id)

    def get_all_users(self):
        api_call = self._slack_client.api_call("users.list")
        if api_call.get('ok'):
            return api_call.get('members')
        return None

    def get_user_by_id(self, user_id):
        api_call = self._slack_client.api_call("users.list")
        if api_call.get('ok'):
            users = api_call.get('members')
            for user in users:
                if user.get('id') == user_id:
                    return user
        return None

    def get_user_by_name(self, username):
        api_call = self._slack_client.api_call("users.list")
        if api_call.get('ok'):
            users = api_call.get('members')
            for user in users:
                if user.get('name') == username:
                    return user
        return None

    def get_username_by_id(self, user_id):
        user = self.get_user_by_id(user_id)
        if user is not None:
            return user.get('name')
        return None

    def get_all_public_channels(self):
        api_call = self._slack_client.api_call("channels.list")
        if api_call.get('ok'):
            return api_call.get('channels')
        return None

    def get_channel_by_name(self, channel_name):
        channels = self.get_all_public_channels()
        if channels is not None:
            for ch in channels:
                if ch.get('name') == channel_name:
                    return ch
        return None

    def get_channel_by_id(self, channel_id):
        channels = self.get_all_public_channels()
        if channels is not None:
            for ch in channels:
                if ch.get('id') == channel_id:
                    return ch
        return None

    def get_all_private_channels(self):
        api_call = self._slack_client.api_call("groups.list")
        if api_call.get('ok'):
            return api_call.get('groups')
        return None

    def get_private_channel_by_name(self, channel_name):
        channels = self.get_all_private_channels()
        if channels is not None:
            for ch in channels:
                if ch.get('name') == channel_name:
                    return ch
        return None

    def get_private_channel_by_id(self, channel_id):
        channels = self.get_all_private_channels()
        if channels is not None:
            for ch in channels:
                if ch.get('id') == channel_id:
                    return ch
        return None

    def custom_api_call(self, method, **kwargs):
        return self._slack_client.api_call(method, **kwargs)

    def parse_at_usage(self, slack_rtm_output):
        output_list = slack_rtm_output
        if output_list and len(output_list) > 0:
            for output in output_list:
                if output and 'text' in output and self._bot_at in output['text']:
                    # return text after the @ mention, whitespace removed
                    if not output['text'].split(' ')[0] == self._bot_at:
                        return output['text'].split(self._bot_at + ':')[1].strip().lower(), output['channel'], \
                               self.get_username_by_id(output['user'])
                    return output['text'].split(self._bot_at)[1].strip().lower(), output['channel'], \
                           self.get_username_by_id(output['user'])
        return None, None, None

    def poll(self, non_stop=True, delta=60):
        if self._slack_client.rtm_connect():
            logger.log("{} started polling".format(self._bot_name))
            if non_stop:
                self.__handler_wrapper__()
            else:
                try:
                    with time_limit(delta):
                        self.__handler_wrapper__()
                except TimeoutException:
                    logger.log("{} stopped polling".format(self._bot_name))
                    return
        else:
            logger.log("Connection failed. Invalid Slack token or bot ID?")
            raise SlackBotException("{} failed to start polling".format(self._bot_name))

    def __handler_wrapper__(self):
        while True:
            command, channel, user = self.parse_at_usage(self._slack_client.rtm_read())
            if command and channel:
                self._command_handler.handle_command(command, channel, user)
            time.sleep(self._READ_WEBSOCKET_DELAY)

    def __parse_answer__(self, slack_client):
        slack_rtm_output = slack_client.rtm_read()
        output_list = slack_rtm_output
        if output_list and len(output_list) > 0:
            for output in output_list:
                if output and 'text' in output and 'channel' in output:
                    return output['text'].lower().strip(), output['channel'], self.get_username_by_id(output['user'])
        return None, None, None

    def wait_for_answer_from_user(self, question, answers, channel, user, wait_time=120, new_thread=False):
        '''
            Function to wait for the answer from user.
            If you don't want your bot stuck waiting for answer,
            whole method that uses this function should be run in a NEW thread
        '''
        counter = 0
        com = None
        answers = [x.lower() for x in answers]
        cancel_msg = "\nOr just type cancel to cancel :facepalm:"

        # Get new client for a thread if new_thread option is enabled
        if new_thread:
            client = SlackClient(self._bot_token)
            logger.log("Creating new thread for {}".format(self._bot_name))
        else:
            client = self._slack_client

        if client.rtm_connect():
            logger.log("Asking @{}: {}".format(user, question))

            msg = "{}\nAvailiable answers are:`{}`\n{}" \
                .format(question,
                        str(answers).translate(None, '\''),
                        cancel_msg)

            self.send_rtm_message(channel=channel,
                                  message=msg,
                                  slack_client=client)

            logger.log("{} is waiting answer from @{}".format(self._bot_name, user))
            while counter < wait_time:
                com, chnl, u = self.__parse_answer__(client)
                if com and chnl and u == user and chnl == channel:
                    com = re.sub(' +', ' ', com)
                    if com.strip() in answers:
                        logger.log("@{} answer: {}".format(user, com))
                        return com
                    else:
                        msg = "Answer should be one of the: `{}`".format(str(answers).translate(None, '\''))
                        client.rtm_send_message(channel=channel, message=msg)

                    if com == 'cancel':
                        return None

                if counter % 30 == 0 and counter >= 60:
                    msg = "Hey @{} I'm still waiting for the answer :neutral_face:".format(user)
                    self.send_rtm_message(channel=channel, message=msg, slack_client=client)

                time.sleep(self._READ_WEBSOCKET_DELAY)
                counter += 1
        else:
            logger.log("Bot connection failed. Invalid Slack token or bot ID?")
        return com

    def wait_for_reaction_from_user(self, message, channel, user, wait_time=120, new_thread=False):
        # TODO
        '''
            Function to wait for the reaction from user.
            If you don't want your bot stuck waiting for answer,
            whole method that uses this function should be run in a NEW thread
        '''
        pass

    def send_rtm_message(self, channel, message, slack_client=None):
        '''

        Note that this method MUST be used while connected to RTM websocket
        man rtm_connect()
        '''
        logger.log('Sending message to {}'.format(channel))
        logger.log(str(message))
        if slack_client is None:
            self._slack_client.rtm_send_message(channel=channel, message=message)
        else:
            slack_client.rtm_send_message(channel=channel, message=message)

    def post_message(self, channel, message):
        '''

        Post message to channel

        :param channel: slack channel id
        :param message: text of the message
        :return: message entity
        '''
        logger.log('Posting message to {}'.format(channel))
        logger.log(str(message))
        res = self._slack_client.api_call("chat.postMessage",
                                          channel=channel,
                                          text=message,
                                          as_user=True)
        return res.get('message')

    def add_reaction(self, message, emoji_name, channel):
        '''
        Add reaction to specific message

        :param message: slack message entity
        :param emoji_name: name of emoji
        :param channel: slack channel id
        :return: None
        '''
        resp = self._slack_client.api_call('reactions.add',
                                           timestamp=message.get('ts'),
                                           name=emoji_name,
                                           channel=channel)
        if not resp.get('ok'):
            raise SlackBotException('Error while adding reaction. {}'.format(resp.get('error')))

    def __del__(self):
        logger.log("{} destroyed".format(self._bot_name))
