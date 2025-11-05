import networkx as nx
from typing import List, Tuple, Dict, Optional
import heapq


class DijkstraPathfinder:
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
    
    def find_shortest_path(self, source: Tuple[float, float], target: Tuple[float, float]) -> Optional[List[Tuple[float, float]]]:
        """
        Find shortest path using Dijkstra's algorithm
        """
        try:
            path = nx.dijkstra_path(self.graph, source, target, weight='weight')
            return path
        except nx.NetworkXNoPath:
            print(f"No path found between {source} and {target}")
            return None
        except nx.NodeNotFound:
            print(f"Node not found in graph")
            return None
    
    def find_k_shortest_paths(self, source: Tuple[float, float], target: Tuple[float, float], k: int = 5) -> List[Dict]:
        """
        Find k shortest paths using Yen's algorithm
        Returns list of paths with their costs
        """
        try:
            paths = []
            
            # Use simple k-shortest paths if available in networkx
            for i, path in enumerate(nx.shortest_simple_paths(self.graph, source, target, weight='weight')):
                if i >= k:
                    break
                
                # Calculate path cost
                cost = sum(self.graph[path[j]][path[j+1]]['weight'] for j in range(len(path)-1))
                distance = sum(self.graph[path[j]][path[j+1]].get('distance', 0) for j in range(len(path)-1))
                
                paths.append({
                    'path': path,
                    'cost': cost,
                    'distance_m': distance,
                    'distance_km': distance / 1000
                })
            
            return paths
        except Exception as e:
            print(f"Error finding k shortest paths: {e}")
            return []
    
    def find_shortest_distance(self, source: Tuple[float, float], target: Tuple[float, float]) -> Optional[float]:
        """
        Find shortest distance (cost) between source and target
        """
        try:
            distance = nx.dijkstra_path_length(self.graph, source, target, weight='weight')
            return distance
        except:
            return None
    
    def manual_dijkstra(self, source: Tuple[float, float], target: Tuple[float, float]) -> Optional[Tuple[List, float]]:
        """
        Manual implementation of Dijkstra's algorithm for educational purposes
        """
        # Initialize
        distances = {node: float('infinity') for node in self.graph.nodes()}
        distances[source] = 0
        previous = {node: None for node in self.graph.nodes()}
        
        # Priority queue: (distance, node)
        pq = [(0, source)]
        visited = set()
        
        while pq:
            current_distance, current_node = heapq.heappop(pq)
            
            if current_node in visited:
                continue
            
            visited.add(current_node)
            
            # Found target
            if current_node == target:
                # Reconstruct path
                path = []
                node = target
                while node is not None:
                    path.append(node)
                    node = previous[node]
                path.reverse()
                return path, current_distance
            
            # Check neighbors
            for neighbor in self.graph.neighbors(current_node):
                if neighbor in visited:
                    continue
                
                edge_weight = self.graph[current_node][neighbor].get('weight', 1)
                distance = current_distance + edge_weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current_node
                    heapq.heappush(pq, (distance, neighbor))
        
        return None, float('infinity')
    
    def get_path_details(self, path: List[Tuple[float, float]]) -> Dict:
        """
        Get detailed information about a path
        """
        if not path or len(path) < 2:
            return {}
        
        total_distance = 0
        total_duration = 0
        
        for i in range(len(path) - 1):
            if self.graph.has_edge(path[i], path[i+1]):
                edge = self.graph[path[i]][path[i+1]]
                total_distance += edge.get('distance', 0)
                total_duration += edge.get('duration', 0)
        
        return {
            'waypoints': path,
            'total_distance_m': total_distance,
            'total_distance_km': total_distance / 1000,
            'total_duration_s': total_duration,
            'total_duration_min': total_duration / 60,
            'num_segments': len(path) - 1
        }

