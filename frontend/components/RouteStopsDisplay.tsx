"use client";

import React from 'react';

interface IntermediateStop {
  name: string;
  lat: number;
  lng: number;
  sequence: number;
  distance_from_start_km: number;
  estimated_time_from_start_min: number;
}

interface RouteStopsDisplayProps {
  stops: IntermediateStop[];
  routeName: string;
}

export default function RouteStopsDisplay({ stops, routeName }: RouteStopsDisplayProps) {
  if (!stops || stops.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mt-4">
      <h3 className="text-xl font-bold text-gray-800 mb-4">
        📍 Route Stops - {routeName}
      </h3>

      <div className="space-y-3">
        {stops.map((stop, index) => (
          <div key={index} className="flex items-start">
            {/* Timeline */}
            <div className="flex flex-col items-center mr-4">
              {/* Circle */}
              <div
                className={`w-4 h-4 rounded-full ${
                  index === 0
                    ? 'bg-green-500'
                    : index === stops.length - 1
                    ? 'bg-red-500'
                    : 'bg-blue-500'
                }`}
              ></div>
              {/* Line */}
              {index < stops.length - 1 && (
                <div className="w-0.5 h-12 bg-gray-300"></div>
              )}
            </div>

            {/* Stop Info */}
            <div className="flex-1 pb-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-800 text-base">
                    {index === 0 && '🚏 Start: '}
                    {index === stops.length - 1 && '🏁 End: '}
                    {/* Show place name prominently */}
                    {stop.name.startsWith('Stop at') ? (
                      <span className="text-gray-500 italic">
                        {stop.name}
                      </span>
                    ) : (
                      <span className="text-gray-900 font-bold">
                        {stop.name}
                      </span>
                    )}
                  </h4>
                  <p className="text-sm text-gray-600 mt-1">
                    Stop #{stop.sequence}
                  </p>
                  {/* Show coordinates inline if place name is available */}
                  {!stop.name.startsWith('Stop at') && (
                    <p className="text-xs text-gray-400 mt-1">
                      📍 {stop.lat.toFixed(4)}, {stop.lng.toFixed(4)}
                    </p>
                  )}
                </div>
                <div className="text-right ml-4">
                  <div className="text-sm font-semibold text-blue-600">
                    ⏰ {stop.estimated_time_from_start_min} min
                  </div>
                  <div className="text-xs text-gray-500">
                    📏 {stop.distance_from_start_km.toFixed(1)} km
                  </div>
                </div>
              </div>

              {/* Coordinates (collapsible) - only if place name is shown */}
              {!stop.name.startsWith('Stop at') && (
                <details className="mt-2">
                  <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                    📍 View precise coordinates
                  </summary>
                  <p className="text-xs text-gray-500 mt-1">
                    Latitude: {stop.lat.toFixed(6)}, Longitude: {stop.lng.toFixed(6)}
                  </p>
                </details>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-blue-600">{stops.length}</div>
            <div className="text-xs text-gray-600">Total Stops</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-blue-600">
              {stops[stops.length - 1]?.distance_from_start_km.toFixed(1) || 0}
            </div>
            <div className="text-xs text-gray-600">Total Distance (km)</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-blue-600">
              {stops[stops.length - 1]?.estimated_time_from_start_min || 0}
            </div>
            <div className="text-xs text-gray-600">Total Time (min)</div>
          </div>
        </div>
      </div>
    </div>
  );
}

