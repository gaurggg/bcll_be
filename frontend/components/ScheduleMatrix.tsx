"use client";

import React, { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';

interface StopTiming {
  stop_name: string;
  stop_lat: number;
  stop_lng: number;
  arrival_time: string;
  departure_time: string;
}

interface BusSchedule {
  bus_number: string;
  bus_instance_id: string;
  deployment_sequence: number;
  departure_times: string[];
  stop_timings: StopTiming[];
}

interface IntermediateStop {
  name: string;
  lat: number;
  lng: number;
  sequence: number;
  distance_from_start_km: number;
  estimated_time_from_start_min: number;
}

interface ScheduleMatrixData {
  route_id: string;
  route_name: string;
  stops: IntermediateStop[];
  buses: BusSchedule[];
}

interface ScheduleMatrixProps {
  routeId: string;
}

export default function ScheduleMatrix({ routeId }: ScheduleMatrixProps) {
  const [matrixData, setMatrixData] = useState<ScheduleMatrixData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadScheduleMatrix();
  }, [routeId]);

  const loadScheduleMatrix = async () => {
    try {
      setLoading(true);
      const response = await adminAPI.getScheduleMatrix(routeId);
      setMatrixData(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load schedule matrix');
    } finally {
      setLoading(false);
    }
  };

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

  if (!matrixData || matrixData.buses.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-700">No schedules found for this route. Deploy buses first.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Schedule Matrix - {matrixData.route_name}
        </h2>
        <p className="text-gray-600">
          {matrixData.buses.length} bus(es) deployed on this route
        </p>
      </div>

      {/* Metro/Train Style Schedule Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse border border-gray-300">
          <thead>
            <tr className="bg-blue-600 text-white">
              <th className="border border-gray-300 px-4 py-3 text-left font-semibold">
                Stop Name
              </th>
              <th className="border border-gray-300 px-4 py-3 text-center font-semibold">
                Distance (km)
              </th>
              {matrixData.buses.map((bus) => (
                <th
                  key={bus.bus_instance_id}
                  className="border border-gray-300 px-4 py-3 text-center font-semibold"
                >
                  Bus {bus.deployment_sequence}
                  <br />
                  <span className="text-xs font-normal">({bus.bus_number})</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrixData.stops.map((stop, stopIndex) => (
              <tr
                key={stopIndex}
                className={stopIndex % 2 === 0 ? 'bg-gray-50' : 'bg-white'}
              >
                <td className="border border-gray-300 px-4 py-3 font-medium text-gray-800">
                  {stop.name}
                </td>
                <td className="border border-gray-300 px-4 py-3 text-center text-gray-600">
                  {stop.distance_from_start_km.toFixed(1)}
                </td>
                {matrixData.buses.map((bus) => {
                  const timing = bus.stop_timings.find(
                    (t) => t.stop_name === stop.name
                  );
                  return (
                    <td
                      key={bus.bus_instance_id}
                      className="border border-gray-300 px-4 py-3 text-center"
                    >
                      {timing ? (
                        <div className="space-y-1">
                          <div className="text-sm font-semibold text-blue-600">
                            {timing.arrival_time}
                          </div>
                          <div className="text-xs text-gray-500">
                            Dep: {timing.departure_time}
                          </div>
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Departure Times Summary */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {matrixData.buses.map((bus) => (
          <div
            key={bus.bus_instance_id}
            className="bg-blue-50 border border-blue-200 rounded-lg p-4"
          >
            <h3 className="font-semibold text-blue-800 mb-2">
              Bus {bus.deployment_sequence} - {bus.bus_number}
            </h3>
            <div className="text-sm text-gray-700">
              <p className="mb-2">
                <strong>Total Trips:</strong> {bus.departure_times.length}
              </p>
              <p className="mb-2">
                <strong>First Departure:</strong> {bus.departure_times[0] || 'N/A'}
              </p>
              <p>
                <strong>Last Departure:</strong>{' '}
                {bus.departure_times[bus.departure_times.length - 1] || 'N/A'}
              </p>
            </div>
            <details className="mt-3">
              <summary className="cursor-pointer text-blue-600 hover:text-blue-800 text-sm font-medium">
                View All Departures
              </summary>
              <div className="mt-2 max-h-40 overflow-y-auto bg-white rounded p-2 text-xs">
                <div className="grid grid-cols-4 gap-2">
                  {bus.departure_times.map((time, idx) => (
                    <span key={idx} className="text-gray-700">
                      {time}
                    </span>
                  ))}
                </div>
              </div>
            </details>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h3 className="font-semibold text-gray-800 mb-2">Legend</h3>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• <strong>Arrival Time:</strong> When the bus arrives at the stop</li>
          <li>• <strong>Departure Time (Dep):</strong> When the bus leaves the stop</li>
          <li>• <strong>Distance:</strong> Distance from the starting point</li>
          <li>• <strong>Bus Number:</strong> Deployment sequence on this route</li>
        </ul>
      </div>
    </div>
  );
}

