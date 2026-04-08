(function () {
    'use strict';

    function init() {
        var tooltip = document.createElement('div');
        tooltip.id = 'quality-tooltip';
        Object.assign(tooltip.style, {
            position: 'fixed',
            background: '#222',
            color: '#fff',
            padding: '5px 9px',
            borderRadius: '4px',
            fontSize: '12px',
            pointerEvents: 'none',
            zIndex: '99999',
            display: 'none',
            maxWidth: '320px',
            lineHeight: '1.4',
            whiteSpace: 'pre-wrap',
        });
        document.body.appendChild(tooltip);

        document.addEventListener('mouseover', function (e) {
            var badge = e.target.closest('.quality-badge');
            if (!badge) return;
            var text = badge.getAttribute('data-tooltip');
            if (!text) return;
            tooltip.textContent = text;
            tooltip.style.display = 'block';
        });

        document.addEventListener('mousemove', function (e) {
            if (tooltip.style.display === 'none') return;
            tooltip.style.left = (e.clientX - 100) + 'px';
            tooltip.style.top = (e.clientY + 12) + 'px';
        });

        document.addEventListener('mouseout', function (e) {
            var badge = e.target.closest('.quality-badge');
            if (!badge) return;
            tooltip.style.display = 'none';
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
}());
