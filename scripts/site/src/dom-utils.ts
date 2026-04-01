/* dom-utils.ts — shared DOM binding guards and card-filter helpers */

// ── Binding guard ──────────────────────────────────────────────────────────
export type Bindable = HTMLElement & { _bound?: boolean };

export function alreadyBound(el: HTMLElement): boolean {
    return (el as Bindable)._bound === true;
}

export function markBound(el: HTMLElement): void {
    (el as Bindable)._bound = true;
}

export function bindOnce(el: HTMLElement | null, setup: (el: HTMLElement) => void): void {
    if (!el || alreadyBound(el)) return;
    markBound(el);
    setup(el);
}

// ── Card filtering (tracks + speakers) ─────────────────────────────────────
export function cardMatchesQuery(card: HTMLElement, query: string): boolean {
    return !query || (card.dataset.name ?? '').includes(query);
}

export function filterCards(cards: NodeListOf<HTMLElement>, query: string): number {
    let visible = 0;
    cards.forEach((card) => {
        const match = cardMatchesQuery(card, query);
        card.hidden = !match;
        if (match) visible++;
    });
    return visible;
}
