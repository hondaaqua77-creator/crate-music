# App Store Connect 入力シート（CRATE）

## 登録状況（2026-11-05）

| 項目 | 値 |
|---|---|
| Apple Developer Program | 承認済み（個人、チームID 9YK6TS56W7、更新日 2027-11-05） |
| アプリID | com.hondaatsushi.crate（登録済み） |
| App Store Connect のアプリ | 「CRATE 移調できる楽譜アプリ」Apple ID 6830933661、SKU CRATE-IOS-001（作成済み） |
| App内課金 | 広告なし版 com.hondaatsushi.crate.noads（非消耗型、¥1,200、表示名・説明・審査メモ入力済み、Apple ID 6830933954） |
| 契約・口座・税務 | すべて有効（2026-11-06 確認） |
| TestFlight | ビルド18 ベータ版審査通過・テスト中。公開リンク https://testflight.apple.com/join/s5b3c6F8 |
| 課金の審査用スクリーンショット | 登録済み（app/store/iap/noads_review.png、Actions → Store screenshots → target=iap で再登録可） |
| 本審査 | 2026-11-06 10:50 提出（iOS 1.0 ビルド18 ＋ 広告なし版）。コンテンツ配信権「いいえ」、課金の配信可否は全175地域 |

Apple Developer Program の承認後、この順に入力する。値はそのまま貼り付けられる。

## 1. アプリの作成（マイApp →「＋」→ 新規App）

| 項目 | 入力値 |
|---|---|
| プラットフォーム | iOS |
| 名前 | CRATE 移調できる楽譜アプリ（2026-11-05 決定・App Store Connect に設定済み） |
| プライマリ言語 | 日本語 |
| バンドルID | com.hondaatsushi.crate（先に「Certificates, IDs & Profiles」→ Identifiers で登録） |
| SKU | CRATE-IOS-001 |
| ユーザアクセス | フルアクセス |

## 2. 価格と配信状況

| 項目 | 入力値 |
|---|---|
| 価格 | 無料 |
| 配信国 | 日本（英語版の公開までは日本のみ） |

## 3. App内課金（収益化 → App内課金 →「＋」）

| 項目 | 入力値 |
|---|---|
| 種類 | 非消耗型 |
| 参照名 | 広告なし版 |
| 製品ID | com.hondaatsushi.crate.noads（アプリ側のコードと一致させる。変更不可） |
| 価格 | 1,200円 |
| 表示名 | 広告なし版 |
| 説明 | 広告を表示しないようにします。機能は無料版と同じです。 |
| 審査用スクリーンショット | 設定画面の「広告なし版」欄（アプリ版で撮影） |
| 審査メモ | 設定 →「広告なし版」→「広告なし版を購入」で購入できます。「購入を復元」で復元できます。 |

※ App内課金を販売するには「契約／税金／口座情報」で有料App契約・口座・税務情報の登録が必要（本田さんが入力）。

## 4. Appのプライバシー（データの収集）

広告（Google AdMob）を使うため「データを収集する」を選び、次を申告する。利用者に合わせた広告（トラッキング）は使っていない（npa=true）。

| データの種類 | 用途 | ユーザーに紐付け | トラッキング |
|---|---|---|---|
| ID → デバイスID | サードパーティ広告 | いいえ | いいえ |
| 使用状況データ → 広告データ | サードパーティ広告、分析 | いいえ | いいえ |
| 診断 → クラッシュデータ・パフォーマンスデータ | App機能 | いいえ | いいえ |
| 位置情報 → おおよその場所 | サードパーティ広告 | いいえ | いいえ |

購入（App内課金）の情報はAppleが扱うため、申告不要。楽譜・音楽ファイルは端末外に送らないため申告不要。

プライバシーポリシーURL：https://hondaaqua77-creator.github.io/crate-music/support/privacy.html

## 5. その他の申告

| 項目 | 回答 |
|---|---|
| 年齢制限 | すべて「なし」→ 4+（広告は一般向け） |
| 暗号化（輸出規制） | 標準の暗号化のみ（Info.plist に ITSAppUsesNonExemptEncryption=false 設定済み） |
| コンテンツの権利 | 他者のコンテンツを含まない（サンプル楽譜は著作権切れの曲を自前で浄書） |
| 広告の有無 | はい（含む） |
| サポートURL | https://hondaaqua77-creator.github.io/crate-music/support/ |
| マーケティングURL | https://hondaaqua77-creator.github.io/crate-music/ |
| カテゴリ | ミュージック（サブ：教育） |
| 著作権 | © 2026 Atsushi Honda |

## 6. 審査メモ（App Review Information）

```
CRATE は印刷された楽譜（PDF・写真）を読み込み、♭／♯ボタンで別のキーに移調するアプリです。
ログインは不要です。審査用に「サンプル楽譜」（著作権切れのシューマン作品を自前で浄書）を用意しています。

確認手順：
1. 「サンプル楽譜で試す」を押す
2. 移調の ♯ ボタンを押すと、音符と調号が新しいキーで描き直されます
3. 「PDF保存」→「送る」で、移調した楽譜をPDFで共有できます
4. 設定 →「広告なし版」でApp内課金（非消耗型）を購入・復元できます

広告（Google AdMob）は楽譜の演奏中には表示せず、PDFの保存・送信の後にのみ表示します。
```

## 7. GitHub Secrets（Settings → Secrets and variables → Actions）

| 名前 | 中身 | 用意する人 |
|---|---|---|
| ASC_KEY_ID | App Store Connect APIキーのキーID | 本田さん（ユーザとアクセス → 統合 → App Store Connect API、権限「App Manager」） |
| ASC_ISSUER_ID | 同じ画面の発行者ID | 本田さん |
| ASC_KEY_P8 | ダウンロードした .p8 ファイルの中身（全文） | 本田さん。チャットには貼らない |
| APPLE_TEAM_ID | 9YK6TS56W7（公開値のため ios.yml に設定済み。登録不要） | — |

AdMob（登録済み・2026-11-04）：アプリID `ca-app-pub-6323228654710695~1395552037`、インタースティシャル「PDF書き出し後」`ca-app-pub-6323228654710695/8096516749`。
公開値なので Secrets ではなく ios.yml の testflight ジョブに直接設定済み。TestFlight／配信版は本番広告、シミュレータ用ビルドはテスト広告。

## 8. TestFlight へのアップロード

GitHub → Actions → iOS → Run workflow（「TestFlight にアップロードする」にチェック）。
