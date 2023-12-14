import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QGridLayout, QFileDialog
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPainter, QColor
import time
from chip8 import cpu

class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixels = [0] * (64 * 32)  # Initialize pixel data
        self.setStyleSheet("background-color: black;")

    def paintEvent(self, event):
        qp = QPainter(self)
        self.drawCanvas(qp)

    def drawCanvas(self, qp):
        o_width, o_height = 64, 32
        width, height = self.width(), self.height()
        pixel_width = width // o_width
        pixel_height = height // o_height

        for i, p in enumerate(self.pixels):
            x = i % o_width
            y = i // o_width
            color = QColor(255, 255, 255) if p else QColor(0, 0, 0)
            qp.setBrush(color)
            qp.drawRect(int(x * pixel_width), int(y * pixel_height), pixel_width, pixel_height)

class MainWindow(QMainWindow):
    start_signal = pyqtSignal()
    pause_signal = pyqtSignal()
    reset_signal = pyqtSignal()
    exit_signal = pyqtSignal()
    load_signal = pyqtSignal(str)
    key_down_signal = pyqtSignal(int)
    key_up_signal = pyqtSignal(int)
    def __init__(self, worker):
        super().__init__()

        self.worker = worker
        self.worker.draw_signal.connect(self.draw)
        self.start_signal.connect(self.worker.start)
        self.pause_signal.connect(self.worker.pause)
        self.reset_signal.connect(self.worker.reset)
        self.exit_signal.connect(self.worker.exit)
        self.load_signal.connect(self.worker.load)
        self.key_down_signal.connect(self.worker.key_down)
        self.key_up_signal.connect(self.worker.key_up)

        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.thread.start()

        self.setWindowTitle("Chip-8 Emulator")

        self.resize(800, 600)  # Width: 800 pixels, Height: 600 pixels
        # Main Widget and Layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # Display Canvas
        self.canvas = Canvas()
        main_layout.addWidget(self.canvas)

        # Input Section with Grid Layout for Buttons
        grid_layout = QGridLayout()
        self.buttons = []
        for i in range(16):  # Creating 16 buttons
            button = QPushButton(f"{i:X}")  # Hexadecimal representation
            self.buttons.append(button)
            row = i // 4  # Determine the row
            col = i % 4   # Determine the column
            grid_layout.addWidget(button, row, col)
            # button.clicked.connect(self.on_button_clicked)
            button.pressed.connect(self.on_key_down)
            button.released.connect(self.on_key_up)

        main_layout.addLayout(grid_layout)

        control_layout = QVBoxLayout()
        control_layout.setDirection(QVBoxLayout.LeftToRight)
        # control_layout.addStretch(1)
        # Start Button
        start_button = QPushButton("Start")
        start_button.clicked.connect(self.start_clicked)
        control_layout.addWidget(start_button)
        # Pause Button
        pause_button = QPushButton("Pause")
        pause_button.clicked.connect(self.pause_clicked)
        control_layout.addWidget(pause_button)
        # Reset Button
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset_clicked)
        control_layout.addWidget(reset_button)
        # Exit Button
        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.exit_clicked)
        control_layout.addWidget(exit_button)
        # load Button
        load_button = QPushButton("Load")
        load_button.clicked.connect(self.load_clicked)
        control_layout.addWidget(load_button)

        main_layout.addLayout(control_layout)

        # Set the layout for the main widget
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def start_clicked(self):
        self.start_signal.emit()
    
    def pause_clicked(self):
        self.pause_signal.emit()

    def reset_clicked(self):
        self.reset_signal.emit()

    def exit_clicked(self):
        self.exit_signal.emit()

    def load_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;Chip-8 ROMs (*.ch8)")
        # Check if a file was selected (file_path is not empty)
        if file_path:
            print(f"Selected file: {file_path}")
            # You can now pass the file_path to your worker or another method to handle the file loading
            self.load_signal.emit(file_path) 

    def on_button_clicked(self):
        # Handle button click event
        button = self.sender()
        if button:
            print(f'Button "{button.text()}" Pressed')
    
    def on_key_down(self):
        sender = self.sender()
        if sender:
            index = self.buttons.index(sender)
            print(f'Button "{sender.text()}" Pressed')
            self.key_down_signal.emit(index)
    
    def on_key_up(self):
        sender = self.sender()
        if sender:
            index = self.buttons.index(sender)
            print(f'Button "{sender.text()}" Released')
            self.key_up_signal.emit(index)

    def draw(self, pixels):
        self.canvas.pixels = pixels
        self.canvas.update()  # Triggers a repaint


class worker(QObject):
    draw_signal = pyqtSignal(list)

    def __init__(self, _cpu:cpu):
        super().__init__()
        self.path = None
        self.running = False
        self.paused = False
        self.cpu:cpu = _cpu
        self.freq = 1 # hz

    def run(self):
        while True:
            if self.running:
                time.sleep(0.01)
                if not self.paused:
                    # print(self.keys)
                    self.cpu.cycle()
                    # print(self.cpu.pc)
                    if self.cpu.update_display:
                        self.draw_signal.emit(self.cpu.display_buffer.copy())
                        self.cpu.update_display = False
                else:
                    print("Paused")
            else:
                print("Stopped")
                time.sleep(1)

    def start(self):
        self.cpu.init_cpu()
        if self.path:
            self.cpu.load_rom(self.path)
            self.running = True
        print(self.running)
    
    def pause(self):
        self.paused = not self.paused

    def reset(self):
        self.running = False
        self.paused = False
    
    def exit(self):
        self.running = False
        self.paused = False
    
    def key_down(self, key):
        self.cpu.key_inputs[key] = 1
    
    def key_up(self, key):
        self.cpu.key_inputs[key] = 0
    
    def draw(self):
        pass

    def load(self, path):
        print(path)
        self.path = path
        # self.cpu.load_rom(path)
        # dump memory
        for i in range(0x200, 0x200+0x100):
            print(hex(i), hex(self.cpu.memory[i]))

if __name__ == "__main__":
    # Create a worker object and a thread
    emulator = worker(cpu())

    # Run the application
    app = QApplication(sys.argv)
    window = MainWindow(emulator)
    window.show()
    sys.exit(app.exec_())
