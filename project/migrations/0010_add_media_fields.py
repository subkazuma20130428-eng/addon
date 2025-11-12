# Generated migration for adding media fields to models

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0009_addonvideo'),
    ]

    operations = [
        # Wiki に video_url フィールドを追加
        migrations.AddField(
            model_name='wiki',
            name='video_url',
            field=models.URLField(blank=True, null=True, verbose_name='動画URL（YouTubeなど）'),
        ),
        
        # Announcement に image と video_url を追加
        migrations.AddField(
            model_name='announcement',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='announcements/', verbose_name='画像'),
        ),
        migrations.AddField(
            model_name='announcement',
            name='video_url',
            field=models.URLField(blank=True, null=True, verbose_name='動画URL（YouTubeなど）'),
        ),
        
        # ContactMessage に image フィールドを追加
        migrations.AddField(
            model_name='contactmessage',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='contact_images/', verbose_name='画像添付'),
        ),
    ]
