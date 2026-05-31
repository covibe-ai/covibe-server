/**
 * WechatOrder 变更页：在 native_code_url 控件下方动态插入二维码（内容为当前 URL）。
 * 写法与 agent/static/agent/js/json_array_select_widget.js 一致：jQuery + document.ready。
 */
(function ($) {
    'use strict';

    var MOUNT_ID = 'wechat-native-codeurl-qr-addon';

    function qrImageUrl(text) {
        return (
            'https://api.qrserver.com/v1/create-qr-code/?size=200x200&margin=10&data=' +
            encodeURIComponent(text)
        );
    }

    function removeMount() {
        $('#' + MOUNT_ID).remove();
    }

    function mount($input) {
        removeMount();
        var raw = ($input.val() || '').trim();
        if (!raw) {
            return;
        }
        var $wrap = $('<div/>', {
            id: MOUNT_ID,
            class:
                'mt-4 max-w-xs rounded-lg border border-gray-200 bg-gray-50 p-4 shadow-sm dark:border-gray-600 dark:bg-gray-900/40',
        });
        $wrap.append(
            $('<div/>', {
                class: 'mb-1 text-sm font-medium text-gray-800 dark:text-gray-100',
                text: 'Native 支付二维码',
            })
        );
        $wrap.append(
            $('<p/>', {
                class: 'mb-3 text-xs text-gray-500 dark:text-gray-400',
                text: '编码为上方 code_url，可用微信扫一扫测试。',
            })
        );
        $wrap.append(
            $('<img/>', {
                class: 'h-48 w-48 rounded-md border border-gray-200 bg-white object-contain p-1 dark:border-gray-600',
                alt: 'QR',
                src: qrImageUrl(raw),
            })
        );
        $input.after($wrap);
    }

    function isWechatOrderChangePage() {
        if ($('form#wechatorder_form').length) {
            return true;
        }
        var p = window.location.pathname || '';
        return /\/wechat\/wechatorder\/[^/]+\/change\//.test(p);
    }

    function tryBind() {
        if (!isWechatOrderChangePage()) {
            return;
        }
        var $ta = $('#id_native_code_url');
        if ($ta.length === 0) {
            return;
        }
        mount($ta);
        $ta.off('input.wechatNativeQr change.wechatNativeQr').on(
            'input.wechatNativeQr change.wechatNativeQr',
            function () {
                mount($(this));
            }
        );
    }

    $(document).ready(function () {
        tryBind();
    });
})(jQuery);
