/* tracks.ts — client-side filter for the tracks list */
function initTrackFilter(): void {
    const input = document.getElementById('track-filter') as HTMLInputElement | null;
    if (!input || (input as HTMLElement & { _bound?: boolean })._bound) return;
    (input as HTMLElement & { _bound?: boolean })._bound = true;
    const cards = document.querySelectorAll<HTMLElement>('#tracks-list .track-card');
    const countEl = document.getElementById('tracks-count');
    input.addEventListener('input', () => {
        const q = input.value.toLowerCase().trim();
        let visible = 0;
        cards.forEach((card) => {
            const match = !q || (card.dataset.name ?? '').includes(q);
            card.hidden = !match;
            if (match) visible++;
        });
        if (countEl) {
            countEl.textContent =
                visible +
                ' track' +
                (visible !== 1 ? 's' : '') +
                (q ? ` matching \u201c${input.value}\u201d` : ' across the conference');
        }
    });
}

initTrackFilter();
document.addEventListener('htmx:afterSettle', initTrackFilter);
