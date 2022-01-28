import json
import logging
import time
from datetime import datetime, timedelta


class Token(object):
    TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
    TOKEN_FILE_NAME = "../config/token.json"

    def __init__(self, data):
        """
        Created Token type object
        :param data: data is a dictionary containing information in this format
        `{
            "last_use_time": "2020-07-17T04:56:27.756885",
            "next_use_time": "2020-07-17T04:57:27.756889",
            "token": "sbdbdsbdfbdfbdf"
        }`
        last_use_time is the time last this token is used in `%Y-%m-%dT%H:%M:%S.%f` this format
        next_use_time is the time when this token will be usable again in `%Y-%m-%dT%H:%M:%S.%f` this format
        token is the Github access token
        """
        self.__dict__ = data
        self.last_use_time = datetime.strptime(self.last_use_time, self.TIME_FORMAT)
        self.next_use_time = datetime.strptime(self.next_use_time, self.TIME_FORMAT)

    def get_waiting_period(self):
        """

        :return: waiting period  to reuse this token in second
        """
        waiting_period = (self.next_use_time - datetime.utcnow()).seconds
        return waiting_period if self.next_use_time > datetime.utcnow() else 0

    @staticmethod
    def get_token_list():
        """

        :return: returns a list of Token type object by loading tokens from config/token.json
        """
        data = json.load(open(Token.TOKEN_FILE_NAME, 'r'))
        token_list = []
        for item in data:
            token_list.append(Token(item))
        return token_list

    @staticmethod
    def serialize(obj):
        """
        Serialize the object by converting datetime object into iso formatted string.
        :param obj: Token type object
        :return: serialized object
        """
        if isinstance(obj, datetime):
            serialized_datetime = obj.strftime(Token.TIME_FORMAT)
            return serialized_datetime
        return obj.__dict__

    @staticmethod
    def dump_all_token(token_list):
        """
        Dumps all tokens to config/token.json file
        :param token_list: A list of Token type object
        :return: returns nothing
        """
        logging.info("Dumping all token")
        json.dump(token_list, open(Token.TOKEN_FILE_NAME, "w"), default=Token.serialize)

    @staticmethod
    def update_token(github_object, token_list):
        """
        Updates the token inside Github connector based on per `minute` or per `hour` limit
        :param current_token:
        :param github_object: Github connector
        :param token_list: A list of Token type object
        :param criteria: criteria either contains `hour` or `minute`
        :return: updated Github connector
        """
        logging.info("Checking token limit")
        current_token = github_object._Github__requester._Requester__authorizationHeader.split(" ")[1]
        logging.info("Current token {}".format(current_token))
        logging.info("Current token rate limit")
        current_token_rate_limit = github_object.get_rate_limit()
        logging.info("Minute : " + str(current_token_rate_limit.search))
        logging.info("Hour : " + str(current_token_rate_limit.core))

        if current_token_rate_limit.search.remaining > 3 and \
                current_token_rate_limit.core.remaining > 1000:
            logging.info("Not switching now")
            return

        for token_item in token_list:
            if token_item.token == current_token:
                token_item.last_use_time = datetime.utcnow()
                break

        if current_token_rate_limit.search.remaining < 3 and \
                current_token_rate_limit.core.remaining < 1000:
            token_item.next_use_time = max(current_token_rate_limit.core.reset, current_token_rate_limit.search.reset) + timedelta(seconds=10)
        elif current_token_rate_limit.search.remaining < 3:
            token_item.next_use_time = current_token_rate_limit.search.reset + timedelta(seconds=3)
        elif current_token_rate_limit.core.remaining < 1000:
            token_item.next_use_time = current_token_rate_limit.core.reset + timedelta(seconds=3)

        token_list.sort(key=lambda x: x.get_waiting_period(), reverse=False)
        if token_list[0].get_waiting_period() > 0:
            logging.info("Going into sleep for {}".format(token_list[0].get_waiting_period()))
            time.sleep(token_list[0].get_waiting_period() + 3)
        logging.info("Switching token")
        github_object._Github__requester._Requester__authorizationHeader = "token " + token_list[0].token
