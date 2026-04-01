/* base.ts — UI shell: dark mode, nav, grid helpers, toast, SW, PWA banner */
import { bindOnce } from './dom-utils.js';

// ── Grid hour toggle ───────────────────────────────────────────────────────
function getHourFromHeader(headerRow: HTMLElement): string {
    return headerRow.getAttribute('data-hour') ?? '';
}

function getContentRowsForHour(hour: string): NodeListOf<HTMLTableRowElement> {
    return document.querySelectorAll<HTMLTableRowElement>(
        `tr.grid-hour-content[data-hour="${CSS.escape(hour)}"]`,
    );
}

function setContentRowOpen(row: HTMLTableRowElement, open: boolean): void {
    if (open) {
        row.classList.remove('grid-hour-content--hidden');
        row.removeAttribute('inert');
    } else {
        row.classList.add('grid-hour-content--hidden');
        row.setAttribute('inert', '');
    }
}

export function toggleHour(btn: HTMLElement): void {
    const headerRow = btn.closest('tr.grid-hour-header') as HTMLTableRowElement;
    const hour = getHourFromHeader(headerRow);
    const contentRows = getContentRowsForHour(hour);
    const isOpen = headerRow.classList.toggle('grid-hour--open');
    btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    contentRows.forEach((row) => setContentRowOpen(row, isOpen));
}

function bindGridHourToggles(): void {
    document.querySelectorAll<HTMLElement>('tr.grid-hour-header').forEach((row) => {
        bindOnce(row, (r) => r.addEventListener('click', () => toggleHour(r)));
    });
}

// ── Toast notification ─────────────────────────────────────────────────────
function createToastElement(message: string, type?: string): HTMLDivElement {
    const toast = document.createElement('div');
    toast.className = 'toast' + (type === 'success' ? ' toast--success' : '');
    toast.textContent = message;
    return toast;
}

function animateToastIn(toast: HTMLElement): void {
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            toast.classList.add('toast--visible');
        });
    });
}

function animateToastOut(toast: HTMLElement): void {
    toast.classList.remove('toast--visible');
    setTimeout(() => toast.remove(), 300);
}

function scheduleToastDismiss(toast: HTMLElement, delay = 4000): void {
    setTimeout(() => animateToastOut(toast), delay);
}

export function showToast(message: string, type?: string): void {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = createToastElement(message, type);
    container.appendChild(toast);
    animateToastIn(toast);
    scheduleToastDismiss(toast);
}
window.showToast = showToast;

// ── Dark mode ──────────────────────────────────────────────────────────────
function applyTheme(btn: HTMLButtonElement, dark: boolean): void {
    if (dark) {
        document.documentElement.setAttribute('data-theme', 'dark');
        btn.textContent = '☀️';
        btn.title = 'Switch to light mode';
    } else {
        document.documentElement.removeAttribute('data-theme');
        btn.textContent = '🌙';
        btn.title = 'Switch to dark mode';
    }
}

function isDarkActive(): boolean {
    return document.documentElement.getAttribute('data-theme') === 'dark';
}

function resolveInitialTheme(): boolean {
    const saved = localStorage.getItem('fosdem_theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    return saved === 'dark' || (!saved && prefersDark);
}

function handleDarkModeClick(btn: HTMLButtonElement): void {
    const dark = isDarkActive();
    localStorage.setItem('fosdem_theme', dark ? 'light' : 'dark');
    applyTheme(btn, !dark);
}

function bindDarkModeToggle(): void {
    const btn = document.getElementById('dark-mode-toggle') as HTMLButtonElement | null;
    bindOnce(btn, (el) => {
        const b = el as HTMLButtonElement;
        applyTheme(b, resolveInitialTheme());
        b.addEventListener('click', () => handleDarkModeClick(b));
    });
}

// ── Mobile nav ─────────────────────────────────────────────────────────────
function handleNavToggleClick(toggle: HTMLButtonElement, links: HTMLElement): void {
    const open = links.classList.toggle('nav-open');
    toggle.classList.toggle('nav-open', open);
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
}

function bindMobileNav(): void {
    const toggle = document.getElementById('nav-toggle') as HTMLButtonElement | null;
    const links = document.getElementById('nav-links') as HTMLElement | null;
    if (!links) return;
    bindOnce(toggle, (el) => {
        const t = el as HTMLButtonElement;
        t.addEventListener('click', () => handleNavToggleClick(t, links));
    });
}

// ── PWA install prompt ─────────────────────────────────────────────────────
interface BeforeInstallPromptEvent extends Event {
    prompt(): Promise<void>;
    userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

function handleInstallClick(
    banner: HTMLElement,
    deferred: { current: BeforeInstallPromptEvent | null },
): void {
    banner.hidden = true;
    if (deferred.current) {
        deferred.current.prompt();
        deferred.current.userChoice.then(() => { deferred.current = null; });
    }
}

function handleDismissClick(banner: HTMLElement): void {
    banner.hidden = true;
    localStorage.setItem('fosdem_pwa_dismissed', '1');
}

function listenForInstallPrompt(
    banner: HTMLElement,
    deferred: { current: BeforeInstallPromptEvent | null },
): void {
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferred.current = e as BeforeInstallPromptEvent;
        banner.hidden = false;
    });
}

function bindPwaInstallBanner(): void {
    const banner = document.getElementById('pwa-install-banner') as HTMLElement | null;
    if (!banner || localStorage.getItem('fosdem_pwa_dismissed')) return;
    bindOnce(banner, () => {
        const deferred: { current: BeforeInstallPromptEvent | null } = { current: null };
        listenForInstallPrompt(banner, deferred);
        document.getElementById('pwa-install-btn')
            ?.addEventListener('click', () => handleInstallClick(banner, deferred));
        document.getElementById('pwa-dismiss-btn')
            ?.addEventListener('click', () => handleDismissClick(banner));
    });
}

// ── Init (runs on first load + every hx-boost page swap) ──────────────────
export function initBase(): void {
    bindGridHourToggles();
    bindDarkModeToggle();
    bindMobileNav();
    bindPwaInstallBanner();
}

// ── One-time global listeners (survive all DOM swaps) ──────────────────────
function onHtmxResponseError(e: Event): void {
    const detail = (e as CustomEvent<{ xhr: XMLHttpRequest }>).detail;
    showToast(`Request failed (${detail.xhr.status}). Please try again.`, 'error');
}

function onHtmxSendError(): void {
    showToast('Network error. Check your connection and try again.', 'error');
}

function registerServiceWorker(): void {
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/static/sw.js', { scope: '/' }).catch(() => {});
        });
    }
}

document.addEventListener('htmx:responseError', onHtmxResponseError);
document.addEventListener('htmx:sendError', onHtmxSendError);
registerServiceWorker();

// Run init now (modules are deferred, DOM is ready) and on every hx-boost swap
initBase();
document.addEventListener('htmx:afterSettle', initBase);
