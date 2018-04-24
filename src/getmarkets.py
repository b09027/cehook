# -*- coding: utf-8 -*-
import sys
import os
import os.path
import urllib.request
import json
import slackweb
import datetime

debug_flag = False

webhook_url = "https://hooks.slack.com/services/どっかのちゃんねるのWEBHOOK_URL"
healthcheck_webhook_url = "https://hooks.slack.com/services/どっかのちゃんねるのWEBHOOK_URL"
exchange_listup_hook_url = "https://hooks.slack.com/services/どっかのちゃんねるのWEBHOOK_URL"

POST_TYPE_ALERT = 0
POST_TYPE_HEALTHCHECK = 1
POST_TYPE_LISTUP = 2

EXCHANGE_TYPE_CE = 0

class ExchangeApiExecutor():
    def __init__(self, search_target_code):
        self.search_target_code = search_target_code #調査対象コード
        self.result_json = None                      #API 実施結果の JSON
        self.result_api_stat = False                 #API の HTTP 疎通状態
        self.result_flag = False                     #コード検索結果
        self.result_code_list = []                   #API 実施結果で取得できたコードリスト
        self.result_length = 0                       #API 実施結果リストのサイズ
        self.new_only_list = []                      #前結果比較時に、新結果のみにあるコード
        self.old_only_list = []                      #前結果比較時に、前結果のみにあるコード
        self.additional_info = None                  #追加で出力したい内容があるなら文字列を設定する

        now = datetime.datetime.now()
        self.date_str = now.strftime("%Y/%m/%d %H:%M:%S")

    def call_api(self):
        return

    def psrse(self):
        self.result_api_stat = False
        self.result_length = 0
        return

    def get_code_csv(self):
        ret_csv = ""
        for needle in self.result_code_list:
            if ret_csv == "":
                ret_csv = needle
            else:
                ret_csv = ret_csv + "," + needle
        return ret_csv

    def compare_with_last_result(self):
        if (not self.result_api_stat or self.result_length == 0):
            print("skip compare_with_last_result()")
            return

        if (os.path.exists("../conf/last_result.json")):
            with open("../conf/last_result.json", "r") as file_obj:
                json_config = json.load(file_obj)

            debug_print("{0}".format(json.dumps(json_config, indent=4)))

            if (self.get_exchange_name() in json_config):
                for needle in self.result_code_list:
                    if needle not in json_config[self.get_exchange_name()]["last_result"]:
                        #前のリストになかった
                        self.new_only_list.append(needle)
                        print(needle + " is listed.")

                for needle in json_config[self.get_exchange_name()]["last_result"]:
                    if needle not in self.result_code_list:
                        #今回のリストになかった
                        self.old_only_list.append(needle)
                        print(needle + " is delisted.")

                json_config[self.get_exchange_name()]["last_result"] = self.result_code_list

            else:
                my_dict = {"last_timestamp": self.date_str, "last_result": self.result_code_list}
                json_config[self.get_exchange_name()] = my_dict
                print(self.get_exchange_name() + " data is created.")

        else:
            if (not os.path.exists("../conf/")):
                os.makedirs("../conf/")
            my_dict = {"last_timestamp": self.date_str, "last_result": self.result_code_list}
            json_config = {self.get_exchange_name(): my_dict}
            print("conf file is created.")


        with open("../conf/last_result.json", "w") as file_obj:
            json.dump(json_config, file_obj, indent=4)


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

            for needle in self.result_json["result"]:
                if (needle["MarketAssetCode"] not in self.result_code_list):
                    self.result_code_list.append(needle["MarketAssetCode"])

                    if self.search_target_code != "" and needle["MarketAssetCode"] == self.search_target_code:
                        print("found. " + needle["MarketAssetName"])
                        self.result_flag = True

            self.result_code_list.sort()
            self.result_length = len(self.result_code_list)

        if (self.search_target_code != "" and not self.result_flag):
           print("not found.")

    def get_exchange_name(self):
        return "CoinExchange"


