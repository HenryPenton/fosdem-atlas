import { describe, it, expect, beforeEach, vi } from 'vitest';
import { alreadyBound, markBound, bindOnce, cardMatchesQuery, filterCards } from '../dom-utils.js';

describe('alreadyBound / markBound', () => {
    let el: HTMLElement;

    beforeEach(() => {
        el = document.createElement('div');
    });

    it('returns false for a fresh element', () => {
        expect(alreadyBound(el)).toBe(false);
    });

    it('returns true after markBound', () => {
        markBound(el);
        expect(alreadyBound(el)).toBe(true);
    });

    it('markBound is idempotent', () => {
        markBound(el);
        markBound(el);
        expect(alreadyBound(el)).toBe(true);
    });
});

describe('bindOnce', () => {
    it('calls setup exactly once for a given element', () => {
        const el = document.createElement('div');
        const setup = vi.fn();
        bindOnce(el, setup);
        bindOnce(el, setup);
        expect(setup).toHaveBeenCalledTimes(1);
        expect(setup).toHaveBeenCalledWith(el);
    });

    it('does nothing when element is null', () => {
        const setup = vi.fn();
        bindOnce(null, setup);
        expect(setup).not.toHaveBeenCalled();
    });

    it('marks the element as bound', () => {
        const el = document.createElement('div');
        bindOnce(el, () => {});
        expect(alreadyBound(el)).toBe(true);
    });
});

describe('cardMatchesQuery', () => {
    function makeCard(name: string): HTMLElement {
        const card = document.createElement('div');
        card.dataset.name = name;
        return card;
    }

    it('matches when query is empty', () => {
        expect(cardMatchesQuery(makeCard('anything'), '')).toBe(true);
    });

    it('matches when dataset.name contains the query', () => {
        expect(cardMatchesQuery(makeCard('my-topic'), 'topic')).toBe(true);
    });

    it('does not match when dataset.name lacks the query', () => {
        expect(cardMatchesQuery(makeCard('something'), 'xyz')).toBe(false);
    });

    it('handles card with no data-name attribute', () => {
        const card = document.createElement('div');
        expect(cardMatchesQuery(card, 'foo')).toBe(false);
    });

    it('handles card with no data-name when query is empty', () => {
        const card = document.createElement('div');
        expect(cardMatchesQuery(card, '')).toBe(true);
    });
});

describe('filterCards', () => {
    function buildCardList(names: string[]): { parent: HTMLElement; cards: NodeListOf<HTMLElement> } {
        const parent = document.createElement('div');
        parent.id = 'card-container';
        names.forEach((n) => {
            const card = document.createElement('div');
            card.className = 'card';
            card.dataset.name = n;
            parent.appendChild(card);
        });
        document.body.replaceChildren(parent);
        return {
            parent,
            cards: parent.querySelectorAll<HTMLElement>('.card'),
        };
    }

    it('returns all cards visible when query is empty', () => {
        const { cards } = buildCardList(['a', 'b', 'c']);
        expect(filterCards(cards, '')).toBe(3);
        cards.forEach((c) => expect(c.hidden).toBe(false));
    });

    it('hides non-matching cards', () => {
        const { cards } = buildCardList(['go', 'rust', 'golang']);
        expect(filterCards(cards, 'go')).toBe(2);
        expect(cards[0].hidden).toBe(false); // 'go'
        expect(cards[1].hidden).toBe(true);  // 'rust'
        expect(cards[2].hidden).toBe(false); // 'golang'
    });

    it('returns 0 when nothing matches', () => {
        const { cards } = buildCardList(['a', 'b']);
        expect(filterCards(cards, 'zzz')).toBe(0);
        cards.forEach((c) => expect(c.hidden).toBe(true));
    });

    it('handles empty list', () => {
        const { cards } = buildCardList([]);
        expect(filterCards(cards, 'anything')).toBe(0);
    });
});
