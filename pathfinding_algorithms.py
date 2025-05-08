# pathfinding_algorithms.py

import heapq
from math import sqrt
from collections import deque

class PathfindingAlgorithms:
    # ... (các hàm a_star, dijkstra, bfs giữ nguyên) ...
    @staticmethod
    def a_star(grid, start, goal):
        def heuristic(a, b):
            return sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
        rows, cols = len(grid), len(grid[0])
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        f_score = {start: heuristic(start, goal)}
        closed_set = set()
        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path
            if current in closed_set:
                continue
            closed_set.add(current)
            for dr, dc in directions:
                neighbor = (current[0] + dr, current[1] + dc)
                if (0 <= neighbor[0] < rows and
                    0 <= neighbor[1] < cols and
                    grid[neighbor[0]][neighbor[1]] == 0 and
                    neighbor not in closed_set):
                    tentative_g = g_score[current] + 1
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
        return []

    @staticmethod
    def dijkstra(grid, start, goal):
        rows, cols = len(grid), len(grid[0])
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        distance = {start: 0}
        queue = [(0, start)]
        came_from = {}
        visited = set()
        while queue:
            dist, current = heapq.heappop(queue)
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path
            if current in visited:
                continue
            visited.add(current)
            for dr, dc in directions:
                neighbor = (current[0] + dr, current[1] + dc)
                if (0 <= neighbor[0] < rows and
                    0 <= neighbor[1] < cols and
                    grid[neighbor[0]][neighbor[1]] == 0 and
                    neighbor not in visited):
                    new_dist = dist + 1
                    if neighbor not in distance or new_dist < distance[neighbor]:
                        distance[neighbor] = new_dist
                        came_from[neighbor] = current
                        heapq.heappush(queue, (new_dist, neighbor))
        return []

    @staticmethod
    def bfs(grid, start, goal):
        rows, cols = len(grid), len(grid[0])
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        queue = deque([start])
        visited = {start}
        came_from = {}
        while queue:
            current = queue.popleft()
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path
            for dr, dc in directions:
                neighbor = (current[0] + dr, current[1] + dc)
                if (0 <= neighbor[0] < rows and
                    0 <= neighbor[1] < cols and
                    grid[neighbor[0]][neighbor[1]] == 0 and
                    neighbor not in visited):
                    visited.add(neighbor)
                    came_from[neighbor] = current
                    queue.append(neighbor)
        return []

ALGORITHM_MAP = {
    "A* (A-star)": PathfindingAlgorithms.a_star,
    "Dijkstra": PathfindingAlgorithms.dijkstra,
    "BFS": PathfindingAlgorithms.bfs
}

ALGORITHM_INFO = {
    "A* (A-star)": "Thuật toán tìm đường tối ưu, cân bằng giữa quãng đường và ước lượng đến đích.",
    "Dijkstra": "Tìm đường đi ngắn nhất dựa trên chi phí thực tế từ điểm bắt đầu.",
    "BFS": "Tìm đường đi có số bước ít nhất, không xét trọng số cạnh."
}

# --- Thêm chi phí cho thuật toán ---
ALGORITHM_COSTS = {
    "A* (A-star)": 20,  # Ví dụ: A* tốn 20 tiền
    "Dijkstra": 15,   # Ví dụ: Dijkstra tốn 15 tiền
    "BFS": 10         # Ví dụ: BFS tốn 10 tiền
}

# Thuật toán và chi phí mặc định khi nhấn 'P' (ví dụ dùng A*)
DEFAULT_PATHFINDING_ALGORITHM_NAME = "A* (A-star)"
DEFAULT_PATHFINDING_COST = ALGORITHM_COSTS.get(DEFAULT_PATHFINDING_ALGORITHM_NAME, 0)