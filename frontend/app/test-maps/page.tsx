'use client';

import { useEffect, useRef, useState } from 'react';

export default function TestMapsPage() {
  const mapRef = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState<string>('Initializing...');
  const [apiKey, setApiKey] = useState<string>('');

  useEffect(() => {
    const key = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || '';
    setApiKey(key);
    
    if (!key) {
      setStatus('❌ API Key not found in environment variables');
      return;
    }

    setStatus(`✅ API Key found: ${key.substring(0, 10)}...`);

    const loadGoogleMaps = async () => {
      try {
        // Check if already loaded
        if (window.google && window.google.maps) {
          setStatus('✅ Google Maps already loaded');
          initMap();
          return;
        }

        setStatus('📥 Loading Google Maps script...');

        const script = document.createElement('script');
        script.src = `https://maps.googleapis.com/maps/api/js?key=${key}&libraries=places,geometry`;
        script.async = true;
        script.defer = true;

        script.onload = () => {
          setStatus('✅ Script loaded successfully');
          setTimeout(() => {
            if (window.google && window.google.maps) {
              initMap();
            } else {
              setStatus('❌ Google Maps API not available after script load');
            }
          }, 500);
        };

        script.onerror = (error) => {
          setStatus('❌ Failed to load Google Maps script');
          console.error('Script error:', error);
        };

        document.head.appendChild(script);
      } catch (error) {
        setStatus(`❌ Error: ${error}`);
        console.error('Load error:', error);
      }
    };

    const initMap = () => {
      if (!mapRef.current) {
        setStatus('❌ Map container not found');
        return;
      }

      if (!window.google || !window.google.maps) {
        setStatus('❌ Google Maps API not available');
        return;
      }

      try {
        new window.google.maps.Map(mapRef.current, {
          center: { lat: 23.2599, lng: 77.4126 },
          zoom: 12,
        });
        setStatus('✅ Map initialized successfully!');
      } catch (error) {
        setStatus(`❌ Map initialization error: ${error}`);
        console.error('Map init error:', error);
      }
    };

    loadGoogleMaps();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-4">Google Maps API Test</h1>
        
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-2">Status</h2>
          <p className="text-lg font-mono">{status}</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-2">API Key</h2>
          <p className="text-sm font-mono break-all bg-gray-100 p-3 rounded">
            {apiKey || 'Not found'}
          </p>
          <p className="text-sm text-gray-600 mt-2">
            Length: {apiKey.length} characters
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Map Container</h2>
          <div
            ref={mapRef}
            className="w-full h-[500px] bg-gray-200 rounded-lg border-2 border-gray-300"
          />
        </div>

        <div className="bg-white rounded-lg shadow p-6 mt-6">
          <h2 className="text-xl font-semibold mb-2">Required APIs</h2>
          <p className="text-sm text-gray-700 mb-2">
            Make sure these APIs are enabled in Google Cloud Console:
          </p>
          <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
            <li>Maps JavaScript API</li>
            <li>Places API</li>
            <li>Geocoding API</li>
            <li>Directions API</li>
            <li>Distance Matrix API</li>
          </ul>
          <p className="text-sm text-gray-700 mt-4">
            <strong>API Key Restrictions:</strong> Make sure your API key allows requests from localhost
          </p>
        </div>
      </div>
    </div>
  );
}

