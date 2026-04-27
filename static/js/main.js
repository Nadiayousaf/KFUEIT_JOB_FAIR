// KFUEIT Job Fair - Fixed Main JavaScript

document.addEventListener('DOMContentLoaded', function () {

    // ── Auto-dismiss alerts after 5 seconds ──
    document.querySelectorAll('.alert.alert-dismissible').forEach(function (alert) {
        setTimeout(function () {
            try {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                if (bsAlert) bsAlert.close();
            } catch(e) {}
        }, 5000);
    });

    // ── Active nav link highlighting ──
    const currentPath = window.location.pathname;
    document.querySelectorAll('.navbar-nav .nav-link').forEach(function (link) {
        const href = link.getAttribute('href');
        if (href && href === currentPath) link.classList.add('active');
    });

    // ── Sidebar toggle (mobile) ──
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function (e) {
            e.stopPropagation();
            sidebar.classList.toggle('active');
        });
        document.addEventListener('click', function (e) {
            if (sidebar.classList.contains('active') &&
                !sidebar.contains(e.target) &&
                !sidebarToggle.contains(e.target)) {
                sidebar.classList.remove('active');
            }
        });
    }

    // ── Animate stat numbers on scroll ──
    const statValues = document.querySelectorAll('.stat-value, .stat-num, .info-num');
    if (statValues.length > 0 && 'IntersectionObserver' in window) {
        const observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    animateNumber(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        statValues.forEach(function (el) { observer.observe(el); });
    }

    function animateNumber(el) {
        const raw = el.textContent.replace(/[^0-9.]/g, '');
        const target = parseFloat(raw);
        if (isNaN(target) || target === 0) return;
        const duration = 800;
        const steps = 40;
        const increment = target / steps;
        let current = 0;
        const suffix = el.textContent.replace(/[0-9.]/g, '');
        const isFloat = raw.includes('.');
        const timer = setInterval(function () {
            current += increment;
            if (current >= target) { current = target; clearInterval(timer); }
            el.textContent = (isFloat ? current.toFixed(1) : Math.floor(current)) + suffix;
        }, duration / steps);
    }

    // ── Smooth scroll for anchor links ──
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // ── Navbar scroll effect ──
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', function () {
            navbar.style.boxShadow = window.scrollY > 50
                ? '0 4px 30px rgba(0,0,0,0.35)'
                : '0 2px 20px rgba(0,0,0,0.2)';
        });
    }

});

// ── Global helpers ──

function togglePassword(id, btn) {
    const inp = document.getElementById(id);
    if (!inp) return;
    if (inp.type === 'password') {
        inp.type = 'text';
        btn.innerHTML = '<i class="fas fa-eye-slash"></i>';
    } else {
        inp.type = 'password';
        btn.innerHTML = '<i class="fas fa-eye"></i>';
    }
}

function filterTable(input, tableId) {
    const filter = (typeof input === 'string' ? input : input.value).toLowerCase();
    const table = document.getElementById(tableId);
    if (!table) return;
    table.querySelectorAll('tbody tr').forEach(function(row) {
        row.style.display = row.textContent.toLowerCase().includes(filter) ? '' : 'none';
    });
}

// ── Google Sheets Integration (Apps Script POST) ──
// Replace APPS_SCRIPT_URL with your deployed Web App URL
var APPS_SCRIPT_URL = 'YOUR_APPS_SCRIPT_WEB_APP_URL_HERE';

function sendToGoogleSheets(data) {
    if (!APPS_SCRIPT_URL || APPS_SCRIPT_URL.indexOf('YOUR_') === 0) return;
    fetch(APPS_SCRIPT_URL, {
        method: 'POST',
        mode: 'no-cors',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).catch(function(err) {
        console.warn('Google Sheets sync failed:', err);
    });
}

// Auto-hook: fires after successful Flask form submissions
// Triggered via data-gs-type attribute on <form> elements
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('form[data-gs-type]').forEach(function (form) {
        form.addEventListener('submit', function () {
            var gsType = form.getAttribute('data-gs-type');
            var formData = new FormData(form);
            var payload = { type: gsType, timestamp: new Date().toISOString() };
            formData.forEach(function (val, key) {
                // Skip sensitive fields
                if (key !== 'password' && key !== 'confirm_password') {
                    payload[key] = val;
                }
            });
            sendToGoogleSheets(payload);
        });
    });
});
