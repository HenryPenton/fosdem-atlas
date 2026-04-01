/* copy-code.ts — clipboard copy buttons (used on index/home page) */
import { alreadyBound, markBound } from './dom-utils.js';

function getCopyTarget(btn: HTMLButtonElement): HTMLElement | null {
    const targetId = btn.getAttribute('data-copy-target');
    return targetId ? document.getElementById(targetId) : null;
}

function showCopiedFeedback(btn: HTMLButtonElement): void {
    btn.classList.add('copy-btn--copied');
    const label = btn.querySelector('.copy-btn-label');
    const icon = btn.querySelector('.copy-btn-icon');
    if (label) label.textContent = 'Copied!';
    if (icon) icon.textContent = '✅';
}

function resetCopyButton(btn: HTMLButtonElement): void {
    btn.classList.remove('copy-btn--copied');
    const label = btn.querySelector('.copy-btn-label');
    const icon = btn.querySelector('.copy-btn-icon');
    if (label) label.textContent = 'Copy';
    if (icon) icon.textContent = '📋';
}

function scheduleCopyReset(btn: HTMLButtonElement, delay = 2000): void {
    setTimeout(() => resetCopyButton(btn), delay);
}

function handleCopyClick(btn: HTMLButtonElement): void {
    const target = getCopyTarget(btn);
    if (!target) return;
    const text = target.textContent ?? '';
    navigator.clipboard.writeText(text).then(() => {
        showCopiedFeedback(btn);
        scheduleCopyReset(btn);
    });
}

function bindCopyButton(btn: HTMLButtonElement): void {
    btn.addEventListener('click', () => handleCopyClick(btn));
}

function initCopyButtons(): void {
    document.querySelectorAll<HTMLButtonElement>('.copy-btn').forEach((btn) => {
        if (alreadyBound(btn)) return;
        markBound(btn);
        bindCopyButton(btn);
    });
}

initCopyButtons();
document.addEventListener('htmx:afterSettle', initCopyButtons);
