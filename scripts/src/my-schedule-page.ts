/* my-schedule-page.ts — page-specific logic for /my-schedule */
import { MySchedule } from './my-schedule.js';
import { showToast } from './base.js';

function esc(s: string | number): string {
    const d = document.createElement('div');
    d.appendChild(document.createTextNode(String(s)));
    return d.innerHTML;
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
            eventsDiv!.innerHTML =
                '<p class="empty-state">No events saved yet. Browse the <a href="/">schedule</a> and click the bookmark icon to add events.</p>';
            return;
        }
        controls!.hidden = false;
        countSpan.textContent = ids.length + ' event' + (ids.length !== 1 ? 's' : '');
        icalLink.href = '/my-schedule/export.ics?ids=' + encodeURIComponent(ids.join(','));

        fetch('/my-schedule/grid?ids=' + encodeURIComponent(ids.join(',')))
            .then((r) => r.text())
            .then((html) => {
                eventsDiv!.innerHTML = html;
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
                    conflictList.innerHTML = conflicts
                        .map(
                            (c) =>
                                `<li class="conflict-item">` +
                                `<a href="/event/${esc(c.a.id)}">${esc(c.a.title)}</a>` +
                                ` conflicts with ` +
                                `<a href="/event/${esc(c.b.id)}">${esc(c.b.title)}</a>` +
                                ` <span class="conflict-detail">(${esc(c.a.room)} / ${esc(c.b.room)})</span>` +
                                `</li>`,
                        )
                        .join('');
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
