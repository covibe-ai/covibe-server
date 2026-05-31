import os
from django.db import models
from django.core.files.storage import default_storage
from covibe_server.models import BaseModel
from django.conf import settings
from urllib.parse import urljoin


class S3FileMixin(BaseModel):
    """
    支持S3存储的文件模型基类
    
    使用约定：
    1. 子类必须定义 file_fields 列表，用于指定文件字段名列表
    2. 子类必须定义对应的文件字段，用于存储文件
    
    示例：
        class Image(S3FileMixin):
            file_fields = ['image']
            image = models.ImageField(upload_to='images/', verbose_name="图片")
            
            def image_public_url(self):
                return self.image_public_url  # 自动生成
    """
    file_fields = []

    class Meta:
        abstract = True
    
    def __getattr__(self, name):
        """
        动态处理 FOO_public_url 属性，其中 FOO 是 file_fields 中的值
        """
        for field in self.file_fields:
            if name == f"{field}_public_url":
                if getattr(self, field):
                    if settings.OSS_ENABLED:
                        return urljoin(settings.OSS_CDN_DOMAIN, getattr(self, field).path)
                    else:
                        return getattr(self, field).url
                return None
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def save(self, *args, **kwargs):
        # 如果是新建对象且没有 uuid，先生成 uuid
        if not self.pk and not self.uuid:
            self.uuid = self.uuid.default()
        
        # 如果是更新且文件字段有变化，删除旧文件
        if self.pk:
            try:
                old_instance = self.__class__.objects.get(pk=self.pk)
                for field in self.file_fields:
                    if getattr(old_instance, field) and getattr(old_instance, field) != getattr(self, field):
                        # 删除旧文件
                        if default_storage.exists(getattr(old_instance, field).name):
                            default_storage.delete(getattr(old_instance, field).name)
            except self.__class__.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # 删除时同时删除所有文件
        for field in self.file_fields:
            if getattr(self, field):
                if default_storage.exists(getattr(self, field).name):
                    default_storage.delete(getattr(self, field).name)
        super().delete(*args, **kwargs)

