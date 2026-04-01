/* my-schedule.ts — localStorage helper + conflict detection */
import type { EventData, Conflict, ParsedEvent } from './global.js';

const KEY = 'fosdem_my_schedule';

// ── Local storage CRUD ─────────────────────────────────────────────────────
function readStorage(): string {
    return localStorage.getItem(KEY) ?? '[]';
}

function parseIds(raw: string): string[] {
    try {
        return JSON.parse(raw) as string[];
    } catch (_) {
        return [];
    }
}

export function getIds(): string[] {
    return parseIds(readStorage());
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

// ── Conflict detection helpers ─────────────────────────────────────────────
function hasValidTiming(e: EventData): boolean {
    return !!e.start_time && !!e.duration_minutes;
}

function toParseEvent(e: EventData): ParsedEvent {
    const start = new Date(e.start_time);
    const end = new Date(start.getTime() + e.duration_minutes * 60000);
    return { id: e.id, title: e.title, room: e.room, start, end };
}

function parseAndSort(events: EventData[]): ParsedEvent[] {
    return events
        .filter(hasValidTiming)
        .map(toParseEvent)
        .sort((a, b) => a.start.getTime() - b.start.getTime());
}

function eventsOverlap(a: ParsedEvent, b: ParsedEvent): boolean {
    return b.start < a.end;
}

function inDifferentRooms(a: ParsedEvent, b: ParsedEvent): boolean {
    return a.room !== b.room;
}

function calcOverlapStart(a: ParsedEvent, b: ParsedEvent): Date {
    return new Date(Math.max(a.start.getTime(), b.start.getTime()));
}

function calcOverlapEnd(a: ParsedEvent, b: ParsedEvent): Date {
    return new Date(Math.min(a.end.getTime(), b.end.getTime()));
}

function calcOverlapMinutes(overlapStart: Date, overlapEnd: Date): number {
    return Math.round((overlapEnd.getTime() - overlapStart.getTime()) / 60000);
}

function buildConflict(a: ParsedEvent, b: ParsedEvent): Conflict {
    const overlapStart = calcOverlapStart(a, b);
    const overlapEnd = calcOverlapEnd(a, b);
    return {
        a,
        b,
        overlapMinutes: calcOverlapMinutes(overlapStart, overlapEnd),
        overlapStart,
        overlapEnd,
    };
}

export function detectConflicts(events: EventData[]): Conflict[] {
    const parsed = parseAndSort(events);
    const conflicts: Conflict[] = [];
    for (let i = 0; i < parsed.length; i++) {
        for (let j = i + 1; j < parsed.length; j++) {
            if (!eventsOverlap(parsed[i], parsed[j])) break;
            if (inDifferentRooms(parsed[i], parsed[j])) {
                conflicts.push(buildConflict(parsed[i], parsed[j]));
            }
        }
    }
    return conflicts;
}

// ── Bookmark button UI ─────────────────────────────────────────────────────
type BookmarkBindable = HTMLElement & { _bookmarkBound?: boolean };

function isBookmarkBound(el: HTMLElement): boolean {
    return (el as BookmarkBindable)._bookmarkBound === true;
}

function markBookmarkBound(el: HTMLElement): void {
    (el as BookmarkBindable)._bookmarkBound = true;
}

function setBookmarkActive(btn: HTMLElement): void {
    btn.classList.add('bookmark-btn--active');
    btn.title = 'Remove from My Schedule';
    btn.setAttribute('aria-label', 'Remove from My Schedule');
}

function setBookmarkInactive(btn: HTMLElement): void {
    btn.classList.remove('bookmark-btn--active');
    btn.title = 'Add to My Schedule';
    btn.setAttribute('aria-label', 'Add to My Schedule');
}

function syncBookmarkState(btn: HTMLElement, id: string): void {
    if (has(id)) {
        setBookmarkActive(btn);
    } else {
        setBookmarkInactive(btn);
    }
}

function handleBookmarkClick(btn: HTMLElement, id: string): void {
    const added = toggle(id);
    if (added) {
        setBookmarkActive(btn);
    } else {
        setBookmarkInactive(btn);
    }
    updateNavBadge();
}

function bindBookmarkButton(btn: HTMLElement): void {
    const id = btn.getAttribute('data-bookmark-id') ?? '';
    syncBookmarkState(btn, id);
    if (isBookmarkBound(btn)) return;
    markBookmarkBound(btn);
    btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        handleBookmarkClick(btn, id);
    });
}

export function initBookmarkButtons(): void {
    document.querySelectorAll<HTMLElement>('[data-bookmark-id]').forEach(bindBookmarkButton);
}

// ── Nav badge ──────────────────────────────────────────────────────────────
export function updateNavBadge(): void {
    const badge = document.getElementById('schedule-badge');
    if (badge) {
        const c = count();
        badge.textContent = c > 0 ? String(c) : '';
        badge.hidden = c === 0;
    }
}

// ── Public API ─────────────────────────────────────────────────────────────
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
