"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store";
import { adminAPI, type Route, type Schedule } from "@/lib/api";
import LoadingSpinner from "@/components/LoadingSpinner";
import AdminSidebar from "@/components/AdminSidebar";
import BusDeploymentModal from "@/components/BusDeploymentModal";
import ScheduleMatrix from "@/components/ScheduleMatrix";
import RouteStopsDisplay from "@/components/RouteStopsDisplay";
import RoutePathPreview from "@/components/RoutePathPreview";
import {
  MapPin,
  Clock,
  Bus,
  TrendingUp,
  Plus,
  List,
  Trash2,
  Navigation,
} from "lucide-react";

// Google Maps API Key
const GOOGLE_MAPS_API_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "";

interface BusRoute {
  id: string;
  busNumber: string;
  source: string;
  destination: string;
  sourceCoords?: { lat: number; lng: number };
  destCoords?: { lat: number; lng: number };
  peak_hour: "morning" | "evening" | "off-peak";
  color: string;
  expectedPassengers?: number; // Daily passenger count for frequency calculation
}

interface RouteOption {
  route_index: number;
  distance_km: number;
  duration_min: number;
  waypoints: [number, number][];
  gemini_score: number;
  traffic_score: number;
  reasoning: string;
  rank: number;
}

interface BusRouteResult {
  bus_number: string;
  source: { lat: number; lng: number };
  destination: { lat: number; lng: number };
  peak_hour: string;
  total_routes: number;
  routes: RouteOption[];
  selectedRouteIndex?: number; // Which route is selected (0, 1, or 2)
}

