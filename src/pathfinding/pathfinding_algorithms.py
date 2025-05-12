# src/pathfinding/pathfinding_algorithms.py

import heapq
from math import sqrt
from collections import deque
# Import QLearningAgent từ cùng package pathfinding
import numpy as np
import src.config as config # Import config

class PathfindingAlgorithms:
    @staticmethod
    def heuristic(a, b):
        # Kiểm tra đầu vào cơ bản
        if not (isinstance(a, (list, tuple)) and len(a) == 2 and 
                isinstance(b, (list, tuple)) and len(b) == 2):
            # print(f"Lỗi heuristic: Đầu vào không hợp lệ. a: {a}, b: {b}") # Gỡ lỗi nếu cần
            return float('inf') # Trả về giá trị lớn nếu đầu vào không hợp lệ
        try:
            return sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
        except TypeError: # Bắt lỗi nếu a[0], a[1], b[0], b[1] không phải là số
            # print(f"Lỗi heuristic TypeError: Đầu vào không phải số. a: {a}, b: {b}") # Gỡ lỗi nếu cần
            return float('inf')

    @staticmethod
    def a_star(grid, start, goal):
        visited_cnt = 0
        rows, cols = len(grid), len(grid[0])
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        # Khởi tạo g_score an toàn hơn
        g_score = {}
        for r in range(rows):
            for c in range(cols):
                g_score[(r, c)] = float('inf')
        g_score[start] = 0

        # Khởi tạo f_score (chỉ cần cho điểm bắt đầu để đưa vào open_set)
        # f_score của các nút khác sẽ được tính khi cần
        start_h = PathfindingAlgorithms.heuristic(start, goal)
        open_set = [(g_score[start] + start_h, start_h, start)] # (f_score, h_score, node)
        
        came_from = {}
        open_set_hash = {start} # Theo dõi các nút trong open_set để tránh trùng lặp

        while open_set:
            current_f, current_h, current_node = heapq.heappop(open_set) # Sửa lại tên biến ở đây

            # Nếu f_score hiện tại lớn hơn g_score đã biết + heuristic (tức là có đường tốt hơn đã được xử lý)
            # hoặc nếu g_score của current_node đã tốt hơn giá trị hiện tại (do có thể có nhiều entry cho cùng 1 node trong heap)
            # Điều này giúp bỏ qua các đường đi đã lỗi thời đến current_node
            if current_f > g_score[current_node] + current_h : # current_h là heuristic(current_node, goal)
                 continue


            if current_node == goal: # Đổi current thành current_node
                path = []
                temp = current_node # Đổi current thành current_node
                while temp in came_from:
                    path.append(temp)
                    temp = came_from[temp]
                path.append(start)
                path.reverse()
                return path, visited_cnt

            # Không cần remove khỏi open_set_hash ở đây nữa nếu dùng cách kiểm tra f_score ở trên
            # if current_node in open_set_hash:
            #    open_set_hash.remove(current_node)
            
            visited_cnt +=1

            for dr, dc in directions:
                neighbor = (current_node[0] + dr, current_node[1] + dc) # Đổi current thành current_node

                if (0 <= neighbor[0] < rows and
                    0 <= neighbor[1] < cols and
                    grid[neighbor[0]][neighbor[1]] == 0): # Ô đi được
                    
                    tentative_g_score = g_score[current_node] + 1 # Đổi current thành current_node

                    if tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current_node # Đổi current thành current_node
                        g_score[neighbor] = tentative_g_score
                        neighbor_h = PathfindingAlgorithms.heuristic(neighbor, goal)
                        neighbor_f = tentative_g_score + neighbor_h
                        
                        heapq.heappush(open_set, (neighbor_f, neighbor_h, neighbor))
                        # open_set_hash.add(neighbor) # Không cần thiết nếu kiểm tra f_score ở trên
                                                    # hoặc nếu bạn muốn tránh thêm nhiều lần, bạn có thể giữ lại
                                                    # nhưng logic kiểm tra f_score khi pop thường hiệu quả hơn
        return [], visited_cnt

    @staticmethod
    def dijkstra(grid, start, goal):
        visited_count = 0
        rows, cols = len(grid), len(grid[0])
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        distance = {node: float('inf') for r_idx, r in enumerate(grid) for c_idx, _ in enumerate(r) for node in [(r_idx, c_idx)]}
        distance[start] = 0
        
        queue = [(0, start)] # (dist, node)
        came_from = {}
        
        processed_nodes = set() 

        while queue:
            dist, current = heapq.heappop(queue)

            if current in processed_nodes:
                continue
            processed_nodes.add(current)
            visited_count += 1

            if current == goal:
                path = []
                temp = current
                while temp in came_from:
                    path.append(temp)
                    temp = came_from[temp]
                path.append(start)
                path.reverse()
                return path, visited_count

            for dr, dc in directions:
                neighbor = (current[0] + dr, current[1] + dc)
                if (0 <= neighbor[0] < rows and
                    0 <= neighbor[1] < cols and
                    grid[neighbor[0]][neighbor[1]] == 0): # Ô đi được
                    
                    new_dist = dist + 1 # Chi phí di chuyển là 1
                    if new_dist < distance[neighbor]: # Nếu tìm thấy đường ngắn hơn đến neighbor
                        distance[neighbor] = new_dist
                        came_from[neighbor] = current
                        heapq.heappush(queue, (new_dist, neighbor))
        return [], visited_count

    @staticmethod
    def bfs(grid, start, goal):
        visited_cnt = 0
        rows, cols = len(grid), len(grid[0])
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        queue = deque([start])
        visited = {start} # Chỉ cần set visited là đủ, không cần closed_set riêng
        came_from = {}

        while queue:
            current = queue.popleft()
            visited_cnt += 1 # Tăng khi một nút được lấy ra khỏi queue để xử lý

            if current == goal:
                path = []
                temp = current
                while temp in came_from:
                    path.append(temp)
                    temp = came_from[temp]
                path.append(start)
                path.reverse()
                return path, visited_cnt

            for dr, dc in directions:
                neighbor = (current[0] + dr, current[1] + dc)
                if (0 <= neighbor[0] < rows and
                    0 <= neighbor[1] < cols and
                    grid[neighbor[0]][neighbor[1]] == 0 and
                    neighbor not in visited):
                    visited.add(neighbor)
                    came_from[neighbor] = current
                    queue.append(neighbor)
        return [], visited_cnt
    
    @staticmethod
    def greedy_bfs(grid, start, goal):
        visited_cnt = 0
        rows, cols = len(grid), len(grid[0])
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        # Priority queue lưu (heuristic_value, node)
        open_set = [(PathfindingAlgorithms.heuristic(start, goal), start)]
        came_from = {}
        visited_nodes = {start} # Để tránh thêm lại vào open_set và xử lý lặp

        while open_set:
            _, current = heapq.heappop(open_set)
            visited_cnt +=1 # Đếm nút được pop ra để mở rộng

            if current == goal:
                path = []
                temp = current
                while temp in came_from:
                    path.append(temp)
                    temp = came_from[temp]
                path.append(start)
                path.reverse()
                return path, visited_cnt

            for dr, dc in directions:
                neighbor = (current[0] + dr, current[1] + dc)
                if (0 <= neighbor[0] < rows and
                    0 <= neighbor[1] < cols and
                    grid[neighbor[0]][neighbor[1]] == 0 and
                    neighbor not in visited_nodes): # Chỉ thêm nếu chưa từng thêm vào open_set/visited
                        visited_nodes.add(neighbor) # Đánh dấu đã xem xét để thêm vào hàng đợi
                        came_from[neighbor] = current
                        priority = PathfindingAlgorithms.heuristic(neighbor, goal)
                        heapq.heappush(open_set, (priority, neighbor))
        return [], visited_cnt
    
    @staticmethod
    def beam_search(grid, start, goal, beam_width=config.BEAM_SEARCH_WIDTH_DEFAULT):
        rows, cols = len(grid), len(grid[0])
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        if not (isinstance(start, (list, tuple)) and len(start) == 2):
            return [], 0
        
        # current_beam: list của (heuristic_value, path)
        current_beam = [(PathfindingAlgorithms.heuristic(start, goal), [start])]
        
        # Set để theo dõi các nút đã được mở rộng (expanded) để tính visited_cnt chính xác
        expanded_nodes_for_count = set()

        # Giới hạn số lần lặp để tránh vòng lặp vô hạn (ví dụ, nếu goal không thể đạt được)
        # Một giới hạn hợp lý có thể là số ô trên bản đồ
        for _iteration_count in range(rows * cols): 
            potential_next_candidates = []

            if not current_beam:
                return [], len(expanded_nodes_for_count)
            
            for h_value, path in current_beam:
                current_node = path[-1]

                if not (isinstance(current_node, (list, tuple)) and len(current_node) == 2):
                    continue 

                # Đếm nút được mở rộng (lấy ra từ beam để tạo các nút con)
                if current_node not in expanded_nodes_for_count:
                    expanded_nodes_for_count.add(current_node)

                if current_node == goal:
                    return path, len(expanded_nodes_for_count)

                for dr, dc in directions:
                    neighbor_r, neighbor_c = current_node[0] + dr, current_node[1] + dc
                    neighbor = (neighbor_r, neighbor_c)

                    if (0 <= neighbor_r < rows and
                        0 <= neighbor_c < cols and
                        grid[neighbor_r][neighbor_c] == 0):
                        # Tránh đi ngược lại ngay trong path hiện tại để tránh vòng lặp nhỏ đơn giản
                        # Một cách kiểm tra tốt hơn là không thêm neighbor nếu nó đã nằm trong path hiện tại.
                        if neighbor in path: 
                            continue
                        
                        new_path = path + [neighbor]
                        heuristic_val = PathfindingAlgorithms.heuristic(neighbor, goal)
                        potential_next_candidates.append((heuristic_val, new_path))
            
            if not potential_next_candidates: # Không có ứng viên nào được tạo ra
                return [], len(expanded_nodes_for_count)

            # Sắp xếp tất cả các ứng viên và chọn ra top 'beam_width'
            potential_next_candidates.sort(key=lambda x: x[0]) # Sắp xếp theo heuristic
            current_beam = potential_next_candidates[:beam_width]
        
        return [], len(expanded_nodes_for_count)
    
    @staticmethod
    def backtracking_search(grid, start, goal, max_depth_factor=1.5, max_calls_factor=5):
        rows, cols = len(grid), len(grid[0])
        # Giới hạn dựa trên kích thước bản đồ
        MAX_RECURSION_DEPTH = int(rows * cols * max_depth_factor) 
        MAX_VISITED_CALLS = int(rows * cols * max_calls_factor)    
        
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)] 
        
        _visited_call_count = 0 
     
        def solve_recursive(current_r, current_c, current_path, current_depth):
            nonlocal _visited_call_count 
            _visited_call_count += 1 # Đếm mỗi lần gọi hàm đệ quy (mỗi lần "thăm" một ô)

            if current_depth > MAX_RECURSION_DEPTH:
                return None 
            if _visited_call_count > MAX_VISITED_CALLS:
                return None 

            current_path.append((current_r, current_c)) 

            if (current_r, current_c) == goal:
                return list(current_path) 

            # Ưu tiên các hướng (có thể thử nghiệm để xem có cải thiện không)
            # random.shuffle(directions) # Bỏ nếu muốn thứ tự cố định
            for dr, dc in directions:
                next_r, next_c = current_r + dr, current_c + dc

                if (0 <= next_r < rows and 0 <= next_c < cols and
                    grid[next_r][next_c] == 0 and
                    (next_r, next_c) not in current_path): # Không đi lại vào ô đã có trong path hiện tại

                    found_path = solve_recursive(next_r, next_c, current_path, current_depth + 1) 
                    if found_path:
                        return found_path 

            current_path.pop() # Quay lui: xóa ô hiện tại khỏi đường đi nếu không tìm thấy giải pháp từ đây
            return None

        final_path = solve_recursive(start[0], start[1], [], 0)
        
        if final_path:
            return final_path, _visited_call_count
        else:
            return [], _visited_call_count
    
