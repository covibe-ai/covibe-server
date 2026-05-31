from django.contrib import admin
from constance.admin import ConstanceAdmin, Config
from unfold.admin import ModelAdmin
from unfold.widgets import UnfoldAdminSelectWidget, UnfoldAdminTextInputWidget
from unfold.admin import TabularInline as UnfoldTabularInline, StackedInline as UnfoldStackedInline
from simple_history.admin import SimpleHistoryAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group

from django_celery_beat.models import (
    ClockedSchedule,
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
    SolarSchedule,
)
from django_celery_beat.admin import ClockedScheduleAdmin as BaseClockedScheduleAdmin
from django_celery_beat.admin import CrontabScheduleAdmin as BaseCrontabScheduleAdmin
from django_celery_beat.admin import PeriodicTaskAdmin as BasePeriodicTaskAdmin
from django_celery_beat.admin import PeriodicTaskForm, TaskSelectWidget


class BaseTabularInline(UnfoldTabularInline):
    """
    基础 TabularInline 类
    
    特性：
    - 支持 not_change_related_fields 列表，禁止修改关联字段
    - 支持 override_field_name 字典，自定义字段显示名称
    """
    not_change_related_fields = []
    override_field_name = {}

    def formfield_for_dbfield(self, db_field, request, obj=None, **kwargs):
        formfields = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name in self.not_change_related_fields:
            formfields.widget.can_add_related = False
            formfields.widget.can_change_related = False
            formfields.widget.can_delete_related = False
        if db_field.name in self.override_field_name:
            formfields.label = self.override_field_name[db_field.name]
        return formfields


class BaseStackedInline(UnfoldStackedInline):
    """
    基础 StackedInline 类
    
    特性：
    - 支持 not_change_related_fields 列表，禁止修改关联字段
    - 支持 override_field_name 字典，自定义字段显示名称
    """
    not_change_related_fields = []
    override_field_name = {}

    def formfield_for_dbfield(self, db_field, request, obj=None, **kwargs):
        formfields = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name in self.not_change_related_fields:
            formfields.widget.can_add_related = False
            formfields.widget.can_change_related = False
            formfields.widget.can_delete_related = False
        if db_field.name in self.override_field_name:
            formfields.label = self.override_field_name[db_field.name]
        return formfields


class BaseModelAdmin(SimpleHistoryAdmin, ModelAdmin):
    """
    基础 ModelAdmin 类
    
    特性：
    - 集成 simple_history 历史记录功能
    - 集成 Unfold 现代化 UI
    - 自动将"保存并继续编辑"改为"保存并添加另一个"
    - 支持 not_change_related_fields 列表，禁止修改关联字段
    - 支持 override_field_name 字典，自定义字段显示名称
    """
    warn_unsaved_form = True
    list_filter_submit = True
    list_filter_sheet = False
    change_form_show_cancel_button = False
    not_change_related_fields = []
    override_field_name = {}

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context.update({
            'show_save_and_continue': False,
            'show_save_and_add_another': True,
        })
        return super().render_change_form(request, context, add, change, form_url, obj)
    
    def change_view(self, request, object_id, form_url="", extra_context=None):
        if '_continue' not in request.POST:
            POST2 = request.POST.copy()
            POST2['_continue'] = 'true'
            request.POST = POST2
        return super().change_view(request, object_id, form_url, extra_context)

    def formfield_for_dbfield(self, db_field, request, obj=None, **kwargs):
        formfields = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name in self.not_change_related_fields:
            formfields.widget.can_add_related = False
            formfields.widget.can_change_related = False
            formfields.widget.can_delete_related = False
        if db_field.name in self.override_field_name:
            formfields.label = self.override_field_name[db_field.name]
        return formfields

# User and Group
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Forms loaded from `unfold.forms`
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass

## Constance
admin.site.unregister([Config])
class _ConstanceAdmin(ConstanceAdmin, ModelAdmin):
    pass

admin.site.register([Config], _ConstanceAdmin)


## Celery Beat

admin.site.unregister(PeriodicTask)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(SolarSchedule)
admin.site.unregister(ClockedSchedule)


class UnfoldTaskSelectWidget(UnfoldAdminSelectWidget, TaskSelectWidget):
    pass


class UnfoldPeriodicTaskForm(PeriodicTaskForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["task"].widget = UnfoldAdminTextInputWidget()
        self.fields["regtask"].widget = UnfoldTaskSelectWidget()


@admin.register(PeriodicTask)
class PeriodicTaskAdmin(BasePeriodicTaskAdmin, ModelAdmin):
    form = UnfoldPeriodicTaskForm


@admin.register(IntervalSchedule)
class IntervalScheduleAdmin(ModelAdmin):
    pass


@admin.register(CrontabSchedule)
class CrontabScheduleAdmin(BaseCrontabScheduleAdmin, ModelAdmin):
    pass


@admin.register(SolarSchedule)
class SolarScheduleAdmin(ModelAdmin):
    pass

@admin.register(ClockedSchedule)
class ClockedScheduleAdmin(BaseClockedScheduleAdmin, ModelAdmin):
    pass

