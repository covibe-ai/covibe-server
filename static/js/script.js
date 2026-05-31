// 全局消息通知组件
const showNotification = (function() {
    // 创建通知容器
    const createContainer = () => {
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'fixed top-4 right-4 z-50 flex flex-col gap-3 min-w-[320px] max-w-[420px]';
            document.body.appendChild(container);
        }
        return container;
    };

    // 创建单个通知
    const createNotification = (message, type = 'error') => {
        const notification = document.createElement('div');
        
        // 基础样式
        let baseClasses = 'flex items-center p-4 rounded-xl shadow-lg transition-all duration-500 ease-in-out transform translate-x-0 opacity-100';
        
        // 根据类型设置不同的样式
        let typeClasses = {
            'error': 'bg-gradient-to-r from-red-50 to-red-100 border-l-4 border-red-500',
            'success': 'bg-gradient-to-r from-green-50 to-green-100 border-l-4 border-green-500',
            'warning': 'bg-gradient-to-r from-yellow-50 to-yellow-100 border-l-4 border-yellow-500',
            'info': 'bg-gradient-to-r from-blue-50 to-blue-100 border-l-4 border-blue-500'
        };
        
        notification.className = `${baseClasses} ${typeClasses[type]}`;
        
        // 设置图标
        const icons = {
            'error': `<svg class="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                     </svg>`,
            'success': `<svg class="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                         <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                       </svg>`,
            'warning': `<svg class="w-6 h-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                         <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                       </svg>`,
            'info': `<svg class="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>`
        };

        const textColors = {
            'error': 'text-red-800',
            'success': 'text-green-800',
            'warning': 'text-yellow-800',
            'info': 'text-blue-800'
        };
        
        notification.innerHTML = `
            <div class="flex items-center w-full">
                <div class="flex-shrink-0">
                    ${icons[type]}
                </div>
                <div class="ml-3 flex-grow">
                    <p class="text-sm font-medium ${textColors[type]}">${message}</p>
                </div>
                <button type="button" 
                        class="flex-shrink-0 ml-4 flex items-center justify-center h-6 w-6 rounded-full hover:bg-black/5 transition-colors duration-200" 
                        onclick="this.closest('div[role=alert]').remove()">
                    <svg class="w-4 h-4 ${textColors[type]}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>
        `;

        notification.setAttribute('role', 'alert');

        // 添加进入动画
        notification.style.transform = 'translateX(100%)';
        notification.style.opacity = '0';
        
        requestAnimationFrame(() => {
            notification.style.transform = 'translateX(0)';
            notification.style.opacity = '1';
        });

        // 自动消失
        const timeout = setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 500);
        }, 4000);

        // 鼠标悬停时暂停自动消失
        notification.addEventListener('mouseenter', () => clearTimeout(timeout));
        notification.addEventListener('mouseleave', () => {
            setTimeout(() => {
                notification.style.transform = 'translateX(100%)';
                notification.style.opacity = '0';
                setTimeout(() => notification.remove(), 500);
            }, 2000);
        });

        return notification;
    };

    // 返回公共方法
    return {
        show: function(message, type = 'error') {
            const container = createContainer();
            const notification = createNotification(message, type);
            container.appendChild(notification);
        },
        error: function(message) {
            this.show(message, 'error');
        },
        success: function(message) {
            this.show(message, 'success');
        },
        warning: function(message) {
            this.show(message, 'warning');
        },
        info: function(message) {
            this.show(message, 'info');
        }
    };
})();

// 导出到全局作用域
window.showNotification = showNotification; 

$(document).ready(function() {
    $('.click_to_copy').click(function() {
        var text = $(this).attr('data-text');
        navigator.clipboard.writeText(text);
        showNotification.success('已复制到剪贴板');
    });
});

