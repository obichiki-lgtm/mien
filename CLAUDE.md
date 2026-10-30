# Claude 向けメモ

## Pomo Timer の反映（Artifact → `pomo/`）

「Pomo Timer を反映して」と頼まれても、すぐに push しない。

1. 最新の Artifact を読み込み、`tools/port_pomo.py` で変換する
2. 現在の `pomo/` との差分を確認し、反映される変更を **1 件ずつ** ユーザーに提示する
   （何が変わるか・画面や動作への影響。変更が複数ある場合はそれぞれ）
3. ユーザーが確認・承認した変更だけを反映して commit / push する
