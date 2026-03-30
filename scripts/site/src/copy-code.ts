/* copy-code.ts — clipboard copy buttons (used on index/home page) */
function initCopyButtons(): void {
    document.querySelectorAll<HTMLButtonElement>('.copy-btn').forEach((btn) => {
        if ((btn as HTMLElement & { _bound?: boolean })._bound) return;
        (btn as HTMLElement & { _bound?: boolean })._bound = true;
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-copy-target');
            const target = targetId ? document.getElementById(targetId) : null;
            if (!target) return;
            const text = target.textContent ?? '';
            navigator.clipboard.writeText(text).then(() => {
                btn.classList.add('copy-btn--copied');
                const label = btn.querySelector('.copy-btn-label');
                const icon = btn.querySelector('.copy-btn-icon');
                if (label) label.textContent = 'Copied!';
                if (icon) icon.textContent = '✅';
                setTimeout(() => {
                    btn.classList.remove('copy-btn--copied');
                    if (label) label.textContent = 'Copy';
                    if (icon) icon.textContent = '📋';
                }, 2000);
            });
        });
    });
}

initCopyButtons();
document.addEventListener('htmx:afterSettle', initCopyButtons);
