# -*- coding: utf-8 -*-
import sys
import os
import os.path
import urllib.request
import json
import slackweb
import datetime
import copy

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

                self.compare_from_last_to_current(json_config)
                self.compare_from_current_to_last(json_config)

                json_config[self.get_exchange_name()]["last_result"] = self.get_result()
                json_config[self.get_exchange_name()]["last_timestamp"] = self.date_str

            else:
                my_dict = {"last_timestamp": self.date_str, "last_result": self.get_result()}
                json_config[self.get_exchange_name()] = my_dict
                print(self.get_exchange_name() + " data is created.")

        else:
            if (not os.path.exists("../conf/")):
                os.makedirs("../conf/")
            my_dict = {"last_timestamp": self.date_str, "last_result": self.get_result()}
            json_config = {self.get_exchange_name(): my_dict}
            print("conf file is created.")


        with open("../conf/last_result.json", "w") as file_obj:
            json.dump(json_config, file_obj, indent=4, sort_keys=True)

    def compare_from_last_to_current(self, json_config):
        for needle in self.result_code_list:
            if needle not in json_config[self.get_exchange_name()]["last_result"]:
                #前のリストになかった
                self.new_only_list.append(needle)
                print(needle + " is listed.")

    def compare_from_current_to_last(self, json_config):
        for needle in json_config[self.get_exchange_name()]["last_result"]:
            if needle not in self.result_code_list:
                #今回のリストになかった
                self.old_only_list.append(needle)
                print(needle + " is delisted.")

    def get_exchange_name(self):
        return "parent class"

    def get_result(self):
        return self.result_code_list

    def get_listed_msg(self):
        return self.get_exchange_name() + " リストに " + str(self.new_only_list) + " がリストアップされました！"

    def get_delisted_msg(self):
        return self.get_exchange_name() + " リストから " + str(self.old_only_list) + " が削除されました..."


