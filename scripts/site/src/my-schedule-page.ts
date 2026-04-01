/* my-schedule-page.ts — page-specific logic for /my-schedule */
import type { Conflict } from './global.js';
import { MySchedule } from './my-schedule.js';
import { showToast, initBase } from './base.js';
import { alreadyBound, markBound } from './dom-utils.js';

// ── Time formatting ────────────────────────────────────────────────────────
function fmtTime(d: Date): string {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
}

function pctOfRange(ms: number, totalMs: number): string {
    return ((ms / totalMs) * 100).toFixed(1) + '%';
}

// ── Conflict card: header ──────────────────────────────────────────────────
function buildOverlapBadge(minutes: number): HTMLSpanElement {
    const badge = document.createElement('span');
    badge.className = 'conflict-overlap-badge';
    badge.textContent = `${minutes} min overlap`;
    return badge;
}

function buildOverlapTimeLabel(start: Date, end: Date): HTMLSpanElement {
    const span = document.createElement('span');
    span.className = 'conflict-overlap-time';
    span.textContent = `${fmtTime(start)}–${fmtTime(end)}`;
    return span;
}

function buildConflictHeader(c: Conflict): HTMLDivElement {
    const header = document.createElement('div');
    header.className = 'conflict-card-header';
    header.append(
        buildOverlapBadge(c.overlapMinutes),
        buildOverlapTimeLabel(c.overlapStart, c.overlapEnd),
    );
    return header;
}

// ── Conflict card: overlap zone ────────────────────────────────────────────
function buildOverlapZone(c: Conflict, rangeStart: number, totalMs: number): HTMLDivElement {
    const zone = document.createElement('div');
    zone.className = 'conflict-overlap-zone';
    zone.style.left = pctOfRange(c.overlapStart.getTime() - rangeStart, totalMs);
    zone.style.width = pctOfRange(c.overlapEnd.getTime() - c.overlapStart.getTime(), totalMs);
    return zone;
}

// ── Conflict card: event bar ───────────────────────────────────────────────
interface BarEvent {
    id: string;
    title: string;
    room: string;
    start: Date;
    end: Date;
}

function buildBarLink(ev: BarEvent): HTMLAnchorElement {
    const link = document.createElement('a');
    link.href = `/event/${ev.id}`;
    link.className = 'conflict-bar-label';
    link.textContent = ev.title;
    link.title = `${ev.title} · ${ev.room} · ${fmtTime(ev.start)}–${fmtTime(ev.end)}`;
    return link;
}

function buildBarTime(ev: BarEvent): HTMLSpanElement {
    const time = document.createElement('span');
    time.className = 'conflict-bar-time';
    time.textContent = `${fmtTime(ev.start)}–${fmtTime(ev.end)}`;
    return time;
}

function buildBarRoom(ev: BarEvent): HTMLSpanElement {
    const room = document.createElement('span');
    room.className = 'conflict-bar-room';
    room.textContent = ev.room;
    return room;
}

function buildBar(ev: BarEvent, rangeStart: number, totalMs: number, modifier: string): HTMLDivElement {
    const bar = document.createElement('div');
    bar.className = `conflict-bar ${modifier}`;
    bar.style.left = pctOfRange(ev.start.getTime() - rangeStart, totalMs);
    bar.style.width = pctOfRange(ev.end.getTime() - ev.start.getTime(), totalMs);
    bar.append(buildBarLink(ev), buildBarTime(ev), buildBarRoom(ev));
    return bar;
}

function buildEventBar(ev: BarEvent, rangeStart: number, totalMs: number, modifier: string): HTMLDivElement {
    const track = document.createElement('div');
    track.className = 'conflict-bar-track';
    track.appendChild(buildBar(ev, rangeStart, totalMs, modifier));
    return track;
}

// ── Conflict card: time axis ───────────────────────────────────────────────
function buildAxisTick(timestamp: number, rangeStart: number, totalMs: number): HTMLSpanElement {
    const tick = document.createElement('span');
    tick.className = 'conflict-axis-tick';
    tick.style.left = pctOfRange(timestamp - rangeStart, totalMs);
    tick.textContent = fmtTime(new Date(timestamp));
    return tick;
}

function buildTimeAxis(rangeStart: number, rangeEnd: number, totalMs: number): HTMLDivElement {
    const axis = document.createElement('div');
    axis.className = 'conflict-axis';
    axis.append(
        buildAxisTick(rangeStart, rangeStart, totalMs),
        buildAxisTick(rangeEnd, rangeStart, totalMs),
    );
    return axis;
}

