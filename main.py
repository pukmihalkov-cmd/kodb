import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from functools import partial

# Файл для хранения избранных пользователей
FAVORITES_FILE = "favorites.json"


class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("700x550")
        self.root.resizable(True, True)

        # Загрузка избранных пользователей
        self.favorites = self.load_favorites()

        # Создание интерфейса
        self.create_widgets()

        # Обновление списка избранных при запуске
        self.update_favorites_list()

    def create_widgets(self):
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Блок поиска ---
        search_frame = ttk.LabelFrame(main_frame, text="Поиск пользователей GitHub", padding="10")
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Введите имя пользователя:").pack(anchor=tk.W)

        self.search_entry = ttk.Entry(search_frame, width=50)
        self.search_entry.pack(fill=tk.X, pady=(5, 10))
        self.search_entry.bind("<Return>", lambda e: self.search_users())

        self.search_button = ttk.Button(search_frame, text="🔍 Найти", command=self.search_users)
        self.search_button.pack()

        # --- Результаты поиска ---
        results_frame = ttk.LabelFrame(main_frame, text="Результаты поиска", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Создание Treeview для результатов
        columns = ("username", "user_id", "score")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=8)

        self.results_tree.heading("username", text="Логин")
        self.results_tree.heading("user_id", text="ID")
        self.results_tree.heading("score", text="Рейтинг")

        self.results_tree.column("username", width=200)
        self.results_tree.column("user_id", width=100)
        self.results_tree.column("score", width=100)

        # Скроллбар для результатов
        results_scroll = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scroll.set)

        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Блок избранного ---
        favorites_frame = ttk.LabelFrame(main_frame, text="⭐ Избранные пользователи", padding="10")
        favorites_frame.pack(fill=tk.BOTH, expand=True)

        self.favorites_listbox = tk.Listbox(favorites_frame, height=5)
        self.favorites_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # Кнопки управления избранным
        fav_buttons_frame = ttk.Frame(favorites_frame)
        fav_buttons_frame.pack(fill=tk.X)

        self.add_fav_button = ttk.Button(fav_buttons_frame, text="➕ Добавить в избранное", command=self.add_to_favorites, state=tk.DISABLED)
        self.add_fav_button.pack(side=tk.LEFT, padx=(0, 5))

        self.remove_fav_button = ttk.Button(fav_buttons_frame, text="❌ Удалить из избранного", command=self.remove_from_favorites)
        self.remove_fav_button.pack(side=tk.LEFT)

        # Привязка выбора в результатах для активации кнопки "Добавить"
        self.results_tree.bind("<<TreeviewSelect>>", self.on_results_select)

    def load_favorites(self):
        """Загрузка избранных пользователей из JSON файла"""
        if os.path.exists(FAVORITES_FILE):
            try:
                with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def save_favorites(self):
        """Сохранение избранных пользователей в JSON файл"""
        with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.favorites, f, ensure_ascii=False, indent=2)

    def update_favorites_list(self):
        """Обновление отображения списка избранных"""
        self.favorites_listbox.delete(0, tk.END)
        for fav in self.favorites:
            self.favorites_listbox.insert(tk.END, f"{fav['login']} (ID: {fav['id']})")

    def search_users(self):
        """Поиск пользователей через GitHub API"""
        query = self.search_entry.get().strip()

        # Проверка корректности ввода
        if not query:
            messagebox.showwarning("Ошибка ввода", "Поле поиска не может быть пустым!")
            return

        # Очистка предыдущих результатов
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Деактивация кнопки добавления до нового выбора
        self.add_fav_button.config(state=tk.DISABLED)

        try:
            # Запрос к GitHub API для поиска пользователей
            url = f"https://api.github.com/search/users?q={query}&per_page=20"
            response = requests.get(url)
            response.raise_for_status()

            data = response.json()

            if data.get('total_count', 0) == 0:
                messagebox.showinfo("Результаты поиска", "Пользователи не найдены.")
                return

            # Отображение результатов
            for user in data.get('items', []):
                self.results_tree.insert("", tk.END, values=(
                    user['login'],
                    user['id'],
                    f"{user.get('score', 0):.2f}"
                ))

            messagebox.showinfo("Результаты поиска", f"Найдено пользователей: {data.get('total_count', 0)}")

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Ошибка", f"Не удалось выполнить поиск:\n{str(e)}")

    def on_results_select(self, event):
        """Обработчик выбора пользователя в результатах поиска"""
        selected = self.results_tree.selection()
        if selected:
            self.add_fav_button.config(state=tk.NORMAL)
        else:
            self.add_fav_button.config(state=tk.DISABLED)

    def get_selected_user_from_results(self):
        """Получение данных выбранного пользователя из результатов поиска"""
        selected = self.results_tree.selection()
        if not selected:
            return None

        item = self.results_tree.item(selected[0])
        values = item['values']
        return {
            'login': values[0],
            'id': values[1]
        }

    def add_to_favorites(self):
        """Добавление выбранного пользователя в избранное"""
        user = self.get_selected_user_from_results()
        if not user:
            messagebox.showwarning("Ошибка", "Пожалуйста, выберите пользователя из результатов поиска.")
            return

        # Проверка, не добавлен ли уже пользователь в избранное
        if any(fav['id'] == user['id'] for fav in self.favorites):
            messagebox.showinfo("Информация", f"Пользователь {user['login']} уже в избранном.")
            return

        # Добавление в избранное
        self.favorites.append(user)
        self.save_favorites()
        self.update_favorites_list()
        messagebox.showinfo("Успех", f"Пользователь {user['login']} добавлен в избранное.")

    def remove_from_favorites(self):
        """Удаление выбранного пользователя из избранного"""
        selection = self.favorites_listbox.curselection()
        if not selection:
            messagebox.showwarning("Ошибка", "Пожалуйста, выберите пользователя из списка избранного.")
            return

        # Получение индекса и удаление
        index = selection[0]
        removed_user = self.favorites.pop(index)
        self.save_favorites()
        self.update_favorites_list()
        messagebox.showinfo("Успех", f"Пользователь {removed_user['login']} удален из избранного.")


def main():
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()


if __name__ == "__main__":
    main()