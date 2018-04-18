# -*- coding: utf-8 -*-
import sys
import urllib.request
import json
import slackweb

debug_flag = False
webhook_url = "https://hooks.slack.com/services/どっかのちゃんねるのWEBHOOK_URL"

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

        for needle in result_json["result"]:
            if needle["MarketAssetCode"] == name:
                print("found. " + needle["MarketAssetName"])
                return True

        print("not found.")
        return False

    except ValueError :
        print("error")
        return False

def post_to_slack(name):
    slack = slackweb.Slack(url=webhook_url)
    slack.notify(text="CE list に " + name + " を発見しました")

def main():
    argv = sys.argv
    argc = len(argv)
    if (argc != 2):
        print("Usage: python " + argv[0] + " TARGETCODE")
        quit()

    target_code = argv[1]
    market_result = getmarket(target_code)
    if market_result:
        post_to_slack(target_code)


if __name__=='__main__':
    main()

