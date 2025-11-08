'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { passengerAPI, type BusSearchResult, type TravelHistory } from '@/lib/api';
import LoadingSpinner from '@/components/LoadingSpinner';
import InterconnectedRoutes from '@/components/InterconnectedRoutes';
import { Search, MapPin, Clock, DollarSign, History, Sparkles } from 'lucide-react';

export default function PassengerDashboard() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'search' | 'history' | 'recommendations'>('search');
  const [loading, setLoading] = useState(false);

  // Google Maps
  const [mapsLoaded, setMapsLoaded] = useState(false);
  const sourceInputRef = useRef<HTMLInputElement>(null);
  const destInputRef = useRef<HTMLInputElement>(null);
  const sourceAutocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);
  const destAutocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);

  // Search form
  const [sourceName, setSourceName] = useState('');
  const [destName, setDestName] = useState('');
  const [searchForm, setSearchForm] = useState({
    source_lat: 0,
    source_lng: 0,
    dest_lat: 0,
    dest_lng: 0,
  });
  const [searchResults, setSearchResults] = useState<BusSearchResult[]>([]);
  const [searching, setSearching] = useState(false);

  // History
  const [history, setHistory] = useState<TravelHistory[]>([]);
  const [recommendations, setRecommendations] = useState<any>(null);

  // Trip management
  const [activeTrip, setActiveTrip] = useState<any>(null);
  const [showInterconnectedRoutes, setShowInterconnectedRoutes] = useState(false);

  useEffect(() => {
    if (!isAuthenticated || user?.role !== 'passenger') {
      router.push('/login');
      return;
    }
  }, [isAuthenticated, user, router]);

  // Load Google Maps API
  useEffect(() => {
    const loadGoogleMaps = () => {
      if (typeof window !== 'undefined' && !window.google) {
        const script = document.createElement('script');
        const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
        script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places`;
        script.async = true;
        script.defer = true;
        script.onload = () => {
          console.log('Google Maps API loaded');
          setMapsLoaded(true);
        };
        script.onerror = () => {
          console.error('Failed to load Google Maps API');
        };
        document.head.appendChild(script);
      } else if (window.google) {
        setMapsLoaded(true);
      }
    };

    loadGoogleMaps();
  }, []);

  // Setup autocomplete for source and destination
  useEffect(() => {
    if (!mapsLoaded || !window.google) return;

    // Setup source autocomplete
    if (sourceInputRef.current && !sourceAutocompleteRef.current) {
      const autocomplete = new window.google.maps.places.Autocomplete(sourceInputRef.current, {
        componentRestrictions: { country: 'in' },
        fields: ['formatted_address', 'geometry', 'name'],
      });

      autocomplete.addListener('place_changed', () => {
        const place = autocomplete.getPlace();
        if (place.geometry?.location) {
          const lat = place.geometry.location.lat();
          const lng = place.geometry.location.lng();
          setSourceName(place.formatted_address || place.name || '');
          setSearchForm((prev) => ({ ...prev, source_lat: lat, source_lng: lng }));
          console.log('Source selected:', place.formatted_address, lat, lng);
        }
      });

      sourceAutocompleteRef.current = autocomplete;
    }

    // Setup destination autocomplete
    if (destInputRef.current && !destAutocompleteRef.current) {
      const autocomplete = new window.google.maps.places.Autocomplete(destInputRef.current, {
        componentRestrictions: { country: 'in' },
        fields: ['formatted_address', 'geometry', 'name'],
      });

      autocomplete.addListener('place_changed', () => {
        const place = autocomplete.getPlace();
        if (place.geometry?.location) {
          const lat = place.geometry.location.lat();
          const lng = place.geometry.location.lng();
          setDestName(place.formatted_address || place.name || '');
          setSearchForm((prev) => ({ ...prev, dest_lat: lat, dest_lng: lng }));
          console.log('Destination selected:', place.formatted_address, lat, lng);
        }
      });

      destAutocompleteRef.current = autocomplete;
    }
  }, [mapsLoaded]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate that locations are selected
    if (!searchForm.source_lat || !searchForm.source_lng) {
      alert('Please select a source location from the suggestions');
      return;
    }
    if (!searchForm.dest_lat || !searchForm.dest_lng) {
      alert('Please select a destination location from the suggestions');
      return;
    }

    setSearching(true);
    try {
      const response = await passengerAPI.searchBuses(searchForm);
      console.log('Search response:', response.data);
      // Backend returns { available_routes: [...], ... }
      setSearchResults(response.data.available_routes || []);
    } catch (error: any) {
      console.error('Search error:', error);
      alert(error.response?.data?.detail || 'Search failed');
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleStartTrip = async (routeId: string, busNumber: string) => {
    try {
      const response = await passengerAPI.startTrip({
        source_name: sourceName,
        source_lat: searchForm.source_lat,
        source_lng: searchForm.source_lng,
        dest_name: destName,
        dest_lat: searchForm.dest_lat,
        dest_lng: searchForm.dest_lng,
        route_id: routeId,
        bus_number: busNumber,
      });
      setActiveTrip(response.data.trip);
      alert('Trip started! You can now switch routes if needed.');
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to start trip');
    }
  };

  const handleSelectRoute = async (option: any, legIndex: number) => {
    const leg = option.legs[legIndex];

    if (!activeTrip) {
      // Start new trip
      await handleStartTrip(leg.route_id, leg.route_name);
    } else {
      // Switch route
      try {
        const response = await passengerAPI.switchRoute({
          new_route_id: leg.route_id,
          new_bus_number: leg.route_name,
          boarding_location_name: leg.boarding_point.name,
          boarding_lat: leg.boarding_point.lat,
          boarding_lng: leg.boarding_point.lng,
        });
        setActiveTrip(response.data);
        alert(`Switched to ${leg.route_name}. Fare so far: ₹${response.data.total_fare_so_far}`);
      } catch (error: any) {
        alert(error.response?.data?.detail || 'Failed to switch route');
      }
    }
  };

  const handleCompleteTrip = async () => {
    try {
      const response = await passengerAPI.completeTrip();
      alert(`Trip completed! Total fare: ₹${response.data.total_fare}`);
      setActiveTrip(null);
      fetchHistory(); // Refresh history
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to complete trip');
    }
  };

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const response = await passengerAPI.getHistory();
      setHistory(response.data.history);
    } catch (error) {
      console.error('Error fetching history:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const response = await passengerAPI.getRecommendations();
      setRecommendations(response.data);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistory();
    } else if (activeTab === 'recommendations') {
      fetchRecommendations();
    }
  }, [activeTab]);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Passenger Portal</h1>
          <p className="text-gray-600">Search buses, view history, and get personalized recommendations</p>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <div className="flex border-b">
            <button
              onClick={() => setActiveTab('search')}
              className={`px-6 py-4 font-medium transition ${
                activeTab === 'search'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Search className="w-5 h-5 inline mr-2" />
              Search Buses
            </button>
            <button
              onClick={() => setActiveTab('recommendations')}
              className={`px-6 py-4 font-medium transition ${
                activeTab === 'recommendations'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Sparkles className="w-5 h-5 inline mr-2" />
              AI Recommendations
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`px-6 py-4 font-medium transition ${
                activeTab === 'history'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <History className="w-5 h-5 inline mr-2" />
              Travel History
            </button>
          </div>
        </div>

        {/* Search Tab */}
        {activeTab === 'search' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Search Buses</h2>
              <form onSubmit={handleSearch} className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  {/* Source Location */}
                  <div className="md:col-span-1">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <MapPin className="w-4 h-4 inline mr-2 text-green-600" />
                      Source Location
                    </label>
                    <input
                      ref={sourceInputRef}
                      type="text"
                      value={sourceName}
                      onChange={(e) => setSourceName(e.target.value)}
                      placeholder="Enter source location (e.g., MP Nagar, Bhopal)"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      required
                    />
                    {searchForm.source_lat !== 0 && (
                      <p className="text-xs text-gray-500 mt-1">
                        📍 {searchForm.source_lat.toFixed(4)}, {searchForm.source_lng.toFixed(4)}
                      </p>
                    )}
                  </div>

                  {/* Destination Location */}
                  <div className="md:col-span-1">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <MapPin className="w-4 h-4 inline mr-2 text-red-600" />
                      Destination Location
                    </label>
                    <input
                      ref={destInputRef}
                      type="text"
                      value={destName}
                      onChange={(e) => setDestName(e.target.value)}
                      placeholder="Enter destination location (e.g., New Market, Bhopal)"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      required
                    />
                    {searchForm.dest_lat !== 0 && (
                      <p className="text-xs text-gray-500 mt-1">
                        📍 {searchForm.dest_lat.toFixed(4)}, {searchForm.dest_lng.toFixed(4)}
                      </p>
                    )}
                  </div>
                </div>

                {/* Search Button */}
                <button
                  type="submit"
                  disabled={searching || !mapsLoaded}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {!mapsLoaded ? (
                    'Loading Maps...'
                  ) : searching ? (
                    <LoadingSpinner size="sm" />
                  ) : (
                    <>
                      <Search className="w-5 h-5 inline mr-2" />
                      Search Buses
                    </>
                  )}
                </button>

                {/* Helper Text */}
                <p className="text-sm text-gray-500 text-center">
                  💡 Start typing to see location suggestions from Google Maps
                </p>

                {/* Find Connections Button */}
                {searchForm.source_lat !== 0 && searchForm.dest_lat !== 0 && (
                  <button
                    type="button"
                    onClick={() => setShowInterconnectedRoutes(!showInterconnectedRoutes)}
                    className="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg font-semibold transition"
                  >
                    🔄 {showInterconnectedRoutes ? 'Hide' : 'Find'} Multi-Route Connections
                  </button>
                )}
              </form>

              {/* Active Trip Banner */}
              {activeTrip && (
                <div className="mt-4 bg-green-50 border-2 border-green-300 rounded-lg p-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-bold text-green-800 mb-2">🚌 Active Trip</h3>
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
                    <button
                      onClick={handleCompleteTrip}
                      className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-semibold"
                    >
                      Complete Trip
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Interconnected Routes */}
            {showInterconnectedRoutes && searchForm.source_lat !== 0 && searchForm.dest_lat !== 0 && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <InterconnectedRoutes
                  currentLat={searchForm.source_lat}
                  currentLng={searchForm.source_lng}
                  destLat={searchForm.dest_lat}
                  destLng={searchForm.dest_lng}
                  onSelectRoute={handleSelectRoute}
                />
              </div>
            )}

            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-4">
                  🚍 Available Buses ({searchResults.length} {searchResults.length === 1 ? 'route' : 'routes'} found)
                </h3>
                <div className="space-y-4">
                  {searchResults.map((result, index) => (
                    <div key={index} className="border-2 border-gray-200 rounded-lg p-5 hover:shadow-lg hover:border-blue-300 transition">
                      {/* Header with Route Name and Fare */}
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h4 className="text-lg font-bold text-gray-900">{result.route_name}</h4>
                          <p className="text-sm text-gray-600">
                            <span className="text-green-600 font-medium">{result.source_name}</span>
                            {' → '}
                            <span className="text-red-600 font-medium">{result.dest_name}</span>
                          </p>
                        </div>
                        <div className="text-right">
                          <div className="text-3xl font-bold text-blue-600">₹{result.fare}</div>
                          {result.is_peak_hour && (
                            <span className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded">
                              Peak Hour
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Bus Numbers */}
                      {result.bus_numbers && result.bus_numbers.length > 0 && (
                        <div className="mb-3 flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-medium text-gray-700">🚌 Buses:</span>
                          {result.bus_numbers.map((busNum, idx) => (
                            <span
                              key={idx}
                              className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-blue-100 text-blue-800 border border-blue-300"
                            >
                              {busNum}
                            </span>
                          ))}
                          <span className="text-xs text-gray-500">
                            ({result.total_buses} {result.total_buses === 1 ? 'bus' : 'buses'} on this route)
                          </span>
                        </div>
                      )}

                      {/* Route Details Grid */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                        <div className="bg-gray-50 p-2 rounded">
                          <div className="text-xs text-gray-500">Distance</div>
                          <div className="text-sm font-semibold text-gray-900">
                            <MapPin className="w-4 h-4 inline mr-1 text-blue-600" />
                            {result.distance_km.toFixed(1)} km
                          </div>
                        </div>
                        <div className="bg-gray-50 p-2 rounded">
                          <div className="text-xs text-gray-500">ETA</div>
                          <div className="text-sm font-semibold text-gray-900">
                            <Clock className="w-4 h-4 inline mr-1 text-green-600" />
                            {result.eta_min.toFixed(0)} min
                          </div>
                        </div>
                        <div className="bg-gray-50 p-2 rounded">
                          <div className="text-xs text-gray-500">Frequency</div>
                          <div className="text-sm font-semibold text-gray-900">
                            <DollarSign className="w-4 h-4 inline mr-1 text-purple-600" />
                            Every {result.frequency_min} min
                          </div>
                        </div>
                        <div className="bg-gray-50 p-2 rounded">
                          <div className="text-xs text-gray-500">Route ID</div>
                          <div className="text-sm font-semibold text-gray-900">
                            {result.route_id}
                          </div>
                        </div>
                      </div>

                      {/* Next Departures */}
                      {result.departure_times && result.departure_times.length > 0 && (
                        <div className="bg-blue-50 border border-blue-200 rounded p-3 mb-3">
                          <div className="text-xs font-medium text-blue-900 mb-2">⏰ Next Departures:</div>
                          <div className="flex gap-2 flex-wrap">
                            {result.departure_times.map((time, idx) => (
                              <span
                                key={idx}
                                className="inline-flex items-center px-2 py-1 rounded bg-white text-blue-700 font-mono text-sm border border-blue-300"
                              >
                                {time}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Start Trip Button */}
                      <button
                        onClick={() => handleStartTrip(result.route_id, result.bus_numbers?.[0] || result.route_id)}
                        className="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg font-semibold transition"
                      >
                        🚌 Start Trip on This Route
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Recommendations Tab */}
        {activeTab === 'recommendations' && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">AI-Powered Recommendations</h2>
            {loading ? (
              <div className="flex justify-center py-12">
                <LoadingSpinner size="lg" />
              </div>
            ) : recommendations ? (
              <div className="space-y-4">
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h3 className="font-semibold text-blue-900 mb-2">Personalized for You</h3>
                  <p className="text-blue-700">
                    Based on your travel history and preferences, here are our AI recommendations.
                  </p>
                </div>
                <pre className="bg-gray-50 p-4 rounded-lg overflow-auto text-sm">
                  {JSON.stringify(recommendations, null, 2)}
                </pre>
              </div>
            ) : (
              <p className="text-gray-600">No recommendations available yet. Start traveling to get personalized suggestions!</p>
            )}
          </div>
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Travel History</h2>
            {loading ? (
              <div className="flex justify-center py-12">
                <LoadingSpinner size="lg" />
              </div>
            ) : history.length > 0 ? (
              <div className="space-y-4">
                {history.map((trip) => (
                  <div key={trip._id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-gray-900">Route: {trip.route_id}</h4>
                      <span className="text-sm text-gray-600">
                        {new Date(trip.timestamp).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="text-sm text-gray-600">
                      <p>Travel Time: {trip.travel_time_min} minutes</p>
                      <p>Day: {trip.day_of_week}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-600">No travel history yet. Start your first journey!</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

