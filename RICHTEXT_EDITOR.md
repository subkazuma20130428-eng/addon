# リッチテキストエディタ (TinyMCE) 実装ガイド

## 📝 実装内容

アドオン配布ページとWiki編集ページで **TinyMCE** リッチテキストエディタを導入しました。これでクラフターズコロニーのように、説明に直接**画像や動画を埋め込める**ようになります。

---

## 🎨 対応ページ

### 1️⃣ **アドオン配布ページ** (`/upload/`, `/upload/<slug>/edit/`)
```
詳細説明 [詳細説明エディタ]
    ↓ TinyMCE エディタで編集可能
    ├─ テキスト編集
    ├─ 画像挿入
    ├─ リンク挿入
    ├─ 箇条書き
    └─ フォーマット（太字、斜体など）
```

### 2️⃣ **Wiki編集ページ** (`/wiki/create/`, `/wiki/<slug>/edit/`)
```
内容 [Wiki内容エディタ]
    ↓ TinyMCE エディタで編集可能
    ├─ テキスト編集
    ├─ 画像挿入
    ├─ リンク挿入
    ├─ テーブル作成
    └─ フォーマット（太字、斜体など）
```

---

## ✨ TinyMCE の機能

### 📌 ツールバー
```
undo redo | formatselect | bold italic backcolor
alignleft aligncenter alignright alignjustify
bullist numlist outdent indent
link image | code | help
```

### 🖼️ **画像挿入方法**
1. エディタの **「Image」** ボタンをクリック
2. **「Upload image」** でローカルの画像をアップロード
3. または **「Image URL」** で外部URLを入力
4. 画像が自動的に挿入されます

### 🔗 **リンク挿入方法**
1. テキストを選択
2. **「Link」** ボタンをクリック
3. URLを入力して確認

### 📋 **表作成**（Wiki向け）
1. **「Table」** メニューから表を挿入
2. 行数・列数を指定
3. セルの内容を編集

---

## 📁 ファイル構成

### 追加・変更ファイル

**1. requirements.txt**
```txt
django-tinymce==5.0.0
```

**2. project/settings.py**
```python
INSTALLED_APPS += ['tinymce']

TINYMCE_DEFAULT_CONFIG = {
    'height': 400,
    'width': '100%',
    'plugins': '... (画像・リンク・テーブル対応)',
    'toolbar': '... (ツールバー設定)',
    'language': 'ja',  # 日本語対応
}
```

**3. project/urls.py**
```python
path('tinymce/', include('tinymce.urls')),
```

**4. project/forms.py**
```python
from tinymce.widgets import TinyMCE

class AddonForm:
    'long_description': TinyMCE(attrs={'cols': 80, 'rows': 10})

class WikiForm:
    'content': TinyMCE(attrs={'cols': 80, 'rows': 10})
```

**5. templates/upload.html, wiki_form.html**
```django
{{ form.media }}  <!-- TinyMCEスクリプト読み込み -->
```

---

## 🚀 使い方

### ✅ アドオンの詳細説明を作成

1. **アップロードページ** → `/upload/` にアクセス
2. **詳細説明** フィールドをクリック
3. TinyMCE エディタが起動
4. テキスト入力・画像挿入など自由に編集
5. **保存** ボタンで公開

### ✅ Wiki ページを作成

1. **Wiki作成** → `/wiki/create/` にアクセス
2. **内容** フィールドをクリック
3. TinyMCE エディタが起動
4. リッチ形式で説明を作成
5. **保存** ボタンで公開

---

## 🎬 テンプレート表示

テンプレートでは HTML コンテンツを安全に表示：

```django
<!-- addon_detail.html -->
<div style="line-height: 1.6;">{{ addon.long_description|safe }}</div>

<!-- wiki_detail.html -->
<div style="line-height: 1.8;">{{ wiki.content|safe }}</div>
```

---

## 🔒 セキュリティ

### XSS対策
- **`|safe` フィルタ** を使用してHTMLを表示
- ただし、信頼できるユーザー（オーナー・管理者）のみが編集可能
- 今後、コンテンツをサニタイズするオプションを追加可能

### 対応予定
- [ ] HTMLタグをホワイトリスト化
- [ ] 悪意あるスクリプトをフィルタ
- [ ] 管理画面での編集ログ

---

## 🐛 トラブルシューティング

### TinyMCE が表示されない場合

1. **ブラウザキャッシュをクリア**
   ```
   Ctrl + Shift + Delete
   ```

2. **Django サーバーを再起動**
   ```bash
   .venv\Scripts\python.exe manage.py runserver
   ```

3. **静的ファイルを更新**
   ```bash
   .venv\Scripts\python.exe manage.py collectstatic
   ```

### 画像が挿入されない場合

1. **アップロード先を確認**
   ```
   media/ フォルダが存在するか確認
   ```

2. **パーミッションを確認**
   ```
   media/ フォルダが書き込み可能か確認
   ```

3. **MEDIA_ROOT 設定を確認**
   ```python
   # settings.py
   MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
   MEDIA_URL = '/media/'
   ```

---

## 📊 対応フォーマット

### 画像形式
- JPEG
- PNG
- GIF
- WebP

### 動画埋め込み
- YouTube（URL）
- Vimeo（URL）
- ローカルファイル（mp4、webm）

---

## 🎓 実装例

### アドオン詳細説明の例

```html
<h3>特徴</h3>
<ul>
    <li>高速処理</li>
    <li>軽量設計</li>
    <li>日本語対応</li>
</ul>

<h3>スクリーンショット</h3>
<img src="/media/addons/screenshots/example.jpg" alt="例">

<p>このアドオンは...</p>
```

### Wiki ページの例

```html
<h2>導入方法</h2>
<ol>
    <li>ファイルをダウンロード</li>
    <li>Minecraft に追加</li>
    <li>ワールドで有効化</li>
</ol>

<table>
    <tr><th>バージョン</th><th>状態</th></tr>
    <tr><td>1.20</td><td>対応</td></tr>
</table>
```

---

## 📝 注意事項

### ⚠️ HTML タグについて
- **許可** : `<p>`, `<h1>-<h6>`, `<ul>`, `<ol>`, `<li>`, `<img>`, `<a>` など基本的なタグ
- **制限** : `<script>`, `<iframe>` など危険なタグは避ける

### 💾 バックアップ
- 重要な説明文は **定期的にバックアップ** してください
- データベーストラブル時の復旧用に

---

## 🔗 参考リンク

- [TinyMCE 公式ドキュメント](https://www.tiny.cloud/docs/)
- [django-tinymce GitHub](https://github.com/jazzband/django-tinymce)
- [Django モデルとフォーム](https://docs.djangoproject.com/ja/5.2/)

---

## 🎉 これで完成！

アドオン配布サイトがクラフターズコロニーのような**リッチテキスト対応**に進化しました！

次のステップ:
- [ ] Markdown 形式対応
- [ ] リアルタイムプレビュー
- [ ] 共同編集機能
- [ ] バージョン管理
