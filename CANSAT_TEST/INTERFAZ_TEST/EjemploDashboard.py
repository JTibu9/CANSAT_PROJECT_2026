import tkinter as tk
from tkinter import ttk
import random
import math
import time
from collections import deque

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class PrinterDashboard:
    """
    Clase principal del dashboard para impresora 3D.
    
    Responsable de:
    - Construcción de la interfaz gráfica
    - Simulación de datos de sensores
    - Gestión de buffers históricos (ring buffers)
    - Control de ventanas secundarias (patrón singleton)
    
    Muestra temperaturas (hotend y bed) y posición de ejes (X, Y, Z) en tiempo real.
    """

    def __init__(self, root):
        """
        Inicializa el dashboard.
        
        Parámetros:
            root (tk.Tk): Ventana raíz de tkinter
        """
        self.root = root
        self.root.title("3D Printer Dashboard")
        self.root.geometry("900x600")
        self.root.configure(bg="#1e1e1e")

        self.start_time = time.time()

        # Buffers circulares para almacenar histórico (máximo 100 valores)
        self.temp_hotend_history = deque(maxlen=100)
        self.temp_bed_history = deque(maxlen=100)
        self.axis_x_history = deque(maxlen=100)
        self.axis_y_history = deque(maxlen=100)
        self.axis_z_history = deque(maxlen=100)

        # Referencias para evitar crear múltiples ventanas del mismo tipo
        self.temp_graph_window = None
        self.axis_graph_window = None

        self.create_widgets()
        self.update_data()

    # ================= UI =================

    def create_widgets(self):
        """Crea todos los widgets de la interfaz gráfica."""

        main_frame = tk.Frame(self.root, bg="#1e1e1e")
        main_frame.pack(fill="both", expand=True, padx=20)

        # -------- TEMPERATURE FRAME --------
        # Panel para mostrar temperaturas del hotend y cama
        self.temp_frame = tk.LabelFrame(
            main_frame,
            text="Temperatures",
            bg="#2b2b2b",
            fg="white"
        )
        self.temp_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        # Temperatura del hotend (rojo)
        self.hotend_label = tk.Label(
            self.temp_frame,
            text="Hotend: 0°C",
            bg="#2b2b2b",
            fg="red"
        )
        self.hotend_label.pack(pady=10)

        # Temperatura de la cama (naranja)
        self.bed_label = tk.Label(
            self.temp_frame,
            text="Bed: 0°C",
            bg="#2b2b2b",
            fg="orange"
        )
        self.bed_label.pack(pady=10)

        # Permitir click en el panel para abrir gráfica
        self.temp_frame.bind("<Button-1>", self.open_temp_graph)
        self.hotend_label.bind("<Button-1>", self.open_temp_graph)
        self.bed_label.bind("<Button-1>", self.open_temp_graph)

        # -------- POSITION FRAME --------
        # Panel para mostrar posición de los ejes
        self.pos_frame = tk.LabelFrame(
            main_frame,
            text="Axis Position",
            bg="#2b2b2b",
            fg="white"
        )
        self.pos_frame.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")

        # Label con posición actual X, Y, Z (cian)
        self.pos_label = tk.Label(
            self.pos_frame,
            text="X: 0.00 Y: 0.00 Z: 0.00",
            bg="#2b2b2b",
            fg="cyan"
        )
        self.pos_label.pack(pady=20)

        # Permitir click en el panel para abrir gráfica
        self.pos_frame.bind("<Button-1>", self.open_axis_graph)
        self.pos_label.bind("<Button-1>", self.open_axis_graph)

    # ================= LOOP DE DATOS =================

    def update_data(self):
        """
        Simula adquisición de datos y actualiza los buffers históricos.
        Se ejecuta periódicamente cada 200ms usando after().
        """

        # Simular temperaturas con ruido pequeño
        hotend = 200 + random.uniform(-3, 3)  # Alrededor de 200°C
        bed = 60 + random.uniform(-2, 2)      # Alrededor de 60°C

        # Actualizar labels
        self.hotend_label.config(text=f"Hotend: {hotend:.1f}°C")
        self.bed_label.config(text=f"Bed: {bed:.1f}°C")

        # Guardar en buffers
        self.temp_hotend_history.append(hotend)
        self.temp_bed_history.append(bed)

        # Simular movimiento de ejes con funciones senoidales
        t = time.time() - self.start_time
        x = 100 + 50 * math.sin(t / 2)
        y = 100 + 50 * math.cos(t / 3)
        z = 10 + 5 * math.sin(t / 4)

        # Actualizar label de posición
        self.pos_label.config(text=f"X: {x:.2f} Y: {y:.2f} Z: {z:.2f}")

        # Guardar en buffers
        self.axis_x_history.append(x)
        self.axis_y_history.append(y)
        self.axis_z_history.append(z)

        # Programar siguiente actualización
        self.root.after(200, self.update_data)

    # ================= CONTROL DE VENTANAS =================

    def open_temp_graph(self, event=None):
        """
        Abre ventana de gráfica de temperaturas.
        
        Implementa patrón singleton: verifica si la ventana ya existe
        usando winfo_exists() antes de crear una nueva.
        Si existe, solo la trae al frente.
        """

        if self.temp_graph_window is None or not self.temp_graph_window.winfo_exists():
            self.temp_graph_window = GraphWindow(
                self.root,
                "Temperature Graph",
                ["Hotend", "Bed"],
                [self.temp_hotend_history, self.temp_bed_history],
                ["red", "orange"]
            )
        else:
            self.temp_graph_window.lift()

    def open_axis_graph(self, event=None):
        """
        Abre ventana de gráfica de ejes.
        
        Implementa patrón singleton por tipo de gráfica.
        Solo permite una ventana abierta de gráfica de ejes a la vez.
        """

        if self.axis_graph_window is None or not self.axis_graph_window.winfo_exists():
            self.axis_graph_window = GraphWindow(
                self.root,
                "Axis Position Graph",
                ["X", "Y", "Z"],
                [self.axis_x_history,
                 self.axis_y_history,
                 self.axis_z_history],
                ["cyan", "green", "magenta"]
            )
        else:
            self.axis_graph_window.lift()


