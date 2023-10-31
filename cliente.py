import time
import socket
import random
import sys
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QColor


class TelaPrincipal(QWidget):
    def __init__(self,):
        super().__init__()
    
        self.initUI()

        self.dado_thread_rodando = False

    def initUI(self):
        
        self.t = '00:00:00'
        # Widgets
        self.tempo = QLabel(f'{self.t}', self)
        self.botao_cancelar = QPushButton('X',self)
        

    
        self.setWindowTitle('Cliente')
        self.setGeometry(100, 100, 400, 300) #(X, Y, W, H)
        

        # Posicionar os widgets na tela
        self.tempo.setGeometry(90,90,223,100)
        self.botao_cancelar.setGeometry(350, 10, 40, 30)

        #Estilização
        self.tempo.setStyleSheet("background-color: rgb(255,255,255); color: black; border: 1px solid black; font-size: 50px; border-radius: 50px;")
        self.tempo.setAlignment(QtCore.Qt.AlignCenter)

        self.botao_cancelar.setStyleSheet("background-color: red; color: black;")

        # Configurar layout
        self.botao_cancelar.clicked.connect(self.close)

        # Iniciando cliente em uma thread separada
        self.cliente = Cliente()
        self.cliente.start()

        # Iniciando relogio em uma thread separada
        self.relogio = ThreadRelogio()
        self.relogio.start()

        self.relogio.sinal.connect(self.atualizar_tempo)
        self.cliente.sinal.connect(self.atualizar_tempo_cliente)
    
    def atualizar_tempo(self, tempo):
        self.t = tempo
        self.tempo.setText(self.t)
    
    def atualizar_tempo_cliente(self, tempo):
        print(tempo)
        h = tempo[0:1]
        m = tempo[2:3]
        s = tempo[4:]
        self.relogio.atualizar_tempo_relogio(int(h),int(m),int(s))

class Cliente(QThread):
    sinal = pyqtSignal(str)

    def __init__(self, parent=None,):
        super().__init__(parent)

    def run(self):
        HOST = '127.0.0.1'
        PORT = 8000
        #Criando objeto socket IPV4 usando protocolo TCP.
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((HOST,PORT))
        cliente.send(str.encode("Cliente conectado!"))

        while True:
            tempo = cliente.recv(1024).decode()
            self.sinal.emit(tempo)

        

class ThreadRelogio(QThread):
    sinal = pyqtSignal(str)

    def __init__(self, parent=None,):
        super().__init__(parent)
        self.h = 0
        self.m = 0
        self.s = 0

    def run(self):
        while True:
            if self.h == 23 and self.m == 59 and self.s == 59:
                self.h = 0
                self.m = 0
                self.s = 0
            if self.m == 59 and self.s == 59:
                self.h+=1
                self.m = 0
                self.s = 0
            if self.s == 59:
                self.m+=1
                self.s = 0

            self.s += 1
            tempo = f'{self.h}:{self.m}:{self.s}' 
            self.sinal.emit(tempo)
            time.sleep(1)
    
    def atualizar_tempo_relogio(self, h, m, s):
        self.h = h
        self.m = m
        self.s = s
        print(f"{self.h}:{self.m}:{self.s}")

#Widgets
class QuadradoWidget(QWidget):
    cor_quadrado = QColor(255, 0, 0)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QColor(0, 0, 0))
        painter.setBrush(self.cor_quadrado)
        
        painter.drawRect(0, 0, 150, 150)
    
    

if __name__ == '__main__':
    #Cria uma instancia da aplicação PyQt, necessária para configurar a interface gráfica e o loop de eventos
    app = QApplication(sys.argv)
    #Cria uma instância da classe TelaLogin, que representa a tela de login da aplicação
    ui = TelaPrincipal()
    #Mostra a tela de login
    ui.show()
    #app.exec inicia o loop de eventos da aplicação, que aguarda por cliques de mouse e pressionamentos de teclas por exemplo
    #sys.exit termina a aplicação quando tem um retorno de 0, ou seja, quando app.exec_() retornar 0, a aplicação será terminada
    sys.exit(app.exec_())