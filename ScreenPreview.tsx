"use client";

import { useState, useEffect } from "react";
import { useAgentStore } from "@/store/agentStore";
import {
  Camera,
  RefreshCw,
  Maximize2,
  Eye,
  Crosshair,
  MousePointer,
} from "lucide-react";

export function ScreenPreview() {
  const { screenshot, analysis, isAnalyzing, takeScreenshot, analyzeScreen } = useAgentStore();
  const [showOverlay, setShowOverlay] = useState(true);
  const [scale, setScale] = useState(1);

  return (
    <div className="bg-dark-card rounded-xl border border-dark-border overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-dark-border">
        <div className="flex items-center gap-2">
          <Monitor className="w-5 h-5 text-primary-400" />
          <h3 className="text-lg font-semibold text-white">Live Screen Preview</h3>
          <span className="px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 text-xs font-medium">
            LIVE
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowOverlay(!showOverlay)}
            className={`p-2 rounded-lg transition-colors ${
              showOverlay ? "bg-primary-500/20 text-primary-400" : "text-gray-400 hover:bg-dark-border"
            }`}
            title="Toggle UI Overlay"
          >
            <Eye className="w-4 h-4" />
          </button>
          <button
            onClick={takeScreenshot}
            className="p-2 rounded-lg text-gray-400 hover:bg-dark-border hover:text-white transition-colors"
            title="Take Screenshot"
          >
            <Camera className="w-4 h-4" />
          </button>
          <button
            onClick={analyzeScreen}
            disabled={isAnalyzing}
            className="p-2 rounded-lg text-gray-400 hover:bg-dark-border hover:text-white transition-colors disabled:opacity-50"
            title="Analyze Screen"
          >
            <RefreshCw className={`w-4 h-4 ${isAnalyzing ? "animate-spin" : ""}`} />
          </button>
          <button
            onClick={() => setScale(scale === 1 ? 0.5 : 1)}
            className="p-2 rounded-lg text-gray-400 hover:bg-dark-border hover:text-white transition-colors"
            title="Toggle Scale"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Screen Content */}
      <div className="relative bg-black overflow-hidden" style={{ height: "400px" }}>
        {screenshot ? (
          <div className="relative w-full h-full">
            <img
              src={screenshot}
              alt="Screen preview"
              className="w-full h-full object-contain"
              style={{ transform: `scale(${scale})`, transformOrigin: "top left" }}
            />

            {/* UI Element Overlay */}
            {showOverlay && analysis?.elements && (
              <div className="absolute inset-0 pointer-events-none">
                {analysis.elements.map((element: any, index: number) => (
                  <div
                    key={index}
                    className="absolute border-2 border-primary-500/50 rounded"
                    style={{
                      left: `${(element.x / 1920) * 100}%`,
                      top: `${(element.y / 1080) * 100}%`,
                      width: `${(element.width / 1920) * 100}%`,
                      height: `${(element.height / 1080) * 100}%`,
                    }}
                  >
                    <span className="absolute -top-5 left-0 px-1.5 py-0.5 bg-primary-500 text-white text-xs rounded whitespace-nowrap">
                      {element.element_type}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Mouse Position Indicator */}
            <div className="absolute bottom-4 right-4 flex items-center gap-2 px-3 py-1.5 bg-black/80 rounded-lg text-xs text-gray-300">
              <MousePointer className="w-3 h-3" />
              <span>960, 540</span>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <Camera className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No screenshot available</p>
              <button
                onClick={takeScreenshot}
                className="mt-3 px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg text-sm transition-colors"
              >
                Take Screenshot
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Analysis Info */}
      {analysis && (
        <div className="p-4 border-t border-dark-border">
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-400">Elements Detected</p>
              <p className="text-white font-medium">{analysis.elements?.length || 0}</p>
            </div>
            <div>
              <p className="text-gray-400">Text Regions</p>
              <p className="text-white font-medium">{analysis.text_regions?.length || 0}</p>
            </div>
            <div>
              <p className="text-gray-400">Resolution</p>
              <p className="text-white font-medium">
                {analysis.dimensions?.width}x{analysis.dimensions?.height}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

import { Monitor } from "lucide-react";
