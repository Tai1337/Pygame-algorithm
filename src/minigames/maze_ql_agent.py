import numpy as np
import csv
import os
import src.config as config

class MazeQLearningAgent:
    def __init__(self, actions, maze_shape, learning_rate, discount_factor, 
                 epsilon_start, epsilon_end, epsilon_decay_rate, initial_q_value):
        self.actions = actions
        self.maze_shape = maze_shape
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon_start
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay_rate = epsilon_decay_rate
        self.q_table = {}
        self.initial_q_value = initial_q_value

    def get_q_value(self, state, action):
        state = self._serialize_state(state)
        if state not in self.q_table:
            self.q_table[state] = {a: self.initial_q_value for a in self.actions}
        return self.q_table[state].get(action, self.initial_q_value)

    def update_q_table(self, state, action, reward, next_state):
        state = self._serialize_state(state)
        next_state = self._serialize_state(next_state)
        
        if state not in self.q_table:
            self.q_table[state] = {a: self.initial_q_value for a in self.actions}
        if next_state not in self.q_table:
            self.q_table[next_state] = {a: self.initial_q_value for a in self.actions}
        
        current_q = self.q_table[state][action]
        max_next_q = max(self.q_table[next_state].values())
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        self.q_table[state][action] = new_q

    def choose_action(self, state, learn=True):
        state = self._serialize_state(state)
        if state not in self.q_table:
            self.q_table[state] = {a: self.initial_q_value for a in self.actions}
        
        if learn and np.random.random() < self.epsilon:
            return np.random.choice(self.actions)
        else:
            q_values = self.q_table[state]
            max_q = max(q_values.values())
            best_actions = [a for a, q in q_values.items() if q == max_q]
            return np.random.choice(best_actions)

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay_rate)

    def save_q_table(self, file_path):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['state', 'action', 'q_value'])
                for state, actions in self.q_table.items():
                    for action, q_value in actions.items():
                        writer.writerow([state, action, q_value])
            print(f"Q-table saved to {file_path}")
        except Exception as e:
            print(f"Error saving Q-table to {file_path}: {e}")

    def load_q_table(self, file_path):
        try:
            if not os.path.exists(file_path):
                print(f"Q-table file {file_path} does not exist.")
                return
            self.q_table = {}
            with open(file_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    state = row['state']
                    action = int(row['action'])
                    q_value = float(row['q_value'])
                    if state not in self.q_table:
                        self.q_table[state] = {a: self.initial_q_value for a in self.actions}
                    self.q_table[state][action] = q_value
            print(f"Q-table loaded from {file_path}")
        except Exception as e:
            print(f"Error loading Q-table from {file_path}: {e}")

    def _serialize_state(self, state):
        """Convert state tuple to a string for dictionary key."""
        mouse_row, mouse_col, cheese_set = state
        cheese_str = ','.join([f"{r}:{c}" for r, c in sorted(cheese_set)])
        return f"{mouse_row},{mouse_col}|{cheese_str}"