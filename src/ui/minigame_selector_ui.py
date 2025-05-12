# src/ui/minigame_selector_ui.py
import pygame
import pygame_gui
import src.config as config

class MinigameSelectorUI:
    def __init__(self, ui_manager):
        self.ui_manager = ui_manager
        self.window = None
        self.buttons_with_instances = [] # List of dicts: {"ui_element": button, "instance": minigame_instance}
        self.is_visible = False

    def show(self, available_minigame_instances):
        if self.is_visible and self.window and self.window.alive():
            return # Đã hiển thị rồi

        self.kill() # Dọn dẹp cửa sổ cũ nếu có

        num_games = len(available_minigame_instances)
        if num_games == 0:
            print("MinigameSelectorUI: Không có minigame nào để hiển thị.")
            return

        button_height = config.MINIGAME_SELECTION_BUTTON_HEIGHT
        button_width = config.SOLVE_AI_BUTTON_WIDTH # Tạm dùng chiều rộng của nút AI Solve, hoặc tạo config mới
        margin = config.MINIGAME_SELECTION_BUTTON_MARGIN
        
        prompt_height = 40 
        title_bar_height = 30 
        padding = 20
        
        total_buttons_height = num_games * button_height + (max(0, num_games - 1)) * margin
        window_height = title_bar_height + prompt_height + total_buttons_height + padding * 2 + 10 # Thêm chút đệm dưới
        window_width = config.MINIGAME_SELECTION_WINDOW_WIDTH
        
        window_rect = pygame.Rect(
            (config.SCREEN_WIDTH - window_width) // 2,
            (config.SCREEN_HEIGHT - window_height) // 2,
            window_width,
            window_height
        )

        self.window = pygame_gui.elements.UIWindow(
            rect=window_rect,
            manager=self.ui_manager,
            window_display_title=config.MINIGAME_SELECTION_WINDOW_TITLE,
            object_id="#minigame_selection_window"
        )

        container_rect = self.window.get_container().get_rect()

        prompt_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(0, padding // 2, container_rect.width, prompt_height),
            text=config.MINIGAME_SELECTION_PROMPT,
            manager=self.ui_manager,
            container=self.window,
            anchors={'centerx': 'centerx', 'top': 'top'}
        )

        current_y = prompt_height + padding

        for mg_instance in available_minigame_instances:
            game_class_name = mg_instance.__class__.__name__
            button_text = config.MINIGAME_DISPLAY_NAMES.get(game_class_name, game_class_name)

            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (container_rect.width - button_width) // 2,
                    current_y,
                    button_width,
                    button_height
                ),
                text=button_text,
                manager=self.ui_manager,
                container=self.window,
                object_id=f"#minigame_select_btn_{game_class_name}" # Đảm bảo ID là hợp lệ
            )
            self.buttons_with_instances.append({"ui_element": button, "instance": mg_instance})
            current_y += button_height + margin
        
        self.window.show()
        self.is_visible = True
        print("Minigame selection window shown.")

    def kill(self):
        if self.window and self.window.alive():
            self.window.kill()
        self.window = None
        self.buttons_with_instances = []
        self.is_visible = False
        # print("Minigame selection window killed.")

    def process_event(self, event):
        """
        Xử lý sự kiện cho cửa sổ chọn.
        Trả về minigame_instance nếu một nút được chọn,
        "closed" nếu cửa sổ bị đóng,
        None nếu không có gì xảy ra.
        """
        if not self.is_visible or not self.window:
            return None

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            for item in self.buttons_with_instances:
                if event.ui_element == item["ui_element"]:
                    print(f"Minigame selected: {item['instance'].__class__.__name__}")
                    self.kill() # Đóng cửa sổ sau khi chọn
                    return item["instance"]
        
        if event.type == pygame_gui.UI_WINDOW_CLOSE:
            if event.ui_element == self.window:
                print("Minigame selection window closed by user.")
                self.kill()
                return "closed" # Tín hiệu cửa sổ đã bị đóng
        
        return None 