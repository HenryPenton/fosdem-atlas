/* analytics.ts — CSV download, tab switcher, dual-range keyword filter */
import { alreadyBound, markBound, bindOnce } from './dom-utils.js';

// ── CSV download ───────────────────────────────────────────────────────────
function triggerBlobDownload(blob: Blob, filename: string): void {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(a.href);
}

export function downloadCsv(url: string, filename: string): void {
    fetch(url)
        .then((r) => r.blob())
        .then((blob) => triggerBlobDownload(blob, filename));
}

function bindCsvButton(btn: HTMLElement): void {
    btn.addEventListener('click', () => {
        const url = btn.dataset.csvUrl;
        const filename = btn.dataset.csvFilename;
        if (url && filename) downloadCsv(url, filename);
    });
}

function bindCsvDownloadButtons(): void {
    document.querySelectorAll<HTMLElement>('[data-csv-url]').forEach((btn) => {
        bindOnce(btn, bindCsvButton);
    });
}

// ── Tab switcher ───────────────────────────────────────────────────────────
function deactivateAllTabs(buttons: NodeListOf<HTMLElement>): void {
    buttons.forEach((b) => {
        b.classList.remove('sort-btn--active');
        b.setAttribute('aria-selected', 'false');
    });
}

function hideAllPanels(): void {
    document.querySelectorAll<HTMLElement>('.tab-panel').forEach((p) => {
        p.hidden = true;
    });
}

function activateTab(btn: HTMLElement): void {
    btn.classList.add('sort-btn--active');
    btn.setAttribute('aria-selected', 'true');
    const tabId = btn.dataset.tab;
    if (tabId) {
        const panel = document.getElementById(tabId);
        if (panel) panel.hidden = false;
    }
}

function handleTabClick(btn: HTMLElement, allButtons: NodeListOf<HTMLElement>): void {
    deactivateAllTabs(allButtons);
    hideAllPanels();
    activateTab(btn);
}

function bindTabSwitcher(): void {
    const buttons = document.querySelectorAll<HTMLElement>('[role="tab"]');
    buttons.forEach((btn) => {
        bindOnce(btn, (el) => {
            el.addEventListener('click', () => handleTabClick(el, buttons));
        });
    });
}

// ── Dual-range keyword filter ──────────────────────────────────────────────
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

function bindDualRangeFilter(): void {
    const sliderMinEl = document.getElementById('range-min') as HTMLInputElement | null;
    const sliderMaxEl = document.getElementById('range-max') as HTMLInputElement | null;
    if (!sliderMinEl || !sliderMaxEl) return;
    if (alreadyBound(sliderMinEl)) return;
    markBound(sliderMinEl);

    const sliderMin: HTMLInputElement = sliderMinEl;
    const sliderMax: HTMLInputElement = sliderMaxEl;
    const fill = document.getElementById('range-fill') as HTMLElement;
    const labelMin = document.getElementById('range-min-label') as HTMLElement;
    const labelMax = document.getElementById('range-max-label') as HTMLElement;
    const barRows = document.querySelectorAll<HTMLElement>(
        '#keyword-bar-chart .bar-row[data-keyword-count]',
    );
    const cloudTerms = document.querySelectorAll<HTMLElement>(
        '#keyword-word-cloud .word-cloud-term[data-keyword-count]',
    );
    const absMin = parseInt(sliderMin.min, 10);
    const absMax = parseInt(sliderMin.max, 10);

    function update(): void {
        const { lo, hi } = clampSliderValues(sliderMin, sliderMax);
        updateRangeLabels(labelMin, labelMax, lo, hi);
        updateRangeFill(fill, lo, hi, absMin, absMax);
        filterByCountRange(barRows, lo, hi);
        filterByCountRange(cloudTerms, lo, hi);
    }

    sliderMin.addEventListener('input', update);
    sliderMax.addEventListener('input', update);
    update();
}

// ── Init (runs on first load + every hx-boost page swap) ───────────────────
function initAnalytics(): void {
    bindCsvDownloadButtons();
    bindTabSwitcher();
    bindDualRangeFilter();
}

initAnalytics();
document.addEventListener('htmx:afterSettle', initAnalytics);