// ── Conflict card: timeline ────────────────────────────────────────────────
function calcTimelineRange(c: Conflict): { rangeStart: number; rangeEnd: number; totalMs: number } {
    const rangeStart = Math.min(c.a.start.getTime(), c.b.start.getTime());
    const rangeEnd = Math.max(c.a.end.getTime(), c.b.end.getTime());
    return { rangeStart, rangeEnd, totalMs: rangeEnd - rangeStart };
}

function buildTimeline(c: Conflict, rangeStart: number, totalMs: number): HTMLDivElement {
    const timeline = document.createElement('div');
    timeline.className = 'conflict-timeline';
    timeline.append(
        buildOverlapZone(c, rangeStart, totalMs),
        buildEventBar(c.a, rangeStart, totalMs, 'conflict-bar--a'),
        buildEventBar(c.b, rangeStart, totalMs, 'conflict-bar--b'),
    );
    return timeline;
}

// ── Conflict card: assembly ────────────────────────────────────────────────
function buildConflictCard(c: Conflict): HTMLLIElement {
    const li = document.createElement('li');
    li.className = 'conflict-card';
    const { rangeStart, rangeEnd, totalMs } = calcTimelineRange(c);
    li.append(
        buildConflictHeader(c),
        buildTimeline(c, rangeStart, totalMs),
        buildTimeAxis(rangeStart, rangeEnd, totalMs),
    );
    return li;
}

// ── Conflict markers on event cards ────────────────────────────────────────
function collectConflictIds(conflicts: Conflict[]): Set<string> {
    const ids = new Set<string>();
    for (const c of conflicts) {
        ids.add(c.a.id);
        ids.add(c.b.id);
    }
    return ids;
}

function markEventAsConflicting(id: string): void {
    const btn = document.querySelector(`[data-bookmark-id="${CSS.escape(id)}"]`);
    const wrapper = btn?.closest('.grid-event-wrapper');
    if (wrapper) {
        wrapper.classList.add('grid-event-wrapper--conflict');
    }
}

function markConflictingEvents(conflicts: Conflict[]): void {
    for (const id of collectConflictIds(conflicts)) {
        markEventAsConflicting(id);
    }
}

// ── Schedule page: empty state ─────────────────────────────────────────────
function buildEmptyState(): HTMLParagraphElement {
    const empty = document.createElement('p');
    empty.className = 'empty-state';
    empty.textContent = 'No events saved yet. Browse the ';
    const link = document.createElement('a');
    link.href = '/';
    link.textContent = 'schedule';
    empty.appendChild(link);
    empty.appendChild(document.createTextNode(' and click the bookmark icon to add events.'));
    return empty;
}

// ── Schedule grid loading ──────────────────────────────────────────────────
function buildIdsParam(ids: string[]): string {
    return encodeURIComponent(ids.join(','));
}

function updateScheduleCount(countSpan: HTMLElement, ids: string[]): void {
    countSpan.textContent = ids.length + ' event' + (ids.length !== 1 ? 's' : '');
}

function updateIcalLink(icalLink: HTMLAnchorElement, ids: string[]): void {
    icalLink.href = '/my-schedule/export.ics?ids=' + buildIdsParam(ids);
}

function fetchAndRenderGrid(eventsDiv: HTMLElement, ids: string[]): void {
    fetch('/my-schedule/grid?ids=' + buildIdsParam(ids))
        .then((r) => r.text())
        .then((html) => {
            insertGridHtml(eventsDiv, html);
        })
        .catch(() => {
            showToast('Failed to load your schedule. Please try again.', 'error');
        });
}

function insertGridHtml(eventsDiv: HTMLElement, html: string): void {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    eventsDiv.replaceChildren(...Array.from(doc.body.childNodes));
    initBase();
    MySchedule.initBookmarkButtons();
}

function fetchAndShowConflicts(conflictsDiv: HTMLElement, conflictList: HTMLElement, ids: string[]): void {
    fetch('/api/v1/events/by-ids?ids=' + buildIdsParam(ids))
        .then((r) => r.json())
        .then((events: Parameters<typeof MySchedule.detectConflicts>[0]) => {
            renderConflicts(conflictsDiv, conflictList, events);
        });
}

function renderConflicts(
    conflictsDiv: HTMLElement,
    conflictList: HTMLElement,
    events: Parameters<typeof MySchedule.detectConflicts>[0],
): void {
    const conflicts = MySchedule.detectConflicts(events);
    if (conflicts.length > 0) {
        conflictsDiv.hidden = false;
        conflictList.replaceChildren(...conflicts.map(buildConflictCard));
        markConflictingEvents(conflicts);
    }
}

