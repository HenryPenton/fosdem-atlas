import { describe, it, expect, beforeEach } from 'vitest';

// Mirror pure functions from analytics.ts (not exported)
function calcPct(val: number, absMin: number, absMax: number): number {
    return absMax === absMin ? 0 : ((val - absMin) / (absMax - absMin)) * 100;
}

function clampSliderValues(
    sliderMin: HTMLInputElement,
    sliderMax: HTMLInputElement,
): { lo: number; hi: number } {
    let lo = parseInt(sliderMin.value, 10);
    let hi = parseInt(sliderMax.value, 10);
    if (lo > hi) {
        [lo, hi] = [hi, lo];
        sliderMin.value = String(lo);
        sliderMax.value = String(hi);
    }
    return { lo, hi };
}

function updateRangeLabels(labelMin: HTMLElement, labelMax: HTMLElement, lo: number, hi: number): void {
    labelMin.textContent = String(lo);
    labelMax.textContent = String(hi);
}

function updateRangeFill(fill: HTMLElement, lo: number, hi: number, absMin: number, absMax: number): void {
    fill.style.left = calcPct(lo, absMin, absMax) + '%';
    fill.style.width = (calcPct(hi, absMin, absMax) - calcPct(lo, absMin, absMax)) + '%';
}

function filterByCountRange(
    elements: NodeListOf<HTMLElement>,
    lo: number,
    hi: number,
): void {
    elements.forEach((el) => {
        const c = parseInt(el.dataset.keywordCount ?? '0', 10);
        el.classList.toggle('hidden', c < lo || c > hi);
    });
}

// ── calcPct ────────────────────────────────────────────────────────────────
describe('calcPct', () => {
    it('returns 0 when absMin equals absMax', () => {
        expect(calcPct(5, 5, 5)).toBe(0);
    });

    it('returns 0 at the minimum', () => {
        expect(calcPct(0, 0, 100)).toBe(0);
    });

    it('returns 100 at the maximum', () => {
        expect(calcPct(100, 0, 100)).toBe(100);
    });

    it('returns 50 at midpoint', () => {
        expect(calcPct(50, 0, 100)).toBe(50);
    });

    it('works with non-zero min', () => {
        expect(calcPct(15, 10, 20)).toBe(50);
    });
});

// ── clampSliderValues ──────────────────────────────────────────────────────
describe('clampSliderValues', () => {
    function makeSlider(val: string): HTMLInputElement {
        const input = document.createElement('input');
        input.type = 'range';
        input.value = val;
        return input;
    }

    it('returns lo/hi in order when already correct', () => {
        const min = makeSlider('3');
        const max = makeSlider('7');
        expect(clampSliderValues(min, max)).toEqual({ lo: 3, hi: 7 });
    });

    it('swaps values when min > max', () => {
        const min = makeSlider('9');
        const max = makeSlider('2');
        const result = clampSliderValues(min, max);
        expect(result).toEqual({ lo: 2, hi: 9 });
        expect(min.value).toBe('2');
        expect(max.value).toBe('9');
    });

    it('handles equal values', () => {
        const min = makeSlider('5');
        const max = makeSlider('5');
        expect(clampSliderValues(min, max)).toEqual({ lo: 5, hi: 5 });
    });
});

// ── updateRangeLabels ──────────────────────────────────────────────────────
describe('updateRangeLabels', () => {
    it('sets textContent of both labels', () => {
        const minLabel = document.createElement('span');
        const maxLabel = document.createElement('span');
        updateRangeLabels(minLabel, maxLabel, 3, 10);
        expect(minLabel.textContent).toBe('3');
        expect(maxLabel.textContent).toBe('10');
    });
});

// ── updateRangeFill ────────────────────────────────────────────────────────
describe('updateRangeFill', () => {
    it('sets left and width styles based on range percentages', () => {
        const fill = document.createElement('div');
        updateRangeFill(fill, 25, 75, 0, 100);
        expect(fill.style.left).toBe('25%');
        expect(fill.style.width).toBe('50%');
    });

    it('handles full range', () => {
        const fill = document.createElement('div');
        updateRangeFill(fill, 0, 100, 0, 100);
        expect(fill.style.left).toBe('0%');
        expect(fill.style.width).toBe('100%');
    });

    it('handles collapsed range', () => {
        const fill = document.createElement('div');
        updateRangeFill(fill, 50, 50, 0, 100);
        expect(fill.style.left).toBe('50%');
        expect(fill.style.width).toBe('0%');
    });
});

// ── filterByCountRange ─────────────────────────────────────────────────────
describe('filterByCountRange', () => {
    function buildRows(counts: number[]): NodeListOf<HTMLElement> {
        const container = document.createElement('div');
        counts.forEach((c) => {
            const el = document.createElement('div');
            el.className = 'bar-row';
            el.dataset.keywordCount = String(c);
            container.appendChild(el);
        });
        document.body.replaceChildren(container);
        return container.querySelectorAll<HTMLElement>('.bar-row');
    }

    it('shows rows within range', () => {
        const rows = buildRows([1, 5, 10, 15]);
        filterByCountRange(rows, 5, 10);
        expect(rows[0].classList.contains('hidden')).toBe(true);  // 1
        expect(rows[1].classList.contains('hidden')).toBe(false); // 5
        expect(rows[2].classList.contains('hidden')).toBe(false); // 10
        expect(rows[3].classList.contains('hidden')).toBe(true);  // 15
    });

    it('shows all when range covers everything', () => {
        const rows = buildRows([2, 4, 6]);
        filterByCountRange(rows, 1, 10);
        rows.forEach((r) => expect(r.classList.contains('hidden')).toBe(false));
    });

    it('hides all when range excludes everything', () => {
        const rows = buildRows([2, 4, 6]);
        filterByCountRange(rows, 100, 200);
        rows.forEach((r) => expect(r.classList.contains('hidden')).toBe(true));
    });

    it('handles missing data-keyword-count (defaults to 0)', () => {
        const container = document.createElement('div');
        const el = document.createElement('div');
        el.className = 'bar-row';
        container.appendChild(el);
        document.body.replaceChildren(container);
        const rows = container.querySelectorAll<HTMLElement>('.bar-row');
        filterByCountRange(rows, 0, 0);
        expect(rows[0].classList.contains('hidden')).toBe(false);
    });
});

// ── pctOfRange (from my-schedule-page.ts) ──────────────────────────────────
function pctOfRange(ms: number, totalMs: number): string {
    return ((ms / totalMs) * 100).toFixed(1) + '%';
}

describe('pctOfRange', () => {
    it('returns 0.0% at start', () => {
        expect(pctOfRange(0, 1000)).toBe('0.0%');
    });

    it('returns 100.0% for full range', () => {
        expect(pctOfRange(1000, 1000)).toBe('100.0%');
    });

    it('returns 50.0% at midpoint', () => {
        expect(pctOfRange(500, 1000)).toBe('50.0%');
    });

    it('rounds to one decimal place', () => {
        expect(pctOfRange(333, 1000)).toBe('33.3%');
    });
});
