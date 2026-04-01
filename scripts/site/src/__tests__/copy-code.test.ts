import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';

// Mirror the pure DOM-manipulation functions from copy-code.ts (not exported)
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

function makeBtn(targetId: string): HTMLButtonElement {
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.setAttribute('data-copy-target', targetId);
    btn.innerHTML = '<span class="copy-btn-label">Copy</span><span class="copy-btn-icon">📋</span>';
    return btn;
}

describe('getCopyTarget', () => {
    beforeEach(() => {
        document.body.innerHTML = '<pre id="code-block">echo hello</pre>';
    });

    it('returns the element matching data-copy-target', () => {
        const btn = makeBtn('code-block');
        document.body.appendChild(btn);
        expect(getCopyTarget(btn)).toBe(document.getElementById('code-block'));
    });

    it('returns null when target id is missing', () => {
        const btn = document.createElement('button') as HTMLButtonElement;
        expect(getCopyTarget(btn)).toBeNull();
    });

    it('returns null when target element does not exist', () => {
        const btn = makeBtn('nonexistent');
        expect(getCopyTarget(btn)).toBeNull();
    });
});

describe('showCopiedFeedback', () => {
    it('adds copied class and updates label/icon', () => {
        const btn = makeBtn('x');
        showCopiedFeedback(btn);
        expect(btn.classList.contains('copy-btn--copied')).toBe(true);
        expect(btn.querySelector('.copy-btn-label')!.textContent).toBe('Copied!');
        expect(btn.querySelector('.copy-btn-icon')!.textContent).toBe('✅');
    });
});

describe('resetCopyButton', () => {
    it('removes copied class and restores label/icon', () => {
        const btn = makeBtn('x');
        showCopiedFeedback(btn);
        resetCopyButton(btn);
        expect(btn.classList.contains('copy-btn--copied')).toBe(false);
        expect(btn.querySelector('.copy-btn-label')!.textContent).toBe('Copy');
        expect(btn.querySelector('.copy-btn-icon')!.textContent).toBe('📋');
    });

    it('is safe to call on a button that was never in copied state', () => {
        const btn = makeBtn('x');
        resetCopyButton(btn);
        expect(btn.classList.contains('copy-btn--copied')).toBe(false);
    });
});

describe('showCopiedFeedback handles missing children', () => {
    it('does not throw when label/icon spans are absent', () => {
        const btn = document.createElement('button') as HTMLButtonElement;
        btn.setAttribute('data-copy-target', 'x');
        // no .copy-btn-label or .copy-btn-icon children
        expect(() => showCopiedFeedback(btn)).not.toThrow();
        expect(btn.classList.contains('copy-btn--copied')).toBe(true);
    });
});
