import { create } from "zustand";
import type {
  PipelineEvent,
  PipelineRun,
  ValidationItem,
  ValidationSummary,
} from "../types/pipeline";
import { PIPELINE } from "../constants/ui";

export interface SectionProgress {
  totalSections: number;
  completedSections: number;
  currentSection: number;
  currentHeading: string;
  status: "writing" | "done";
}

interface PipelineState {
  currentRun: PipelineRun | null;
  events: PipelineEvent[];
  validations: ValidationItem[];
  validationSummary: ValidationSummary | null;
  sectionProgress: SectionProgress | null;
  isRunning: boolean;
  error: string | null;

  setCurrentRun: (run: PipelineRun | null) => void;
  addEvent: (event: PipelineEvent) => void;
  setEvents: (events: PipelineEvent[]) => void;
  setValidations: (
    items: ValidationItem[],
    summary: ValidationSummary,
  ) => void;
  setSectionProgress: (progress: SectionProgress | null) => void;
  setRunning: (running: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const INITIAL: Pick<
  PipelineState,
  | "currentRun"
  | "events"
  | "validations"
  | "validationSummary"
  | "sectionProgress"
  | "isRunning"
  | "error"
> = {
  currentRun: null,
  events: [],
  validations: [],
  validationSummary: null,
  sectionProgress: null,
  isRunning: false,
  error: null,
};

export const usePipelineStore = create<PipelineState>((set) => ({
  ...INITIAL,

  setCurrentRun: (run) => set({ currentRun: run }),
  addEvent: (event) =>
    set((s) => {
      const last = s.events[s.events.length - 1];
      if (
        last &&
        last.event_type === event.event_type &&
        last.stage === event.stage &&
        last.message === event.message
      ) {
        return s;
      }
      const next = [...s.events, event];
      return { events: next.length > PIPELINE.MAX_EVENTS ? next.slice(-PIPELINE.MAX_EVENTS) : next };
    }),
  setEvents: (events) => set({ events }),
  setValidations: (items, summary) =>
    set({ validations: items, validationSummary: summary }),
  setSectionProgress: (progress) => set({ sectionProgress: progress }),
  setRunning: (running) => set({ isRunning: running }),
  setError: (error) => set({ error }),
  reset: () => set(INITIAL),
}));
