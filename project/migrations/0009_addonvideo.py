# Generated migration for AddonVideo model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0008_wiki_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='AddonVideo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video_type', models.CharField(choices=[('file', 'ファイルアップロード'), ('youtube', 'YouTube URL'), ('other', 'その他URL')], default='file', max_length=20, verbose_name='動画タイプ')),
                ('video_file', models.FileField(blank=True, null=True, upload_to='addons/videos/', verbose_name='動画ファイル')),
                ('video_url', models.URLField(blank=True, null=True, verbose_name='動画URL（YouTubeなど）')),
                ('caption', models.CharField(blank=True, max_length=255, verbose_name='キャプション')),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='addons/video_thumbnails/', verbose_name='サムネイル')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='順序')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='作成日')),
                ('addon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='videos', to='project.addon')),
            ],
            options={
                'verbose_name': '動画',
                'verbose_name_plural': '動画',
                'ordering': ['order'],
            },
        ),
    ]
