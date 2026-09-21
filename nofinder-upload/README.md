# ノーファインダー

プレビューの映らないフィルムカメラ。覗き穴ほどの窓しか見えず、撮った写真は
「裏ぶた」を開けるまで確認できません。横位置で構えて使います。

- 撮影時にフィルムの現像処理を焼き込みます（トーンカーブ・ハレーション・
  グレイン・周辺光量落ち）。フィルムは カラーネガ / モノクロ / 期限切れ / そのまま
- 写真は端末のブラウザ内（IndexedDB）に保存され、外には送られません
- カメラが使えない環境では自動でテスト信号に切り替わり、操作だけ確かめられます

## 実機で使う

### GitHub Pages（公開 URL）

`main` ブランチの `/docs` を GitHub Pages のソースに設定すると、
`https://<ユーザー名>.github.io/<リポジトリ名>/` で開けます。
スマホの Safari で開き、共有ボタン →「ホーム画面に追加」でアプリになります。

### ローカルで配信する

```
python3 docs/serve.py
```

自己署名証明書を作って HTTPS で配信します。詳しくは [docs/README.md](docs/README.md)。
Mac の中だけで試すなら証明書なしでも動きます（`localhost` はセキュアコンテキスト扱い）:

```
cd docs && python3 -m http.server 8731
```

## 構成

| パス | 役割 |
| --- | --- |
| `nofinder.html` | アプリ本体のソース。直すのはここ |
| `docs/index.html` | 配信用に組み立てたページ（`docs/build.py` が生成） |
| `docs/manifest.webmanifest` | アプリ名・アイコン・横向き固定 |
| `docs/sw.js` | オフライン用キャッシュ |
| `docs/build.py` | `nofinder.html` から `docs/index.html` を生成 |
| `docs/make_icons.py` | アイコン画像を生成 |
| `docs/serve.py` | ローカル HTTPS 配信サーバー |
| `docs/img/` | ボディとシャッターボタンの画像 |

`nofinder.html` を編集したら `python3 docs/build.py` を走らせてください。
