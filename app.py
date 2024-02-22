import sys
import os
import subprocess
import requests
import zipfile
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel, QMessageBox, QFileDialog, QDialog, QDialogButtonBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class FrpcOutputThread(QThread):
    output_signal = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        while True:
            line = process.stdout.readline()
            if line:
                self.output_signal.emit(line.strip())
            else:
                break

class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('关于')
        self.setGeometry(200, 200, 400, 200)

        self.layout = QVBoxLayout()

        self.label = QLabel('frpc管理工具 v1.0\n\n作者: 没用的小废鼠\n软件免费开源\n')
        self.layout.addWidget(self.label)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)
        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)

class FrpcConfigWindow(QDialog):
    def __init__(self, frpc_toml_path):
        super().__init__()

        self.setWindowTitle('编辑frpc.toml文件')
        self.setGeometry(200, 200, 600, 400)

        self.layout = QVBoxLayout()

        self.label = QLabel('frpc.toml 文件内容:')
        self.layout.addWidget(self.label)

        self.text_edit = QTextEdit()
        self.layout.addWidget(self.text_edit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)

        self.frpc_toml_path = frpc_toml_path

        self.load_frpc_config()

    def load_frpc_config(self):
        try:
            with open(self.frpc_toml_path, 'r') as file:
                self.text_edit.setText(file.read())
        except Exception as e:
            QMessageBox.warning(self, '错误', f'加载文件失败: {e}')

    def accept(self):
        try:
            with open(self.frpc_toml_path, 'w') as file:
                file.write(self.text_edit.toPlainText())
            QMessageBox.information(self, '成功', '保存成功')
            self.close()
        except Exception as e:
            QMessageBox.warning(self, '错误', f'保存文件失败: {e}')

class FrpcManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('frpc管理工具')
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

        self.output_label = QLabel('frpc输出:')
        self.layout.addWidget(self.output_label)

        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)
        self.layout.addWidget(self.output_text_edit)

        self.central_widget.setLayout(self.layout)

        self.edit_button = QPushButton('编辑frpc.toml')
        self.edit_button.clicked.connect(self.edit_frpc_config)
        self.layout.addWidget(self.edit_button)

        self.start_button = QPushButton('启动frpc')
        self.start_button.clicked.connect(self.start_frpc)
        self.layout.addWidget(self.start_button)

        self.stop_button = QPushButton('关闭frpc')
        self.stop_button.clicked.connect(self.stop_frpc)
        self.layout.addWidget(self.stop_button)

        self.about_button = QPushButton('关于')
        self.about_button.clicked.connect(self.show_about_dialog)
        self.layout.addWidget(self.about_button)



        # 设置frp文件夹路径
        self.frp_folder_path = 'frp'
        if not os.path.exists(self.frp_folder_path):
            self.download_and_extract_frp()

        # 设置frpc.toml文件路径
        self.frpc_toml_path = os.path.join(self.frp_folder_path, 'frpc.toml')

        self.frpc_process = None

    def edit_frpc_config(self):
        editor = FrpcConfigWindow(self.frpc_toml_path)
        editor.exec_()

    def start_frpc(self):
        if self.frpc_process is not None:
            QMessageBox.warning(self, '警告', 'frpc已经在运行中。')
            return

        command = [os.path.join(self.frp_folder_path, 'frpc.exe'), '-c', self.frpc_toml_path]
        self.frpc_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        self.output_thread = FrpcOutputThread(command)
        self.output_thread.output_signal.connect(self.update_output)
        self.output_thread.start()

        QMessageBox.information(self, '成功', 'frpc已启动')

    def stop_frpc(self):
        if self.frpc_process is None:
            QMessageBox.warning(self, '警告', 'frpc未启动。')
            return

        self.frpc_process.terminate()
        self.frpc_process = None

        QMessageBox.information(self, '成功', 'frpc已关闭')

    def update_output(self, output):
        self.output_text_edit.append(output)

    def show_about_dialog(self):
        dialog = AboutDialog()
        dialog.exec_()

    def download_and_extract_frp(self):
        try:
            url = 'https://dlink.host/lanzou/aHR0cHM6Ly94aWFvZmVpc2h1LmxhbnpvdXEuY29tL2lURmNlMXAyOWs1aSZwYXNzQ29kZT14cG1zbA.zip'
            response = requests.get(url)
            with open('frp.zip', 'wb') as f:
                f.write(response.content)
            with zipfile.ZipFile('frp.zip', 'r') as zip_ref:
                zip_ref.extractall(self.frp_folder_path)
            QMessageBox.information(self, '成功', 'frp下载并解压成功。')
        except Exception as e:
            QMessageBox.warning(self, '错误', f'下载或解压frp失败: {e}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FrpcManagerWindow()
    window.show()
    sys.exit(app.exec_())
