/* my-schedule.ts — localStorage helper + conflict detection */
import type { EventData, Conflict, ParsedEvent } from './global.js';

const KEY = 'fosdem_my_schedule';

export function getIds(): string[] {
    try {
        return JSON.parse(localStorage.getItem(KEY) ?? '[]') as string[];
    } catch (_) {
        return [];
    }
}

function save(ids: string[]): void {
    localStorage.setItem(KEY, JSON.stringify(ids));
}

export function has(id: string): boolean {
    return getIds().indexOf(id) !== -1;
}

export function add(id: string): void {
    const ids = getIds();
    if (ids.indexOf(id) === -1) {
        ids.push(id);
        save(ids);
    }
}

export function remove(id: string): void {
    save(getIds().filter((x) => x !== id));
}

export function toggle(id: string): boolean {
    if (has(id)) {
        remove(id);
        return false;
    }
    add(id);
    return true;
}

export function clear(): void {
    localStorage.removeItem(KEY);
}

export function count(): number {
    return getIds().length;
}

/**
 * Detect time conflicts among a list of events.
 * Each event needs: id, title, start_time (ISO string), duration_minutes, room.
 * Returns array of { a: event, b: event } pairs.
 */
export function detectConflicts(events: EventData[]): Conflict[] {
    const parsed: ParsedEvent[] = events
        .filter((e) => e.start_time && e.duration_minutes)
        .map((e) => {
            const start = new Date(e.start_time);
            const end = new Date(start.getTime() + e.duration_minutes * 60000);
            return { id: e.id, title: e.title, room: e.room, start, end };
        })
        .sort((a, b) => a.start.getTime() - b.start.getTime());

    const conflicts: Conflict[] = [];
    for (let i = 0; i < parsed.length; i++) {
        for (let j = i + 1; j < parsed.length; j++) {
            if (parsed[j].start >= parsed[i].end) break;
            if (parsed[i].room !== parsed[j].room) {
                conflicts.push({ a: parsed[i], b: parsed[j] });
            }
        }
    }
    return conflicts;
}

export function initBookmarkButtons(): void {
    const buttons = document.querySelectorAll<HTMLElement>('[data-bookmark-id]');
    buttons.forEach((btn) => {
        const id = btn.getAttribute('data-bookmark-id') ?? '';
        if (has(id)) {
            btn.classList.add('bookmark-btn--active');
            btn.title = 'Remove from My Schedule';
            btn.setAttribute('aria-label', 'Remove from My Schedule');
        } else {
            btn.classList.remove('bookmark-btn--active');
            btn.title = 'Add to My Schedule';
            btn.setAttribute('aria-label', 'Add to My Schedule');
        }
        if ((btn as HTMLElement & { _bookmarkBound?: boolean })._bookmarkBound) return;
        (btn as HTMLElement & { _bookmarkBound?: boolean })._bookmarkBound = true;
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const added = toggle(id);
            if (added) {
                btn.classList.add('bookmark-btn--active');
                btn.title = 'Remove from My Schedule';
                btn.setAttribute('aria-label', 'Remove from My Schedule');
            } else {
                btn.classList.remove('bookmark-btn--active');
                btn.title = 'Add to My Schedule';
                btn.setAttribute('aria-label', 'Add to My Schedule');
            }
            updateNavBadge();
        });
    });
}

export function updateNavBadge(): void {
    const badge = document.getElementById('schedule-badge');
    if (badge) {
        const c = count();
        badge.textContent = c > 0 ? String(c) : '';
        badge.hidden = c === 0;
    }
}

export const MySchedule = {
    getIds,
    has,
    add,
    remove,
    toggle,
    clear,
    count,
    detectConflicts,
    initBookmarkButtons,
    updateNavBadge,
};

// Expose globally for pages that reference MySchedule in HTML attributes
window.MySchedule = MySchedule;

function _myScheduleInit(): void {
    MySchedule.initBookmarkButtons();
    MySchedule.updateNavBadge();
}
document.addEventListener('DOMContentLoaded', _myScheduleInit);
document.addEventListener('htmx:afterSettle', _myScheduleInit);
