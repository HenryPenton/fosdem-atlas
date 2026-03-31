/* my-schedule-page.ts — page-specific logic for /my-schedule */
import type { Conflict } from './global.js';
import { MySchedule } from './my-schedule.js';
import { showToast, initBase } from './base.js';

function fmtTime(d: Date): string {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
}

/** Build a visual timeline card for a conflict pair. */
function buildConflictCard(c: Conflict): HTMLLIElement {
    const li = document.createElement('li');
    li.className = 'conflict-card';

    const rangeStart = Math.min(c.a.start.getTime(), c.b.start.getTime());
    const rangeEnd = Math.max(c.a.end.getTime(), c.b.end.getTime());
    const totalMs = rangeEnd - rangeStart;

    const pct = (ms: number): string => ((ms / totalMs) * 100).toFixed(1) + '%';

    // Header: overlap badge + time range
    const header = document.createElement('div');
    header.className = 'conflict-card-header';
    const badge = document.createElement('span');
    badge.className = 'conflict-overlap-badge';
    badge.textContent = `${c.overlapMinutes} min overlap`;
    const timeRange = document.createElement('span');
    timeRange.className = 'conflict-overlap-time';
    timeRange.textContent = `${fmtTime(c.overlapStart)}–${fmtTime(c.overlapEnd)}`;
    header.append(badge, timeRange);

    // Timeline container
    const timeline = document.createElement('div');
    timeline.className = 'conflict-timeline';

    // Overlap zone (background stripe)
    const overlapZone = document.createElement('div');
    overlapZone.className = 'conflict-overlap-zone';
    overlapZone.style.left = pct(c.overlapStart.getTime() - rangeStart);
    overlapZone.style.width = pct(c.overlapEnd.getTime() - c.overlapStart.getTime());
    timeline.appendChild(overlapZone);

    // Bar for event A
    const barA = buildEventBar(c.a, rangeStart, totalMs, 'conflict-bar--a');
    // Bar for event B
    const barB = buildEventBar(c.b, rangeStart, totalMs, 'conflict-bar--b');
    timeline.append(barA, barB);

    // Time axis labels
    const axis = document.createElement('div');
    axis.className = 'conflict-axis';
    const times = [
        { t: rangeStart, label: fmtTime(new Date(rangeStart)) },
        { t: rangeEnd, label: fmtTime(new Date(rangeEnd)) },
    ];
    for (const { t, label } of times) {
        const tick = document.createElement('span');
        tick.className = 'conflict-axis-tick';
        tick.style.left = pct(t - rangeStart);
        tick.textContent = label;
        axis.appendChild(tick);
    }

    li.append(header, timeline, axis);
    return li;
}

function buildEventBar(
    ev: { id: string; title: string; room: string; start: Date; end: Date },
    rangeStart: number,
    totalMs: number,
    modifier: string,
): HTMLDivElement {
    const pct = (ms: number): string => ((ms / totalMs) * 100).toFixed(1) + '%';
    const track = document.createElement('div');
    track.className = 'conflict-bar-track';

    const bar = document.createElement('div');
    bar.className = `conflict-bar ${modifier}`;
    bar.style.left = pct(ev.start.getTime() - rangeStart);
    bar.style.width = pct(ev.end.getTime() - ev.start.getTime());

    const link = document.createElement('a');
    link.href = `/event/${ev.id}`;
    link.className = 'conflict-bar-label';
    link.textContent = ev.title;
    link.title = `${ev.title} · ${ev.room} · ${fmtTime(ev.start)}–${fmtTime(ev.end)}`;

    const time = document.createElement('span');
    time.className = 'conflict-bar-time';
    time.textContent = `${fmtTime(ev.start)}–${fmtTime(ev.end)}`;

    const room = document.createElement('span');
    room.className = 'conflict-bar-room';
    room.textContent = ev.room;

    bar.append(link, time, room);
    track.appendChild(bar);
    return track;
}

