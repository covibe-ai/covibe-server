from django.db import models
from shortuuid.django_fields import ShortUUIDField
from simple_history.models import HistoricalRecords


class BaseModel(models.Model):
    """
    基础模型类，提供通用字段和功能
    
    特性：
    - 使用 ShortUUID 作为主键
    - 自动记录创建和更新时间
    - 集成 simple_history 用于历史记录追踪
    """
    uuid = ShortUUIDField(
        verbose_name="UUID",
        length=16,
        max_length=40,
        prefix="",
        primary_key=True,
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    history = HistoricalRecords(inherit=True)

    @property
    def get_str(self) -> str:
        return str(self.uuid)

    class Meta:
        abstract = True
        ordering = ['-updated_at']