class GraphWindow(tk.Toplevel):
    """
    Ventana secundaria especializada para graficación de múltiples series.
    
    Hereda de Toplevel y muestra múltiples líneas en el mismo gráfico
    usando matplotlib embebido en tkinter.
    """

    def __init__(self, parent, title, labels, buffers, colors):
        """
        Inicializa ventana de gráfico.
        
        Parámetros:
            parent (tk.Widget): Ventana padre
            title (str): Título de la ventana
            labels (list[str]): Etiquetas para cada serie (ej: ["X", "Y", "Z"])
            buffers (list[deque]): Buffers circulares con datos de cada serie
            colors (list[str]): Colores para cada línea (ej: ["red", "blue"])
        """
        super().__init__(parent)

        self.title(title)
        self.geometry("700x500")

        self.buffers = buffers  # Lista de deques con datos
        self.labels = labels    # Etiquetas de series
        self.colors = colors    # Colores de líneas

        # Crear figura matplotlib embebida
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)

        # Integrar matplotlib en tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Primera actualización
        self.update_graph()

    def update_graph(self):
        """
        Redibuja la gráfica con los datos más recientes.
        
        Grafica múltiples series de datos (una línea por cada buffer)
        con una leyenda y grilla.
        """

        self.ax.clear()

        # Graficar cada serie de datos con su color y etiqueta
        for buffer, label, color in zip(self.buffers,
                                        self.labels,
                                        self.colors):
            self.ax.plot(list(buffer), label=label, color=color)

        # Añadir leyenda y grilla
        self.ax.legend()
        self.ax.grid(True)

        # Redibujar en canvas
        self.canvas.draw()

        # Reprogramar siguiente actualización cada 500ms
        self.after(500, self.update_graph)


if __name__ == "__main__":
    """Inicializa y ejecuta la aplicación del dashboard."""
    root = tk.Tk()
    app = PrinterDashboard(root)
    root.mainloop()
