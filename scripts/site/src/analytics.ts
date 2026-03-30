/* analytics.ts — CSV download, tab switcher, dual-range keyword filter */

// ── CSV download ───────────────────────────────────────────────────────────
export function downloadCsv(url: string, filename: string): void {
    fetch(url)
        .then((r) => r.blob())
        .then((blob) => {
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(a.href);
        });
}

// ── Init (runs on first load + every hx-boost page swap) ───────────────────
function initAnalytics(): void {
    // CSV download buttons
    document.querySelectorAll<HTMLElement>('[data-csv-url]').forEach((btn) => {
        if ((btn as HTMLElement & { _bound?: boolean })._bound) return;
        (btn as HTMLElement & { _bound?: boolean })._bound = true;
        btn.addEventListener('click', () => {
            const url = btn.dataset.csvUrl;
            const filename = btn.dataset.csvFilename;
            if (url && filename) downloadCsv(url, filename);
        });
    });

    // Tab switcher
    const buttons = document.querySelectorAll<HTMLElement>('[role="tab"]');
    buttons.forEach((btn) => {
        if ((btn as HTMLElement & { _bound?: boolean })._bound) return;
        (btn as HTMLElement & { _bound?: boolean })._bound = true;
        btn.addEventListener('click', () => {
            buttons.forEach((b) => {
                b.classList.remove('sort-btn--active');
                b.setAttribute('aria-selected', 'false');
            });
            document.querySelectorAll<HTMLElement>('.tab-panel').forEach((p) => {
                p.hidden = true;
            });
            btn.classList.add('sort-btn--active');
            btn.setAttribute('aria-selected', 'true');
            const tabId = btn.dataset.tab;
            if (tabId) {
                const panel = document.getElementById(tabId);
                if (panel) panel.hidden = false;
            }
        });
    });

    // Dual-range keyword filter
    const sliderMinEl = document.getElementById('range-min') as HTMLInputElement | null;
    const sliderMaxEl = document.getElementById('range-max') as HTMLInputElement | null;
    if (!sliderMinEl || !sliderMaxEl) return;
    if ((sliderMinEl as HTMLElement & { _bound?: boolean })._bound) return;
    (sliderMinEl as HTMLElement & { _bound?: boolean })._bound = true;
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

    function pct(val: number): number {
        return absMax === absMin ? 0 : ((val - absMin) / (absMax - absMin)) * 100;
    }

    function update(): void {
        let lo = parseInt(sliderMin.value, 10);
        let hi = parseInt(sliderMax.value, 10);
        if (lo > hi) {
            [lo, hi] = [hi, lo];
            sliderMin.value = String(lo);
            sliderMax.value = String(hi);
        }
        labelMin.textContent = String(lo);
        labelMax.textContent = String(hi);
        fill.style.left = pct(lo) + '%';
        fill.style.width = pct(hi) - pct(lo) + '%';

        barRows.forEach((row) => {
            const c = parseInt(row.dataset.keywordCount ?? '0', 10);
            row.classList.toggle('hidden', c < lo || c > hi);
        });
        cloudTerms.forEach((term) => {
            const c = parseInt(term.dataset.keywordCount ?? '0', 10);
            term.classList.toggle('hidden', c < lo || c > hi);
        });
    }

    sliderMin.addEventListener('input', update);
    sliderMax.addEventListener('input', update);
    update();
}

initAnalytics();
document.addEventListener('htmx:afterSettle', initAnalytics);
