"""Tk dashboard: connection, explicit controls, telemetry and embedded plot."""
import queue
import threading
from pathlib import Path
import time
import tkinter as tk
from tkinter import ttk
from .client import Client, ProcessTransport, SerialTransport


def run(port="sim"):
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    root = tk.Tk()
    root.title("Open Elbow | Bench dashboard | SI units")
    root.geometry("1000x760")
    client = None
    tasks = queue.Queue()
    results = queue.Queue()
    connected = tk.StringVar(value="Disconnected — outputs inhibited at boot")
    port_var = tk.StringVar(value=port)
    value_var = tk.StringVar(value="0.5")
    op_var = tk.StringVar(value="TARGET")
    output_var = tk.StringVar(value="artifacts/session.csv")
    status = tk.StringVar(value="No telemetry")

    def worker():
        while True:
            item = tasks.get()
            if item is None:
                return
            action, args = item
            try:
                results.put((True, action(*args)))
            except Exception as exc:
                results.put((False, str(exc)))

    threading.Thread(target=worker, daemon=True).start()

    def connect():
        nonlocal client
        if client:
            return
        try:
            transport = ProcessTransport() if port_var.get() == "sim" else SerialTransport(port_var.get())
            client = Client(transport, output_var.get())
            connected.set("Connected | " + port_var.get() + " | heartbeat 20 Hz")
            tasks.put((client.command, ("PING",)))
        except Exception as exc:
            connected.set(str(exc))

    def disconnect():
        nonlocal client
        if client:
            client.close()
            client = None
        connected.set("Disconnected")

    def command(op=None):
        if not client:
            return
        try:
            chosen = op or op_var.get()
            value = float(value_var.get()) if not op else 0.0
            tasks.put((client.command, (chosen, value)))
        except ValueError:
            connected.set("Enter a numeric SI value")

    header = ttk.Frame(root, padding=12)
    header.pack(fill="x")
    ttk.Label(header, text="Port (sim or COMx)").grid(row=0, column=0)
    ttk.Entry(header, textvariable=port_var, width=15).grid(row=0, column=1, padx=6)
    ttk.Button(header, text="Connect", command=connect).grid(row=0, column=2)
    ttk.Button(header, text="Disconnect / stop", command=disconnect).grid(row=0, column=3, padx=8)
    ttk.Label(header, text="CSV log").grid(row=1, column=0)
    ttk.Entry(header, textvariable=output_var, width=48).grid(row=1, column=1, columnspan=3, sticky="we", pady=6)
    ttk.Label(root, textvariable=connected, padding=10).pack(fill="x")
    controls = ttk.Frame(root, padding=10)
    controls.pack(fill="x")
    for col, (op, text) in enumerate((("CAL", "Calibrate at zero"), ("ARM", "Run"), ("STOP", "Standby"), ("RESET", "Reset + physical button"), ("ESTOP", "Software E-stop"))):
        ttk.Button(controls, text=text, command=lambda o=op: command(o)).grid(row=0, column=col, padx=3)
    ttk.Combobox(controls, textvariable=op_var, values=("TARGET", "ASSIST", "KP", "KD", "TMAX", "VMAX"), state="readonly", width=12).grid(row=1, column=0, pady=10)
    ttk.Entry(controls, textvariable=value_var, width=14).grid(row=1, column=1)
    ttk.Button(controls, text="Apply SI value", command=command).grid(row=1, column=2)
    ttk.Label(controls, text="rad, Nm, Nm/rad, Nm·s/rad, Nm, rad/s").grid(row=1, column=3, columnspan=2)
    # Simulation fixture operations are explicitly separated from physical commands.
    def fixture():
        if client and client.transport.simulated:
            client.inject("Q", 0.2245329252)
    ttk.Button(controls, text="SIM only: move zero fixture to 0.225 rad", command=fixture).grid(row=2, column=0, columnspan=3, sticky="w")
    ttk.Label(root, textvariable=status, font=("Consolas", 11), padding=12).pack(fill="x")
    fig = Figure(figsize=(8, 3.8), dpi=100)
    axis = fig.add_subplot(111)
    axis.set_xlabel("Controller time [s]")
    axis.set_ylabel("Elbow angle [rad]")
    axis.grid(alpha=0.2)
    curve, = axis.plot([], [], color="#137e91")
    canvas = FigureCanvasTkAgg(fig, root)
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=12)

    def update():
        while not results.empty():
            ok, result = results.get_nowait()
            connected.set(str(result) if not ok else "Command accepted | heartbeat 20 Hz")
        if client and client.latest:
            s = client.latest
            status.set(f"{s.get('state')}   fault={s.get('fault')}   enabled={s.get('enabled')}\n"
                       f"q={s.get('q', 0):.3f} rad   dq={s.get('dq', 0):.3f} rad/s   I={s.get('current', 0):.3f} A\n"
                       f"T={s.get('temperature', 0):.1f} C   bus={s.get('voltage', 0):.2f} V   torque={s.get('torque', 0):.3f} Nm")
            samples = list(client.samples[-400:])
            curve.set_data([s["time_ms"] / 1000 for s in samples], [s["q"] for s in samples])
            axis.relim()
            axis.autoscale_view()
            canvas.draw_idle()
            if client.last_error:
                connected.set(client.last_error)
        root.after(100, update)

    def close():
        disconnect()
        tasks.put(None)
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", close)
    root.after(100, update)
    root.mainloop()

