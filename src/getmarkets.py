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

class MarketResult():
    def __init__(self, result_json = None):
        self.result_json = result_json

    def parse(self, name = ""):
        self.result_flag = False
        self.result_csv = ""

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

                if needle["MarketAssetCode"] == name:
                    print("found. " + needle["MarketAssetName"])
                    self.result_flag = True

            tmp_list.sort()
            for needle in tmp_list:
                if self.result_csv == "":
                    self.result_csv = needle
                else:
                    self.result_csv = self.result_csv + "," + needle

        if (not self.result_flag):
           print("not found.")


def debug_print(target):
    if debug_flag:
        print(target)

def getmarket(name):
    url = "https://www.coinexchange.io/api/v1/getmarkets"

    try :
        with urllib.request.urlopen(url) as res:
            result = res.read().decode("utf-8")
            debug_print(result)
            result_json = json.loads(result)

        result_obj = MarketResult(result_json)
        result_obj.parse(name)
        return result_obj

    except ValueError :
        result_obj = MarketResult()
        print("error")
        return returl_obj

def post_to_slack(post_type, message):
    if (post_type == POST_TYPE_ALERT):
        target_url = webhook_url
    elif (post_type == POST_TYPE_HEALTHCHECK):
        target_url = healthcheck_webhook_url

    if debug_flag:
        return

    slack = slackweb.Slack(url=target_url)
    slack.notify(text=message)

def build_healthcheck_msg(market_result, name):
    now = datetime.datetime.now()
    date_str = now.strftime("%Y/%m/%d %H:%M:%S")

    if market_result.result_api_stat:
        if market_result.result_flag:
            result_msg = name + " が見つかりました！！"
        else:
            result_msg = name + " はまだないみたい（´・ω・｀）"

        msg = "BOT 実行時刻：" + date_str + "\n" + result_msg + "\n\nリスト総数：" + str(market_result.result_length) + "\n現在のリスト：\n```\n" + market_result.result_csv + "\n```"

    else:
        msg = "BOT 実行時刻： " + date_str + "\nCE API 実行結果を解析できませんでした。"

    return msg

def main():
    argv = sys.argv
    argc = len(argv)
    if (argc != 2):
        print("Usage: python " + argv[0] + " TARGETCODE")
        quit()

    target_code = argv[1]
    market_result = getmarket(target_code)

    if market_result.result_flag:
        post_to_slack(POST_TYPE_ALERT, "CE list に " + target_code + " を発見しました")

    healthcheck_msg = build_healthcheck_msg(market_result, target_code)
    debug_print(healthcheck_msg)
    post_to_slack(POST_TYPE_HEALTHCHECK, healthcheck_msg)



if __name__=='__main__':
    main()

