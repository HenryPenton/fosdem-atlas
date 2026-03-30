/* base.ts — UI shell: dark mode, nav, grid helpers, toast, SW, PWA banner */

// ── Grid hour toggle (called from HTML onclick) ────────────────────────────
export function toggleHour(btn: HTMLElement): void {
    const headerRow = btn.closest('tr.grid-hour-header') as HTMLTableRowElement;
    const hour = headerRow.getAttribute('data-hour') ?? '';
    const contentRows = document.querySelectorAll<HTMLTableRowElement>(
        `tr.grid-hour-content[data-hour="${CSS.escape(hour)}"]`,
    );
    const isOpen = headerRow.classList.toggle('grid-hour--open');
    btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    contentRows.forEach((row) => {
        if (isOpen) {
            row.style.display = '';
            row.removeAttribute('inert');
        } else {
            row.style.display = 'none';
            row.setAttribute('inert', '');
        }
    });
}
window.toggleHour = toggleHour;

// ── Toast notification ─────────────────────────────────────────────────────
export function showToast(message: string, type?: string): void {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast' + (type === 'success' ? ' toast--success' : '');
    toast.textContent = message;
    container.appendChild(toast);
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            toast.classList.add('toast--visible');
        });
    });
    setTimeout(() => {
        toast.classList.remove('toast--visible');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 4000);
}
window.showToast = showToast;

// ── Init (runs on first load + every hx-boost page swap) ──────────────────
function initBase(): void {
    // Dark mode toggle
    const btn = document.getElementById('dark-mode-toggle') as HTMLButtonElement | null;
    if (btn && !(btn as HTMLElement & { _bound?: boolean })._bound) {
        (btn as HTMLElement & { _bound?: boolean })._bound = true;
        function applyTheme(dark: boolean): void {
            if (dark) {
                document.documentElement.setAttribute('data-theme', 'dark');
                btn!.textContent = '☀️';
                btn!.title = 'Switch to light mode';
            } else {
                document.documentElement.removeAttribute('data-theme');
                btn!.textContent = '🌙';
                btn!.title = 'Switch to dark mode';
            }
        }
        const saved = localStorage.getItem('fosdem_theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        applyTheme(saved === 'dark' || (!saved && prefersDark));
        btn.addEventListener('click', () => {
            const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            localStorage.setItem('fosdem_theme', isDark ? 'light' : 'dark');
            applyTheme(!isDark);
        });
    }

    // Mobile nav toggle
    const toggle = document.getElementById('nav-toggle') as HTMLButtonElement | null;
    const links = document.getElementById('nav-links') as HTMLElement | null;
    if (toggle && links && !(toggle as HTMLElement & { _bound?: boolean })._bound) {
        (toggle as HTMLElement & { _bound?: boolean })._bound = true;
        toggle.addEventListener('click', () => {
            const open = links.classList.toggle('nav-open');
            toggle.classList.toggle('nav-open', open);
            toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        });
    }

    // PWA install prompt
    const banner = document.getElementById('pwa-install-banner') as HTMLElement | null;
    const installBtn = document.getElementById('pwa-install-btn');
    const dismissBtn = document.getElementById('pwa-dismiss-btn');
    if (banner && !localStorage.getItem('fosdem_pwa_dismissed')
        && !(banner as HTMLElement & { _bound?: boolean })._bound) {
        (banner as HTMLElement & { _bound?: boolean })._bound = true;
        let deferred: BeforeInstallPromptEvent | null = null;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferred = e as BeforeInstallPromptEvent;
            banner.hidden = false;
        });
        installBtn?.addEventListener('click', () => {
            banner.hidden = true;
            if (deferred) {
                deferred.prompt();
                deferred.userChoice.then(() => { deferred = null; });
            }
        });
        dismissBtn?.addEventListener('click', () => {
            banner.hidden = true;
            localStorage.setItem('fosdem_pwa_dismissed', '1');
        });
    }
}

// ── One-time global listeners (survive all DOM swaps) ──────────────────────
document.addEventListener('htmx:responseError', (e) => {
    const detail = (e as CustomEvent<{ xhr: XMLHttpRequest }>).detail;
    showToast(`Request failed (${detail.xhr.status}). Please try again.`, 'error');
});
document.addEventListener('htmx:sendError', () => {
    showToast('Network error. Check your connection and try again.', 'error');
});

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js', { scope: '/' }).catch(() => {});
    });
}

// Run init now (modules are deferred, DOM is ready) and on every hx-boost swap
initBase();
document.addEventListener('htmx:afterSettle', initBase);

interface BeforeInstallPromptEvent extends Event {
    prompt(): Promise<void>;
    userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}
