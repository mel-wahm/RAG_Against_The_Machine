from collections.abc import Callable
from typing import Any, Optional

import arcade

from src.config.parser import load_options, save_options


class Selection:
    """Represents a selectable menu item and its trigger callback."""

    def __init__(self, name: str, action: Callable[[], Any]) -> None:
        self.name = name
        self.action = action


class Menu:
    """Interactive navigation menu with keyboard and mouse support."""

    def __init__(
        self,
        items: list[Selection],
        x: float,
        y: float,
        gap: float = 65,
        font_size: int = 35,
    ) -> None:
        self.menus = items
        self.x = x
        self.y = y
        self.gap = gap
        self.font_size = font_size
        self.selected_index = 0
        self.labels: list[arcade.Text] = []
        self.scale = 1.3

        total_height = (len(items) - 1) * gap
        for i, item in enumerate(items):
            item_y = self.y + total_height / 2 - (i * self.gap)
            self.labels.append(
                arcade.Text(
                    item.name,
                    self.x,
                    item_y,
                    arcade.color.WHITE,
                    self.font_size,
                    anchor_x="center",
                    font_name="Renogare",
                )
            )

    def mouse_motion(
        self, x: float, y: float, menu: Optional["Menu"] = None
    ) -> None:
        target = menu or self
        for i, label in enumerate(target.labels):
            if label.left < x < label.right and label.bottom < y < label.top:
                target.selected_index = i

    def mouse_press(
        self, x: float, y: float, menu: Optional["Menu"] = None
    ) -> None:
        target = menu or self
        for i, label in enumerate(target.labels):
            if label.left < x < label.right and label.bottom < y < label.top:
                target.menus[i].action()

    def move_up(self) -> None:
        self.selected_index = (self.selected_index - 1) % len(self.menus)
        self.scale = 1.0

    def move_down(self) -> None:
        self.selected_index = (self.selected_index + 1) % len(self.menus)
        self.scale = 1.0

    def action(self) -> None:
        self.menus[self.selected_index].action()

    def draw(
        self,
        color: Any = arcade.color.WHITE,
        selected_color: Any = arcade.color.YELLOW,
    ) -> None:
        for i, text in enumerate(self.labels):
            if i == self.selected_index:
                text.color = selected_color
                text.font_size = self.font_size * self.scale
            else:
                text.color = color
                text.font_size = self.font_size
            text.draw()


class AudioControl:
    """UI component for displaying and adjusting game volume settings."""

    def __init__(
        self, x: float, y: float, text_color: Any = arcade.color.WHITE
    ) -> None:
        self.x = x
        self.y = y
        options = load_options()
        self.volume: int = options["volume"]
        self.text_color = text_color
        self._rebuild_label()

    def _rebuild_label(self) -> None:
        self.label = arcade.Text(
            f"< {self.volume} >",
            self.x,
            self.y,
            self.text_color,
            35,
            anchor_x="center",
            font_name="Renogare",
        )

    def update_json(self, volume: int) -> None:
        options = load_options()
        options["volume"] = volume
        save_options(options, "src/config/options.json")

    def volume_up(self) -> None:
        self.volume = min(10, self.volume + 1)
        self._rebuild_label()
        self.update_json(self.volume)

    def volume_down(self) -> None:
        self.volume = max(0, self.volume - 1)
        self._rebuild_label()
        self.update_json(self.volume)

    def draw(self) -> None:
        self.label.draw()


class ThemeToggle:
    """UI component for toggling between visual themes."""

    def __init__(
        self, x: float, y: float, current_theme: str = "dark"
    ) -> None:
        self.x = x
        self.y = y
        self.selection = 0 if current_theme == "dark" else 1
        self.dark_text = arcade.Text(
            "Dark",
            x - 80,
            y,
            arcade.color.WHITE,
            35,
            anchor_x="center",
            font_name="Renogare",
        )
        self.light_text = arcade.Text(
            "Light",
            x + 80,
            y,
            arcade.color.WHITE,
            35,
            anchor_x="center",
            font_name="Renogare",
        )
        self._update_display(current_theme)

    def update_json(self, theme: str) -> None:
        options = load_options()
        options["theme"] = theme
        save_options(options, "src/config/options.json")

    def _update_display(self, theme: str) -> None:
        self.update_json(theme)
        if theme == "light":
            unselected_color = arcade.color.BLACK
            selected_color = arcade.color.RED
        else:
            unselected_color = arcade.color.WHITE
            selected_color = arcade.color.YELLOW

        if self.selection == 0:
            self.dark_text.color = selected_color
            self.light_text.color = unselected_color
        else:
            self.light_text.color = selected_color
            self.dark_text.color = unselected_color

    def move(self, current_theme: str) -> None:
        self.selection = (self.selection + 1) % 2
        self._update_display(current_theme)

    def get_theme(self) -> str:
        return "dark" if self.selection == 0 else "light"

    def draw(self) -> None:
        self.dark_text.draw()
        self.light_text.draw()
