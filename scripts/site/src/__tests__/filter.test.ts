import { describe, it, expect, beforeEach } from 'vitest';
import { filterCards, cardMatchesQuery } from '../dom-utils.js';

// Pure functions inlined from tracks.ts / speakers.ts (not exported, so we mirror them)
function formatTrackCount(visible: number, rawQuery: string): string {
    const suffix = visible !== 1 ? 's' : '';
    const context = rawQuery
        ? ` matching \u201c${rawQuery}\u201d`
        : ' across the conference';
    return `${visible} track${suffix}${context}`;
}

function formatSpeakerCount(visible: number, rawQuery: string): string {
    const suffix = visible !== 1 ? 's' : '';
    const context = rawQuery
        ? ` matching \u201c${rawQuery}\u201d`
        : " at this year's conference";
    return `${visible} speaker${suffix}${context}`;
}

// ── formatTrackCount ───────────────────────────────────────────────────────
describe('formatTrackCount', () => {
    it('singular with no query', () => {
        expect(formatTrackCount(1, '')).toBe('1 track across the conference');
    });

    it('plural with no query', () => {
        expect(formatTrackCount(5, '')).toBe('5 tracks across the conference');
    });

    it('zero tracks with no query', () => {
        expect(formatTrackCount(0, '')).toBe('0 tracks across the conference');
    });

    it('includes query in output', () => {
        expect(formatTrackCount(3, 'go')).toBe('3 tracks matching \u201cgo\u201d');
    });

    it('singular with query', () => {
        expect(formatTrackCount(1, 'rust')).toBe('1 track matching \u201crust\u201d');
    });
});

// ── formatSpeakerCount ─────────────────────────────────────────────────────
describe('formatSpeakerCount', () => {
    it('singular with no query', () => {
        expect(formatSpeakerCount(1, '')).toBe("1 speaker at this year's conference");
    });

    it('plural with no query', () => {
        expect(formatSpeakerCount(12, '')).toBe("12 speakers at this year's conference");
    });

    it('includes query in output', () => {
        expect(formatSpeakerCount(2, 'alice')).toBe('2 speakers matching \u201calice\u201d');
    });
});

// ── Track filter integration ───────────────────────────────────────────────
describe('track filter integration', () => {
    function setupTrackDom(names: string[]): {
        input: HTMLInputElement;
        cards: NodeListOf<HTMLElement>;
        countEl: HTMLElement;
    } {
        document.body.innerHTML = `
            <input id="track-filter" type="text" />
            <span id="tracks-count"></span>
            <div id="tracks-list">
                ${names.map((n) => `<div class="track-card" data-name="${n}">${n}</div>`).join('')}
            </div>
        `;
        return {
            input: document.getElementById('track-filter') as HTMLInputElement,
            cards: document.querySelectorAll<HTMLElement>('#tracks-list .track-card'),
            countEl: document.getElementById('tracks-count') as HTMLElement,
        };
    }

    it('shows all cards when input is empty', () => {
        const { cards } = setupTrackDom(['go', 'rust', 'python']);
        const visible = filterCards(cards, '');
        expect(visible).toBe(3);
    });

    it('filters to matching cards', () => {
        const { cards } = setupTrackDom(['golang', 'rust', 'go-workshop']);
        const visible = filterCards(cards, 'go');
        expect(visible).toBe(2);
        expect((cards[1] as HTMLElement).hidden).toBe(true);
    });
});

// ── Speaker filter integration ─────────────────────────────────────────────
describe('speaker filter integration', () => {
    function setupSpeakerDom(names: string[]): {
        input: HTMLInputElement;
        cards: NodeListOf<HTMLElement>;
        countEl: HTMLElement;
    } {
        document.body.innerHTML = `
            <input id="speaker-filter" type="text" />
            <span id="speakers-count"></span>
            <div id="speakers-list">
                ${names.map((n) => `<div class="track-card" data-name="${n}">${n}</div>`).join('')}
            </div>
        `;
        return {
            input: document.getElementById('speaker-filter') as HTMLInputElement,
            cards: document.querySelectorAll<HTMLElement>('#speakers-list .track-card'),
            countEl: document.getElementById('speakers-count') as HTMLElement,
        };
    }

    it('shows all speaker cards when input is empty', () => {
        const { cards } = setupSpeakerDom(['alice', 'bob']);
        expect(filterCards(cards, '')).toBe(2);
    });

    it('hides non-matching speaker cards', () => {
        const { cards } = setupSpeakerDom(['alice', 'bob', 'alicia']);
        expect(filterCards(cards, 'ali')).toBe(2);
        expect((cards[1] as HTMLElement).hidden).toBe(true);
    });
});
