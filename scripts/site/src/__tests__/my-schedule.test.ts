import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
    getIds,
    add,
    remove,
    has,
    toggle,
    clear,
    count,
    detectConflicts,
} from '../my-schedule.js';

// jsdom's localStorage is broken in this vitest setup — provide a fully working mock
const _store: Record<string, string> = {};
const mockLocalStorage = {
    getItem: (key: string): string | null => _store[key] ?? null,
    setItem: (key: string, value: string): void => { _store[key] = value; },
    removeItem: (key: string): void => { delete _store[key]; },
    clear: (): void => { Object.keys(_store).forEach((k) => delete _store[k]); },
    key: (_i: number): null => null,
    length: 0,
};

beforeEach(() => {
    vi.stubGlobal('localStorage', mockLocalStorage);
    Object.keys(_store).forEach((k) => delete _store[k]);
});

afterEach(() => {
    vi.unstubAllGlobals();
});

describe('getIds', () => {
    it('returns empty array when nothing saved', () => {
        expect(getIds()).toEqual([]);
    });

    it('returns saved ids', () => {
        localStorage.setItem('fosdem_my_schedule', JSON.stringify(['1', '2']));
        expect(getIds()).toEqual(['1', '2']);
    });

    it('returns empty array on corrupt storage', () => {
        localStorage.setItem('fosdem_my_schedule', 'not-json');
        expect(getIds()).toEqual([]);
    });
});

describe('add / has / remove', () => {
    it('adds an id', () => {
        add('42');
        expect(has('42')).toBe(true);
    });

    it('does not duplicate an id', () => {
        add('42');
        add('42');
        expect(count()).toBe(1);
    });

    it('removes an id', () => {
        add('42');
        remove('42');
        expect(has('42')).toBe(false);
    });

    it('remove is a no-op for unknown id', () => {
        add('1');
        remove('99');
        expect(count()).toBe(1);
    });
});

describe('toggle', () => {
    it('adds and returns true when not present', () => {
        expect(toggle('7')).toBe(true);
        expect(has('7')).toBe(true);
    });

    it('removes and returns false when present', () => {
        add('7');
        expect(toggle('7')).toBe(false);
        expect(has('7')).toBe(false);
    });
});

describe('clear', () => {
    it('removes all ids', () => {
        add('1');
        add('2');
        clear();
        expect(getIds()).toEqual([]);
    });
});

describe('count', () => {
    it('reflects current number of saved ids', () => {
        expect(count()).toBe(0);
        add('a');
        add('b');
        expect(count()).toBe(2);
    });
});

describe('detectConflicts', () => {
    const base = '2026-02-01T10:00:00';

    it('returns empty for no events', () => {
        expect(detectConflicts([])).toEqual([]);
    });

    it('returns empty for single event', () => {
        expect(
            detectConflicts([{ id: '1', title: 'A', start_time: base, duration_minutes: 60, room: 'H.1' }]),
        ).toEqual([]);
    });

    it('detects overlap in different rooms', () => {
        const conflicts = detectConflicts([
            { id: '1', title: 'A', start_time: base, duration_minutes: 60, room: 'H.1' },
            { id: '2', title: 'B', start_time: base, duration_minutes: 60, room: 'H.2' },
        ]);
        expect(conflicts).toHaveLength(1);
        expect(conflicts[0].a.id).toBe('1');
        expect(conflicts[0].b.id).toBe('2');
        expect(conflicts[0].overlapMinutes).toBe(60);
        expect(conflicts[0].overlapStart).toEqual(new Date(base));
        expect(conflicts[0].overlapEnd).toEqual(new Date('2026-02-01T11:00:00'));
    });

    it('does not flag overlap in the same room', () => {
        const conflicts = detectConflicts([
            { id: '1', title: 'A', start_time: base, duration_minutes: 60, room: 'H.1' },
            { id: '2', title: 'B', start_time: base, duration_minutes: 60, room: 'H.1' },
        ]);
        expect(conflicts).toHaveLength(0);
    });

    it('does not flag sequential events', () => {
        const conflicts = detectConflicts([
            { id: '1', title: 'A', start_time: '2026-02-01T10:00:00', duration_minutes: 60, room: 'H.1' },
            { id: '2', title: 'B', start_time: '2026-02-01T11:00:00', duration_minutes: 60, room: 'H.2' },
        ]);
        expect(conflicts).toHaveLength(0);
    });

    it('detects partial overlap', () => {
        const conflicts = detectConflicts([
            { id: '1', title: 'A', start_time: '2026-02-01T10:00:00', duration_minutes: 60, room: 'H.1' },
            { id: '2', title: 'B', start_time: '2026-02-01T10:30:00', duration_minutes: 60, room: 'H.2' },
        ]);
        expect(conflicts).toHaveLength(1);
        expect(conflicts[0].overlapMinutes).toBe(30);
        expect(conflicts[0].overlapStart).toEqual(new Date('2026-02-01T10:30:00'));
        expect(conflicts[0].overlapEnd).toEqual(new Date('2026-02-01T11:00:00'));
    });

    it('skips events missing start_time or duration_minutes', () => {
        const conflicts = detectConflicts([
            { id: '1', title: 'A', start_time: '', duration_minutes: 60, room: 'H.1' },
            { id: '2', title: 'B', start_time: base, duration_minutes: 0, room: 'H.2' },
        ]);
        expect(conflicts).toHaveLength(0);
    });
});
