"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useAuthStore } from "@/lib/store";
import {
  LayoutDashboard,
  Map,
  List,
  Clock,
  ChevronLeft,
  ChevronRight,
  LogOut,
  User,
} from "lucide-react";

type AdminSidebarProps = {
  activeTab: string;
  setActiveTab: (tab: "overview" | "plan" | "routes" | "schedules") => void;
  routesCount: number;
  schedulesCount: number;
};

export default function AdminSidebar({
  activeTab,
  setActiveTab,
  routesCount,
  schedulesCount,
}: AdminSidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
  };

  const navItems = [
    {
      id: "overview",
      label: "Overview",
      icon: LayoutDashboard,
      count: null,
    },
    {
      id: "plan",
      label: "Plan Route",
      icon: Map,
      count: null,
    },
    {
      id: "routes",
      label: "Routes",
      icon: List,
      count: routesCount,
    },
    {
      id: "schedules",
      label: "Schedules",
      icon: Clock,
      count: schedulesCount,
    },
  ];

  return (
    <div
      className={`relative flex h-full flex-col bg-white text-gray-600 shadow-xl transition-all duration-300 ease-in-out ${
        isCollapsed ? "w-20" : "w-64"
      }`}
    >
      {/* Collapse/Expand Toggle */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute -right-3 top-8 z-10 grid h-6 w-6 place-items-center rounded-full border border-cool-slate/20 bg-white text-primary-blue shadow-md hover:bg-warm-neutral-sand"
      >
        {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>

      {/* Logo and Header */}
      <div
        className={`flex h-20 items-center border-b border-cool-slate/10 transition-all duration-300 ease-in-out ${
          isCollapsed
            ? "justify-center"
            : "m-2 rounded-2xl bg-warm-neutral-sand px-4"
        }`}
      >
        <Link href="/" className="flex items-center gap-s">
          <div className="bg-white p-1.5 rounded-lg">
            <Image
              src="/bcll logo.png"
              alt="BCLL Logo"
              width={isCollapsed ? 32 : 40}
              height={isCollapsed ? 32 : 40}
              className="rounded transition-all duration-300 ease-in-out"
            />
          </div>
          {!isCollapsed && (
            <p className="font-display text-sm text-primary-blue font-semibold">
              Smart Bus Planner
              <br />
              <span className="text-xs text-cool-slate">City Transport</span>
            </p>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-s px-4 py-l">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id as any)}
            className={`flex w-full items-center rounded-lg p-m text-left text-sm font-medium transition-colors ${
              activeTab === item.id
                ? "bg-status-success/20 text-primary-blue"
                : "text-cool-slate hover:bg-primary-blue/10 hover:text-primary-blue"
            } ${isCollapsed ? "justify-center" : ""}`}
          >
            <item.icon size={20} />
            {!isCollapsed && <span className="ml-s flex-1">{item.label}</span>}
            {!isCollapsed && item.count !== null && (
              <span
                className={`rounded-full px-2 py-0.5 text-xs ${
                  activeTab === item.id
                    ? "bg-status-success/30 text-primary-blue"
                    : "bg-cool-slate/10 text-cool-slate"
                }`}
              >
                {item.count}
              </span>
            )}
          </button>
        ))}
      </nav>

      {/* Footer - User Info & Logout */}
      <div className="border-t border-cool-slate/20 p-4">
        <div
          className={`flex items-center ${isCollapsed ? "justify-center" : ""}`}
        >
          <User className="h-8 w-8 flex-shrink-0 rounded-full bg-warm-neutral-sand p-1 text-primary-blue" />
          {!isCollapsed && (
            <div className="ml-s overflow-hidden">
              <p className="truncate text-sm font-semibold text-graphite-gray">{user?.email}</p>
              <p className="truncate text-xs text-cool-slate">{user?.role}</p>
            </div>
          )}
        </div>
        <button
          onClick={handleLogout}
          className={`mt-l flex w-full items-center rounded-lg p-m text-left text-cool-slate transition-colors hover:bg-status-error/10 hover:text-status-error ${
            isCollapsed ? "justify-center" : ""
          }`}
        >
          <LogOut size={20} />
          {!isCollapsed && <span className="ml-s">Logout</span>}
        </button>
      </div>
    </div>
  );
}
