from django.contrib.auth.backends import ModelBackend
from django.utils.timezone import now
from django.db.models import Q

from .models import BanRecord


class BanProtectBackend(ModelBackend):
    """拡張 ModelBackend: ユーザーがアクティブであり、かつ有効なBANが無いことを確認する。

    既存の user_can_authenticate の振る舞いを保ちつつ、
    BanRecord に現在有効なエントリがあれば認証を拒否します。
    """

    def user_can_authenticate(self, user):
        # まず既存のチェック（is_active 等）を実施
        if not super().user_can_authenticate(user):
            return False

        # BanRecord が存在してかつ現在有効であればログイン不可
        now_dt = now()
        has_active_ban = BanRecord.objects.filter(
            user=user
        ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now_dt)).exists()

        return not has_active_ban
