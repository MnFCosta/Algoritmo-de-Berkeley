import time
import socket
import random
import threading
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
        
        self.t0 = '00:00:00'
        # Widgets
        self.tempo = QLabel(f'{self.t0}', self)
        self.teste = QLabel(f'TESTE', self)
        self.botao_ajustar = QPushButton('Ajustar Relógios', self)
        self.botao_cancelar = QPushButton('X',self)
        

    
        self.setWindowTitle('Servidor')
        self.setGeometry(670, 100, 400, 300) #(X, Y, W, H)
        

        # Posicionar os widgets na tela
        self.tempo.setGeometry(90,100,223,100)
        self.teste.setGeometry(90,200,223,100)
        self.botao_ajustar.setGeometry(10, 10, 150, 45)
        self.botao_cancelar.setGeometry(350, 10, 40, 30)

        #Estilização
        self.tempo.setStyleSheet("background-color: rgb(255,255,255); color: black; border: 1px solid black; font-size: 50px;")
        self.tempo.setAlignment(QtCore.Qt.AlignCenter)

        self.botao_ajustar.setStyleSheet("background-color: rgb(255,255,255); color: black; border: 1px solid black; border-radius: 12px;")

        self.botao_cancelar.setStyleSheet("background-color: red; color: black;")

        # Configurar layout
        self.botao_cancelar.clicked.connect(self.close)
        self.botao_ajustar.clicked.connect(self.ajustar_relogios)

        # Iniciando servidor em uma thread separada
        self.servidor = Servidor()
        self.servidor.start()

        self.servidor.sinal.connect(self.atualizar_tempo_interface)

    def atualizar_tempo_interface(self, tempo):
        self.t = tempo
        self.tempo.setText(self.t)
    
    def ajustar_relogios(self):
        self.servidor.atualizar_tempos_clientes(self.t)

class Servidor(QThread):
    sinal = pyqtSignal(str)

    def __init__(self, parent=None,):
        super().__init__(parent)
        self.cliente_sockets = []
        self.tempo_atual = 0

    def atualizar_tempos_clientes(self, tempo):
        for client_socket in self.cliente_sockets:
            try:
                client_socket.send(tempo.encode())
            except Exception as e:
                print("Erro ao enviar o tempo ao cliente:", str(e))
    
    def conecta_cliente(self, cliente, endereco):
        print(f"Conexão aceita de {endereco[1]}")
        self.cliente_sockets.append(cliente) 
        print("Clientes conectados:", len(self.cliente_sockets))
    
    def atualizar_tempo(self, tempo):
        self.tempo_atual = tempo
        self.sinal.emit(tempo)
        

    def run(self):
        HOST = '127.0.0.1'
        PORT = 8000
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT))
        s.listen(4)
        print("Servidor escutando...")
        
        # Iniciando relogio em uma thread separada
        self.relogio = ThreadRelogio()
        self.relogio.start()

        self.relogio.sinal.connect(self.atualizar_tempo)

        while True:
            conn, ender = s.accept()
            self.conecta_cliente(conn, ender)
            # Start a new thread to handle the client
            client_thread = ClienteHandler(conn, self)
            client_thread.start()

class ClienteHandler(QThread):
    def __init__(self, socket_cliente, servidor):
        super().__init__()
        self.socket_cliente = socket_cliente
        self.servidor_instance = servidor

    def run(self):
        while True:
            data = self.socket_cliente.recv(1024).decode()
            t1 = self.servidor_instance.tempo_atual
            t2 = self.servidor_instance.tempo_atual
            self.socket_cliente.send(str.encode(f'{data}|{t1}|{t2}|'))
            
            if not data:
                break
            
        self.socket_cliente.close()
        
    
class ThreadRelogio(QThread):
    sinal = pyqtSignal(str)

    def __init__(self, parent=None,):
        super().__init__(parent)

    def run(self):
        h = 0
        m = 0
        s = 0
        while True:
            if h == 23 and m == 59 and s == 59:
                h = 0
                m = 0
                s = 0
            if m == 59 and s == 59:
                h+=1
                m = 0
                s = 0
            if s == 59:
                m+=1
                s = 0

            s += 1
            tempo = f'{h}:{m}:{s}' 
            self.sinal.emit(tempo)
            time.sleep(1)
    
    def get_tempo(self):
        tempo = f'{self.h}:{self.m}:{self.s}' 
        return tempo

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