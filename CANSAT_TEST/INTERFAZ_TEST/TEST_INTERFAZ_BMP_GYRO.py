import tkinter as tk
from tkinter import ttk, filedialog
import threading
import queue
import serial
import json
import cv2
from PIL import Image, ImageTk
from collections import deque
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


# ============================================================
# SERIAL THREAD
# ============================================================

class SerialReader(threading.Thread):
    """
    Hilo daemon para leer datos del puerto serial sin bloquear la GUI.
    
    Lee líneas de datos JSON continuamente y las coloca en una cola
    thread-safe para comunicación con el hilo principal.
    """

    def __init__(self, port, baudrate, data_queue):
        """
        Inicializa el lector serial.
        
        Parámetros:
            port (str): Puerto serial (ej: "/dev/ttyUSB0")
            baudrate (int): Velocidad en baudios (ej: 115200)
            data_queue (queue.Queue): Cola donde se colocan los datos leídos
        """
        super().__init__(daemon=True)
        self.queue = data_queue
        self.running = True

        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            print("[OK] Serial connected")
        except:
            print("[ERROR] Serial not connected")
            self.ser = None

    def run(self):
        """Método principal: lee continuamente líneas del puerto serial."""
        if not self.ser:
            return

        while self.running:
            try:
                line = self.ser.readline().decode().strip()
                if line:
                    self.queue.put(line)
            except:
                pass


# ============================================================
# GRAPH WINDOW
# ============================================================

class GraphWindow(tk.Toplevel):
    """
    Ventana emergente para mostrar gráficos dinámicos de sensores.
    
    Muestra un gráfico de líneas actualizado en tiempo real cada 500ms
    con los datos históricos de un sensor específico.
    Tema oscuro para mejor visualización nocturna.
    """

    def __init__(self, parent):
        """
        Inicializa la ventana de gráficos.
        
        Parámetros:
            parent (tk.Widget): Ventana padre que actúa como propietaria
        """
        super().__init__(parent)

        self.geometry("800x500")
        self.configure(bg="#121212")

        # Crear figura matplotlib con tema oscuro
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.fig.patch.set_facecolor("#121212")

        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#1e1e1e")

        # Integrar matplotlib en tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.sensor_name = None  # Nombre del sensor actual
        self.buffer = None       # Buffer con datos históricos

        # Comenzar actualización periódica
        self.after(50, self.update_graph)

    def set_sensor(self, name, buffer):
        """
        Configura qué sensor se va a graficar.
        
        Parámetros:
            name (str): Nombre del sensor (ej: "Temperature")
            buffer (deque): Buffer circular con los datos históricos
        """
        self.sensor_name = name
        self.buffer = buffer
        self.title(f"Graph - {name}")

    def update_graph(self):
        """Redibuja el gráfico cada 500ms con los datos más recientes."""
        if self.buffer and len(self.buffer) > 0:
            self.ax.clear()
            self.ax.set_facecolor("#1e1e1e")
            # Graficar los datos en color cian
            self.ax.plot(list(self.buffer), color="cyan")
            self.ax.set_title(self.sensor_name, color="white")
            self.ax.tick_params(colors="white")
            self.ax.grid(color="#444444")
            self.canvas.draw()

        # Programar siguiente actualización
        self.after(500, self.update_graph)


# ============================================================
# CAMERA
# ============================================================

class CameraManager:
    """
    Gestor de captura y visualización de video en tiempo real.
    
    Captura frames de una cámara y los redimensiona para mostrar
    en un widget Label de tkinter aproximadamente cada 30ms.
    """

    def __init__(self, label):
        """
        Inicializa el gestor de cámara.
        
        Parámetros:
            label (ttk.Label): Widget donde mostrar los frames de video
        """
        self.label = label
        self.cap = cv2.VideoCapture(0)  # Abrir cámara por defecto

    def update(self):
        """Captura un frame, lo procesa y lo muestra en el Label."""
        ret, frame = self.cap.read()
        if ret:
            # Convertir de BGR (OpenCV) a RGB (PIL)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Convertir numpy array a imagen PIL
            img = Image.fromarray(frame)
            # Redimensionar para que se ajuste al widget
            img = img.resize((500, 350))
            # Convertir a PhotoImage compatible con tkinter
            imgtk = ImageTk.PhotoImage(img)
            # Actualizar label con la nueva imagen
            self.label.imgtk = imgtk
            self.label.configure(image=imgtk)

        # Programar siguiente captura (30ms = ~33 FPS)
        self.label.after(30, self.update)


