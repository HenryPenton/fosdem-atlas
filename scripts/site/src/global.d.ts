// Ambient types for functions exposed to HTML attribute handlers (onclick etc.)
export {};

declare global {
    interface Window {
        showToast: (message: string, type?: string) => void;
        removeAndRefresh: (id: string) => void;
        MySchedule: MyScheduleAPI;
    }
}

export interface EventData {
    id: string;
    title: string;
    start_time: string;
    duration_minutes: number;
    room: string;
}

export interface Conflict {
    a: ParsedEvent;
    b: ParsedEvent;
    overlapMinutes: number;
    overlapStart: Date;
    overlapEnd: Date;
}

export interface ParsedEvent {
    id: string;
    title: string;
    room: string;
    start: Date;
    end: Date;
}

export interface MyScheduleAPI {
    getIds: () => string[];
    has: (id: string) => boolean;
    add: (id: string) => void;
    remove: (id: string) => void;
    toggle: (id: string) => boolean;
    clear: () => void;
    count: () => number;
    detectConflicts: (events: EventData[]) => Conflict[];
    initBookmarkButtons: () => void;
    updateNavBadge: () => void;
}
