"use client";

import { useState } from "react";
import { useAgentStore } from "@/store/agentStore";
import {
  Play,
  Pause,
  Square,
  Plus,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
} from "lucide-react";
import toast from "react-hot-toast";

interface Task {
  id: string;
  goal: string;
  status: "pending" | "running" | "paused" | "completed" | "failed";
  progress: number;
  createdAt: string;
}

export function TaskQueue() {
  const { status, runTask, pauseTask, resumeTask, stopTask } = useAgentStore();
  const [newTask, setNewTask] = useState("");
  const [tasks, setTasks] = useState<Task[]>([
    {
      id: "1",
      goal: "Open Chrome and navigate to Google",
      status: "completed",
      progress: 100,
      createdAt: "2024-01-15T10:00:00Z",
    },
    {
      id: "2",
      goal: "Search for latest news",
      status: "running",
      progress: 45,
      createdAt: "2024-01-15T10:05:00Z",
    },
  ]);

  const handleAddTask = async () => {
    if (!newTask.trim()) {
      toast.error("Please enter a task goal");
      return;
    }

    const task: Task = {
      id: Date.now().toString(),
      goal: newTask,
      status: "pending",
      progress: 0,
      createdAt: new Date().toISOString(),
    };

    setTasks([...tasks, task]);
    setNewTask("");
    toast.success("Task added to queue");

    // Start task execution
    try {
      await runTask(newTask);
      toast.success("Task completed successfully");
    } catch (error) {
      toast.error("Task failed");
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "running":
        return <Loader2 className="w-4 h-4 text-yellow-400 animate-spin" />;
      case "completed":
        return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      case "failed":
        return <XCircle className="w-4 h-4 text-red-400" />;
      case "paused":
        return <Pause className="w-4 h-4 text-orange-400" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return "bg-yellow-500/20 text-yellow-400";
      case "completed":
        return "bg-green-500/20 text-green-400";
      case "failed":
        return "bg-red-500/20 text-red-400";
      case "paused":
        return "bg-orange-500/20 text-orange-400";
      default:
        return "bg-gray-500/20 text-gray-400";
    }
  };

  return (
    <div className="bg-dark-card rounded-xl border border-dark-border">
      {/* Header */}
      <div className="p-4 border-b border-dark-border">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-white">Task Queue</h3>
          <div className="flex items-center gap-2">
            {status?.status === "executing" ? (
              <>
                <button
                  onClick={pauseTask}
                  className="p-1.5 rounded-lg bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 transition-colors"
                >
                  <Pause className="w-4 h-4" />
                </button>
                <button
                  onClick={stopTask}
                  className="p-1.5 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
                >
                  <Square className="w-4 h-4" />
                </button>
              </>
            ) : (
              <button
                onClick={resumeTask}
                className="p-1.5 rounded-lg bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors"
              >
                <Play className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Add Task Input */}
        <div className="flex gap-2">
          <input
            type="text"
            value={newTask}
            onChange={(e) => setNewTask(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAddTask()}
            placeholder="Enter task goal..."
            className="flex-1 bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
          />
          <button
            onClick={handleAddTask}
            className="px-3 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Task List */}
      <div className="max-h-80 overflow-y-auto">
        {tasks.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No tasks in queue</p>
          </div>
        ) : (
          <div className="divide-y divide-dark-border">
            {tasks.map((task) => (
              <div key={task.id} className="p-4 hover:bg-dark-border/50 transition-colors">
                <div className="flex items-start gap-3">
                  {getStatusIcon(task.status)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{task.goal}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                        {task.status}
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(task.createdAt).toLocaleTimeString()}
                      </span>
                    </div>
                    {task.status === "running" && (
                      <div className="mt-2">
                        <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary-500 rounded-full transition-all"
                            style={{ width: `${task.progress}%` }}
                          />
                        </div>
                        <p className="text-xs text-gray-400 mt-1">{task.progress}% complete</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
