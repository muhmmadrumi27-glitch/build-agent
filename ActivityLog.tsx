"use client";

import { useState } from "react";
import {
  MousePointer,
  Keyboard,
  Camera,
  Eye,
  Brain,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Filter,
} from "lucide-react";

interface LogEntry {
  id: string;
  type: "action" | "observation" | "plan" | "error" | "security";
  message: string;
  details?: string;
  timestamp: string;
  severity?: "low" | "medium" | "high" | "critical";
}

const sampleLogs: LogEntry[] = [
  {
    id: "1",
    type: "observation",
    message: "Screen captured",
    details: "1920x1080, 24 elements detected",
    timestamp: "2024-01-15T10:00:00Z",
    severity: "low",
  },
  {
    id: "2",
    type: "plan",
    message: "Action plan created",
    details: "5 steps generated for: Open Chrome",
    timestamp: "2024-01-15T10:00:02Z",
    severity: "low",
  },
  {
    id: "3",
    type: "action",
    message: "Mouse click executed",
    details: "Position: (100, 200), Target: button",
    timestamp: "2024-01-15T10:00:05Z",
    severity: "low",
  },
  {
    id: "4",
    type: "action",
    message: "Keyboard input",
    details: "Typed: 'google.com'",
    timestamp: "2024-01-15T10:00:08Z",
    severity: "low",
  },
  {
    id: "5",
    type: "security",
    message: "URL validated",
    details: "https://google.com - Safe",
    timestamp: "2024-01-15T10:00:10Z",
    severity: "medium",
  },
  {
    id: "6",
    type: "error",
    message: "Element not found",
    details: "Retrying with alternative selector",
    timestamp: "2024-01-15T10:00:15Z",
    severity: "high",
  },
];

const typeIcons = {
  action: MousePointer,
  observation: Eye,
  plan: Brain,
  error: AlertTriangle,
  security: CheckCircle2,
};

const typeColors = {
  action: "text-blue-400",
  observation: "text-purple-400",
  plan: "text-green-400",
  error: "text-red-400",
  security: "text-yellow-400",
};

const severityColors = {
  low: "bg-gray-500/20 text-gray-400",
  medium: "bg-yellow-500/20 text-yellow-400",
  high: "bg-orange-500/20 text-orange-400",
  critical: "bg-red-500/20 text-red-400",
};

export function ActivityLog() {
  const [filter, setFilter] = useState<string>("all");
  const [logs] = useState<LogEntry[]>(sampleLogs);

  const filteredLogs = filter === "all" ? logs : logs.filter((l) => l.type === filter);

  return (
    <div className="bg-dark-card rounded-xl border border-dark-border">
      {/* Header */}
      <div className="p-4 border-b border-dark-border">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Activity Log</h3>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="bg-dark-bg border border-dark-border rounded-lg px-2 py-1 text-sm text-white focus:outline-none focus:border-primary-500"
            >
              <option value="all">All</option>
              <option value="action">Actions</option>
              <option value="observation">Observations</option>
              <option value="plan">Plans</option>
              <option value="error">Errors</option>
              <option value="security">Security</option>
            </select>
          </div>
        </div>
      </div>

      {/* Log Entries */}
      <div className="max-h-64 overflow-y-auto">
        {filteredLogs.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <Clock className="w-6 h-6 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No activity logs</p>
          </div>
        ) : (
          <div className="divide-y divide-dark-border">
            {filteredLogs.map((log) => {
              const Icon = typeIcons[log.type];
              return (
                <div key={log.id} className="p-3 hover:bg-dark-border/30 transition-colors">
                  <div className="flex items-start gap-3">
                    <div className={`mt-0.5 ${typeColors[log.type]}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-white">{log.message}</p>
                        {log.severity && (
                          <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${severityColors[log.severity]}`}>
                            {log.severity}
                          </span>
                        )}
                      </div>
                      {log.details && (
                        <p className="text-xs text-gray-400 mt-0.5">{log.details}</p>
                      )}
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
