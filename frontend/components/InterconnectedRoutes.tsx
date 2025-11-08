"use client";

import React, { useState } from 'react';
import { passengerAPI } from '@/lib/api';

interface RouteOption {
  type: 'direct' | 'transfer';
  total_legs: number;
  total_distance_km: number;
  total_transfers: number;
  total_fare: number;
  legs: RouteLeg[];
}

interface RouteLeg {
  route_id: string;
  route_name: string;
  boarding_point: LocationPoint;
  alighting_point: LocationPoint;
  distance_km: number;
  fare: number;
  departure_times?: string[];
  frequency_min?: number;
}

interface LocationPoint {
  name: string;
  lat: number;
  lng: number;
  walk_distance_km: number;
}

interface InterconnectedRoutesProps {
  currentLat: number;
  currentLng: number;
  destLat: number;
  destLng: number;
  onSelectRoute: (option: RouteOption, legIndex: number) => void;
}

export default function InterconnectedRoutes({
  currentLat,
  currentLng,
  destLat,
  destLng,
  onSelectRoute,
}: InterconnectedRoutesProps) {
  const [routeOptions, setRouteOptions] = useState<RouteOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTrip, setActiveTrip] = useState<any>(null);

  const findConnections = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await passengerAPI.findConnections({
        current_lat: currentLat,
        current_lng: currentLng,
        final_dest_lat: destLat,
        final_dest_lng: destLng,
      });

      setRouteOptions(response.data.route_options || []);
      setActiveTrip(response.data.active_trip);
    } catch (err: any) {
      console.error('Find connections error:', err);
      // Handle validation errors (422) which return an array
      let errorMessage = 'Failed to find connections';
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          errorMessage = err.response.data.detail.map((e: any) => e.msg).join(', ');
        } else if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail;
        }
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    if (currentLat && currentLng && destLat && destLng) {
      findConnections();
    }
  }, [currentLat, currentLng, destLat, destLng]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  if (routeOptions.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-700">No routes found. Try different locations.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Active Trip Banner */}
      {activeTrip && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="font-semibold text-green-800 mb-2">🚌 Active Trip</h3>
          <p className="text-sm text-green-700">
            Currently on: <strong>{activeTrip.current_bus_number}</strong>
          </p>
          <p className="text-sm text-green-700">
            Route: {activeTrip.current_route_id}
          </p>
          <p className="text-sm text-green-700">
            Fare so far: ₹{activeTrip.total_fare_so_far?.toFixed(2) || '0.00'}
          </p>
        </div>
      )}

      {/* Route Options */}
      <h2 className="text-xl font-bold text-gray-800">
        Available Routes ({routeOptions.length})
      </h2>

      {routeOptions.map((option, optionIndex) => (
        <div
          key={optionIndex}
          className="bg-white border border-gray-200 rounded-lg shadow-md overflow-hidden"
        >
          {/* Option Header */}
          <div className="bg-blue-600 text-white px-4 py-3">
            <div className="flex justify-between items-center">
              <div>
                <span className="font-semibold">
                  {option.type === 'direct' ? '🚌 Direct Route' : '🔄 Transfer Route'}
                </span>
                <span className="ml-3 text-sm">
                  {option.total_legs} leg(s) • {option.total_transfers} transfer(s)
                </span>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold">₹{option.total_fare.toFixed(2)}</div>
                <div className="text-xs">{option.total_distance_km.toFixed(1)} km</div>
              </div>
            </div>
          </div>

          {/* Legs */}
          <div className="p-4 space-y-4">
            {option.legs.map((leg, legIndex) => (
              <div key={legIndex} className="relative">
                {/* Leg Card */}
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h4 className="font-semibold text-gray-800">
                        Leg {legIndex + 1}: {leg.route_name}
                      </h4>
                      <p className="text-sm text-gray-600">Route ID: {leg.route_id}</p>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-blue-600">
                        ₹{leg.fare.toFixed(2)}
                      </div>
                      <div className="text-xs text-gray-500">
                        {leg.distance_km.toFixed(1)} km
                      </div>
                    </div>
                  </div>

                  {/* Boarding Point */}
                  <div className="mb-2">
                    <div className="flex items-start">
                      <div className="w-3 h-3 bg-green-500 rounded-full mt-1 mr-3"></div>
                      <div className="flex-1">
                        <p className="font-medium text-gray-800">
                          Board: {leg.boarding_point.name}
                        </p>
                        {leg.boarding_point.walk_distance_km > 0 && (
                          <p className="text-xs text-orange-600">
                            🚶 Walk {(leg.boarding_point.walk_distance_km * 1000).toFixed(0)}m
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Route Line */}
                  <div className="ml-1 border-l-2 border-dashed border-gray-300 h-8"></div>

                  {/* Alighting Point */}
                  <div>
                    <div className="flex items-start">
                      <div className="w-3 h-3 bg-red-500 rounded-full mt-1 mr-3"></div>
                      <div className="flex-1">
                        <p className="font-medium text-gray-800">
                          Alight: {leg.alighting_point.name}
                        </p>
                        {leg.alighting_point.walk_distance_km > 0 && (
                          <p className="text-xs text-orange-600">
                            🚶 Walk {(leg.alighting_point.walk_distance_km * 1000).toFixed(0)}m
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Bus Timings */}
                  {leg.departure_times && leg.departure_times.length > 0 && (
                    <div className="mt-3 bg-white rounded p-2">
                      <p className="text-xs font-semibold text-gray-700 mb-1">
                        Next Departures:
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {leg.departure_times.slice(0, 5).map((time, idx) => (
                          <span
                            key={idx}
                            className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded"
                          >
                            {time}
                          </span>
                        ))}
                        {leg.departure_times.length > 5 && (
                          <span className="text-xs text-gray-500">
                            +{leg.departure_times.length - 5} more
                          </span>
                        )}
                      </div>
                      {leg.frequency_min && (
                        <p className="text-xs text-gray-500 mt-1">
                          Every {leg.frequency_min} minutes
                        </p>
                      )}
                    </div>
                  )}

                  {/* Select Button */}
                  <button
                    onClick={() => onSelectRoute(option, legIndex)}
                    className="mt-3 w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Select This Bus
                  </button>
                </div>

                {/* Transfer Indicator */}
                {legIndex < option.legs.length - 1 && (
                  <div className="flex items-center justify-center my-2">
                    <div className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-xs font-semibold">
                      🔄 Transfer Required
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