# ============================================================
# DASHBOARD
# ============================================================

class DashboardApp:
    """
    Aplicación principal del dashboard CANSAT.
    
    Interfaz gráfica con 4 cuadrantes:
    - Superior izquierda: Métricas en vivo (BMP390L + IMU)
    - Inferior izquierda: Acciones (limpiar datos, exportar JSON)
    - Superior derecha: Feed de cámara en tiempo real
    - Inferior derecha: Datos crudos (JSON) en texto
    
    Lee del puerto serial en hilo separado sin bloquear la GUI.
    Muestra temperatura, presión, altitud, aceleración y giroscopio.
    """

    def __init__(self, root):
        """
        Inicializa la aplicación.
        
        Parámetros:
            root (tk.Tk): Ventana raíz de tkinter
        """
        self.root = root
        self.root.title("CANSAT Dashboard - Final")
        self.root.geometry("1300x850")

        self.setup_dark_theme()

        # Configurar grid 2x2 responsivo
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Buffers históricos para todos los sensores (máximo 300 valores)
        self.sensors = {
            "Temperature": deque(maxlen=300),
            "Pressure": deque(maxlen=300),
            "Altitude": deque(maxlen=300),
            "Accel X": deque(maxlen=300),
            "Accel Y": deque(maxlen=300),
            "Accel Z": deque(maxlen=300),
            "Gyro X": deque(maxlen=300),
            "Gyro Y": deque(maxlen=300),
            "Gyro Z": deque(maxlen=300),
        }

        self.graph_window = None

        # Inicializar y lanzar hilo de lectura serial
        self.data_queue = queue.Queue()
        self.serial_thread = SerialReader("/dev/ttyUSB0", 115200, self.data_queue)
        self.serial_thread.start()

        self.create_layout()
        self.process_serial()

    # =========================================================

    def setup_dark_theme(self):
        """Configura el tema oscuro para toda la interfaz."""
        style = ttk.Style()
        style.theme_use("clam")

        # Colores del tema oscuro
        style.configure("TFrame", background="#121212")
        style.configure("TLabelFrame", background="#121212", foreground="white")
        style.configure("TLabelFrame.Label", background="#121212", foreground="white")
        style.configure("TLabel", background="#121212", foreground="white")
        style.configure("TButton", background="#1e1e1e", foreground="white")
        style.configure("TCombobox",
                        fieldbackground="#1e1e1e",
                        background="#1e1e1e",
                        foreground="white")

        self.root.configure(bg="#121212")

    # =========================================================

    def create_layout(self):
        """Crea los 4 cuadrantes principales de la interfaz."""

        # Cuadrante II (superior izquierda): Métricas en vivo
        self.quad_II = ttk.LabelFrame(self.root, text="Live Metrics")
        self.quad_II.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Cuadrante III (inferior izquierda): Acciones
        self.quad_III = ttk.Frame(self.root)
        self.quad_III.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Cuadrante I (superior derecha): Cámara
        self.quad_I = ttk.LabelFrame(self.root, text="Camera")
        self.quad_I.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Cuadrante IV (inferior derecha): Datos crudos
        self.quad_IV = ttk.LabelFrame(self.root, text="Raw Data")
        self.quad_IV.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # Crear labels para cada sensor
        self.sensor_labels = {}

        for sensor in self.sensors:
            frame = ttk.Frame(self.quad_II, padding=6)
            frame.pack(fill="x", pady=2)

            # Label con nombre del sensor y valor inicial
            label = ttk.Label(frame,
                              text=f"{sensor}: --",
                              font=("Consolas", 12))
            label.pack(anchor="w")

            # Vincular clicks para abrir gráfico
            frame.bind("<Button-1>",
                       lambda e, s=sensor: self.open_graph(s))
            label.bind("<Button-1>",
                       lambda e, s=sensor: self.open_graph(s))

            self.sensor_labels[sensor] = label

        # Widget de texto para datos crudos (JSON)
        self.raw_text = tk.Text(self.quad_IV,
                                bg="#000000",
                                fg="#00ff00",
                                insertbackground="white")
        self.raw_text.pack(fill="both", expand=True)

        # ComboBox para seleccionar acciones
        self.action_combo = ttk.Combobox(self.quad_III,
                                         values=["Clear Data", "Export JSON"])
        self.action_combo.pack(pady=10)

        # Botón para ejecutar la acción seleccionada
        ttk.Button(self.quad_III,
                   text="Execute",
                   command=self.execute_action).pack()

        # Label para mostrar frames de cámara
        self.camera_label = ttk.Label(self.quad_I)
        self.camera_label.pack(fill="both", expand=True)

        # Inicializar y actualizar cámara
        self.camera = CameraManager(self.camera_label)
        self.camera.update()

    # =========================================================

    def process_serial(self):
        """
        Procesa datos del puerto serial cada 50ms.
        
        Lee líneas JSON de la cola, las interpreta, y actualiza
        los buffers de sensores y la UI con los nuevos valores.
        Mapea claves JSON a nombres de sensores internos.
        """
        while not self.data_queue.empty():
            line = self.data_queue.get()

            try:
                # Parsear línea como JSON
                data = json.loads(line)

                # Mapeo de claves JSON a nombres de sensores en la UI
                mapping = {
                    "temp_bmp": "Temperature",
                    "pres": "Pressure",
                    "alt": "Altitude",
                    "ax": "Accel X",
                    "ay": "Accel Y",
                    "az": "Accel Z",
                    "gx": "Gyro X",
                    "gy": "Gyro Y",
                    "gz": "Gyro Z"
                }

                # Actualizar cada sensor con su nuevo valor
                for key, name in mapping.items():
                    if key in data:
                        value = data[key]
                        # Agregar valor al buffer histórico
                        self.sensors[name].append(value)
                        # Actualizar label en la UI
                        self.sensor_labels[name].config(
                            text=f"{name}: {value:.2f}"
                        )

            except:
                # Ignorar líneas que no sean JSON válido
                pass

            # Mostrar línea cruda en el widget de texto
            self.raw_text.insert("end", line + "\n")
            self.raw_text.see("end")  # Scroll automático al final

        # Reprogramar procesamiento para los próximos 50ms
        self.root.after(50, self.process_serial)

    # =========================================================

    def open_graph(self, sensor_name):
        """
        Abre o trae al frente la ventana de gráfico.
        
        Parámetros:
            sensor_name (str): Nombre del sensor a graficar
        """
        # Crear ventana si no existe o si fue cerrada
        if self.graph_window is None or not self.graph_window.winfo_exists():
            self.graph_window = GraphWindow(self.root)

        # Configurar el sensor a mostrar
        self.graph_window.set_sensor(sensor_name,
                                     self.sensors[sensor_name])

    # =========================================================

    def execute_action(self):
        """
        Ejecuta la acción seleccionada en el combobox.
        
        Acciones disponibles:
        - "Clear Data": Limpia todos los buffers de sensores y el texto crudо
        - "Export JSON": Exporta los datos a un archivo JSON
        """
        action = self.action_combo.get()

        if action == "Clear Data":
            # Limpiar todos los buffers
            for key in self.sensors:
                self.sensors[key].clear()
            # Limpiar widget de texto
            self.raw_text.delete("1.0", tk.END)

        elif action == "Export JSON":
            # Abrir diálogo de guardado
            file_path = filedialog.asksaveasfilename(defaultextension=".json")
            if file_path:
                # Guardar sensores como JSON
                with open(file_path, "w") as f:
                    json.dump(
                        {k: list(v) for k, v in self.sensors.items()},
                        f,
                        indent=4
                    )