class BinanceExecutor(ExchangeApiExecutor):
    def __init__(self, search_target_code):
        super().__init__(search_target_code)

    def call_api(self):
        url = "https://www.binance.com/api/v1/ticker/24hr"

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
        price_change_percent_list = []

        if self.result_json is None:
            self.result_api_stat = False
            self.result_length = 0

        else:
            self.result_api_stat = True

            for needle in self.result_json:
                if (needle["symbol"] not in self.result_code_list):
                    self.result_code_list.append(needle["symbol"])
                    price_change_percent_list.append({"name":needle["symbol"], "percent":float(needle["priceChangePercent"]), "volume":needle["volume"]})
                    

                    if self.search_target_code != "" and needle["symbol"] == self.search_target_code:
                        print("found. " + needle["symbol"])
                        self.result_flag = True

            self.result_code_list.sort()
            self.result_length = len(self.result_code_list)

            sorted_percent_list = sorted(price_change_percent_list, key=lambda x: x["percent"], reverse=True)
            if (len(sorted_percent_list) >= 20):
                # 20銘柄以下はソートした価格変化率を表示しない
                self.additional_info = "\n```\n騰落率 上位下位 10ペア\n\n"

                for i in range(0,9):
                    self.additional_info += sorted_percent_list[i]["name"] + ": " + str(sorted_percent_list[i]["percent"]) + "% (volume: " + sorted_percent_list[i]["volume"] + ")\n"

                self.additional_info += "\n" 
                for i in range(len(sorted_percent_list) - 10, len(sorted_percent_list) - 1):
                    self.additional_info += sorted_percent_list[i]["name"] + ": " + str(sorted_percent_list[i]["percent"]) + "% (volume: " + sorted_percent_list[i]["volume"] + ")\n"
                self.additional_info += "```"

        if (self.search_target_code != "" and not self.result_flag):
           print("not found.")

    def get_exchange_name(self):
        return "Binance"


def debug_print(target):
    if debug_flag:
        print(target)

def post_to_slack(post_type, message):
    if (post_type == POST_TYPE_ALERT):
        target_url = webhook_url
    elif (post_type == POST_TYPE_HEALTHCHECK):
        target_url = healthcheck_webhook_url
    elif (post_type == POST_TYPE_LISTUP):
        target_url = exchange_listup_hook_url

    if debug_flag:
        return

    slack = slackweb.Slack(url=target_url)
    slack.notify(text=message)

def build_healthcheck_msg(exchange_obj, search_target_code):
    if exchange_obj.result_api_stat:
        if search_target_code == "":
            result_msg = "コイン名称検索は実施せず、リスト取得のみを行いました。"
        elif exchange_obj.result_flag:
            result_msg = search_target_code + " が見つかりました！！"
        else:
            result_msg = search_target_code + " はまだないみたい（´・ω・｀）"

        msg = "*【" + exchange_obj.get_exchange_name() + "】*\nBOT 実行時刻：" + exchange_obj.date_str + "\n" + result_msg + "\n\nリスト総数：" + str(exchange_obj.result_length) + "\n現在の " + exchange_obj.get_exchange_name() + " リスト：\n```\n" + exchange_obj.get_code_csv() + "\n```"

        if (exchange_obj.additional_info is not None):
            msg = msg + "\n" + exchange_obj.additional_info

    else:
        msg = "*【" + exchange_obj.get_exchange_name() + "】*\nBOT 実行時刻： " + exchange_obj.date_str + "\nAPI 実行結果を解析できませんでした。"

    return msg

def main():
    argv = sys.argv
    argc = len(argv)
    if (argc != 2 and argc != 3):
        print("Usage: python " + argv[0] + " EXCHANGE_NAME [TARGET_CODE]\nEXCHANGE_NAME: CE or Binance")
        quit()

    exchange_name = argv[1]

    if (argc == 2):
        target_code = ""
    elif (argc == 3):
        target_code = argv[2]

    if (exchange_name == "CE"):
        exchange_obj = CoinExchangeExecutor(target_code)
    elif (exchange_name == "Binance"):
        exchange_obj = BinanceExecutor(target_code)

    exchange_obj.call_api()
    exchange_obj.compare_with_last_result()

    if exchange_obj.result_flag:
        post_to_slack(POST_TYPE_ALERT, exchange_obj.get_exchange_name() + " list に " + target_code + " を発見しました")

    if len(exchange_obj.new_only_list) != 0:
        post_to_slack(POST_TYPE_LISTUP, exchange_obj.get_exchange_name() + " list に " + str(exchange_obj.new_only_list) + " がリストアップされました！")

    if len(exchange_obj.old_only_list) != 0:
        post_to_slack(POST_TYPE_LISTUP, exchange_obj.get_exchange_name() + " list から " + str(exchange_obj.old_only_list) + " が削除されました...")


    healthcheck_msg = build_healthcheck_msg(exchange_obj, target_code)
    debug_print(healthcheck_msg)
    post_to_slack(POST_TYPE_HEALTHCHECK, healthcheck_msg)



if __name__=='__main__':
    main()

