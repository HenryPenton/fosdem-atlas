import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { initBookmarkButtons, updateNavBadge, has, add, clear } from '../my-schedule.js';

const _store: Record<string, string> = {};
const mockLocalStorage = {
    getItem: (key: string): string | null => _store[key] ?? null,
    setItem: (key: string, value: string): void => { _store[key] = value; },
    removeItem: (key: string): void => { delete _store[key]; },
    clear: (): void => { Object.keys(_store).forEach((k) => delete _store[k]); },
    key: (_i: number): null => null,
    length: 0,
};

beforeEach(() => {
    vi.stubGlobal('localStorage', mockLocalStorage);
    Object.keys(_store).forEach((k) => delete _store[k]);
});

afterEach(() => {
    vi.unstubAllGlobals();
    document.body.innerHTML = '';
});

describe('initBookmarkButtons', () => {
    it('marks saved events as active', () => {
        add('42');
        document.body.innerHTML = `
            <button data-bookmark-id="42">★</button>
            <button data-bookmark-id="99">★</button>
        `;
        initBookmarkButtons();

        const btn42 = document.querySelector('[data-bookmark-id="42"]') as HTMLElement;
        const btn99 = document.querySelector('[data-bookmark-id="99"]') as HTMLElement;
        expect(btn42.classList.contains('bookmark-btn--active')).toBe(true);
        expect(btn42.getAttribute('aria-label')).toBe('Remove from My Schedule');
        expect(btn99.classList.contains('bookmark-btn--active')).toBe(false);
        expect(btn99.getAttribute('aria-label')).toBe('Add to My Schedule');
    });

    it('toggles bookmark on click', () => {
        document.body.innerHTML = `
            <button data-bookmark-id="7">★</button>
            <span id="schedule-badge"></span>
        `;
        initBookmarkButtons();

        const btn = document.querySelector('[data-bookmark-id="7"]') as HTMLElement;
        btn.click();
        expect(has('7')).toBe(true);
        expect(btn.classList.contains('bookmark-btn--active')).toBe(true);

        btn.click();
        expect(has('7')).toBe(false);
        expect(btn.classList.contains('bookmark-btn--active')).toBe(false);
    });

    it('does not double-bind on repeated init calls', () => {
        document.body.innerHTML = '<button data-bookmark-id="1">★</button>';
        initBookmarkButtons();
        initBookmarkButtons();

        const btn = document.querySelector('[data-bookmark-id="1"]') as HTMLElement;
        btn.click();
        expect(has('1')).toBe(true);
        // if double-bound, a second click would toggle twice (add then remove)
        // with correct single bind: second click removes
        btn.click();
        expect(has('1')).toBe(false);
    });
});

describe('updateNavBadge', () => {
    it('shows count when events are saved', () => {
        document.body.innerHTML = '<span id="schedule-badge" hidden></span>';
        add('a');
        add('b');
        updateNavBadge();

        const badge = document.getElementById('schedule-badge')!;
        expect(badge.textContent).toBe('2');
        expect(badge.hidden).toBe(false);
    });

    it('hides badge when no events are saved', () => {
        document.body.innerHTML = '<span id="schedule-badge">5</span>';
        updateNavBadge();

        const badge = document.getElementById('schedule-badge')!;
        expect(badge.textContent).toBe('');
        expect(badge.hidden).toBe(true);
    });

    it('does nothing when badge element is missing', () => {
        document.body.innerHTML = '';
        // should not throw
        updateNavBadge();
    });
});
