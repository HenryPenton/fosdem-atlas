/* My Schedule — localStorage helper + conflict detection */
var MySchedule = (function () {
    var KEY = 'fosdem_my_schedule';

    function getIds() {
        try {
            return JSON.parse(localStorage.getItem(KEY) || '[]');
        } catch (_) {
            return [];
        }
    }

    function save(ids) {
        localStorage.setItem(KEY, JSON.stringify(ids));
    }

    function has(id) {
        return getIds().indexOf(id) !== -1;
    }

    function add(id) {
        var ids = getIds();
        if (ids.indexOf(id) === -1) {
            ids.push(id);
            save(ids);
        }
    }

    function remove(id) {
        var ids = getIds().filter(function (x) { return x !== id; });
        save(ids);
    }

    function toggle(id) {
        if (has(id)) {
            remove(id);
            return false;
        }
        add(id);
        return true;
    }

    function clear() {
        localStorage.removeItem(KEY);
    }

    function count() {
        return getIds().length;
    }

    /**
     * Detect time conflicts among a list of events.
     * Each event needs: id, title, start_time (ISO string), duration_minutes, room.
     * Returns array of { a: event, b: event } pairs.
     */
    function detectConflicts(events) {
        var parsed = events
            .filter(function (e) { return e.start_time && e.duration_minutes; })
            .map(function (e) {
                var start = new Date(e.start_time);
                var end = new Date(start.getTime() + e.duration_minutes * 60000);
                return { id: e.id, title: e.title, room: e.room, start: start, end: end };
            })
            .sort(function (a, b) { return a.start - b.start; });

        var conflicts = [];
        for (var i = 0; i < parsed.length; i++) {
            for (var j = i + 1; j < parsed.length; j++) {
                // If j starts after i ends, no more conflicts for i
                if (parsed[j].start >= parsed[i].end) break;
                // Same room isn't a conflict the user can control — different rooms are
                if (parsed[i].room !== parsed[j].room) {
                    conflicts.push({ a: parsed[i], b: parsed[j] });
                }
            }
        }
        return conflicts;
    }

    /**
     * Init bookmark buttons on a page. Call after DOM is ready.
     * Looks for elements with data-bookmark-id attribute.
     */
    function initBookmarkButtons() {
        var buttons = document.querySelectorAll('[data-bookmark-id]');
        buttons.forEach(function (btn) {
            var id = btn.getAttribute('data-bookmark-id');
            if (has(id)) {
                btn.classList.add('bookmark-btn--active');
                btn.title = 'Remove from My Schedule';
                btn.setAttribute('aria-label', 'Remove from My Schedule');
            } else {
                btn.classList.remove('bookmark-btn--active');
                btn.title = 'Add to My Schedule';
                btn.setAttribute('aria-label', 'Add to My Schedule');
            }
            if (btn._bookmarkBound) return;
            btn._bookmarkBound = true;
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                var added = toggle(id);
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

    function updateNavBadge() {
        var badge = document.getElementById('schedule-badge');
        if (badge) {
            var c = count();
            badge.textContent = c > 0 ? c : '';
            badge.hidden = c === 0;
        }
    }

    return {
        getIds: getIds,
        has: has,
        add: add,
        remove: remove,
        toggle: toggle,
        clear: clear,
        count: count,
        detectConflicts: detectConflicts,
        initBookmarkButtons: initBookmarkButtons,
        updateNavBadge: updateNavBadge
    };
})();

// Auto-init on page load and after HTMX page swaps
function _myScheduleInit() {
    MySchedule.initBookmarkButtons();
    MySchedule.updateNavBadge();
}
document.addEventListener('DOMContentLoaded', _myScheduleInit);
document.addEventListener('htmx:afterSettle', _myScheduleInit);
