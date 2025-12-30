import tkinter as tk
import requests
import threading
import time
from collections import deque
from datetime import datetime

class CryptoWidget:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)
        self.root.geometry("180x100")

        self.is_topmost = tk.BooleanVar(value=True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.6)

        self.drag_x = 0
        self.drag_y = 0

        self.symbol = "BTCUSDT"
        self.spot_api_url = "https://api.binance.com/api/v3/ticker/price"
        self.futures_api_url = "https://fapi.binance.com/fapi/v1/ticker/price"

        self.proxy_host = "127.0.0.1"
        self.proxy_port = "10808"
        self.proxy_enabled = tk.BooleanVar(value=True)
        self.update_proxy_config()

        self.last_spot_price = None
        self.last_futures_price = None

        self.alert_enabled = tk.BooleanVar(value=False)
        self.alert_type = tk.StringVar(value="spot")
        self.alert_high_price = ""
        self.alert_low_price = ""
        self.rapid_change_enabled = tk.BooleanVar(value=False)
        self.rapid_change_percent = "3.0"

        self.spot_price_history = deque(maxlen=180)
        self.futures_price_history = deque(maxlen=180)

        self.last_alert_time = {}
        self.alert_cooldown = 180

        self.active_bubbles = []

        self.create_widgets()

        self.create_context_menu()

        self.root.bind('<Button-1>', self.start_drag)
        self.root.bind('<B1-Motion>', self.on_drag)

        self.create_context_menu()

        self.root.bind('<Button-1>', self.start_drag)
        self.root.bind('<B1-Motion>', self.on_drag)

        self.running = True
        self.update_thread = threading.Thread(target=self.update_price, daemon=True)
        self.update_thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=8, pady=(3, 0))

        self.time_label = tk.Label(
            top_frame,
            text="--:--:--",
            font=("Arial", 10),
            fg="#757575"
        )
        self.time_label.pack(side=tk.LEFT)

        settings_btn = tk.Button(
            top_frame,
            text="⚙",
            command=self.open_settings,
            font=("Arial", 9),
            width=2,
            relief=tk.FLAT,
            cursor="hand2",
            padx=0,
            pady=0
        )
        settings_btn.pack(side=tk.RIGHT, padx=(0, 3))

        spot_frame = tk.Frame(self.root)
        spot_frame.pack(fill=tk.X, padx=8, pady=(5, 1))

        self.spot_label = tk.Label(
            spot_frame,
            text="Spot",
            font=("Arial", 9),
            fg="#757575",
            width=4,
            anchor='w'
        )
        self.spot_label.pack(side=tk.LEFT)

        self.spot_price_label = tk.Label(
            spot_frame,
            text="Loading...",
            font=("Arial", 14, "bold"),
            fg="#4CAF50",
            anchor='e'
        )
        self.spot_price_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        futures_frame = tk.Frame(self.root)
        futures_frame.pack(fill=tk.X, padx=8, pady=(1, 3))

        self.futures_label = tk.Label(
            futures_frame,
            text="Futures",
            font=("Arial", 9),
            fg="#757575",
            width=6,
            anchor='w'
        )
        self.futures_label.pack(side=tk.LEFT)

        self.futures_price_label = tk.Label(
            futures_frame,
            text="Loading...",
            font=("Arial", 14, "bold"),
            fg="#4CAF50",
            anchor='e'
        )
        self.futures_price_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Settings", command=self.open_settings)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Exit", command=self.on_closing)
        self.root.bind('<Button-3>', self.show_context_menu)

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    def start_drag(self, event):
        self.drag_x = event.x
        self.drag_y = event.y

    def on_drag(self, event):
        x = self.root.winfo_x() + event.x - self.drag_x
        y = self.root.winfo_y() + event.y - self.drag_y
        self.root.geometry(f"+{x}+{y}")
        self.update_bubble_positions()

    def update_bubble_positions(self):
        self.active_bubbles = [b for b in self.active_bubbles if b.winfo_exists()]

        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        screen_width = self.root.winfo_screenwidth()

        main_center_x = main_x + main_width // 2

        for bubble in self.active_bubbles:
            try:
                bubble_width = bubble.winfo_width()

                if main_center_x > screen_width // 2:
                    bubble_x = main_x - bubble_width - 10
                else:
                    bubble_x = main_x + main_width + 10

                bubble_y = main_y

                if bubble_x < 0:
                    bubble_x = 10
                elif bubble_x + bubble_width > screen_width:
                    bubble_x = screen_width - bubble_width - 10

                bubble.geometry(f"+{bubble_x}+{bubble_y}")
            except:
                pass

    def toggle_topmost(self):
        self.root.attributes('-topmost', self.is_topmost.get())

    def update_proxy_config(self):
        if self.proxy_enabled.get():
            proxy_url = f"http://{self.proxy_host}:{self.proxy_port}"
            self.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
        else:
            self.proxies = None

    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("320x500")
        settings_window.resizable(False, False)
        settings_window.attributes('-topmost', True)

        topmost_frame = tk.Frame(settings_window)
        topmost_frame.pack(fill=tk.X, padx=15, pady=(15, 10))

        tk.Checkbutton(
            topmost_frame,
            text="Always on Top",
            variable=self.is_topmost,
            command=self.toggle_topmost,
            font=("Arial", 10)
        ).pack(anchor='w')

        proxy_enable_frame = tk.Frame(settings_window)
        proxy_enable_frame.pack(fill=tk.X, padx=15, pady=(5, 10))

        tk.Checkbutton(
            proxy_enable_frame,
            text="Enable Proxy",
            variable=self.proxy_enabled,
            font=("Arial", 10)
        ).pack(anchor='w')

        host_frame = tk.Frame(settings_window)
        host_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(host_frame, text="Host:", font=("Arial", 9), width=6, anchor='w').pack(side=tk.LEFT)
        host_entry = tk.Entry(host_frame, font=("Arial", 9))
        host_entry.insert(0, self.proxy_host)
        host_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        port_frame = tk.Frame(settings_window)
        port_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(port_frame, text="Port:", font=("Arial", 9), width=6, anchor='w').pack(side=tk.LEFT)
        port_entry = tk.Entry(port_frame, font=("Arial", 9))
        port_entry.insert(0, self.proxy_port)
        port_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        opacity_frame = tk.Frame(settings_window)
        opacity_frame.pack(fill=tk.X, padx=15, pady=(15, 5))

        tk.Label(
            opacity_frame,
            text="Alpha:",
            font=("Arial", 9),
            width=6,
            anchor='w'
        ).pack(side=tk.LEFT, pady=(18, 0))

        opacity_slider = tk.Scale(
            opacity_frame,
            from_=20,
            to=100,
            orient=tk.HORIZONTAL,
            showvalue=True,
            command=lambda v: self.root.attributes('-alpha', float(v)/100),
            length=170
        )
        opacity_slider.set(int(self.root.attributes('-alpha') * 100))
        opacity_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        separator = tk.Frame(settings_window, height=2, bd=1, relief=tk.SUNKEN)
        separator.pack(fill=tk.X, padx=15, pady=(15, 10))

        alert_title = tk.Label(settings_window, text="Price Alert", font=("", 10, "bold"))
        alert_title.pack(anchor='w', padx=15, pady=(5, 5))

        alert_enable_frame = tk.Frame(settings_window)
        alert_enable_frame.pack(fill=tk.X, padx=15, pady=2)
        tk.Checkbutton(
            alert_enable_frame,
            text="Enable Price Alert",
            variable=self.alert_enabled,
            font=("", 9)
        ).pack(anchor='w')

        type_frame = tk.Frame(settings_window)
        type_frame.pack(fill=tk.X, padx=15, pady=2)
        tk.Label(type_frame, text="Type:", font=("", 9), width=6, anchor='w').pack(side=tk.LEFT)
        tk.Radiobutton(
            type_frame,
            text="Spot",
            variable=self.alert_type,
            value="spot",
            font=("", 9)
        ).pack(side=tk.LEFT)
        tk.Radiobutton(
            type_frame,
            text="Future",
            variable=self.alert_type,
            value="futures",
            font=("", 9)
        ).pack(side=tk.LEFT)

        high_alert_frame = tk.Frame(settings_window)
        high_alert_frame.pack(fill=tk.X, padx=15, pady=2)
        tk.Label(high_alert_frame, text="Above:", font=("", 9), width=6, anchor='w').pack(side=tk.LEFT)
        high_alert_entry = tk.Entry(high_alert_frame, font=("", 9))
        high_alert_entry.insert(0, self.alert_high_price)
        high_alert_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        low_alert_frame = tk.Frame(settings_window)
        low_alert_frame.pack(fill=tk.X, padx=15, pady=2)
        tk.Label(low_alert_frame, text="Below:", font=("", 9), width=6, anchor='w').pack(side=tk.LEFT)
        low_alert_entry = tk.Entry(low_alert_frame, font=("", 9))
        low_alert_entry.insert(0, self.alert_low_price)
        low_alert_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        rapid_change_frame = tk.Frame(settings_window)
        rapid_change_frame.pack(fill=tk.X, padx=15, pady=(10, 2))
        tk.Checkbutton(
            rapid_change_frame,
            text="3min Rapid Change Alert",
            variable=self.rapid_change_enabled,
            font=("", 9)
        ).pack(anchor='w')

        percent_frame = tk.Frame(settings_window)
        percent_frame.pack(fill=tk.X, padx=15, pady=2)
        tk.Label(percent_frame, text="Change:", font=("", 9), width=6, anchor='w').pack(side=tk.LEFT)
        percent_entry = tk.Entry(percent_frame, font=("", 9), width=8)
        percent_entry.insert(0, self.rapid_change_percent)
        percent_entry.pack(side=tk.LEFT)
        tk.Label(percent_frame, text="%", font=("", 9)).pack(side=tk.LEFT, padx=(2, 0))

        def save_settings():
            self.proxy_host = host_entry.get()
            self.proxy_port = port_entry.get()
            self.update_proxy_config()
            self.alert_high_price = high_alert_entry.get()
            self.alert_low_price = low_alert_entry.get()
            self.rapid_change_percent = percent_entry.get()
            settings_window.destroy()

        btn_frame = tk.Frame(settings_window)
        btn_frame.pack(fill=tk.X, padx=15, pady=(10, 15))

        tk.Button(
            btn_frame,
            text="Save",
            command=save_settings,
            font=("Arial", 9),
            width=10
        ).pack(side=tk.RIGHT)

        tk.Button(
            btn_frame,
            text="Cancel",
            command=settings_window.destroy,
            font=("Arial", 9),
            width=10
        ).pack(side=tk.RIGHT, padx=(0, 10))

    def change_opacity(self, value):
        opacity = float(value) / 100
        self.root.attributes('-alpha', opacity)

    def get_price(self, api_url):
        try:
            params = {
                'symbol': self.symbol
            }
            response = requests.get(
                api_url, 
                params=params, 
                proxies=self.proxies,
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            return float(data['price'])
        except Exception:
            return None

    def get_current_prices(self):
        spot_price = self.get_price(self.spot_api_url)
        futures_price = self.get_price(self.futures_api_url)
        return spot_price, futures_price

    def update_price(self):
        while self.running:
            spot_price, futures_price = self.get_current_prices()
            if spot_price is not None or futures_price is not None:
                self.root.after(0, self.update_ui, spot_price, futures_price)
            time.sleep(1)

    def update_ui(self, spot_price, futures_price):
        current_time = time.strftime("%H:%M:%S")
        self.time_label.config(text=current_time)

        if spot_price is not None and spot_price > 0:
            self.spot_price_history.append((datetime.now(), spot_price))
            if self.alert_type.get() == "spot":
                self.check_alerts(spot_price, "spot")

        if futures_price is not None and futures_price > 0:
            self.futures_price_history.append((datetime.now(), futures_price))
            if self.alert_type.get() == "futures":
                self.check_alerts(futures_price, "futures")

        if spot_price is not None:
            if self.last_spot_price is not None:
                if spot_price > self.last_spot_price:
                    color = "#00C853"
                elif spot_price < self.last_spot_price:
                    color = "#FF1744"
                else:
                    color = "#757575"
            else:
                color = "#4CAF50"

            self.spot_price_label.config(text=f"${spot_price:,.2f}", fg=color)
            self.last_spot_price = spot_price

        if futures_price is not None:
            if self.last_futures_price is not None:
                if futures_price > self.last_futures_price:
                    color = "#00C853"
                elif futures_price < self.last_futures_price:
                    color = "#FF1744"
                else:
                    color = "#757575"
            else:
                color = "#4CAF50"

            self.futures_price_label.config(text=f"${futures_price:,.2f}", fg=color)
            self.last_futures_price = futures_price

    def check_alerts(self, current_price, price_type):
        if not self.alert_enabled.get() and not self.rapid_change_enabled.get():
            return

        type_text = "Spot" if price_type == "spot" else "Futures"

        if self.alert_enabled.get() and self.alert_high_price.strip():
            try:
                high_price = float(self.alert_high_price)
                if high_price > 0 and current_price >= high_price:
                    self.send_alert(f"high_price_{price_type}", f"{type_text} price above ${high_price:,.2f}", 
                                  f"Current {type_text} price: ${current_price:,.2f}")
            except ValueError:
                pass

        if self.alert_enabled.get() and self.alert_low_price.strip():
            try:
                low_price = float(self.alert_low_price)
                if low_price > 0 and current_price <= low_price:
                    self.send_alert(f"low_price_{price_type}", f"{type_text} price below ${low_price:,.2f}", 
                                  f"Current {type_text} price: ${current_price:,.2f}")
            except ValueError:
                pass

        if self.rapid_change_enabled.get():
            price_history = self.spot_price_history if price_type == "spot" else self.futures_price_history
            if len(price_history) >= 150:
                try:
                    percent_threshold = float(self.rapid_change_percent)
                    if percent_threshold <= 0:
                        return

                    oldest_time, oldest_price = price_history[0]
                    newest_time, newest_price = price_history[-1]
                    time_diff = (newest_time - oldest_time).total_seconds()

                    if time_diff >= 150:
                        is_continuous_high = self._check_continuous_high(price_history)
                        is_continuous_low = self._check_continuous_low(price_history)

                        price_change_percent = ((newest_price - oldest_price) / oldest_price) * 100

                        if is_continuous_high and price_change_percent >= percent_threshold:
                            self.send_alert(f"rapid_rise_{price_type}", 
                                          f"{type_text} continuous new high +{price_change_percent:.2f}%",
                                          f"From ${oldest_price:,.2f} to ${newest_price:,.2f}\n({time_diff/60:.1f} mins)")
                        elif is_continuous_low and abs(price_change_percent) >= percent_threshold:
                            self.send_alert(f"rapid_fall_{price_type}", 
                                          f"{type_text} continuous new low {price_change_percent:.2f}%",
                                          f"From ${oldest_price:,.2f} to ${newest_price:,.2f}\n({time_diff/60:.1f} mins)")
                except ValueError:
                    pass

    def _check_continuous_high(self, price_history):
        if len(price_history) < 20:
            return False

        segment_size = len(price_history) // 10
        if segment_size < 2:
            segment_size = 2

        segment_highs = []
        for i in range(0, len(price_history), segment_size):
            segment = list(price_history)[i:i+segment_size]
            if segment:
                max_price = max(p[1] for p in segment)
                segment_highs.append(max_price)

        if len(segment_highs) < 3:
            return False

        increasing_count = sum(1 for i in range(1, len(segment_highs)) if segment_highs[i] > segment_highs[i-1])
        return increasing_count >= len(segment_highs) * 0.7 - 1

    def _check_continuous_low(self, price_history):
        if len(price_history) < 20:
            return False

        segment_size = len(price_history) // 10
        if segment_size < 2:
            segment_size = 2

        segment_lows = []
        for i in range(0, len(price_history), segment_size):
            segment = list(price_history)[i:i+segment_size]
            if segment:
                min_price = min(p[1] for p in segment)
                segment_lows.append(min_price)

        if len(segment_lows) < 3:
            return False

        decreasing_count = sum(1 for i in range(1, len(segment_lows)) if segment_lows[i] < segment_lows[i-1])
        return decreasing_count >= len(segment_lows) * 0.7 - 1

    def send_alert(self, alert_type, title, message):
        current_time = time.time()
        if alert_type in self.last_alert_time:
            if current_time - self.last_alert_time[alert_type] < self.alert_cooldown:
                return

        self.last_alert_time[alert_type] = current_time

        self.show_popup_alert(title, message)

    def show_popup_alert(self, title, message):
        try:
            self.root.after(0, self._create_alert_window, title, message)
        except Exception:
            pass

    def _create_alert_window(self, title, message):
        bubble = tk.Toplevel(self.root)
        bubble.overrideredirect(True)
        bubble.attributes('-topmost', True)
        bubble.attributes('-alpha', 0.95)

        container = tk.Frame(bubble, bg="#FF9800", bd=0)
        container.pack(fill=tk.BOTH, expand=True)

        inner_frame = tk.Frame(container, bg="#FF9800")
        inner_frame.pack(padx=15, pady=12)

        title_label = tk.Label(
            inner_frame,
            text=f"{self.symbol} - {title}",
            font=("Microsoft YaHei UI", 10, "bold"),
            bg="#FF9800",
            fg="white",
            wraplength=250
        )
        title_label.pack(anchor='w', pady=(0, 5))

        msg_label = tk.Label(
            inner_frame,
            text=message,
            font=("Microsoft YaHei UI", 9),
            bg="#FF9800",
            fg="white",
            wraplength=250,
            justify=tk.LEFT
        )
        msg_label.pack(anchor='w')

        bubble.update_idletasks()
        bubble_width = bubble.winfo_width()

        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        screen_width = self.root.winfo_screenwidth()

        main_center_x = main_x + main_width // 2

        if main_center_x > screen_width // 2:
            bubble_x = main_x - bubble_width - 10
        else:
            bubble_x = main_x + main_width + 10

        bubble_y = main_y

        if bubble_x < 0:
            bubble_x = 10
        elif bubble_x + bubble_width > screen_width:
            bubble_x = screen_width - bubble_width - 10

        bubble.geometry(f"+{bubble_x}+{bubble_y}")

        self.active_bubbles.append(bubble)

        close_timer_id = [None]

        def close_bubble(e):
            if close_timer_id[0]:
                bubble.after_cancel(close_timer_id[0])
            if bubble in self.active_bubbles:
                self.active_bubbles.remove(bubble)
            bubble.destroy()
        container.bind('<Button-1>', close_bubble)

        def auto_close():
            if bubble.winfo_exists():
                if bubble in self.active_bubbles:
                    self.active_bubbles.remove(bubble)
                bubble.destroy()

        def on_enter(e):
            if close_timer_id[0]:
                bubble.after_cancel(close_timer_id[0])
                close_timer_id[0] = None

        def on_leave(e):
            if close_timer_id[0]:
                bubble.after_cancel(close_timer_id[0])
            close_timer_id[0] = bubble.after(5000, auto_close)

        bubble.bind('<Enter>', on_enter)
        bubble.bind('<Leave>', on_leave)
        container.bind('<Enter>', on_enter)
        container.bind('<Leave>', on_leave)

        close_timer_id[0] = bubble.after(3000, auto_close)

    def on_closing(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoWidget(root)
    root.mainloop()