class CoinExchangeExecutor(ExchangeApiExecutor):
    def __init__(self, search_target_code):
        super().__init__(search_target_code)
        self.pair_status_dict = {}      #pair 毎の Active 状態を保持するディクショナリ
        self.activated_list = []        #今回 Active が True になったペア名を保持するリスト
        self.deactivated_list = []      #今回 Active が False になったペア名を保持するリスト
        self.listed_list = []           #今回リストアップされたペア名を保持するリスト
        self.delisted_list = []         #今回リスト削除されたペア名を保持するリスト

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

    def get_code_csv(self):
        ret_csv = ""
        for key, val in sorted(self.pair_status_dict.items()):
            if ret_csv == "":
                ret_csv = key + "(" + str(val) + ")" 
            else:
                ret_csv = ret_csv + "," + key + "(" + str(val) + ")"
        return ret_csv

    def get_pair_name(self, asset_info):
        return asset_info["MarketAssetCode"] + "/" + asset_info["BaseCurrencyCode"]

    def parse(self):
        if self.result_json is None:
            self.result_api_stat = False
            self.result_length = 0

        else:
            self.result_api_stat = True

            for needle in self.result_json["result"]:
                pair_name = self.get_pair_name(needle)

                if (pair_name not in self.result_code_list):
                    self.result_code_list.append(pair_name)
                    self.pair_status_dict[pair_name] = needle["Active"]

                    if self.search_target_code != "" and needle["MarketAssetCode"] == self.search_target_code:
                        print("found. " + needle["MarketAssetName"])
                        self.result_flag = True

            self.result_code_list.sort()
            self.result_length = len(self.result_code_list)

        if (self.search_target_code != "" and not self.result_flag):
           print("not found.")

        #{"MarketID":"748","MarketAssetName":"NANJCOIN","MarketAssetCode":"NANJ","MarketAssetID":"562","MarketAssetType":"ethereum_asset","BaseCurrency":"Bitcoin","BaseCurrencyCode":"BTC","BaseCurrencyID":"1","Active":true},
        #{"MarketID":"782","MarketAssetName":"NANJCOIN","MarketAssetCode":"NANJ","MarketAssetID":"562","MarketAssetType":"ethereum_asset","BaseCurrency":"Dogecoin","BaseCurrencyCode":"DOGE","BaseCurrencyID":"4","Active":false},

    def compare_from_last_to_current(self, json_config):
        for current_key, current_value in sorted(self.pair_status_dict.items()):
            exist_flag = False
            for last_key, last_value in sorted(json_config[self.get_exchange_name()]["last_result"].items()):
                if current_key == last_key:
                    exist_flag = True

                    #前のリストにあったので Active が新たに True になったか比較
                    if not last_value and current_value != last_value:
                        self.new_only_list.append(current_key)
                        self.activated_list.append(current_key)
                        print(current_key + ": status is changed. false -> true")
                    break

            if not exist_flag:
                #前のリストになかった
                self.new_only_list.append(current_key)
                self.listed_list.append(current_key)
                print(current_key + " is listed.")

    def compare_from_current_to_last(self, json_config):
        for last_key, last_value in sorted(json_config[self.get_exchange_name()]["last_result"].items()):
            exist_flag = False
            for current_key, current_value in sorted(self.pair_status_dict.items()):
                if current_key == last_key:
                    exist_flag = True

                    #今回のリストにあったので Active が新たに False になったか比較
                    if last_value and current_value != last_value:
                        self.old_only_list.append(current_key)
                        self.deactivated_list.append(current_key)
                        print(current_key + ": status is changed. true -> false")
                    break

            if not exist_flag:
                #今回のリストになかった
                self.old_only_list.append(last_key)
                self.delisted_list.append(last_key)
                print(last_key + " is delisted.")

    def get_exchange_name(self):
        return "CoinExchange"

    def get_result(self):
        return self.pair_status_dict

    def get_listed_msg(self):
        msg = self.get_exchange_name() + " リスト状態が変わりました\n"
        for needle in self.listed_list:
            msg = msg + "    " + needle + " がリストアップされました！ Active: " + str(self.pair_status_dict[needle]) + "\n"
        for needle in self.activated_list:
            msg = msg + "    " + needle + " の Active 状態が True（有効状態）に変わりました\n"

        return msg

    def get_delisted_msg(self):
        msg = self.get_exchange_name() + " リスト状態が変わりました\n"
        for needle in self.delisted_list:
            msg = msg + "     リストから " + needle + " が削除されました...\n"
        for needle in self.deactivated_list:
            msg = msg + "    " + needle + " の Active 状態が False（無効状態）に変わりました\n"

        return msg


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
                    price_change_percent_list.append({"name":needle["symbol"], "percent":float(needle["priceChangePercent"]), "quoteVolume":needle["quoteVolume"]})
                    

                    if self.search_target_code != "" and needle["symbol"] == self.search_target_code:
                        print("found. " + needle["symbol"])
                        self.result_flag = True

            self.result_code_list.sort()
            self.result_length = len(self.result_code_list)

            sorted_percent_list = sorted(price_change_percent_list, key=lambda x: x["percent"], reverse=True)
            if (len(sorted_percent_list) >= 20):
                # 20銘柄以下はソートした価格変化率を表示しない
                self.additional_info = "\n```\n騰落率 上位下位 10ペア\n\n"

                for i in range(0,10):
                    self.additional_info += sorted_percent_list[i]["name"] + ": " + str(sorted_percent_list[i]["percent"]) + "% (volume: " + sorted_percent_list[i]["quoteVolume"] + ")\n"

                self.additional_info += "\n" 
                for i in range(len(sorted_percent_list) - 10, len(sorted_percent_list)):
                    self.additional_info += sorted_percent_list[i]["name"] + ": " + str(sorted_percent_list[i]["percent"]) + "% (volume: " + sorted_percent_list[i]["quoteVolume"] + ")\n"
                self.additional_info += "```"

        if (self.search_target_code != "" and not self.result_flag):
           print("not found.")

    def get_exchange_name(self):
        return "Binance"


