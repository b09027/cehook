CE API 読み込み ＆ Slack 投稿ツール
====

CoinExchange の API（ https://www.coinexchange.io/api/v1/getmarkets ）を実行し、  
結果の JSON を解析します。  
プログラム起動引数が JSON の result 内のコイン略称（MarketAssetCode）にヒットした場合  
Slack の Incoming-WebHooks を利用して Slack にメッセージを登録します。

## Requirement
* python3  
* slackweb

## Usage
python getmarkets.py [COINNAME]

## Licence

MIT

## Author

[b09027](https://github.com/b09027)
（TOCOTOCOりんご）
