# -*- coding: utf-8 -*-
import sys
import urllib.request
import json
import slackweb
import datetime

debug_flag = False

webhook_url = "https://hooks.slack.com/services/どっかのちゃんねるのWEBHOOK_URL"
healthcheck_webhook_url = "https://hooks.slack.com/services/どっかのちゃんねるのWEBHOOK_URL"

POST_TYPE_ALERT = 0
POST_TYPE_HEALTHCHECK = 1

EXCHANGE_TYPE_CE = 0

class ExchangeApiExecutor():
    def __init__(self, search_target_code):
        self.search_target_code = search_target_code
        self.result_json = None
        self.result_flag = False
        self.result_csv = ""
        self.result_api_stat = False
        self.result_length = 0

    def call_api(self):
        return

    def psrse(self):
        self.result_api_stat = False
        self.result_length = 0
        return
        
    def get_exchange_name(self):
        return "parent class"


class CoinExchangeExecutor(ExchangeApiExecutor):
    def __init__(self, search_target_code):
        super().__init__(search_target_code)

    def call_api(self):
        url = "https://www.coinexchange.io/api/v1/getmarkets"

        try :
            with urllib.request.urlopen(url) as res:
                result = res.read().decode("utf-8")
                debug_print(result)
                self.result_json = json.loads(result)

            self.parse()
            return

        except ValueError :
            print("error")
            return

    def parse(self):
        if self.result_json is None:
            self.result_api_stat = False
            self.result_length = 0

        else:
            self.result_api_stat = True
            self.result_length = len(self.result_json["result"])
            self.result_json["result"]
            tmp_list = []

            for needle in self.result_json["result"]:
                tmp_list.append(needle["MarketAssetCode"])

                if self.search_target_code != "" and needle["MarketAssetCode"] == self.search_target_code:
                    print("found. " + needle["MarketAssetName"])
                    self.result_flag = True

            tmp_list.sort()
            for needle in tmp_list:
                if self.result_csv == "":
                    self.result_csv = needle
                else:
                    self.result_csv = self.result_csv + "," + needle

        if (self.search_target_code != "" and not self.result_flag):
           print("not found.")

    def get_exchange_name(self):
        return "CoinExchange"


def debug_print(target):
    if debug_flag:
        print(target)

def post_to_slack(post_type, message):
    if (post_type == POST_TYPE_ALERT):
        target_url = webhook_url
    elif (post_type == POST_TYPE_HEALTHCHECK):
        target_url = healthcheck_webhook_url

    if debug_flag:
        return

    slack = slackweb.Slack(url=target_url)
    slack.notify(text=message)

def build_healthcheck_msg(exchange_obj, search_target_code):
    now = datetime.datetime.now()
    date_str = now.strftime("%Y/%m/%d %H:%M:%S")

    if exchange_obj.result_api_stat:
        if search_target_code == "":
            result_msg = "コイン名称検索は実施せず、リスト取得のみを行いました。"
        elif exchange_obj.result_flag:
            result_msg = search_target_code + " が見つかりました！！"
        else:
            result_msg = search_target_code + " はまだないみたい（´・ω・｀）"

        msg = "*【" + exchange_obj.get_exchange_name() + "】*\nBOT 実行時刻：" + date_str + "\n" + result_msg + "\n\nリスト総数：" + str(exchange_obj.result_length) + "\n現在の " + exchange_obj.get_exchange_name() + " リスト：\n```\n" + exchange_obj.result_csv + "\n```"

    else:
        msg = "*【" + exchange_obj.get_exchange_name() + "】*\nBOT 実行時刻： " + date_str + "\nAPI 実行結果を解析できませんでした。"

    return msg

def main():
    argv = sys.argv
    argc = len(argv)
    if (argc != 2 and argc != 3):
        print("Usage: python " + argv[0] + " EXCHANGE_NAME [TARGET_CODE]\nEXCHANGE_NAME: CE")
        quit()

    exchange_name = argv[1]

    if (argc == 2):
        target_code = ""
    elif (argc == 3):
        target_code = argv[2]

    exchange_obj = CoinExchangeExecutor(target_code)
    exchange_obj.call_api()

    if exchange_obj.result_flag:
        post_to_slack(POST_TYPE_ALERT, exchange_obj.get_exchange_name() + " list に " + target_code + " を発見しました")

    healthcheck_msg = build_healthcheck_msg(exchange_obj, target_code)
    debug_print(healthcheck_msg)
    post_to_slack(POST_TYPE_HEALTHCHECK, healthcheck_msg)



if __name__=='__main__':
    main()