// ── Main page init ─────────────────────────────────────────────────────────
function initMySchedulePage(): void {
    const controls = document.getElementById('schedule-controls');
    const eventsDiv = document.getElementById('schedule-events');
    if (!controls || !eventsDiv) return;

    const countSpan = document.getElementById('schedule-count') as HTMLElement;
    const icalLink = document.getElementById('schedule-ical') as HTMLAnchorElement;
    const clearBtn = document.getElementById('schedule-clear') as HTMLButtonElement;
    const conflictsDiv = document.getElementById('schedule-conflicts') as HTMLElement;
    const conflictList = document.getElementById('conflict-list') as HTMLElement;

    function loadGrid(): void {
        const ids = MySchedule.getIds();
        if (ids.length === 0) {
            controls!.hidden = true;
            eventsDiv!.replaceChildren(buildEmptyState());
            return;
        }
        controls!.hidden = false;
        updateScheduleCount(countSpan, ids);
        updateIcalLink(icalLink, ids);
        fetchAndRenderGrid(eventsDiv!, ids);
        fetchAndShowConflicts(conflictsDiv, conflictList, ids);
    }

    if (!alreadyBound(clearBtn)) {
        markBound(clearBtn);
        clearBtn.addEventListener('click', () => {
            if (confirm('Remove all saved events?')) {
                MySchedule.clear();
                loadGrid();
            }
        });
    }

    loadGrid();
    initTransferWidget();
}

// ── Transfer widget ────────────────────────────────────────────────────────
function decodeSchedule(raw: string): string[] | null {
    try {
        const decoded = JSON.parse(atob(raw.trim())) as unknown;
        if (!Array.isArray(decoded)) return null;
        return (decoded as unknown[]).filter(
            (x): x is string | number => typeof x === 'string' || typeof x === 'number',
        ).map(String);
    } catch (_) {
        return null;
    }
}

function encodeSchedule(): string {
    const ids = MySchedule.getIds();
    return ids.length > 0
        ? btoa(JSON.stringify(ids))
        : 'Add events to your schedule to see your code here.';
}

function handleTransferCopy(exportText: HTMLElement): void {
    const ids = MySchedule.getIds();
    if (ids.length === 0) {
        showToast('No events in your schedule to export.', 'error');
        return;
    }
    navigator.clipboard.writeText(exportText.textContent ?? '').then(() => {
        showToast('Schedule code copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Could not access clipboard — copy the code above manually.', 'error');
    });
}

function handleMergeImport(importText: HTMLTextAreaElement): void {
    const ids = decodeSchedule(importText.value);
    if (!ids) {
        showToast('Invalid schedule code — please check it and try again.', 'error');
        return;
    }
    const before = MySchedule.count();
    ids.forEach((id) => MySchedule.add(id));
    const added = MySchedule.count() - before;
    showToast(`Merged: ${added} new event(s) added.`, 'success');
    importText.value = '';
    location.reload();
}

function handleOverwriteImport(importText: HTMLTextAreaElement): void {
    const ids = decodeSchedule(importText.value);
    if (!ids) {
        showToast('Invalid schedule code — please check it and try again.', 'error');
        return;
    }
    if (!confirm(`This will replace your entire schedule with ${ids.length} event(s). Continue?`)) return;
    MySchedule.clear();
    ids.forEach((id) => MySchedule.add(id));
    showToast(`Schedule replaced with ${ids.length} event(s).`, 'success');
    importText.value = '';
    location.reload();
}

function initTransferWidget(): void {
    const copyBtn = document.getElementById('transfer-copy-btn') as HTMLButtonElement | null;
    const exportText = document.getElementById('transfer-export-text') as HTMLElement | null;
    const importText = document.getElementById('transfer-import-text') as HTMLTextAreaElement | null;
    const mergeBtn = document.getElementById('transfer-merge-btn') as HTMLButtonElement | null;
    const overwriteBtn = document.getElementById('transfer-overwrite-btn') as HTMLButtonElement | null;
    if (!copyBtn || !exportText || !importText || !mergeBtn || !overwriteBtn) return;
    if (alreadyBound(copyBtn)) return;
    markBound(copyBtn);

    exportText.textContent = encodeSchedule();

    copyBtn.addEventListener('click', () => handleTransferCopy(exportText));
    mergeBtn.addEventListener('click', () => handleMergeImport(importText));
    overwriteBtn.addEventListener('click', () => handleOverwriteImport(importText));
}

// ── Public + lifecycle ─────────────────────────────────────────────────────
export function removeAndRefresh(id: string): void {
    MySchedule.remove(id);
    location.reload();
}
window.removeAndRefresh = removeAndRefresh;

initMySchedulePage();
document.addEventListener('htmx:afterSettle', initMySchedulePage);
