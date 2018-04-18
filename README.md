CE API 読み込み ＆ Slack 投稿ツール
====

CoinExchange の API（ https://www.coinexchange.io/api/v1/getmarkets ）を実行し、  
結果の JSON を解析します。  
プログラム起動引数が JSON の result 内のコイン略称（MarketAssetCode）にヒットした場合  
Slack の Incoming-WebHooks を利用して Slack にメッセージを登録します。

## 注意点

* 本プログラムを利用することによって生じる如何なる損害・損失について、作成者はその責を負いません。  
* CE　API　のリスト更新タイミングは不明なので、リストアップ通知と取引可能になるタイミングがずれることが考えられます。

## TODO

* 動作状況を Slack　他チャンネルに通知し、プログラムが動作している（ヘルスチェック）ことを確認可能にする。
* 設定の外だし。
* 前回実行時点の CE　リストを保持しておき、最終実行時との差分を抽出することで、自動的にリストアップされたコインを抽出する。

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
