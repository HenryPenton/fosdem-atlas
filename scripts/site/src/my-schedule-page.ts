/* my-schedule-page.ts — page-specific logic for /my-schedule */
import { MySchedule } from './my-schedule.js';
import { showToast } from './base.js';

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
                    const items = conflicts.map((c) => {
                        const li = document.createElement('li');
                        li.className = 'conflict-item';
                        const linkA = document.createElement('a');
                        linkA.href = `/event/${c.a.id}`;
                        linkA.textContent = c.a.title;
                        const linkB = document.createElement('a');
                        linkB.href = `/event/${c.b.id}`;
                        linkB.textContent = c.b.title;
                        const detail = document.createElement('span');
                        detail.className = 'conflict-detail';
                        detail.textContent = `(${c.a.room} / ${c.b.room})`;
                        li.append(linkA, ' conflicts with ', linkB, ' ', detail);
                        return li;
                    });
                    conflictList.replaceChildren(...items);
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
