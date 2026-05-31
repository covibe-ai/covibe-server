document.addEventListener('DOMContentLoaded', function() {
    // 为所有多选框组件初始化
    document.querySelectorAll('[id^="multiple-select-container-"]').forEach(container => {
        const widgetId = container.id.replace('multiple-select-container-', '');
        initializeWidget(widgetId);
    });
});

function initializeWidget(widgetId) {
    const container = document.getElementById(`multiple-select-container-${widgetId}`);
    const jsonInput = document.getElementById(`json-input-${widgetId}`);
    const selectedItemsContainer = document.getElementById(`selected-items-${widgetId}`);
    const errorMessage = document.getElementById(`error-message-${widgetId}`);
    const minSelected = parseInt(jsonInput.dataset.minSelected) || 0;

    // 为每个选项标签添加点击事件
    if (!container.hasAttribute('readonly'))
        selectedItemsContainer.querySelectorAll('label').forEach(label => {
            label.addEventListener('click', (e) => {
                e.preventDefault();
                const value = label.dataset.value;
                let selectedValues = [];
                
                try {
                    selectedValues = JSON.parse(jsonInput.value);
                } catch (e) {
                    selectedValues = [];
                }

                const isSelected = selectedValues.includes(value);
                
                // 如果要取消选中，先检查最少选择数量
                if (isSelected && selectedValues.length <= minSelected) {
                    showError(widgetId, `至少需要选择 ${minSelected} 项`);
                    return;
                }

                // 更新选中状态
                if (isSelected) {
                    selectedValues = selectedValues.filter(v => v !== value);
                    label.classList.remove('bg-primary-100', 'text-primary-700');
                    label.classList.add('bg-gray-100', 'text-gray-500');
                    label.querySelector('.material-symbols-outlined')?.remove();
                } else {
                    selectedValues.push(value);
                    label.classList.remove('bg-gray-100', 'text-gray-500');
                    label.classList.add('bg-primary-100', 'text-primary-700');
                    const checkIcon = document.createElement('span');
                    checkIcon.className = 'material-symbols-outlined text-sm';
                    checkIcon.textContent = 'check';
                    label.appendChild(checkIcon);
                }

                // 更新隐藏输入字段的值
                jsonInput.value = JSON.stringify(selectedValues);
                
                // 清除错误消息
                hideError(widgetId);
            });
        });
}

function showError(widgetId, message) {
    const errorMessage = document.getElementById(`error-message-${widgetId}`);
    errorMessage.querySelector('.error-text').textContent = message;
    errorMessage.classList.remove('hidden');
}

function hideError(widgetId) {
    const errorMessage = document.getElementById(`error-message-${widgetId}`);
    errorMessage.classList.add('hidden');
} 