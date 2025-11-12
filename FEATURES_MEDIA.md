# 🎬 Wiki・お知らせ・お問い合わせに動画・画像対応

サイト全体の様々なコンテンツに動画と画像を追加できるようにしました！

## 📝 対応ページ・機能

### 1️⃣ Wiki ページ
**サムネイル画像** ✅  
**YouTube動画** ✅ 新規追加

- 既存：サムネイル画像のみ
- **新規**：YouTube・動画URL対応
- 表示位置：サムネイル画像の下に動画を埋め込み
- 形式：16:9 レスポンシブ

**管理画面での編集:**
```
Wiki 編集画面
├─ 基本情報
│  ├─ タイトル
│  └─ URL用の名前 (slug)
├─ 内容
│  └─ 本文テキスト
├─ メディア（新規セクション）
│  ├─ サムネイル画像
│  └─ 動画URL（YouTubeなど）← 新規
└─ ユーザー情報
```

**使用例：**
```
YouTube URL: https://www.youtube.com/watch?v=xxxxx
または
YouTube 短縮URL: https://youtu.be/xxxxx
```

---

### 2️⃣ お知らせ
**説明文のみ** → **画像 + 動画対応** ✅ 新規追加

**管理画面での編集:**
```
お知らせ 編集画面
├─ 基本情報
│  ├─ タイトル
│  └─ 公開設定
├─ 内容
│  └─ 本文テキスト
├─ メディア（新規セクション）
│  ├─ 画像
│  └─ 動画URL
└─ メタデータ
```

**表示例：**
```
【お知らせ】
━━━━━━━━━━━━━━━━━━━
タイトル：新機能リリース

[画像]

[YouTube動画]

本文内容...
```

---

### 3️⃣ お問い合わせフォーム
**テキストのみ** → **画像添付対応** ✅ 新規追加

**フォームに追加されたフィールド:**
- お名前
- メールアドレス
- 件名（オプション）
- メッセージ
- **画像添付（オプション）** ← 新規

**管理画面での表示:**
```
お問い合わせ 一覧
├─ 日時
├─ お名前
├─ メール
├─ 件名
├─ 本文
│  └─ **[添付画像表示]** ← 新規
└─ 状態
```

---

## 🎯 主な変更点

### モデル変更

#### Wiki モデル
```python
video_url = models.URLField(null=True, blank=True)
get_embed_url()  # YouTube URL変換メソッド
```

#### Announcement モデル
```python
image = models.ImageField(upload_to='announcements/')
video_url = models.URLField(null=True, blank=True)
get_embed_url()  # YouTube URL変換メソッド
```

#### ContactMessage モデル
```python
image = models.ImageField(upload_to='contact_images/', null=True, blank=True)
```

### テンプレート変更

#### wiki_detail.html
- 動画セクション追加（YouTube埋め込み）

#### announcement.html
- 各お知らせに画像と動画セクション追加

#### contact.html
- フォームに画像アップロード追加
- 管理画面で添付画像を表示

### フォーム変更

#### ContactForm
- `image` フィールド追加（オプション）

#### WikiForm
- `video_url` フィールド追加（オプション）

---

## 📋 ストレージ構造

```
media/
├── addons/
│   ├── files/
│   ├── screenshots/
│   ├── thumbnails/
│   ├── videos/
│   └── video_thumbnails/
├── announcements/          ← 新規
│   └── [お知らせ画像]
├── wiki/                   （既存、今後画像ファイルも）
│   └── [Wiki画像]
└── contact_images/         ← 新規
    └── [お問い合わせ添付画像]
```

---

## 🔧 マイグレーション

マイグレーションファイル: `0010_add_media_fields.py`

```bash
python manage.py migrate
```

実行されるSQL:
1. `wiki.video_url` カラムを追加
2. `announcement.image` カラムを追加
3. `announcement.video_url` カラムを追加
4. `contactmessage.image` カラムを追加

