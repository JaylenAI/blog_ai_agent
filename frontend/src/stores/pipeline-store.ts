import { create } from "zustand";
import type {
  PipelineEvent,
  PipelineRun,
  ValidationItem,
  ValidationSummary,
} from "../types/pipeline";

interface PipelineState {
  currentRun: PipelineRun | null;
  events: PipelineEvent[];
  validations: ValidationItem[];
  validationSummary: ValidationSummary | null;
  isRunning: boolean;
  error: string | null;

  setCurrentRun: (run: PipelineRun | null) => void;
  addEvent: (event: PipelineEvent) => void;
  setEvents: (events: PipelineEvent[]) => void;
  setValidations: (
    items: ValidationItem[],
    summary: ValidationSummary,
  ) => void;
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
  | "isRunning"
  | "error"
> = {
  currentRun: null,
  events: [],
  validations: [],
  validationSummary: null,
  isRunning: false,
  error: null,
};

export const usePipelineStore = create<PipelineState>((set) => ({
  ...INITIAL,

  setCurrentRun: (run) => set({ currentRun: run }),
  addEvent: (event) => set((s) => ({ events: [...s.events, event] })),
  setEvents: (events) => set({ events }),
  setValidations: (items, summary) =>
    set({ validations: items, validationSummary: summary }),
  setRunning: (running) => set({ isRunning: running }),
  setError: (error) => set({ error }),
  reset: () => set(INITIAL),
}));
