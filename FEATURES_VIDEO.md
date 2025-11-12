# 動画機能の実装ガイド

## 🎥 実装内容

アドオンの公開ページに動画を追加できるようになりました。

### 追加されたファイル・変更

#### 1. **models.py** - 新しいモデル追加
```python
class AddonVideo(models.Model):
    """動画（アップロード＆URL両対応）"""
```

**機能：**
- ファイルアップロード（MP4など）
- YouTube URLの埋め込み
- その他URLの埋め込み
- カスタムサムネイル
- キャプション付き

#### 2. **admin.py** - 管理画面に追加
- `AddonVideoInline` - Addonページ内でinline編集可能
- `AddonVideoAdmin` - 動画の一覧管理

#### 3. **addon_detail.html** - テンプレートに追加
- 動画セクションをスクリーンショットの下に表示
- ファイルとURL形式に対応した表示

#### 4. **マイグレーション** - 0009_addonvideo.py
```bash
python manage.py migrate
```

## 📝 使い方

### 管理画面での追加方法

1. Django管理画面 → **アドオン** を選択
2. アドオンを編集
3. 下部の **動画** セクションで以下を選択：
   - **動画タイプ**：
     - `ファイルアップロード` - MP4などを直接アップロード
     - `YouTube URL` - YouTubeリンクを貼付
     - `その他URL` - 別のストリーミングサイト
   
4. **ファイルアップロード** の場合：
   - `動画ファイル` にMP4をアップロード
   - `サムネイル`（オプション）でカスタム画像を設定
   
5. **YouTube/URL** の場合：
   - `動画URL` に以下いずれかを貼付：
     - `https://www.youtube.com/watch?v=xxxxx`
     - `https://youtu.be/xxxxx`

6. `キャプション`（オプション）を入力
7. `順序` で並び順を指定（デフォルト：0）

## 🎬 フロントエンド表示

### アドオン詳細ページ

```
スクリーンショット ▼
[画像] [画像] [画像]

動画 ▼
[動画プレイヤー] [動画プレイヤー]
```

- **ファイル形式**：HTML5 `<video>` タグで再生
  - コントロール表示（再生/一時停止など）
  - カスタムサムネイル対応
  - 複数ブラウザ対応
  
- **YouTube/URL形式**：`<iframe>` 埋め込み
  - 自動的にembed URLに変換
  - 全画面対応
  - YouTube controls対応

## 💾 ストレージ構造

```
media/
├── addons/
│   ├── files/           # ダウンロードファイル
│   ├── screenshots/     # スクリーンショット画像
│   ├── thumbnails/      # アドオンサムネイル
│   ├── videos/          # アップロード動画ファイル
│   └── video_thumbnails/ # 動画カスタムサムネイル
```

## 🔧 テンプレートの機能

### responsive対応
```html
<div style="position: relative; width: 100%; padding-bottom: 56.25%;">
    <!-- 16:9 アスペクト比を自動計算 -->
</div>
```

### YouTube URL変換機能
```python
def get_embed_url(self):
    """YouTubeのURLを埋め込み対応のURLに変換"""
```

以下の形式に対応：
- `youtube.com/watch?v=xxxxx` → `youtube.com/embed/xxxxx`
- `youtu.be/xxxxx` → `youtube.com/embed/xxxxx`

## 📱 サポートされるビデオ形式

### ファイルアップロード
- **MP4** （推奨）
- WebM
- Ogg

### ストリーミング
- **YouTube**（推奨）
- Vimeo
- その他embedサポートサイト

## 🚀 今後の拡張案

- [ ] 複数フォーマット対応（WebM、Ogg）
- [ ] 動画プレイリスト
- [ ] 動画解析（再生時間の自動取得）
- [ ] 動画トランスコード（MP4への自動変換）
- [ ] TwitchやTikTokの埋め込み
- [ ] 字幕機能

## 🔒 セキュリティ

- ファイルアップロードは `upload_to='addons/videos/'` に制限
- URLはユーザーが手動入力（XSS対策）
- iframeには `allow` 属性で権限制限

## 🐛 トラブルシューティング

### 動画が表示されない場合

1. **ファイルアップロード**
   - MP4フォーマットか確認
   - ファイルサイズ確認
   - サーバーディスク容量確認

2. **YouTube**
   - URLが正しいか確認
   - 動画が公開設定か確認
   - `youtu.be` の短縮URLか `youtube.com` の正規URLか確認

3. **ブラウザ互換性**
   - Chrome/Firefox/Safari最新版で確認
   - HTTPS環境で確認（HTTPでYouTubeが動作しない場合がある）

## 📝 Database情報

### addonvideo テーブル
| カラム | 型 | 説明 |
|-------|-----|------|
| id | BigAutoField | プライマリキー |
| addon_id | ForeignKey | 紐付けアドオン |
| video_type | CharField | file/youtube/other |
| video_file | FileField | アップロード動画ファイル |
| video_url | URLField | ストリーミングURL |
| caption | CharField | 説明文 |
| thumbnail | ImageField | カスタムサムネイル |
| order | PositiveIntegerField | 表示順序 |
| created_at | DateTimeField | 作成日時 |

## 使用例

### 管理画面でのInline登録
```
アドオン編集画面
├─ 基本情報
├─ 説明
├─ バージョン情報
├─ メディア
├─ スクリーンショット（Inline）
├─ 動画（Inline） ← 新しく追加
└─ 統計
```

### テンプレート変数
```django
{% for video in addon.videos.all %}
    {{ video.caption }}
    {{ video.get_embed_url }}
    {{ video.video_file.url }}
{% endfor %}
```
