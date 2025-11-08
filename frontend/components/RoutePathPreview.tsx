'use client';

import { useState, useEffect } from 'react';
import { MapPin, Clock } from 'lucide-react';

interface RoutePathPreviewProps {
  sourceName: string;
  destName: string;
  sourceLat: number;
  sourceLng: number;
  destLat: number;
  destLng: number;
  waypoints: number[][];
  durationMin: number;
  distanceKm: number;
}

interface StopInfo {
  name: string;
  lat: number;
  lng: number;
  estimatedTime: number;
  estimatedDistance: number;
  isLoading: boolean;
}

export default function RoutePathPreview({
  sourceName,
  destName,
  sourceLat,
  sourceLng,
  destLat,
  destLng,
  waypoints,
  durationMin,
  distanceKm,
}: RoutePathPreviewProps) {
  const [stops, setStops] = useState<StopInfo[]>([]);

  useEffect(() => {
    const fetchPlaceNames = async () => {
      if (!window.google || !window.google.maps) {
        return;
      }

      const geocoder = new google.maps.Geocoder();
      const totalWaypoints = waypoints.length;
      
      // Create initial stops with loading state
      const initialStops: StopInfo[] = waypoints.slice(1, Math.min(7, waypoints.length - 1)).map((waypoint, idx) => {
        const estimatedTime = Math.round((durationMin / totalWaypoints) * (idx + 1));
        const estimatedDistance = parseFloat(((distanceKm / totalWaypoints) * (idx + 1)).toFixed(1));
        
        return {
          name: 'Loading...',
          lat: waypoint[0],
          lng: waypoint[1],
          estimatedTime,
          estimatedDistance,
          isLoading: true,
        };
      });

      setStops(initialStops);

      // Fetch place names for each waypoint
      for (let i = 0; i < initialStops.length; i++) {
        const waypoint = waypoints[i + 1]; // +1 because we skip the first waypoint (source)
        
        try {
          const result = await geocoder.geocode({ 
            location: { lat: waypoint[0], lng: waypoint[1] } 
          });
          
          if (result.results && result.results.length > 0) {
            const place = result.results[0];
            let placeName = '';
            
            // Try to extract a meaningful name
            for (const component of place.address_components) {
              if (component.types.includes('neighborhood') || 
                  component.types.includes('sublocality') ||
                  component.types.includes('sublocality_level_1') ||
                  component.types.includes('locality')) {
                placeName = component.long_name;
                break;
              }
            }
            
            // Fallback to formatted address if no specific name found
            if (!placeName) {
              const parts = place.formatted_address.split(',');
              placeName = parts[0] || place.formatted_address;
            }
            
            // Update the specific stop
            setStops(prev => {
              const updated = [...prev];
              updated[i] = { ...updated[i], name: placeName, isLoading: false };
              return updated;
            });
          } else {
            // No results, show coordinates
            setStops(prev => {
              const updated = [...prev];
              updated[i] = { 
                ...updated[i], 
                name: `${waypoint[0].toFixed(4)}, ${waypoint[1].toFixed(4)}`, 
                isLoading: false 
              };
              return updated;
            });
          }
        } catch (error) {
          console.error('Geocoding error:', error);
          setStops(prev => {
            const updated = [...prev];
            updated[i] = { 
              ...updated[i], 
              name: `${waypoint[0].toFixed(4)}, ${waypoint[1].toFixed(4)}`, 
              isLoading: false 
            };
            return updated;
          });
        }
        
        // Add a small delay to avoid hitting rate limits
        await new Promise(resolve => setTimeout(resolve, 200));
      }
    };

    fetchPlaceNames();
  }, [waypoints, durationMin, distanceKm]);

  return (
    <div className="mt-l border-t border-cool-slate/20 pt-l">
      <h4 className="font-display font-semibold text-graphite-gray mb-m flex items-center gap-s">
        <MapPin className="w-4 h-4 text-primary-blue" />
        Route Path with Stops
      </h4>
      
      <div className="space-y-s max-h-[400px] overflow-y-auto pr-2">
        {/* Source */}
        <div className="flex items-start gap-m">
          <div className="flex flex-col items-center">
            <div className="w-3 h-3 rounded-full bg-green-500 border-2 border-white shadow" />
            <div className="w-0.5 h-8 bg-cool-slate/30" />
          </div>
          <div className="flex-1 pb-s">
            <div className="font-medium text-graphite-gray">{sourceName}</div>
            <div className="text-xs text-cool-slate">
              📍 {sourceLat.toFixed(4)}, {sourceLng.toFixed(4)}
            </div>
            <div className="text-xs text-primary-blue font-medium mt-1 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Start - 0 min
            </div>
          </div>
        </div>

        {/* Intermediate Stops */}
        {stops.map((stop, idx) => (
          <div key={idx} className="flex items-start gap-m">
            <div className="flex flex-col items-center">
              <div className="w-2 h-2 rounded-full bg-blue-400 border border-white shadow" />
              <div className="w-0.5 h-8 bg-cool-slate/30" />
            </div>
            <div className="flex-1 pb-s">
              <div className="text-sm font-medium text-graphite-gray">
                {stop.isLoading ? (
                  <span className="text-cool-slate/60 italic">Loading place name...</span>
                ) : (
                  stop.name
                )}
              </div>
              <div className="text-xs text-cool-slate/70">
                📍 {stop.lat.toFixed(4)}, {stop.lng.toFixed(4)}
              </div>
              <div className="text-xs text-cool-slate mt-1 flex items-center gap-2">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  ~{stop.estimatedTime} min
                </span>
                <span>•</span>
                <span>📏 {stop.estimatedDistance} km</span>
              </div>
            </div>
          </div>
        ))}

        {/* Show "..." if more waypoints */}
        {waypoints.length > 8 && (
          <div className="flex items-start gap-m">
            <div className="flex flex-col items-center">
              <div className="w-2 h-2 rounded-full bg-cool-slate/30" />
              <div className="w-0.5 h-8 bg-cool-slate/30" />
            </div>
            <div className="flex-1 pb-s">
              <div className="text-sm text-cool-slate/60 italic">
                ... {waypoints.length - 8} more stops ...
              </div>
            </div>
          </div>
        )}

        {/* Destination */}
        <div className="flex items-start gap-m">
          <div className="flex flex-col items-center">
            <div className="w-3 h-3 rounded-full bg-red-500 border-2 border-white shadow" />
          </div>
          <div className="flex-1">
            <div className="font-medium text-graphite-gray">{destName}</div>
            <div className="text-xs text-cool-slate">
              📍 {destLat.toFixed(4)}, {destLng.toFixed(4)}
            </div>
            <div className="text-xs text-status-success font-medium mt-1 flex items-center gap-2">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                End - {durationMin.toFixed(0)} min
              </span>
              <span>•</span>
              <span>📏 {distanceKm.toFixed(1)} km</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-m p-m bg-blue-50 border border-blue-200 rounded-lg">
        <div className="text-xs text-blue-800">
          <strong>💡 Info:</strong> Place names are fetched from Google Maps Geocoding API. 
          This route has {waypoints.length} total waypoints.
        </div>
      </div>
    </div>
  );
}