# ============================================================

if __name__ == "__main__":
    """Inicializa y ejecuta la aplicación del dashboard."""
    root = tk.Tk()
    app = DashboardApp(root)
    root.mainloop()

        self.create_layout()
        self.process_serial()

    # =========================================================

    def setup_dark_theme(self):

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background="#121212")
        style.configure("TLabelFrame", background="#121212", foreground="white")
        style.configure("TLabelFrame.Label", background="#121212", foreground="white")
        style.configure("TLabel", background="#121212", foreground="white")
        style.configure("TButton", background="#1e1e1e", foreground="white")
        style.configure("TCombobox",
                        fieldbackground="#1e1e1e",
                        background="#1e1e1e",
                        foreground="white")

        self.root.configure(bg="#121212")

    # =========================================================

    def create_layout(self):

        self.quad_II = ttk.LabelFrame(self.root, text="Live Metrics")
        self.quad_II.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.quad_III = ttk.Frame(self.root)
        self.quad_III.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.quad_I = ttk.LabelFrame(self.root, text="Camera")
        self.quad_I.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.quad_IV = ttk.LabelFrame(self.root, text="Raw Data")
        self.quad_IV.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        self.sensor_labels = {}

        for sensor in self.sensors:
            frame = ttk.Frame(self.quad_II, padding=6)
            frame.pack(fill="x", pady=2)

            label = ttk.Label(frame,
                              text=f"{sensor}: --",
                              font=("Consolas", 12))
            label.pack(anchor="w")

            frame.bind("<Button-1>",
                       lambda e, s=sensor: self.open_graph(s))
            label.bind("<Button-1>",
                       lambda e, s=sensor: self.open_graph(s))

            self.sensor_labels[sensor] = label

        self.raw_text = tk.Text(self.quad_IV,
                                bg="#000000",
                                fg="#00ff00",
                                insertbackground="white")
        self.raw_text.pack(fill="both", expand=True)

        self.action_combo = ttk.Combobox(self.quad_III,
                                         values=["Clear Data", "Export JSON"])
        self.action_combo.pack(pady=10)

        ttk.Button(self.quad_III,
                   text="Execute",
                   command=self.execute_action).pack()

        self.camera_label = ttk.Label(self.quad_I)
        self.camera_label.pack(fill="both", expand=True)

        self.camera = CameraManager(self.camera_label)
        self.camera.update()

    # =========================================================

    def process_serial(self):

        while not self.data_queue.empty():
            line = self.data_queue.get()

            try:
                data = json.loads(line)

                mapping = {
                    "temp_bmp": "Temperature",
                    "pres": "Pressure",
                    "alt": "Altitude",
                    "ax": "Accel X",
                    "ay": "Accel Y",
                    "az": "Accel Z",
                    "gx": "Gyro X",
                    "gy": "Gyro Y",
                    "gz": "Gyro Z"
                }

                for key, name in mapping.items():
                    if key in data:
                        value = data[key]
                        self.sensors[name].append(value)
                        self.sensor_labels[name].config(
                            text=f"{name}: {value:.2f}"
                        )

            except:
                pass

            self.raw_text.insert("end", line + "\n")
            self.raw_text.see("end")

        self.root.after(50, self.process_serial)

    # =========================================================

    def open_graph(self, sensor_name):

        if self.graph_window is None or not self.graph_window.winfo_exists():
            self.graph_window = GraphWindow(self.root)

        self.graph_window.set_sensor(sensor_name,
                                     self.sensors[sensor_name])

    # =========================================================

    def execute_action(self):

        action = self.action_combo.get()

        if action == "Clear Data":
            for key in self.sensors:
                self.sensors[key].clear()
            self.raw_text.delete("1.0", tk.END)

        elif action == "Export JSON":
            file_path = filedialog.asksaveasfilename(defaultextension=".json")
            if file_path:
                with open(file_path, "w") as f:
                    json.dump(
                        {k: list(v) for k, v in self.sensors.items()},
                        f,
                        indent=4
                    )


# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardApp(root)
    root.mainloop()