class CryptoBridgeExecutor(ExchangeApiExecutor):
    def __init__(self, search_target_code):
        super().__init__(search_target_code)

    def call_api(self):
        url = "https://api.crypto-bridge.org/api/v1/ticker"

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
                if (needle["id"] not in self.result_code_list):
                    self.result_code_list.append(needle["id"])

                    if self.search_target_code != "" and needle["id"] == self.search_target_code:
                        print("found. " + needle["id"])
                        self.result_flag = True

            self.result_code_list.sort()
            self.result_length = len(self.result_code_list)

        if (self.search_target_code != "" and not self.result_flag):
           print("not found.")

    def get_exchange_name(self):
        return "CryptoBridge"


class HitBTCExecutor(ExchangeApiExecutor):
    def __init__(self, search_target_code):
        super().__init__(search_target_code)

    def call_api(self):
        url = "https://api.hitbtc.com/api/2/public/ticker"

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

                    if self.search_target_code != "" and needle["symbol"] == self.search_target_code:
                        print("found. " + needle["symbol"])
                        self.result_flag = True

            self.result_code_list.sort()
            self.result_length = len(self.result_code_list)

        if (self.search_target_code != "" and not self.result_flag):
           print("not found.")

    def get_exchange_name(self):
        return "HitBTC"


class FCoinExecutor(ExchangeApiExecutor):
    def __init__(self, search_target_code):
        super().__init__(search_target_code)

    def call_api(self):
        url = "https://api.fcoin.com/v2/public/symbols"

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

            for needle in self.result_json["data"]:
                if (needle["name"] not in self.result_code_list):
                    self.result_code_list.append(needle["name"])

                    if self.search_target_code != "" and needle["name"] == self.search_target_code:
                        print("found. " + needle["name"])
                        self.result_flag = True

            self.result_code_list.sort()
            self.result_length = len(self.result_code_list)

        if (self.search_target_code != "" and not self.result_flag):
           print("not found.")

    def get_exchange_name(self):
        return "FCoin"



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

        msg = "*【" + exchange_obj.get_exchange_name() + "】*\nBOT 実行時刻：" + exchange_obj.date_str + "\n" + result_msg + "\n\nリスト総数：" + str(exchange_obj.result_length)

        if (exchange_obj.additional_info is not None):
            msg = msg + "\n" + exchange_obj.additional_info

    else:
        msg = "*【" + exchange_obj.get_exchange_name() + "】*\nBOT 実行時刻： " + exchange_obj.date_str + "\nAPI 実行結果を解析できませんでした。"

    return msg

def main():
    argv = sys.argv
    argc = len(argv)
    if (argc != 2 and argc != 3):
        print("Usage: python " + argv[0] + " EXCHANGE_NAME [TARGET_CODE]\nEXCHANGE_NAME: CE or Binance or CB or HB or FCoin")
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
    elif (exchange_name == "CB"):
        exchange_obj = CryptoBridgeExecutor(target_code)
    elif (exchange_name == "HB"):
        exchange_obj = HitBTCExecutor(target_code)
    elif (exchange_name == "FCoin"):
        exchange_obj = FCoinExecutor(target_code)

    exchange_obj.call_api()
    exchange_obj.compare_with_last_result()

    if exchange_obj.result_flag:
        post_to_slack(POST_TYPE_ALERT, exchange_obj.get_exchange_name() + " list に " + target_code + " を発見しました")

    if len(exchange_obj.new_only_list) != 0 or len(exchange_obj.old_only_list) != 0:
        post_to_slack(POST_TYPE_LISTUP, exchange_obj.get_exchange_name() + " リスト総数：" + str(exchange_obj.result_length) + "\n現在の " + exchange_obj.get_exchange_name() + " リスト：\n----------\n" + exchange_obj.get_code_csv() + "\n----------")

    if len(exchange_obj.new_only_list) != 0:
        post_to_slack(POST_TYPE_LISTUP, exchange_obj.get_listed_msg())

    if len(exchange_obj.old_only_list) != 0:
        post_to_slack(POST_TYPE_LISTUP, exchange_obj.get_delisted_msg())


    healthcheck_msg = build_healthcheck_msg(exchange_obj, target_code)
    debug_print(healthcheck_msg)
    post_to_slack(POST_TYPE_HEALTHCHECK, healthcheck_msg)



if __name__=='__main__':
    main()

