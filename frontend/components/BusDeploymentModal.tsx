"use client";

import React, { useState } from 'react';
import { adminAPI } from '@/lib/api';

interface BusDeploymentModalProps {
  routeId: string;
  routeName: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function BusDeploymentModal({
  routeId,
  routeName,
  isOpen,
  onClose,
  onSuccess,
}: BusDeploymentModalProps) {
  const [numBuses, setNumBuses] = useState(1);
  const [frequencyMin, setFrequencyMin] = useState(10);
  const [peakHour, setPeakHour] = useState<'morning' | 'evening' | 'off-peak'>('morning');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleDeploy = async () => {
    try {
      setLoading(true);
      setError(null);

      await adminAPI.deployMultipleBuses(routeId, {
        num_buses: numBuses,
        frequency_min: frequencyMin,
        peak_hour: peakHour,
      });

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to deploy buses');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            Deploy Buses on Route
          </h2>
          <p className="text-gray-600 mb-6">{routeName}</p>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          <div className="space-y-4">
            {/* Number of Buses */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Number of Buses
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={numBuses}
                onChange={(e) => setNumBuses(parseInt(e.target.value) || 1)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">
                Deploy 1-20 buses on this route
              </p>
            </div>

            {/* Frequency */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Frequency (minutes)
              </label>
              <input
                type="number"
                min="5"
                max="60"
                value={frequencyMin}
                onChange={(e) => setFrequencyMin(parseInt(e.target.value) || 10)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">
                How often buses depart (5-60 minutes)
              </p>
            </div>

            {/* Peak Hour */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Peak Hour
              </label>
              <select
                value={peakHour}
                onChange={(e) => setPeakHour(e.target.value as any)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="morning">Morning Peak (6 AM - 10 PM)</option>
                <option value="evening">Evening Peak (6 AM - 10 PM)</option>
                <option value="off-peak">Off-Peak (9 AM - 8 PM)</option>
              </select>
            </div>

            {/* Calculation Preview */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-800 mb-2">Deployment Preview</h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• {numBuses} bus(es) will be deployed</li>
                <li>• Buses depart every {frequencyMin} minutes</li>
                <li>
                  • Each bus offset by {Math.floor(frequencyMin / numBuses)} minutes
                </li>
                <li>
                  • Operating hours:{' '}
                  {peakHour === 'off-peak' ? '9 AM - 8 PM' : '6 AM - 10 PM'}
                </li>
              </ul>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 mt-6">
            <button
              onClick={onClose}
              disabled={loading}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleDeploy}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Deploying...
                </>
              ) : (
                'Deploy Buses'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

