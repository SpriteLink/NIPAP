(function () {
    'use strict';
    var preference;
    var systemTheme = window.matchMedia('(prefers-color-scheme: dark)');
    try {
        preference = localStorage.getItem('nipap-theme');
    } catch (error) {
        // The switch still works when browser storage is unavailable.
    }
    if (preference !== 'dark' && preference !== 'light') {
        preference = null;
    }

    function applyTheme() {
        var dark = preference ? preference === 'dark' : systemTheme.matches;
        document.documentElement.dataset.theme = dark ? 'dark' : 'light';
        var control = document.getElementById('theme-switch');
        if (control) {
            control.setAttribute('aria-checked', String(dark));
        }
    }

    applyTheme();
    systemTheme.addEventListener('change', applyTheme);
    document.addEventListener('DOMContentLoaded', function () {
        var control = document.getElementById('theme-switch');
        var startX = null;
        var dragged = false;
        function select(dark) {
            preference = dark ? 'dark' : 'light';
            try {
                localStorage.setItem('nipap-theme', preference);
            } catch (error) {
                // Retain the selection for this page even without storage.
            }
            applyTheme();
        }
        applyTheme();
        control.addEventListener('click', function () {
            if (dragged) {
                dragged = false;
                return;
            }
            select(document.documentElement.dataset.theme !== 'dark');
        });
        control.addEventListener('pointerdown', function (event) {
            if (!event.isPrimary || event.button !== 0) {
                return;
            }
            startX = event.clientX;
            dragged = false;
            control.setPointerCapture(event.pointerId);
        });
        control.addEventListener('pointerup', function (event) {
            if (startX === null) {
                return;
            }
            var distance = event.clientX - startX;
            startX = null;
            if (Math.abs(distance) > 8) {
                dragged = true;
                select(distance > 0);
            }
        });
        control.addEventListener('pointercancel', function () {
            startX = null;
            dragged = false;
        });
        control.addEventListener('keydown', function (event) {
            dragged = false;
            if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
                event.preventDefault();
                select(event.key === 'ArrowRight');
            }
        });
    });
}());