---

## 🎨 YouTube URL対応形式

以下のURLはすべて自動的に埋め込み用のURLに変換されます：

| 形式 | 例 |
|-----|-----|
| 正規URL | `https://www.youtube.com/watch?v=dQw4w9WgXcQ` |
| 短縮URL | `https://youtu.be/dQw4w9WgXcQ` |
| クエリ付き | `https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30` |

**内部的な変換:**
```python
def get_embed_url(self):
    # watch?v=xxxxx → embed/xxxxx
    # youtu.be/xxxxx → embed/xxxxx
```

---

## 📱 レスポンシブ対応

すべての動画埋め込みは16:9アスペクト比で自動レイアウト：

```html
<div style="position: relative; padding-bottom: 56.25%;">
    <!-- 16:9 = 100% × 56.25% -->
    <iframe style="position: absolute; width: 100%; height: 100%;"></iframe>
</div>
```

モバイル～デスクトップまで自動対応！

---

## 💾 管理画面での使用方法

### Wiki に動画を追加

1. **Admin** → **Wiki ページ** → アドオン名を選択
2. **メディア** セクションで：
   - **サムネイル画像**：既存（変更可）
   - **動画URL**：YouTubeリンクを貼付 ← 新規
3. 保存

### お知らせに画像・動画を追加

1. **Admin** → **お知らせ** → 「追加」または既存を編集
2. **メディア** セクションで：
   - **画像**：画像ファイルをアップロード ← 新規
   - **動画URL**：YouTubeリンクを貼付 ← 新規
3. 保存

### お問い合わせフォームに画像を追加

1. ユーザーがお問い合わせフォームで新しく追加された「画像添付」欄から画像を選択
2. 送信
3. 管理者が Admin → **お問い合わせメッセージ** で添付画像を確認

---

## 🔒 セキュリティ

- **ファイルアップロード：** MIME型チェック（Pillow対応）
- **画像ファイル容量：** Djangoのデフォルト（通常2.5MB上限）
- **URL入力：** ユーザー入力URLは iframe の allow 属性で権限制限

---

## 🐛 トラブルシューティング

### 動画が表示されない

**YouTube の場合：**
- URLが正しいか確認（`watch?v=` または `youtu.be/`）
- 動画が「公開」設定になっているか確認
- HTTPSサイトで確認（HTTPではセキュリティエラー）

**Wiki/お知らせの場合：**
- ページが「公開」設定になっているか確認
- ブラウザを再読み込み（Ctrl+F5）

### 画像が表示されない

- ファイル形式が JPEG/PNG/GIF か確認
- ファイルサイズが2.5MB以下か確認
- メディアフォルダへのアクセス権限確認（staticfiles）

### フォームで画像がアップロードできない

- `contact.html` が `enctype="multipart/form-data"` か確認
- サーバーの一時ファイルディレクトリ容量確認

---

## 📊 Database スキーマ

### wiki テーブル
| 新規カラム | 型 | 説明 |
|-----------|-----|------|
| `video_url` | URLField | YouTubeなどの動画URL |

### announcement テーブル
| 新規カラム | 型 | 説明 |
|-----------|-----|------|
| `image` | ImageField | お知らせの画像 |
| `video_url` | URLField | YouTubeなどの動画URL |

### contactmessage テーブル
| 新規カラム | 型 | 説明 |
|-----------|-----|------|
| `image` | ImageField | ユーザーが添付した画像 |

---

## 🚀 今後の拡張可能性

- [ ] Markdown レンダリング（本文に動画埋め込み）
- [ ] 画像の自動リサイズ
- [ ] Vimeo 対応
- [ ] Twitter/TikTok 埋め込み
- [ ] 動画のアップロード機能（Wiki/お知らせ）
- [ ] 複数画像アップロード（ギャラリー化）
- [ ] 画像圧縮・最適化

