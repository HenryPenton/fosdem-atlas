/* speakers.ts — client-side filter for the speakers list */
function initSpeakerFilter(): void {
    const input = document.getElementById('speaker-filter') as HTMLInputElement | null;
    if (!input || (input as HTMLElement & { _bound?: boolean })._bound) return;
    (input as HTMLElement & { _bound?: boolean })._bound = true;
    const cards = document.querySelectorAll<HTMLElement>('#speakers-list .track-card');
    const countEl = document.getElementById('speakers-count');
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
                ' speaker' +
                (visible !== 1 ? 's' : '') +
                (q ? ` matching \u201c${input.value}\u201d` : " at this year's conference");
        }
    });
}

initSpeakerFilter();
document.addEventListener('htmx:afterSettle', initSpeakerFilter);
