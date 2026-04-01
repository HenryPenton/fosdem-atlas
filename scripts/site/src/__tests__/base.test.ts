import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { showToast, toggleHour } from '../base.js';

// jsdom lacks CSS.escape — provide a minimal polyfill
if (typeof globalThis.CSS === 'undefined') {
    (globalThis as Record<string, unknown>).CSS = {
        escape: (s: string) => s.replace(/([^\w-])/g, '\\$1'),
    };
}

describe('showToast', () => {
    beforeEach(() => {
        document.body.innerHTML = '<div id="toast-container"></div>';
    });

    it('appends a toast element to the container', () => {
        showToast('hello');
        const container = document.getElementById('toast-container')!;
        expect(container.children).toHaveLength(1);
        expect(container.children[0].textContent).toBe('hello');
        expect(container.children[0].className).toBe('toast');
    });

    it('adds toast--success class for success type', () => {
        showToast('saved!', 'success');
        const toast = document.querySelector('.toast')!;
        expect(toast.classList.contains('toast--success')).toBe(true);
    });

    it('does not add success class for error type', () => {
        showToast('fail', 'error');
        const toast = document.querySelector('.toast')!;
        expect(toast.classList.contains('toast--success')).toBe(false);
    });

    it('does nothing when container is missing', () => {
        document.body.innerHTML = '';
        showToast('nope');
        expect(document.querySelector('.toast')).toBeNull();
    });

    it('can stack multiple toasts', () => {
        showToast('one');
        showToast('two');
        const container = document.getElementById('toast-container')!;
        expect(container.children).toHaveLength(2);
    });
});

describe('toggleHour', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <table>
                <tr class="grid-hour-header" data-hour="10">
                    <td><button aria-expanded="false">10:00</button></td>
                </tr>
                <tr class="grid-hour-content grid-hour-content--hidden" data-hour="10" inert>
                    <td>Event A</td>
                </tr>
                <tr class="grid-hour-content grid-hour-content--hidden" data-hour="10" inert>
                    <td>Event B</td>
                </tr>
                <tr class="grid-hour-header" data-hour="11">
                    <td><button aria-expanded="false">11:00</button></td>
                </tr>
                <tr class="grid-hour-content grid-hour-content--hidden" data-hour="11" inert>
                    <td>Event C</td>
                </tr>
            </table>
        `;
    });

    it('opens the content rows for the clicked hour', () => {
        const header = document.querySelector('tr[data-hour="10"]') as HTMLElement;
        toggleHour(header);

        const rows = document.querySelectorAll('tr.grid-hour-content[data-hour="10"]');
        rows.forEach((row) => {
            expect(row.classList.contains('grid-hour-content--hidden')).toBe(false);
            expect(row.hasAttribute('inert')).toBe(false);
        });
    });

    it('sets aria-expanded to true when opening', () => {
        const header = document.querySelector('tr[data-hour="10"]') as HTMLElement;
        toggleHour(header);
        expect(header.getAttribute('aria-expanded')).toBe('true');
    });

    it('adds grid-hour--open class to the header', () => {
        const header = document.querySelector('tr[data-hour="10"]') as HTMLElement;
        toggleHour(header);
        expect(header.classList.contains('grid-hour--open')).toBe(true);
    });

    it('closes rows on second toggle', () => {
        const header = document.querySelector('tr[data-hour="10"]') as HTMLElement;
        toggleHour(header); // open
        toggleHour(header); // close

        const rows = document.querySelectorAll('tr.grid-hour-content[data-hour="10"]');
        rows.forEach((row) => {
            expect(row.classList.contains('grid-hour-content--hidden')).toBe(true);
            expect(row.hasAttribute('inert')).toBe(true);
        });
        expect(header.getAttribute('aria-expanded')).toBe('false');
    });

    it('does not affect other hour groups', () => {
        const header10 = document.querySelector('tr[data-hour="10"]') as HTMLElement;
        toggleHour(header10);

        const row11 = document.querySelector('tr.grid-hour-content[data-hour="11"]') as HTMLElement;
        expect(row11.classList.contains('grid-hour-content--hidden')).toBe(true);
        expect(row11.hasAttribute('inert')).toBe(true);
    });
});
