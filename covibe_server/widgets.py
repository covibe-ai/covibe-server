from django import forms
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
import json


class MultipleSelectWidget(forms.Widget):
    """
    多选框Widget，用于处理JSON字段中的列表数据
    支持选项验证和最少选择数量限制
    """
    template_name = 'router/widgets/multiple_select_widget.html'
    
    class Media:
        css = {
            # 'all': ('router/css/multiple_select_widget.css',)
        }
        js = (
            'router/js/multiple_select_widget.js',
        )

    def __init__(self, choices=None, min_selected=0, readonly=False, attrs=None):
        super().__init__(attrs)
        self.choices = choices or []
        self.min_selected = min_selected
        self.readonly = readonly

    def render(self, name, value, attrs=None, renderer=None):
        # 解析现有的 JSON 数据
        selected_values = []
        if value:
            try:
                if isinstance(value, str):
                    selected_values = json.loads(value)
                elif isinstance(value, list):
                    selected_values = value
            except (json.JSONDecodeError, TypeError):
                selected_values = []
        
        # 确保 selected_values 是列表格式
        if not isinstance(selected_values, list):
            selected_values = []
        
        context = {
            'widget': {
                'name': name,
                'value': selected_values,
                'attrs': attrs or {},
                'choices': self.choices,
                'readonly': self.readonly,
                'min_selected': self.min_selected,
                'json_value': json.dumps(selected_values, ensure_ascii=False) if selected_values else '[]',
            }
        }
        return render_to_string(self.template_name, context)
    
    def value_from_datadict(self, data, files, name):
        """从表单数据中获取值，返回 JSON 字符串"""
        value = data.get(name, '')
        
        if isinstance(value, str) and value.strip():
            try:
                # 解析 JSON 字符串，确保格式正确
                parsed_value = json.loads(value)
                
                # 验证是否为列表
                if not isinstance(parsed_value, list):
                    raise ValidationError('数据格式错误：必须是列表')

                # 验证选项是否有效
                valid_values = [choice[0] for choice in self.choices]
                invalid_values = [v for v in parsed_value if v not in valid_values]
                if invalid_values:
                    raise ValidationError(f'无效的选项：{", ".join(map(str, invalid_values))}')

                # 验证最少选择数量
                if len(parsed_value) < self.min_selected:
                    raise ValidationError(f'至少需要选择 {self.min_selected} 项')

                return json.dumps(parsed_value, ensure_ascii=False)
            except json.JSONDecodeError:
                raise ValidationError('JSON 格式错误')
            except ValidationError as e:
                raise e
            except Exception as e:
                raise ValidationError(f'数据验证错误：{str(e)}')
        
        # 如果没有数据，验证最少选择数量
        if self.min_selected > 0:
            raise ValidationError(f'至少需要选择 {self.min_selected} 项')
        
        return '[]'