ALGORITHM_MAP = {
    "A* (A-star)": PathfindingAlgorithms.a_star,
    "Dijkstra": PathfindingAlgorithms.dijkstra,
    "BFS": PathfindingAlgorithms.bfs,
    "Greedy BFS": PathfindingAlgorithms.greedy_bfs,
    "BEAM_SEARCH": PathfindingAlgorithms.beam_search, # Sẽ dùng beam_width mặc định từ config
    "Backtracking": PathfindingAlgorithms.backtracking_search,
}

ALGORITHM_INFO = {
    "A* (A-star)": "Thuật toán tìm đường tối ưu, cân bằng giữa quãng đường và ước lượng đến đích.",
    "Dijkstra": "Tìm đường đi ngắn nhất dựa trên chi phí thực tế từ điểm bắt đầu.",
    "BFS": "Tìm đường đi có số bước ít nhất, không xét trọng số cạnh.",
    "Greedy BFS": "Tìm đường đi dựa trên ước lượng khoảng cách đến đích, không tối ưu.",
    "BEAM_SEARCH": f"Tìm kiếm theo chùm (rộng {config.BEAM_SEARCH_WIDTH_DEFAULT}), giới hạn số nút mở rộng ở mỗi bước. Nhanh, không tối ưu, có thể không tìm thấy đường.",
    "Backtracking": "Tìm kiếm theo chiều sâu, quay lui khi không tìm thấy đường đi. Có thể chậm hơn cho các bài toán lớn.",
}

# DEFAULT_PATHFINDING_ALGORITHM_NAME đã được chuyển vào config.py