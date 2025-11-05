import networkx as nx
from typing import List, Dict, Tuple, Optional
from app.external.google_maps_client import google_maps_client


class GraphBuilder:
    def __init__(self):
        self.graph = nx.DiGraph()
    
    def build_from_directions(self, directions: List[Dict]) -> nx.DiGraph:
        """
        Build a graph from Google Maps directions
        Nodes: waypoints/intersections
        Edges: road segments with distance and duration
        """
        self.graph.clear()
        
        for route_idx, route in enumerate(directions):
            for leg in route.get("legs", []):
                steps = leg.get("steps", [])
                
                for i, step in enumerate(steps):
                    start_loc = step["start_location"]
                    end_loc = step["end_location"]
                    
                    start_node = (round(start_loc["lat"], 6), round(start_loc["lng"], 6))
                    end_node = (round(end_loc["lat"], 6), round(end_loc["lng"], 6))
                    
                    distance = step["distance"]["value"]  # meters
                    duration = step["duration"]["value"]  # seconds
                    
                    # Add nodes
                    self.graph.add_node(start_node, lat=start_loc["lat"], lng=start_loc["lng"])
                    self.graph.add_node(end_node, lat=end_loc["lat"], lng=end_loc["lng"])
                    
                    # Add edge with weight (we'll use duration as primary weight)
                    self.graph.add_edge(
                        start_node,
                        end_node,
                        distance=distance,
                        duration=duration,
                        weight=duration,
                        instructions=step.get("html_instructions", "")
                    )
        
        return self.graph
    
    def build_simple_graph(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> nx.DiGraph:
        """
        Build a simplified graph with alternative routes
        """
        directions = google_maps_client.get_directions(origin, destination, alternatives=True)
        
        if not directions:
            return self.graph
        
        return self.build_from_directions(directions)
    
    def get_route_details(self, path: List[Tuple[float, float]]) -> Dict:
        """
        Get details for a path through the graph
        """
        total_distance = 0
        total_duration = 0
        instructions = []
        
        for i in range(len(path) - 1):
            if self.graph.has_edge(path[i], path[i + 1]):
                edge = self.graph[path[i]][path[i + 1]]
                total_distance += edge.get("distance", 0)
                total_duration += edge.get("duration", 0)
                if edge.get("instructions"):
                    instructions.append(edge["instructions"])
        
        return {
            "distance_m": total_distance,
            "distance_km": total_distance / 1000,
            "duration_s": total_duration,
            "duration_min": total_duration / 60,
            "waypoints": path,
            "instructions": instructions
        }
    
    def get_alternative_routes(self, origin: Tuple[float, float], destination: Tuple[float, float], k: int = 5) -> List[Dict]:
        """
        Get k alternative routes from origin to destination
        Uses Google Maps to get alternatives, then returns them as structured data
        """
        directions = google_maps_client.get_directions(origin, destination, alternatives=True)
        
        routes = []
        for idx, route in enumerate(directions[:k]):
            leg = route["legs"][0]
            
            # Extract waypoints
            waypoints = []
            for step in leg["steps"]:
                start = step["start_location"]
                waypoints.append((start["lat"], start["lng"]))
            
            # Add end point
            end = leg["end_location"]
            waypoints.append((end["lat"], end["lng"]))
            
            routes.append({
                "route_index": idx,
                "distance_m": leg["distance"]["value"],
                "distance_km": leg["distance"]["value"] / 1000,
                "duration_s": leg["duration"]["value"],
                "duration_min": leg["duration"]["value"] / 60,
                "duration_in_traffic_s": leg.get("duration_in_traffic", {}).get("value", leg["duration"]["value"]),
                "waypoints": waypoints,
                "summary": route.get("summary", ""),
                "steps": len(leg["steps"])
            })
        
        return routes


# Singleton instance
graph_builder = GraphBuilder()

