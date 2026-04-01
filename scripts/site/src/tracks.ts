/* tracks.ts — client-side filter for the tracks list */
import { alreadyBound, markBound, filterCards } from './dom-utils.js';

function getTrackFilterInput(): HTMLInputElement | null {
    return document.getElementById('track-filter') as HTMLInputElement | null;
}

function getTrackCards(): NodeListOf<HTMLElement> {
    return document.querySelectorAll<HTMLElement>('#tracks-list .track-card');
}

function getTracksCountEl(): HTMLElement | null {
    return document.getElementById('tracks-count');
}

function formatTrackCount(visible: number, rawQuery: string): string {
    const suffix = visible !== 1 ? 's' : '';
    const context = rawQuery
        ? ` matching \u201c${rawQuery}\u201d`
        : ' across the conference';
    return `${visible} track${suffix}${context}`;
}

function updateTracksCount(countEl: HTMLElement | null, visible: number, rawQuery: string): void {
    if (countEl) {
        countEl.textContent = formatTrackCount(visible, rawQuery);
    }
}

function handleTrackFilterInput(
    input: HTMLInputElement,
    cards: NodeListOf<HTMLElement>,
    countEl: HTMLElement | null,
): void {
    const q = input.value.toLowerCase().trim();
    const visible = filterCards(cards, q);
    updateTracksCount(countEl, visible, q ? input.value : '');
}

function initTrackFilter(): void {
    const input = getTrackFilterInput();
    if (!input || alreadyBound(input)) return;
    markBound(input);
    const cards = getTrackCards();
    const countEl = getTracksCountEl();
    input.addEventListener('input', () => handleTrackFilterInput(input, cards, countEl));
}

initTrackFilter();
document.addEventListener('htmx:afterSettle', initTrackFilter);
