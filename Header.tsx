"use client";

import { useState } from "react";
import {
  Bell,
  Search,
  User,
  LogOut,
  Moon,
  Sun,
} from "lucide-react";

export function Header() {
  const [darkMode, setDarkMode] = useState(true);
  const [notifications, setNotifications] = useState([
    { id: 1, title: "Task completed", message: "Screenshot analysis finished", time: "2m ago" },
    { id: 2, title: "Security alert", message: "High risk action detected", time: "5m ago" },
  ]);
  const [showNotifications, setShowNotifications] = useState(false);

  return (
    <header className="h-16 bg-dark-card border-b border-dark-border flex items-center justify-between px-6">
      {/* Search */}
      <div className="flex items-center gap-4">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search tasks, sessions..."
            className="w-64 bg-dark-bg border border-dark-border rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
          />
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-3">
        {/* Theme Toggle */}
        <button
          onClick={() => setDarkMode(!darkMode)}
          className="p-2 rounded-lg text-gray-400 hover:bg-dark-border hover:text-white transition-colors"
        >
          {darkMode ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
        </button>

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 rounded-lg text-gray-400 hover:bg-dark-border hover:text-white transition-colors relative"
          >
            <Bell className="w-5 h-5" />
            {notifications.length > 0 && (
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 top-full mt-2 w-80 bg-dark-card border border-dark-border rounded-xl shadow-xl z-50">
              <div className="p-3 border-b border-dark-border">
                <h3 className="text-sm font-semibold text-white">Notifications</h3>
              </div>
              <div className="max-h-64 overflow-y-auto">
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className="p-3 hover:bg-dark-border transition-colors cursor-pointer"
                  >
                    <p className="text-sm font-medium text-white">{notification.title}</p>
                    <p className="text-xs text-gray-400 mt-1">{notification.message}</p>
                    <p className="text-xs text-gray-500 mt-1">{notification.time}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* User Menu */}
        <div className="flex items-center gap-2 pl-3 border-l border-dark-border">
          <div className="w-8 h-8 rounded-full bg-primary-500/20 flex items-center justify-center">
            <User className="w-4 h-4 text-primary-400" />
          </div>
          <div className="hidden md:block">
            <p className="text-sm font-medium text-white">Admin User</p>
            <p className="text-xs text-gray-400">admin@buildagent.com</p>
          </div>
          <button className="p-1.5 rounded-lg text-gray-400 hover:bg-dark-border hover:text-white transition-colors">
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
