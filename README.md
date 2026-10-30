# mien

| アプリ | 公開URL（GitHub Pages） | ソース |
| --- | --- | --- |
| 学習スケジューラー | https://obichiki-lgtm.github.io/mien/ | `index.html` |
| Pomo Timer | https://obichiki-lgtm.github.io/mien/pomo/ | `pomo/` |

## Pomo Timer

claude.ai の Artifact「Pomo Timer」を一般公開用に移植したもの。

- ログインなしでも使える（データはその端末のブラウザに保存）
- 設定 > データ の「Google でログイン」で、Firebase Authentication + Firestore による端末間同期
  - データの保存先: `pomo/{uid}/docs/{state | m-YYYY-MM}`
- claude.ai 上で開いた場合は、従来どおり claude.ai の同期を使う

### 更新の流れ

1. Claude Code の会話で Artifact を更新する
2. Claude が最新の Artifact を読み込み、Firebase 対応の差分を当てて変換する
3. Claude が反映される変更を 1 件ずつ提示し、確認・承認を得てから `pomo/` に反映して GitHub に push する

### Firebase 側の設定（初回のみ）

1. Authentication > Sign-in method で **Google** を有効化
2. Authentication > Settings > 承認済みドメイン に `obichiki-lgtm.github.io` を追加
3. Firestore > ルール に `firestore.rules` の内容を反映

### ご意見・要望の受け付け（初回のみ設定）

1. Firebase コンソール → プロジェクトの設定 → サービス アカウント →「新しい秘密鍵を生成」で JSON をダウンロード
2. GitHub のこのリポジトリ → Settings → Secrets and variables → Actions →「New repository secret」
   - Name: `FIREBASE_SA` / Secret: ダウンロードした JSON の中身をそのまま貼り付け
3. Firestore > ルール に `firestore.rules` の内容を反映（`feedback` の部分が追加されています）
4. GitHub の Actions タブ →「feedback-to-issues」→「Run workflow」で動作確認（以後は毎時自動）
