"use client";

import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Activity,
} from "lucide-react";

const data = [
  { time: "00:00", actions: 12, errors: 1, success: 91 },
  { time: "04:00", actions: 8, errors: 0, success: 100 },
  { time: "08:00", actions: 45, errors: 2, success: 95 },
  { time: "12:00", actions: 78, errors: 3, success: 96 },
  { time: "16:00", actions: 62, errors: 1, success: 98 },
  { time: "20:00", actions: 35, errors: 2, success: 94 },
  { time: "23:59", actions: 20, errors: 0, success: 100 },
];

export function StatsChart() {
  const [chartType, setChartType] = useState<"actions" | "success">("actions");

  const totalActions = data.reduce((sum, d) => sum + d.actions, 0);
  const avgSuccess = Math.round(data.reduce((sum, d) => sum + d.success, 0) / data.length);
  const totalErrors = data.reduce((sum, d) => sum + d.errors, 0);

  return (
    <div className="bg-dark-card rounded-xl border border-dark-border p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white">Performance Metrics</h3>
          <p className="text-sm text-gray-400 mt-1">Last 24 hours</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setChartType("actions")}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              chartType === "actions"
                ? "bg-primary-500/20 text-primary-400"
                : "text-gray-400 hover:bg-dark-border"
            }`}
          >
            Actions
          </button>
          <button
            onClick={() => setChartType("success")}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              chartType === "success"
                ? "bg-primary-500/20 text-primary-400"
                : "text-gray-400 hover:bg-dark-border"
            }`}
          >
            Success Rate
          </button>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-dark-bg rounded-lg p-3">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-blue-400" />
            <span className="text-xs text-gray-400">Total Actions</span>
          </div>
          <p className="text-xl font-bold text-white mt-1">{totalActions}</p>
          <div className="flex items-center gap-1 mt-1">
            <TrendingUp className="w-3 h-3 text-green-400" />
            <span className="text-xs text-green-400">+12%</span>
          </div>
        </div>
        <div className="bg-dark-bg rounded-lg p-3">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-green-400" />
            <span className="text-xs text-gray-400">Success Rate</span>
          </div>
          <p className="text-xl font-bold text-white mt-1">{avgSuccess}%</p>
          <div className="flex items-center gap-1 mt-1">
            <TrendingUp className="w-3 h-3 text-green-400" />
            <span className="text-xs text-green-400">+3%</span>
          </div>
        </div>
        <div className="bg-dark-bg rounded-lg p-3">
          <div className="flex items-center gap-2">
            <TrendingDown className="w-4 h-4 text-red-400" />
            <span className="text-xs text-gray-400">Errors</span>
          </div>
          <p className="text-xl font-bold text-white mt-1">{totalErrors}</p>
          <div className="flex items-center gap-1 mt-1">
            <TrendingDown className="w-3 h-3 text-green-400" />
            <span className="text-xs text-green-400">-5%</span>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === "actions" ? (
            <AreaChart data={data}>
              <defs>
                <linearGradient id="actionsGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="time" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                  color: "#fff",
                }}
              />
              <Area
                type="monotone"
                dataKey="actions"
                stroke="#3b82f6"
                fill="url(#actionsGradient)"
                strokeWidth={2}
              />
            </AreaChart>
          ) : (
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="time" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} domain={[80, 100]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                  color: "#fff",
                }}
              />
              <Line
                type="monotone"
                dataKey="success"
                stroke="#10b981"
                strokeWidth={2}
                dot={{ fill: "#10b981", strokeWidth: 2 }}
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
