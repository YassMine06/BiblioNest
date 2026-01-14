const body = document.querySelector('body'),
    sidebar = body.querySelector('nav'),
    toggle = body.querySelector(".image-text"),
    overlay = body.querySelector(".overlay");

// 1. Check LocalStorage on Load and Apply State
const savedStatus = localStorage.getItem('sidebarStatus');
if (savedStatus === 'open') {
    sidebar.classList.remove('close');
} else {
    // Default is close
    sidebar.classList.add('close');
}

// Clean up the anti-flicker class now that JS has applied the correct class to sidebar
document.documentElement.classList.remove('sidebar-open');


// 2. Toggle Logic
toggle.addEventListener("click", () => {
    sidebar.classList.toggle("close");
    // Save new status
    if (sidebar.classList.contains("close")) {
        localStorage.setItem('sidebarStatus', 'close');
    } else {
        localStorage.setItem('sidebarStatus', 'open');
    }
});

// 3. Overlay Logic
overlay.addEventListener("click", () => {
    sidebar.classList.add("close");
    localStorage.setItem('sidebarStatus', 'close');
});
