// Emergency fix for menu button
(function () {
    'use strict';

    const menuBtn = document.getElementById('menu-btn');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');
    const closeSidebarBtn = document.getElementById('close-sidebar-btn');

    function toggleMenu() {
        if (sidebar) sidebar.classList.toggle('open');
        if (overlay) overlay.classList.toggle('active');
    }

    if (menuBtn) {
        // Remove any existing listeners by replacing the element
        const newMenuBtn = menuBtn.cloneNode(true);
        menuBtn.parentNode.replaceChild(newMenuBtn, menuBtn);
        newMenuBtn.addEventListener('click', toggleMenu);
    }

    if (closeSidebarBtn) {
        const newCloseBtn = closeSidebarBtn.cloneNode(true);
        closeSidebarBtn.parentNode.replaceChild(newCloseBtn, closeSidebarBtn);
        newCloseBtn.addEventListener('click', toggleMenu);
    }

    if (overlay) {
        const newOverlay = overlay.cloneNode(true);
        overlay.parentNode.replaceChild(newOverlay, overlay);
        newOverlay.addEventListener('click', toggleMenu);
    }
})();