/** Add visual conflict markers to event cards already in the schedule grid. */
function markConflictingEvents(conflicts: Conflict[]): void {
    const conflictIds = new Set<string>();
    for (const c of conflicts) {
        conflictIds.add(c.a.id);
        conflictIds.add(c.b.id);
    }
    for (const id of conflictIds) {
        const btn = document.querySelector(`[data-bookmark-id="${CSS.escape(id)}"]`);
        const wrapper = btn?.closest('.grid-event-wrapper');
        if (wrapper) {
            wrapper.classList.add('grid-event-wrapper--conflict');
        }
    }
}

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
            const empty = document.createElement('p');
            empty.className = 'empty-state';
            empty.textContent = 'No events saved yet. Browse the ';
            const link = document.createElement('a');
            link.href = '/';
            link.textContent = 'schedule';
            empty.appendChild(link);
            empty.appendChild(document.createTextNode(' and click the bookmark icon to add events.'));
            eventsDiv!.replaceChildren(empty);
            return;
        }
        controls!.hidden = false;
        countSpan.textContent = ids.length + ' event' + (ids.length !== 1 ? 's' : '');
        icalLink.href = '/my-schedule/export.ics?ids=' + encodeURIComponent(ids.join(','));

        fetch('/my-schedule/grid?ids=' + encodeURIComponent(ids.join(',')))
            .then((r) => r.text())
            .then((html) => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                eventsDiv!.replaceChildren(...Array.from(doc.body.childNodes));
                initBase();
                MySchedule.initBookmarkButtons();
            })
            .catch(() => {
                showToast('Failed to load your schedule. Please try again.', 'error');
            });

        fetch('/api/v1/events/by-ids?ids=' + encodeURIComponent(ids.join(',')))
            .then((r) => r.json())
            .then((events: Parameters<typeof MySchedule.detectConflicts>[0]) => {
                const conflicts = MySchedule.detectConflicts(events);
                if (conflicts.length > 0) {
                    conflictsDiv.hidden = false;
                    conflictList.replaceChildren(...conflicts.map(buildConflictCard));
                    markConflictingEvents(conflicts);
                }
            });
    }

    if (!(clearBtn as HTMLElement & { _bound?: boolean })._bound) {
        (clearBtn as HTMLElement & { _bound?: boolean })._bound = true;
        clearBtn.addEventListener('click', () => {
            if (confirm('Remove all saved events?')) {
                MySchedule.clear();
                loadGrid();
            }
        });
    }

    loadGrid();

    // Schedule transfer widget
    initTransferWidget();
}

function initTransferWidget(): void {
    const copyBtn = document.getElementById('transfer-copy-btn') as HTMLButtonElement | null;
    const exportText = document.getElementById('transfer-export-text') as HTMLElement | null;
    const importText = document.getElementById('transfer-import-text') as HTMLTextAreaElement | null;
    const mergeBtn = document.getElementById('transfer-merge-btn') as HTMLButtonElement | null;
    const overwriteBtn = document.getElementById('transfer-overwrite-btn') as HTMLButtonElement | null;
    if (!copyBtn || !exportText || !importText || !mergeBtn || !overwriteBtn) return;
    if ((copyBtn as HTMLElement & { _bound?: boolean })._bound) return;
    (copyBtn as HTMLElement & { _bound?: boolean })._bound = true;

    function refreshExportCode(): void {
        const ids = MySchedule.getIds();
        exportText!.textContent =
            ids.length > 0
                ? btoa(JSON.stringify(ids))
                : 'Add events to your schedule to see your code here.';
    }

    refreshExportCode();

    copyBtn.addEventListener('click', () => {
        const ids = MySchedule.getIds();
        if (ids.length === 0) {
            showToast('No events in your schedule to export.', 'error');
            return;
        }
        navigator.clipboard.writeText(exportText!.textContent ?? '').then(() => {
            showToast('Schedule code copied to clipboard!', 'success');
        }).catch(() => {
            showToast('Could not access clipboard — copy the code above manually.', 'error');
        });
    });

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

    mergeBtn.addEventListener('click', () => {
        const ids = decodeSchedule(importText!.value);
        if (!ids) {
            showToast('Invalid schedule code — please check it and try again.', 'error');
            return;
        }
        const before = MySchedule.count();
        ids.forEach((id) => MySchedule.add(id));
        const added = MySchedule.count() - before;
        showToast(`Merged: ${added} new event(s) added.`, 'success');
        importText!.value = '';
        location.reload();
    });

    overwriteBtn.addEventListener('click', () => {
        const ids = decodeSchedule(importText!.value);
        if (!ids) {
            showToast('Invalid schedule code — please check it and try again.', 'error');
            return;
        }
        if (!confirm(`This will replace your entire schedule with ${ids.length} event(s). Continue?`)) return;
        MySchedule.clear();
        ids.forEach((id) => MySchedule.add(id));
        showToast(`Schedule replaced with ${ids.length} event(s).`, 'success');
        importText!.value = '';
        location.reload();
    });
}

// Called from server-rendered HTML onclick attributes
export function removeAndRefresh(id: string): void {
    MySchedule.remove(id);
    location.reload();
}
window.removeAndRefresh = removeAndRefresh;

initMySchedulePage();
document.addEventListener('htmx:afterSettle', initMySchedulePage);