export default function AdminDashboard() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [routes, setRoutes] = useState<Route[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    "overview" | "routes" | "schedules" | "plan"
  >("overview");
  const [isMounted, setIsMounted] = useState(false);

  // Multi-bus route planning
  const [busRoutes, setBusRoutes] = useState<BusRoute[]>([
    {
      id: "1",
      busNumber: "Bus 1",
      source: "",
      destination: "",
      peak_hour: "morning",
      color: "#FF0000",
      expectedPassengers: 0,
    },
  ]);
  const [planResults, setPlanResults] = useState<BusRouteResult[]>([]);
  const [planning, setPlanning] = useState(false);
  const [savingRoute, setSavingRoute] = useState<string | null>(null); // Track which bus route is being saved

  // New state for enhanced features
  const [deployModalOpen, setDeployModalOpen] = useState(false);
  const [selectedRouteForDeploy, setSelectedRouteForDeploy] = useState<{ id: string; name: string } | null>(null);
  const [matrixViewRouteId, setMatrixViewRouteId] = useState<string | null>(null);

  // State for place names (geocoding results)
  const [placeNames, setPlaceNames] = useState<{ [key: string]: string }>({});

  // Google Maps
  const mapRef = useRef<HTMLDivElement>(null);
  const googleMapRef = useRef<google.maps.Map | null>(null);
  const autocompleteRefs = useRef<{
    [key: string]: google.maps.places.Autocomplete;
  }>({});
  const directionsRenderers = useRef<google.maps.DirectionsRenderer[]>([]);
  const polylines = useRef<google.maps.Polyline[]>([]);
  const [mapsLoaded, setMapsLoaded] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isMounted) return;

    if (!isAuthenticated || user?.role !== "admin") {
      router.push("/login");
      return;
    }
    fetchData();
  }, [isAuthenticated, user, router, isMounted]);

  // Initialize map separately when component is mounted and on Plan Route tab
  useEffect(() => {
    if (
      isMounted &&
      activeTab === "plan" &&
      mapRef.current &&
      !googleMapRef.current
    ) {
      console.log("Initializing Google Maps...");
      initializeMap();
    }
  }, [isMounted, activeTab]);

  const initializeMap = async () => {
    try {
      console.log("=== INITIALIZING GOOGLE MAPS ===");
      console.log("API Key exists:", !!GOOGLE_MAPS_API_KEY);
      console.log("API Key value:", GOOGLE_MAPS_API_KEY);
      console.log("API Key length:", GOOGLE_MAPS_API_KEY?.length);
      console.log("mapRef.current exists:", !!mapRef.current);
      console.log("window.google exists:", !!window.google);

      if (!GOOGLE_MAPS_API_KEY) {
        throw new Error(
          "Google Maps API key is not defined in environment variables"
        );
      }

      // Check if script is already loaded
      if (!window.google) {
        console.log("Loading Google Maps script...");

        // Remove any existing Google Maps scripts to prevent conflicts
        const existingScripts = document.querySelectorAll(
          'script[src*="maps.googleapis.com"]'
        );
        existingScripts.forEach((script) => script.remove());

        const scriptUrl = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&libraries=places,geometry`;
        console.log("Script URL:", scriptUrl);

        const script = document.createElement("script");
        script.src = scriptUrl;
        script.async = true;
        script.defer = true;

        // Wait for script to load
        await new Promise<void>((resolve, reject) => {
          script.onload = () => {
            console.log("✅ Google Maps script loaded successfully");
            resolve();
          };
          script.onerror = (error) => {
            console.error("❌ Script loading error:", error);
            reject(new Error("Failed to load Google Maps script"));
          };
          document.head.appendChild(script);
        });

        // Wait a bit for Google Maps to initialize
        await new Promise((resolve) => setTimeout(resolve, 500));
      } else {
        console.log("✅ Google Maps already loaded");
      }

      // Verify Google Maps is available
      if (!window.google || !window.google.maps) {
        throw new Error("Google Maps API failed to load");
      }

      // Create map instance
      if (mapRef.current && !googleMapRef.current) {
        console.log("Creating map instance...");

        googleMapRef.current = new window.google.maps.Map(mapRef.current, {
          center: { lat: 23.2599, lng: 77.4126 }, // Bhopal center
          zoom: 12,
          mapTypeControl: true,
          streetViewControl: false,
          fullscreenControl: true,
          zoomControl: true,
        });

        setMapsLoaded(true);
        console.log("✅ Google Maps initialized successfully!");
        console.log("Map instance:", googleMapRef.current);
      } else {
        console.log("⚠️ Map not created. Conditions:", {
          hasMapRef: !!mapRef.current,
          hasGoogleMapRef: !!googleMapRef.current,
          hasWindowGoogle: !!window.google,
        });
      }
    } catch (error) {
      console.error("❌ Error loading Google Maps:", error);
      setMapsLoaded(false);
    }
  };

  const fetchData = async () => {
    try {
      const [routesRes, schedulesRes] = await Promise.all([
        adminAPI.getRoutes(),
        adminAPI.getSchedules(),
      ]);
      setRoutes(routesRes.data.routes);
      setSchedules(schedulesRes.data.schedules);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  const addBusRoute = () => {
    const colors = [
      "#FF0000",
      "#00FF00",
      "#0000FF",
      "#FFFF00",
      "#FF00FF",
      "#00FFFF",
      "#FFA500",
      "#800080",
      "#008000",
      "#FFC0CB",
      "#A52A2A",
      "#808080",
      "#FF6B6B",
      "#4ECDC4",
      "#45B7D1",
      "#FFA07A",
      "#98D8C8",
      "#F7DC6F",
      "#BB8FCE",
      "#85C1E2",
      "#F8B739",
      "#52B788",
    ];
    const newRoute: BusRoute = {
      id: Date.now().toString(),
      busNumber: `Bus ${busRoutes.length + 1}`,
      source: "",
      destination: "",
      peak_hour: "morning",
      color: colors[busRoutes.length % colors.length],
    };
    setBusRoutes([...busRoutes, newRoute]);
  };

  const removeBusRoute = (id: string) => {
    setBusRoutes(busRoutes.filter((r) => r.id !== id));
  };

  const updateBusRoute = (id: string, field: keyof BusRoute, value: any) => {
    console.log(`📝 Updating route ${id}, field: ${field}, value: ${value}`);
    setBusRoutes((prevRoutes) =>
      prevRoutes.map((r) => (r.id === id ? { ...r, [field]: value } : r))
    );
  };

  const geocodeAddress = async (
    address: string
  ): Promise<{ lat: number; lng: number } | null> => {
    if (!address || !window.google) return null;

    try {
      const geocoder = new window.google.maps.Geocoder();
      const result = await geocoder.geocode({
        address: address + ", Bhopal, Madhya Pradesh, India",
      });

      if (result.results[0]) {
        const location = result.results[0].geometry.location;
        return { lat: location.lat(), lng: location.lng() };
      }
    } catch (error) {
      console.error("Geocoding error:", error);
    }
    return null;
  };

  const setupAutocomplete = (
    inputId: string,
    routeId: string,
    field: "source" | "destination"
  ) => {
    if (!window.google || !mapsLoaded) {
      console.log(
        `⚠️ Cannot setup autocomplete for ${inputId}: Google Maps not loaded`
      );
      return;
    }

    const input = document.getElementById(inputId) as HTMLInputElement;
    if (!input) {
      console.log(
        `⚠️ Cannot setup autocomplete for ${inputId}: Input element not found`
      );
      return;
    }

    // Check if autocomplete already exists for this input
    if (autocompleteRefs.current[inputId]) {
      console.log(`⚠️ Autocomplete already exists for ${inputId}, skipping...`);
      return;
    }

    try {
      console.log(`🔧 Setting up autocomplete for ${inputId}...`);

      // Create autocomplete with Bhopal bias
      const autocomplete = new window.google.maps.places.Autocomplete(input, {
        componentRestrictions: { country: "in" },
        bounds: new window.google.maps.LatLngBounds(
          new window.google.maps.LatLng(23.1, 77.2),
          new window.google.maps.LatLng(23.4, 77.6)
        ),
        strictBounds: false,
        fields: ["formatted_address", "geometry", "name", "place_id"],
      });

      // Listen for place selection
      autocomplete.addListener("place_changed", () => {
        const place = autocomplete.getPlace();
        if (place && place.geometry && place.geometry.location) {
          // Update the route with the selected place name
          const placeName = place.name || place.formatted_address || "";

          console.log(
            `✅ Place selected for ${field} (${inputId}):`,
            placeName
          );

          // Update state
          setBusRoutes((prevRoutes) =>
            prevRoutes.map((r) =>
              r.id === routeId ? { ...r, [field]: placeName } : r
            )
          );
        }
      });

      // Prevent autocomplete from clearing other fields
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
        }
      });

      autocompleteRefs.current[inputId] = autocomplete;
      console.log(`✅ Autocomplete setup complete for ${inputId}`);
    } catch (error) {
      console.error(`❌ Error setting up autocomplete for ${inputId}:`, error);
    }
  };

  // Track which inputs have autocomplete initialized
  const initializedInputs = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (mapsLoaded && activeTab === "plan" && isMounted) {
      // Setup autocomplete for all visible inputs
      setTimeout(() => {
        busRoutes.forEach((route) => {
          const sourceInputId = `source-${route.id}`;
          const destInputId = `dest-${route.id}`;

          // Only setup if not already initialized
          if (!initializedInputs.current.has(sourceInputId)) {
            setupAutocomplete(sourceInputId, route.id, "source");
            initializedInputs.current.add(sourceInputId);
          }

          if (!initializedInputs.current.has(destInputId)) {
            setupAutocomplete(destInputId, route.id, "destination");
            initializedInputs.current.add(destInputId);
          }
        });
      }, 100);
    }
  }, [mapsLoaded, activeTab, isMounted, busRoutes.length]); // Only depend on length, not the whole array

  // Clear all routes from map
  const clearMapRoutes = () => {
    directionsRenderers.current.forEach((renderer) => renderer.setMap(null));
    directionsRenderers.current = [];
    polylines.current.forEach((polyline) => polyline.setMap(null));
    polylines.current = [];
  };

  // Draw a single route option on the map
  const drawRouteOnMap = (
    waypoints: [number, number][],
    color: string,
    routeIndex: number,
    isSelected: boolean
  ) => {
    if (!googleMapRef.current) return;

    const path = waypoints.map(([lat, lng]) => ({ lat, lng }));

    // Different styles for different route options
    const strokeStyles = [
      { weight: 6, opacity: 0.8 }, // Route 1: Solid thick
      { weight: 5, opacity: 0.6 }, // Route 2: Solid medium
      { weight: 4, opacity: 0.5 }, // Route 3: Solid thin
    ];

    const style = strokeStyles[routeIndex] || strokeStyles[2];

    const polyline = new window.google.maps.Polyline({
      path,
      geodesic: true,
      strokeColor: color,
      strokeOpacity: isSelected ? 1.0 : style.opacity,
      strokeWeight: isSelected ? style.weight + 2 : style.weight,
      map: googleMapRef.current,
      zIndex: isSelected ? 1000 : 100 + routeIndex,
    });

    polylines.current.push(polyline);

    // Add click listener to select route
    polyline.addListener("click", () => {
      console.log(`Route ${routeIndex} clicked`);
    });
  };

  const handlePlanRoute = async (e: React.FormEvent) => {
    e.preventDefault();

    console.log("=== ROUTE PLANNING STARTED ===");

    if (!window.google || !mapsLoaded || !googleMapRef.current) {
      alert(
        "⚠️ Google Maps is still loading. Please wait a moment and try again."
      );
      return;
    }

    setPlanning(true);

    try {
      clearMapRoutes();

      console.log("🚌 Starting route planning for", busRoutes.length, "buses");

      // Geocode all addresses
      const geocodedRoutes = await Promise.all(
        busRoutes.map(async (route) => {
          const sourceCoords = await geocodeAddress(route.source);
          const destCoords = await geocodeAddress(route.destination);
          console.log(`Geocoded ${route.busNumber}:`, {
            sourceCoords,
            destCoords,
          });
          return { ...route, sourceCoords, destCoords };
        })
      );

      // Filter out routes that couldn't be geocoded
      const validRoutes = geocodedRoutes.filter(
        (route) => route.sourceCoords && route.destCoords
      );

      if (validRoutes.length === 0) {
        alert(
          "Could not geocode any of the addresses. Please check the location names."
        );
        setPlanning(false);
        return;
      }

      console.log(
        `Successfully geocoded ${validRoutes.length} out of ${busRoutes.length} routes`
      );

      // Update bus routes with coordinates
      setBusRoutes(geocodedRoutes);

      // Use batch endpoint to get 3 routes per bus
      const batchRequest = {
        routes: validRoutes.map((route) => ({
          source_lat: route.sourceCoords!.lat,
          source_lng: route.sourceCoords!.lng,
          dest_lat: route.destCoords!.lat,
          dest_lng: route.destCoords!.lng,
          peak_hour: route.peak_hour,
        })),
      };

      console.log("Sending batch request to backend:", batchRequest);
      const batchResult = await adminAPI.planBatchRoutes(batchRequest);
      console.log("Batch result:", batchResult.data);

      // Process and display all 3 routes for each bus
      const processedResults: BusRouteResult[] = batchResult.data.routes.map(
        (busData: any, busIndex: number) => {
          const busRoute = validRoutes[busIndex];

          // Draw all 3 route options on the map
          busData.routes.forEach(
            (routeOption: RouteOption, routeIndex: number) => {
              drawRouteOnMap(
                routeOption.waypoints,
                busRoute.color,
                routeIndex,
                routeIndex === 0 // First route is selected by default
              );
            }
          );

          return {
            bus_number: busRoute.busNumber,
            source: busData.source,
            destination: busData.destination,
            peak_hour: busData.peak_hour,
            total_routes: busData.total_routes,
            routes: busData.routes,
            selectedRouteIndex: 0, // Default to first route
          };
        }
      );

      setPlanResults(processedResults);
      console.log("✅ Route planning complete! Showing 3 routes per bus.");
    } catch (error: any) {
      console.error("Route planning error:", error);
      alert(
        error.response?.data?.detail || error.message || "Failed to plan routes"
      );
    } finally {
      setPlanning(false);
    }
  };

  // Fetch place name from coordinates using Google Geocoding API
  const getPlaceName = async (lat: number, lng: number): Promise<string> => {
    const key = `${lat},${lng}`;

    // Check if already cached
    if (placeNames[key]) {
      return placeNames[key];
    }

    try {
      if (!window.google || !window.google.maps) {
        return `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
      }

      const geocoder = new google.maps.Geocoder();
      const result = await geocoder.geocode({ location: { lat, lng } });

      if (result.results && result.results.length > 0) {
        // Try to get a meaningful place name
        const place = result.results[0];
        let placeName = place.formatted_address || '';

        // Try to extract a shorter, more meaningful name
        for (const component of place.address_components) {
          if (component.types.includes('neighborhood') ||
              component.types.includes('sublocality') ||
              component.types.includes('locality')) {
            placeName = component.long_name;
            break;
          }
        }

        // Cache the result
        setPlaceNames(prev => ({ ...prev, [key]: placeName }));
        return placeName;
      }
    } catch (error) {
      console.error('Geocoding error:', error);
    }

    return `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
  };

  // Select a specific route for a bus
  const selectRoute = (busIndex: number, routeIndex: number) => {
    setPlanResults((prevResults) => {
      const newResults = [...prevResults];
      newResults[busIndex].selectedRouteIndex = routeIndex;
      return newResults;
    });

    // Redraw routes with new selection
    clearMapRoutes();
    planResults.forEach((busResult, bIdx) => {
      const busRoute = busRoutes[bIdx];
      busResult.routes.forEach((routeOption, rIdx) => {
        const isSelected =
          bIdx === busIndex
            ? rIdx === routeIndex
            : rIdx === busResult.selectedRouteIndex;
        drawRouteOnMap(routeOption.waypoints, busRoute.color, rIdx, isSelected);
      });
    });
  };

  // Save selected route to database
  const saveSelectedRoute = async (busIndex: number) => {
    const busResult = planResults[busIndex];
    const busRoute = busRoutes[busIndex];
    const selectedRoute = busResult.routes[busResult.selectedRouteIndex || 0];

    if (!selectedRoute) {
      alert("No route selected");
      return;
    }

    setSavingRoute(busRoute.id);

    try {
      const saveRequest = {
        bus_id: busRoute.id,
        bus_number: busRoute.busNumber,
        route_index: busResult.selectedRouteIndex || 0,
        source_name: busRoute.source,
        dest_name: busRoute.destination,
        source_lat: busResult.source.lat,
        source_lng: busResult.source.lng,
        dest_lat: busResult.destination.lat,
        dest_lng: busResult.destination.lng,
        waypoints: selectedRoute.waypoints,
        distance_km: selectedRoute.distance_km,
        duration_min: selectedRoute.duration_min,
        gemini_score: selectedRoute.gemini_score,
        traffic_score: selectedRoute.traffic_score,
        reasoning: selectedRoute.reasoning,
        peak_hour: busRoute.peak_hour,
        expected_passengers_daily: busRoute.expectedPassengers || 0,
      };

      const response = await adminAPI.saveSelectedRoute(saveRequest);
      console.log("Route saved:", response.data);

      const freq = response.data.frequency_recommendation;
      const sched = response.data.schedule;

      let message = `✅ Route and Schedule Saved Successfully!\n\n`;
      message += `📍 Route ID: ${response.data.route_id}\n`;
      message += `🚌 Bus: ${busRoute.busNumber}\n\n`;

      if (freq) {
        message += `🤖 AI Recommendations:\n`;
        message += `━━━━━━━━━━━━━━━━━━━━━━\n`;
        message += `🚍 Buses Needed: ${freq.buses_needed} buses\n`;
        message += `⏱️  Frequency: Every ${freq.frequency_min} minutes\n`;
        if (freq.expected_passengers_daily) {
          message += `👥 Expected Passengers: ${freq.expected_passengers_daily}/day\n`;
          message += `📊 Capacity per Bus: 70 passengers\n`;
        }
        message += `\n`;
      }

      if (sched) {
        message += `📅 Schedule Generated:\n`;
        message += `━━━━━━━━━━━━━━━━━━━━━━\n`;
        message += `🕐 First Departure: ${sched.first_departure}\n`;
        message += `🕙 Last Departure: ${sched.last_departure}\n`;
        message += `🔢 Total Trips: ${sched.total_trips} trips/day\n`;
      }

      alert(message);

      // Refresh routes and schedules list
      fetchData();
    } catch (error: any) {
      console.error("Error saving route:", error);
      alert(error.response?.data?.detail || "Failed to save route");
    } finally {
      setSavingRoute(null);
    }
  };

  if (loading || !isMounted) {
    return (
      <div className="min-h-screen bg-warm-neutral-sand flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-warm-neutral-sand">
      <AdminSidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        routesCount={routes.length}
        schedulesCount={schedules.length}
      />
      <main className="flex-1 overflow-y-auto p-xl">
        {/* Overview Tab */}
        {activeTab === "overview" && (
          <>
            <h1 className="font-display text-h1 text-graphite-gray mb-l">
              Overview
            </h1>
            <div className="grid md:grid-cols-3 gap-l">
              <div className="bg-white p-xl rounded-lg shadow">
                <div className="flex items-center justify-between mb-m">
                  <h3 className="font-display text-h3 text-graphite-gray">
                    Total Routes
                  </h3>
                  <Bus className="w-8 h-8 text-primary-blue" />
                </div>
                <p className="font-display text-h2 font-bold text-primary-blue">
                  {routes.length}
                </p>
              </div>
              <div className="bg-white p-xl rounded-lg shadow">
                <div className="flex items-center justify-between mb-m">
                  <h3 className="font-display text-h3 text-graphite-gray">
                    Active Schedules
                  </h3>
                  <Clock className="w-8 h-8 text-status-success" />
                </div>
                <p className="font-display text-h2 font-bold text-status-success">
                  {schedules.filter((s) => s.active).length}
                </p>
              </div>
              <div className="bg-white p-xl rounded-lg shadow">
                <div className="flex items-center justify-between mb-m">
                  <h3 className="font-display text-h3 text-graphite-gray">
                    Avg AI Score
                  </h3>
                  <TrendingUp className="w-8 h-8 text-highlight-mint" />
                </div>
                <p className="font-display text-h2 font-bold text-highlight-mint">
                  {routes.length > 0
                    ? (
                        routes.reduce(
                          (sum, r) => sum + (r.gemini_score || 0),
                          0
                        ) / routes.length
                      ).toFixed(1)
                    : "0.0"}
                </p>
              </div>
            </div>
          </>
        )}

        {/* Plan Route Tab */}
        {activeTab === "plan" && (
          <>
            <h1 className="font-display text-h1 text-graphite-gray mb-l">
              Route Planner
            </h1>
            <div className="grid lg:grid-cols-3 gap-l mt-5">
              {/* Left Panel - Multi-Bus Form */}
              <div className="col-span-1 ">
                <div className="bg-white rounded-lg shadow p-1 px-4 mb-4">
                  {/* Route Selection Results */}
                  {planResults && planResults.length > 0 && (
                    <div className="mt-l space-y-l">
                      <div className="p-l bg-status-success/10 border border-status-success/30 rounded-lg">
                        <h3 className="font-semibold text-status-success mb-xs">
                          ✓ Route Planning Complete!
                        </h3>
                        <p className="text-body-sm text-status-success/80">
                          Successfully planned {planResults.length} bus routes
                          with 3 options each. Select the best route for each
                          bus below.
                        </p>
                      </div>

                      {/* Route Selection Cards */}
                      <div className="space-y-l max-h-[40rem] overflow-y-auto p-xs ">
                        {planResults.map((busResult, busIndex) => {
                          const busRoute = busRoutes[busIndex];
                          const selectedRoute =
                            busResult.routes[busResult.selectedRouteIndex || 0];

                          return (
                            <div
                              key={busIndex}
                              className="border border-cool-slate/20 rounded-lg p-l bg-white"
                            >
                              <div className="flex items-center gap-s mb-m">
                                <div
                                  className="w-4 h-4 rounded-full"
                                  style={{ backgroundColor: busRoute.color }}
                                />
                                <h4 className="font-display font-semibold text-graphite-gray">
                                  {busResult.bus_number}
                                </h4>
                                <span className="text-body-sm text-cool-slate">
                                  {busRoute.source} → {busRoute.destination}
                                </span>
                              </div>

                              {/* AI Recommendation Box */}
                              {busRoute.expectedPassengers &&
                                busRoute.expectedPassengers > 0 &&
                                (() => {
                                  // SIMPLE AND CORRECT CALCULATION LOGIC
                                  const dailyPassengers =
                                    busRoute.expectedPassengers;
                                  const busCapacity = 70;
                                  const oneWayDuration =
                                    selectedRoute.duration_min;
                                  const layoverTime = 10; // minutes for turnaround
                                  const roundTripTime =
                                    oneWayDuration * 2 + layoverTime;
                                  const operatingHours = 16 * 60; // 16 hours in minutes

                                  // Step 1: How many trips needed to move all passengers?
                                  const tripsNeeded = Math.ceil(
                                    dailyPassengers / busCapacity
                                  );

                                  // Step 2: How many trips can 1 bus make in a day?
                                  const tripsPerBus = Math.floor(
                                    operatingHours / roundTripTime
                                  );

                                  // Step 3: How many buses do we need?
                                  const busesNeeded = Math.ceil(
                                    tripsNeeded / tripsPerBus
                                  );

                                  // Step 4: What's the frequency? (how often does a bus depart)
                                  const actualFrequency = Math.floor(
                                    roundTripTime / busesNeeded
                                  );

                                  // Step 5: Calculate actual capacity
                                  const totalTripsPerDay =
                                    tripsPerBus * busesNeeded;
                                  const totalDailyCapacity =
                                    totalTripsPerDay * busCapacity;

                                  // Step 6: Check utilization
                                  const utilizationRate = (
                                    (dailyPassengers / totalDailyCapacity) *
                                    100
                                  ).toFixed(1);

                                  return (
                                    <div className="mb-m p-m bg-primary-blue/5 border border-primary-blue/20 rounded-lg">
                                      <div className="flex items-center gap-s mb-s">
                                        <TrendingUp className="w-4 h-4 text-primary-blue" />
                                        <span className="font-display font-semibold text-primary-blue">
                                          AI Recommendation
                                        </span>
                                      </div>
                                      <div className="grid grid-cols-2 gap-m text-body-sm mb-s">
                                        <div className="text-cool-slate">
                                          <span className="font-medium text-graphite-gray">
                                            👥 Daily Pax:
                                          </span>{" "}
                                          {dailyPassengers}
                                        </div>
                                        <div className="text-cool-slate">
                                          <span className="font-medium text-graphite-gray">
                                            🚍 Buses Needed:
                                          </span>{" "}
                                          <span className="text-primary-blue font-bold">
                                            {busesNeeded}
                                          </span>
                                        </div>
                                        <div className="text-cool-slate">
                                          <span className="font-medium text-graphite-gray">
                                            ⏱️ Frequency:
                                          </span>{" "}
                                          <span className="text-primary-blue font-bold">
                                            ~{actualFrequency} min
                                          </span>
                                        </div>
                                        <div className="text-cool-slate">
                                          <span className="font-medium text-graphite-gray">
                                            📈 Utilization:
                                          </span>{" "}
                                          <span
                                            className={
                                              parseFloat(utilizationRate) > 90
                                                ? "text-status-error font-bold"
                                                : parseFloat(utilizationRate) >
                                                  70
                                                ? "text-status-warning font-bold"
                                                : "text-status-success font-bold"
                                            }
                                          >
                                            {utilizationRate}%
                                          </span>
                                        </div>
                                      </div>
                                    </div>
                                  );
                                })()}

                              {/* Route Options */}
                              <div className="space-y-s mb-m">
                                {busResult.routes.map(
                                  (routeOption, routeIndex) => (
                                    <div
                                      key={routeIndex}
                                      onClick={() =>
                                        selectRoute(busIndex, routeIndex)
                                      }
                                      className={`p-m rounded-lg border-2 cursor-pointer transition-all ${
                                        busResult.selectedRouteIndex ===
                                        routeIndex
                                          ? "border-primary-blue bg-primary-blue/10"
                                          : "border-cool-slate/20 hover:border-primary-blue/50"
                                      }`}
                                    >
                                      <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                          <div className="flex items-center gap-s mb-s">
                                            <span className="font-display font-medium text-graphite-gray">
                                              Route {routeIndex + 1}
                                            </span>
                                            {busResult.selectedRouteIndex ===
                                              routeIndex && (
                                              <span className="text-xs bg-primary-blue text-white px-2 py-0.5 rounded-md">
                                                Selected
                                              </span>
                                            )}
                                            <span className="text-xs bg-highlight-mint/20 text-highlight-mint/90 px-2 py-0.5 rounded-md font-medium">
                                              Rank #{routeOption.rank}
                                            </span>
                                          </div>
                                          <div className="grid grid-cols-2 gap-s text-body-sm text-cool-slate">
                                            <div>
                                              📏{" "}
                                              {routeOption.distance_km.toFixed(
                                                1
                                              )}{" "}
                                              km
                                            </div>
                                            <div>
                                              ⏱️{" "}
                                              {routeOption.duration_min.toFixed(
                                                0
                                              )}{" "}
                                              min
                                            </div>
                                            <div>
                                              🎯 AI Score:{" "}
                                              {routeOption.gemini_score.toFixed(
                                                1
                                              )}
                                              /10
                                            </div>
                                            <div>
                                              🚦 Traffic:{" "}
                                              {routeOption.traffic_score.toFixed(
                                                1
                                              )}
                                              /10
                                            </div>
                                          </div>
                                          {routeOption.reasoning && (
                                            <p className="text-xs text-cool-slate/80 mt-s italic">
                                              {routeOption.reasoning}
                                            </p>
                                          )}
                                        </div>
                                      </div>
                                    </div>
                                  )
                                )}
                              </div>

                              {/* Save Button */}
                              <button
                                onClick={() => saveSelectedRoute(busIndex)}
                                disabled={savingRoute === busRoute.id}
                                className="w-full bg-highlight-mint hover:opacity-90 text-white py-s rounded-lg font-medium transition disabled:opacity-50 flex items-center justify-center gap-s"
                              >
                                {savingRoute === busRoute.id ? (
                                  <>
                                    <LoadingSpinner size="sm" />
                                    Saving...
                                  </>
                                ) : (
                                  <>
                                    <Bus className="w-4 h-4" />
                                    Save Route{" "}
                                    {busResult.selectedRouteIndex! + 1} for{" "}
                                    {busResult.bus_number}
                                  </>
                                )}
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
                <div className="bg-white rounded-lg shadow p-xl">
                  <div className="flex justify-between items-center mb-l">
                    <h2 className="font-display text-h2 text-graphite-gray">
                      Multi-Bus Route Planning
                    </h2>
                    <button
                      type="button"
                      onClick={addBusRoute}
                      className="flex items-center gap-s px-m py-s rounded-lg font-medium transition-colors border border-primary-blue text-primary-blue hover:bg-primary-blue hover:text-white disabled:opacity-30"
                      disabled={busRoutes.length >= 20}
                    >
                      <Plus className="w-4 h-4" />
                      Add Bus ({busRoutes.length}/20)
                    </button>
                  </div>

                  <form onSubmit={handlePlanRoute} className="space-y-l">
                    {/* Bus Routes List */}
                    <div className="space-y-l max-h-[55vh]  overflow-y-auto p-xs">
                      {busRoutes.map((route, index) => (
                        <div
                          key={route.id}
                          className="border border-cool-slate/20 rounded-lg p-l bg-warm-neutral-sand/60"
                        >
                          <div className="flex justify-between items-center mb-m">
                            <div className="flex items-center gap-s">
                              <div
                                className="w-4 h-4 rounded-full"
                                style={{ backgroundColor: route.color }}
                              />
                              <input
                                type="text"
                                value={route.busNumber}
                                onChange={(e) =>
                                  updateBusRoute(
                                    route.id,
                                    "busNumber",
                                    e.target.value
                                  )
                                }
                                className="font-semibold font-display text-graphite-gray bg-transparent border-none focus:outline-none"
                              />
                            </div>
                            {busRoutes.length > 1 && (
                              <button
                                type="button"
                                onClick={() => removeBusRoute(route.id)}
                                className="text-status-error hover:opacity-80"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            )}
                          </div>

                          <div className="space-y-m">
                            <div>
                              <label className="block text-body-sm font-medium text-cool-slate mb-s">
                                <Navigation className="w-3 h-3 inline mr-xs" />
                                Source Location
                              </label>
                              <input
                                id={`source-${route.id}`}
                                type="text"
                                value={route.source}
                                onChange={(e) =>
                                  updateBusRoute(
                                    route.id,
                                    "source",
                                    e.target.value
                                  )
                                }
                                className="w-full px-m py-s border border-cool-slate/50 rounded-lg focus:ring-2 focus:ring-primary-blue/50 focus:border-primary-blue text-graphite-gray bg-white outline-none transition-shadow"
                                placeholder="Start typing location name..."
                                autoComplete="off"
                                required
                              />
                            </div>

                            <div>
                              <label className="block text-body-sm font-medium text-cool-slate mb-s">
                                <MapPin className="w-3 h-3 inline mr-xs" />
                                Destination Location
                              </label>
                              <input
                                id={`dest-${route.id}`}
                                type="text"
                                value={route.destination}
                                onChange={(e) =>
                                  updateBusRoute(
                                    route.id,
                                    "destination",
                                    e.target.value
                                  )
                                }
                                className="w-full px-m py-s border border-cool-slate/50 rounded-lg focus:ring-2 focus:ring-primary-blue/50 focus:border-primary-blue text-graphite-gray bg-white outline-none transition-shadow"
                                placeholder="Start typing location name..."
                                autoComplete="off"
                                required
                              />
                            </div>

                            <div>
                              <label className="block text-body-sm font-medium text-cool-slate mb-s">
                                <Clock className="w-3 h-3 inline mr-xs" />
                                Peak Hour
                              </label>
                              <select
                                value={route.peak_hour}
                                onChange={(e) =>
                                  updateBusRoute(
                                    route.id,
                                    "peak_hour",
                                    e.target.value
                                  )
                                }
                                className="w-full px-m py-s border border-cool-slate/50 rounded-lg focus:ring-2 focus:ring-primary-blue/50 focus:border-primary-blue text-graphite-gray bg-white outline-none"
                              >
                                <option value="morning">Morning Peak</option>
                                <option value="evening">Evening Peak</option>
                                <option value="off-peak">Off-Peak</option>
                              </select>
                            </div>

                            <div>
                              <label className="block text-body-sm font-medium text-cool-slate mb-s">
                                <TrendingUp className="w-3 h-3 inline mr-xs" />
                                Expected Daily Passengers (Optional)
                              </label>
                              <input
                                type="number"
                                value={route.expectedPassengers || ""}
                                onChange={(e) =>
                                  updateBusRoute(
                                    route.id,
                                    "expectedPassengers",
                                    parseInt(e.target.value) || 0
                                  )
                                }
                                className="w-full px-m py-s border border-cool-slate/50 rounded-lg focus:ring-2 focus:ring-primary-blue/50 focus:border-primary-blue text-graphite-gray bg-white outline-none transition-shadow"
                                placeholder="e.g., 500"
                                min="0"
                              />
                              <p className="text-xs text-cool-slate mt-s">
                                AI will suggest bus frequency based on this
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    <button
                      type="submit"
                      disabled={planning}
                      className="w-full bg-highlight-mint hover:opacity-90 text-white py-m rounded-lg font-semibold transition disabled:opacity-50 flex items-center justify-center gap-s text-body"
                    >
                      {planning ? (
                        <>
                          <LoadingSpinner size="sm" />
                          Planning {busRoutes.length} Routes...
                        </>
                      ) : (
                        <>
                          <Bus className="w-5 h-5" />
                          Plan {busRoutes.length} Route
                          {busRoutes.length > 1 ? "s" : ""} with AI
                        </>
                      )}
                    </button>
                  </form>
                </div>
              </div>

              {/* Right Panel - Google Maps */}
              <div className="bg-white rounded-lg shadow p-xl col-span-2">
                <h2 className="font-display text-h2 text-graphite-gray mb-l">
                  Route Visualization
                </h2>
                <div className="relative">
                  <div
                    ref={mapRef}
                    className="w-full h-[600px] rounded-lg border-2 border-cool-slate/20 bg-warm-neutral-sand"
                  />
                  {!mapsLoaded && (
                    <div className="absolute inset-0 flex items-center justify-center bg-warm-neutral-sand rounded-lg">
                      <div className="text-center">
                        <LoadingSpinner size="lg" />
                        <p className="mt-l text-cool-slate font-medium">
                          Loading Google Maps...
                        </p>
                        <p className="text-body-sm text-cool-slate/80 mt-s">
                          Please wait a moment
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Route Legend */}
                {planResults && planResults.length > 0 && (
                  <div className="mt-l space-y-s">
                    <h3 className="font-display font-semibold text-graphite-gray">
                      Route Legend:
                    </h3>
                    <div className="text-body-sm text-cool-slate mb-s">
                      Each bus has 3 route options shown in the same color with
                      different line styles.
                    </div>
                    {planResults.map((busResult, index) => {
                      const busRoute = busRoutes[index];
                      return (
                        <div
                          key={index}
                          className="flex items-center gap-s text-body-sm"
                        >
                          <div
                            className="w-4 h-4 rounded-full"
                            style={{ backgroundColor: busRoute.color }}
                          />
                          <span className="font-medium text-graphite-gray">
                            {busResult.bus_number}
                          </span>
                          <span className="text-cool-slate">
                            - {busResult.total_routes} options (Route{" "}
                            {(busResult.selectedRouteIndex || 0) + 1} selected)
                          </span>
                        </div>
                      );
                    })}

                    {/* Route Path Preview for Selected Routes */}
                    {planResults.map((busResult, index) => {
                      const busRoute = busRoutes[index];
                      const selectedRoute = busResult.routes[busResult.selectedRouteIndex || 0];

                      if (!selectedRoute || !selectedRoute.waypoints || selectedRoute.waypoints.length === 0) {
                        return null;
                      }

                      return (
                        <div key={`path-${index}`} className="border-t border-cool-slate/20 pt-m mt-m">
                          <div className="flex items-center gap-s mb-s">
                            <div
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: busRoute.color }}
                            />
                            <h4 className="font-display font-medium text-graphite-gray">
                              {busResult.bus_number} - Route {(busResult.selectedRouteIndex || 0) + 1}
                            </h4>
                          </div>
                          <RoutePathPreview
                            sourceName={busRoute.source}
                            destName={busRoute.destination}
                            sourceLat={busResult.source.lat}
                            sourceLng={busResult.source.lng}
                            destLat={busResult.destination.lat}
                            destLng={busResult.destination.lng}
                            waypoints={selectedRoute.waypoints}
                            durationMin={selectedRoute.duration_min}
                            distanceKm={selectedRoute.distance_km}
                          />
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {/* Routes Tab */}
        {activeTab === "routes" && (
          <>
            <h1 className="font-display text-h1 text-graphite-gray mb-l">
              All Routes
            </h1>
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-warm-neutral-sand/60">
                    <tr>
                      <th className="px-xl py-m text-left text-label font-semibold text-cool-slate uppercase">
                        Route ID
                      </th>
                      <th className="px-xl py-m text-left text-label font-semibold text-cool-slate uppercase">
                        Name
                      </th>
                      <th className="px-xl py-m text-left text-label font-semibold text-cool-slate uppercase">
                        Distance
                      </th>
                      <th className="px-xl py-m text-left text-label font-semibold text-cool-slate uppercase">
                        Duration
                      </th>
                      <th className="px-xl py-m text-left text-label font-semibold text-cool-slate uppercase">
                        AI Score
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-cool-slate/20">
                    {routes.map((route) => (
                      <tr
                        key={route._id}
                        className="hover:bg-primary-blue/5 transition-colors"
                      >
                        <td className="px-xl py-l text-body-sm font-medium text-graphite-gray">
                          {route.route_id}
                        </td>
                        <td className="px-xl py-l text-body-sm text-cool-slate">
                          {route.name}
                        </td>
                        <td className="px-xl py-l text-body-sm text-cool-slate">
                          {route.total_distance_km.toFixed(1)} km
                        </td>
                        <td className="px-xl py-l text-body-sm text-cool-slate">
                          {route.estimated_duration_min} min
                        </td>
                        <td className="px-xl py-l text-body-sm">
                          <span className="px-m py-xs bg-primary-blue/10 text-primary-blue rounded-full font-medium">
                            {route.gemini_score?.toFixed(1) || "N/A"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {/* Schedules Tab */}
        {activeTab === "schedules" && (
          <>
            <div className="flex justify-between items-center mb-l">
              <h1 className="font-display text-h1 text-graphite-gray">
                All Schedules
              </h1>
              <button
                onClick={async () => {
                  if (!confirm("Update all routes with proper place names? This will fetch location names from Google Maps.")) {
                    return;
                  }
                  try {
                    setLoading(true);
                    const response = await adminAPI.updateAllRoutePlaceNames();
                    alert(`✅ Success!\n\nRoutes updated: ${response.routes_updated}\nPlace names updated: ${response.total_place_names_updated}`);
                    // Refresh schedules
                    await fetchSchedules();
                  } catch (error: any) {
                    alert(`❌ Error: ${error.message}`);
                  } finally {
                    setLoading(false);
                  }
                }}
                className="px-l py-m bg-primary-blue text-white rounded-lg hover:opacity-90 transition-opacity flex items-center gap-s"
              >
                <MapPin className="w-4 h-4" />
                Update Place Names
              </button>
            </div>
            <div className="space-y-l">
              <div className="bg-white rounded-lg shadow overflow-hidden">
                {schedules.length === 0 ? (
                  <div className="p-xxl text-center text-cool-slate">
                    <Clock className="w-12 h-12 mx-auto mb-l text-cool-slate/50" />
                    <p>
                      No schedules created yet. Save a route to auto-generate
                      schedules.
                    </p>
                  </div>
                ) : (
                  <div className="divide-y divide-cool-slate/20">
                    {schedules.map((schedule: any) => {
                      const route = routes.find(
                        (r) => r.route_id === schedule.route_id
                      );
                      const departureTimes = schedule.departure_times || [];

                      return (
                        <div
                          key={schedule._id}
                          className="p-xl hover:bg-primary-blue/5 transition-colors"
                        >
                          <div className="flex justify-between items-start mb-l">
                            <div>
                              <div className="flex items-center gap-m mb-s">
                                <h3 className="font-display text-h3 text-graphite-gray">
                                  {route?.name || schedule.route_id}
                                </h3>
                                <span
                                  className={`px-m py-xs text-xs rounded-full font-medium ${
                                    schedule.active
                                      ? "bg-status-success/10 text-status-success"
                                      : "bg-cool-slate/10 text-cool-slate"
                                  }`}
                                >
                                  {schedule.active ? "Active" : "Inactive"}
                                </span>
                                <span className="px-m py-xs text-xs rounded-full bg-primary-blue/10 text-primary-blue capitalize font-medium">
                                  {schedule.peak_hour}
                                </span>
                              </div>
                              <div className="flex items-center gap-l text-body-sm text-cool-slate">
                                <span>
                                  🚌 Bus:{" "}
                                  {schedule.bus_number || schedule.bus_id}
                                </span>
                                <span>📍 Route: {schedule.route_id}</span>
                              </div>
                            </div>

                            <div className="text-right">
                              <div className="font-display text-h2 font-bold text-primary-blue">
                                {schedule.suggested_buses_count}
                              </div>
                              <div className="text-body-sm text-cool-slate">
                                Buses Needed
                              </div>
                            </div>
                          </div>

                          <div className="grid md:grid-cols-4 gap-l mb-l">
                            <div className="bg-warm-neutral-sand/60 p-m rounded-lg">
                              <div className="text-label text-cool-slate mb-xs">
                                Frequency
                              </div>
                              <div className="font-display text-h3 font-semibold text-graphite-gray">
                                {schedule.frequency_min} min
                              </div>
                            </div>
                            <div className="bg-warm-neutral-sand/60 p-m rounded-lg">
                              <div className="text-label text-cool-slate mb-xs">
                                First Departure
                              </div>
                              <div className="font-display text-h3 font-semibold text-graphite-gray">
                                {departureTimes[0] ||
                                  schedule.start_time ||
                                  "N/A"}
                              </div>
                            </div>
                            <div className="bg-warm-neutral-sand/60 p-m rounded-lg">
                              <div className="text-label text-cool-slate mb-xs">
                                Last Departure
                              </div>
                              <div className="font-display text-h3 font-semibold text-graphite-gray">
                                {departureTimes[departureTimes.length - 1] ||
                                  schedule.end_time ||
                                  "N/A"}
                              </div>
                            </div>
                            <div className="bg-warm-neutral-sand/60 p-m rounded-lg">
                              <div className="text-label text-cool-slate mb-xs">
                                Total Trips
                              </div>
                              <div className="font-display text-h3 font-semibold text-graphite-gray">
                                {departureTimes.length || 0}
                              </div>
                            </div>
                          </div>

                          {departureTimes.length > 0 && (
                            <div>
                              <div className="flex items-center justify-between mb-s">
                                <h4 className="text-label font-medium text-cool-slate">
                                  🕐 Departure Times (for passenger ETA
                                  tracking)
                                </h4>
                                <span className="text-xs text-cool-slate">
                                  {departureTimes.length} departures
                                </span>
                              </div>
                              <div className="bg-warm-neutral-sand/60 p-m rounded-lg max-h-32 overflow-y-auto">
                                <div className="grid grid-cols-6 sm:grid-cols-8 md:grid-cols-10 lg:grid-cols-12 gap-s">
                                  {departureTimes.map(
                                    (time: string, idx: number) => (
                                      <div
                                        key={idx}
                                        className="text-xs font-mono bg-white px-s py-xs rounded-md border border-cool-slate/20 text-center text-cool-slate"
                                      >
                                        {time}
                                      </div>
                                    )
                                  )}
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Action Buttons */}
                          <div className="mt-l flex gap-m">
                            <button
                              onClick={() => {
                                setSelectedRouteForDeploy({
                                  id: schedule.route_id,
                                  name: route?.name || schedule.route_id
                                });
                                setDeployModalOpen(true);
                              }}
                              className="px-m py-s bg-primary-blue text-white rounded-lg hover:bg-primary-blue/90 transition-colors text-body-sm font-medium"
                            >
                              🚌 Deploy Multiple Buses
                            </button>
                            <button
                              onClick={() => setMatrixViewRouteId(schedule.route_id)}
                              className="px-m py-s bg-warm-neutral-sand border border-cool-slate/20 text-graphite-gray rounded-lg hover:bg-warm-neutral-sand/80 transition-colors text-body-sm font-medium"
                            >
                              📊 View Schedule Matrix
                            </button>
                          </div>

                          {/* Show intermediate stops if available */}
                          {route?.intermediate_stops && route.intermediate_stops.length > 0 && (
                            <div className="mt-l">
                              <RouteStopsDisplay
                                stops={route.intermediate_stops}
                                routeName={route.name}
                              />
                            </div>
                          )}

                          {/* Show schedule matrix if selected */}
                          {matrixViewRouteId === schedule.route_id && (
                            <div className="mt-l">
                              <ScheduleMatrix routeId={schedule.route_id} />
                              <button
                                onClick={() => setMatrixViewRouteId(null)}
                                className="mt-m px-m py-s bg-cool-slate/10 text-cool-slate rounded-lg hover:bg-cool-slate/20 transition-colors text-body-sm"
                              >
                                Hide Matrix
                              </button>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </main>

      {/* Bus Deployment Modal */}
      {selectedRouteForDeploy && (
        <BusDeploymentModal
          routeId={selectedRouteForDeploy.id}
          routeName={selectedRouteForDeploy.name}
          isOpen={deployModalOpen}
          onClose={() => {
            setDeployModalOpen(false);
            setSelectedRouteForDeploy(null);
          }}
          onSuccess={() => {
            fetchData(); // Refresh schedules
          }}
        />
      )}
    </div>
  );
}
