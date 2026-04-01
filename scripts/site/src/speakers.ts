/* speakers.ts — client-side filter for the speakers list */
import { alreadyBound, markBound, filterCards } from './dom-utils.js';

function getSpeakerFilterInput(): HTMLInputElement | null {
    return document.getElementById('speaker-filter') as HTMLInputElement | null;
}

function getSpeakerCards(): NodeListOf<HTMLElement> {
    return document.querySelectorAll<HTMLElement>('#speakers-list .track-card');
}

function getSpeakersCountEl(): HTMLElement | null {
    return document.getElementById('speakers-count');
}

function formatSpeakerCount(visible: number, rawQuery: string): string {
    const suffix = visible !== 1 ? 's' : '';
    const context = rawQuery
        ? ` matching \u201c${rawQuery}\u201d`
        : " at this year's conference";
    return `${visible} speaker${suffix}${context}`;
}

function updateSpeakersCount(countEl: HTMLElement | null, visible: number, rawQuery: string): void {
    if (countEl) {
        countEl.textContent = formatSpeakerCount(visible, rawQuery);
    }
}

function handleSpeakerFilterInput(
    input: HTMLInputElement,
    cards: NodeListOf<HTMLElement>,
    countEl: HTMLElement | null,
): void {
    const q = input.value.toLowerCase().trim();
    const visible = filterCards(cards, q);
    updateSpeakersCount(countEl, visible, q ? input.value : '');
}

function initSpeakerFilter(): void {
    const input = getSpeakerFilterInput();
    if (!input || alreadyBound(input)) return;
    markBound(input);
    const cards = getSpeakerCards();
    const countEl = getSpeakersCountEl();
    input.addEventListener('input', () => handleSpeakerFilterInput(input, cards, countEl));
}

initSpeakerFilter();
document.addEventListener('htmx:afterSettle', initSpeakerFilter);
