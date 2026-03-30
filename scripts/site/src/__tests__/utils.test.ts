import { describe, it, expect, beforeEach } from 'vitest';

// Inline the pure decodeSchedule logic for testing (mirrors my-schedule-page.ts)
function decodeSchedule(raw: string): string[] | null {
    try {
        const decoded = JSON.parse(atob(raw.trim())) as unknown;
        if (!Array.isArray(decoded)) return null;
        return (decoded as unknown[])
            .filter((x): x is string | number => typeof x === 'string' || typeof x === 'number')
            .map(String);
    } catch (_) {
        return null;
    }
}

describe('decodeSchedule', () => {
    it('returns null for empty string', () => {
        expect(decodeSchedule('')).toBeNull();
    });

    it('returns null for non-base64', () => {
        expect(decodeSchedule('!!not-base64!!')).toBeNull();
    });

    it('returns null for valid base64 that is not an array', () => {
        expect(decodeSchedule(btoa(JSON.stringify({ id: '1' })))).toBeNull();
    });

    it('decodes a valid encoded schedule', () => {
        const ids = ['1', '2', '3'];
        expect(decodeSchedule(btoa(JSON.stringify(ids)))).toEqual(['1', '2', '3']);
    });

    it('coerces numbers to strings', () => {
        expect(decodeSchedule(btoa(JSON.stringify([1, 2])))).toEqual(['1', '2']);
    });

    it('filters out non-string/number entries', () => {
        expect(decodeSchedule(btoa(JSON.stringify(['1', null, {}, '2'])))).toEqual(['1', '2']);
    });

    it('handles whitespace around the code', () => {
        const encoded = '  ' + btoa(JSON.stringify(['42'])) + '  ';
        expect(decodeSchedule(encoded)).toEqual(['42']);
    });
});

describe('analytics tab switcher', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <button role="tab" data-tab="panel-a" class="sort-btn--active" aria-selected="true">A</button>
            <button role="tab" data-tab="panel-b" aria-selected="false">B</button>
            <div id="panel-a" class="tab-panel">Panel A</div>
            <div id="panel-b" class="tab-panel" hidden>Panel B</div>
        `;

        // Replicate the tab-switcher logic
        const buttons = document.querySelectorAll<HTMLElement>('[role="tab"]');
        buttons.forEach((btn) => {
            btn.addEventListener('click', () => {
                buttons.forEach((b) => {
                    b.classList.remove('sort-btn--active');
                    b.setAttribute('aria-selected', 'false');
                });
                document.querySelectorAll<HTMLElement>('.tab-panel').forEach((p) => {
                    p.hidden = true;
                });
                btn.classList.add('sort-btn--active');
                btn.setAttribute('aria-selected', 'true');
                const tabId = btn.dataset.tab;
                if (tabId) {
                    const panel = document.getElementById(tabId);
                    if (panel) panel.hidden = false;
                }
            });
        });
    });

    it('activates the clicked tab and shows its panel', () => {
        const btnB = document.querySelector<HTMLElement>('[data-tab="panel-b"]')!;
        btnB.click();

        expect(btnB.classList.contains('sort-btn--active')).toBe(true);
        expect(btnB.getAttribute('aria-selected')).toBe('true');
        expect(document.getElementById('panel-b')!.hidden).toBe(false);
    });

    it('deactivates the previously active tab', () => {
        const btnB = document.querySelector<HTMLElement>('[data-tab="panel-b"]')!;
        btnB.click();

        const btnA = document.querySelector<HTMLElement>('[data-tab="panel-a"]')!;
        expect(btnA.classList.contains('sort-btn--active')).toBe(false);
        expect(document.getElementById('panel-a')!.hidden).toBe(true);
    });
});
