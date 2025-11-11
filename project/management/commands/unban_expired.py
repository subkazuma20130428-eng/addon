from django.core.management.base import BaseCommand
from django.utils.timezone import now
from project.models import BanRecord


class Command(BaseCommand):
    help = '期限切れの BAN を検出してユーザーの is_active を True に戻します'

    def handle(self, *args, **options):
        now_dt = now()
        # expires_at が設定され、期限が切れているレコードを取得
        expired = BanRecord.objects.filter(expires_at__isnull=False, expires_at__lte=now_dt)
        total = expired.count()
        self.stdout.write(f'見つかった期限切れBAN: {total} 件')
        restored = 0
        for b in expired:
            user = b.user
            if not user.is_active:
                user.is_active = True
                user.save(update_fields=['is_active'])
                restored += 1
                self.stdout.write(f'解除: {user.username} (Ban id={b.id})')
            # 期限切れとして処理済みの目印を残したい場合はここで b.processed=True などを設定する

        self.stdout.write(self.style.SUCCESS(f'処理完了: {restored} ユーザーを有効化しました'))
