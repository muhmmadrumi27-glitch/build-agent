import { create } from "zustand";

interface AgentState {
  status: {
    status: string;
    current_task: string | null;
    current_step: number | null;
    session_id: string | null;
    total_actions: number;
    successful_actions: number;
    failed_actions: number;
  } | null;
  screenshot: string | null;
  analysis: any | null;
  isAnalyzing: boolean;
  ws: WebSocket | null;
  isConnected: boolean;

  // Actions
  connect: () => void;
  disconnect: () => void;
  takeScreenshot: () => void;
  analyzeScreen: () => void;
  runTask: (goal: string) => Promise<void>;
  pauseTask: () => void;
  resumeTask: () => void;
  stopTask: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";

export const useAgentStore = create<AgentState>((set, get) => ({
  status: null,
  screenshot: null,
  analysis: null,
  isAnalyzing: false,
  ws: null,
  isConnected: false,

  connect: () => {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log("WebSocket connected");
      set({ ws, isConnected: true });
      // Request initial status
      ws.send(JSON.stringify({ action: "get_status" }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case "status":
          set({ status: data.data });
          break;
        case "screenshot":
          set({ screenshot: data.data.screenshot_path, analysis: data.data.analysis });
          break;
        case "task_started":
        case "step_started":
        case "step_completed":
        case "task_completed":
          // Update status on task events
          ws.send(JSON.stringify({ action: "get_status" }));
          break;
        case "final_result":
          set({ status: { ...get().status, status: "idle" } as any });
          break;
      }
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      set({ ws: null, isConnected: false });
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      set({ isConnected: false });
    };
  },

  disconnect: () => {
    const { ws } = get();
    if (ws) {
      ws.close();
    }
  },

  takeScreenshot: () => {
    const { ws } = get();
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: "screenshot" }));
    }
  },

  analyzeScreen: () => {
    set({ isAnalyzing: true });
    const { ws } = get();
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: "screenshot" }));
    }
    setTimeout(() => set({ isAnalyzing: false }), 2000);
  },

  runTask: async (goal: string) => {
    const { ws } = get();
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        action: "run_task",
        goal,
      }));
    }
  },

  pauseTask: () => {
    const { ws } = get();
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: "pause" }));
    }
  },

  resumeTask: () => {
    const { ws } = get();
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: "resume" }));
    }
  },

  stopTask: () => {
    const { ws } = get();
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: "stop" }));
    }
  },
}));
