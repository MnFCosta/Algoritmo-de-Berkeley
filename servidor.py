import time
import socket
import random
import threading
import datetime
from datetime import timedelta
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
        self.botao_ajustar = QPushButton('Ajustar Relógios', self)
        self.botao_cancelar = QPushButton('X',self)
        
        self.setWindowTitle('Servidor')
        self.setGeometry(670, 100, 400, 300) #(X, Y, W, H)
        

        # Posicionar os widgets na tela
        self.tempo.setGeometry(90,100,223,100)
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

#Servidor aonde são enviados requisições aos clientes, e aonde clientes se conectam.
class Servidor(QThread):
    sinal = pyqtSignal(str)

    def __init__(self, parent=None,):
        super().__init__(parent)
        self.cliente_sockets = []
        self.tempos_clientes = []
        self.tempo_atual = 0

    #envia o ping para que todos os clientes retornem seus tempos (Algoritmo de Berkley)
    def atualizar_tempos_clientes(self, tempo):
        for client_socket in self.cliente_sockets:
            try:
                client_socket.send('PING'.encode())

            except Exception as e:
                print("Erro ao enviar o tempo ao cliente:", str(e))
    
    #Adiciona cliente a lista de clientes conectados
    def conecta_cliente(self, cliente, endereco):
        print(f"Conexão aceita de {endereco[1]}")
        self.cliente_sockets.append(cliente) 
        print("Clientes conectados:", len(self.cliente_sockets))
    
    #Envia o tempo para a interface
    def atualizar_tempo(self, tempo):
        self.tempo_atual = tempo
        self.sinal.emit(tempo)
    
    #Executa o algoritmo de berkley quando requisitado
    def algoritmo_berkley(self):
        #lista com todos os clientes
        clientes = []
        #lista com todos os tempos que enviaram
        tempos = []

        #adiciona os valores recebidos as listas
        for i in self.tempos_clientes:
            clientes.append(i.split('|')[0])
            tempos.append(i.split('|')[1])
        
        #declara uma variável com o valor do tempo do servidor, e uma variável utilizada para converter este tempo em timedelta
        tservidor = self.relogio.get_tempo()
        tservidor = datetime.datetime.strptime(tservidor, '%H:%M:%S')
        
        
        converter_timedelta = f"{0}:{0}:{0}"
        converter_timedelta = datetime.datetime.strptime(converter_timedelta.lstrip(), '%H:%M:%S')

        #todos os tempos são por padrão  um timedelta de 00:00:00, para casos onde os 4 clientes não estão conectados
        tc1, tc2, tc3, tc4 = datetime.timedelta(), datetime.timedelta(), datetime.timedelta(), datetime.timedelta()

        #Adiciona o tempo dos clientes baseado em quantos clientes estão conectados
        if len(tempos) > 0:
            tc1 = datetime.datetime.strptime(tempos[0].lstrip(), '%H:%M:%S')
            tc1 = tc1 - converter_timedelta
        if len(tempos) > 1:
            tc2 = datetime.datetime.strptime(tempos[1].lstrip(), '%H:%M:%S')
            tc2 = tc2 - converter_timedelta
        if len(tempos) > 2:
            tc3 = datetime.datetime.strptime(tempos[2].lstrip(), '%H:%M:%S')
            tc3 = tc3 - converter_timedelta
        if len(tempos) > 3:
            tc4 = datetime.datetime.strptime(tempos[3].lstrip(), '%H:%M:%S')
            tc4 = tc4 - converter_timedelta

        #converte o tempo a timedelta (necessário para operações)
        tservidor = tservidor - converter_timedelta

        #soma os tempos
        soma_segundos = tservidor + tc1 + tc2 + tc3 + tc4

        #transforma a soma em segundos
        soma_segundos = soma_segundos.total_seconds()

        #divide o tempo pela quantidade de clients + o servidor
        tempo_correto = soma_segundos/(len(clientes) + 1)

        #transforma o tempo dividido em segundos
        tempo_timedelta = timedelta(seconds=tempo_correto)

        # formata pra H:M:S
        tempo_formatado = str(f'{tempo_timedelta}').split(".")[0]

        #Atualiza o tempo do servidor e dos clientes conectados com a média de tempos
        tempo_formatado = tempo_formatado.split(':')

        h = int(tempo_formatado[0])
        m = int(tempo_formatado[1])
        s = int(tempo_formatado[2])

        self.relogio.h = h
        self.relogio.m = m
        self.relogio.s = s

        for client_socket in self.cliente_sockets:
            try:
                client_socket.send(f'{tempo_formatado[0]}:{tempo_formatado[1]}:{tempo_formatado[2]}'.encode())

            except Exception as e:
                print("Erro ao enviar o tempo ao cliente:", str(e))

        #Limpa a lista de tempos dos clientes que contém os tempos antigos
        self.tempos_clientes.clear()
        

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

#Thread para lidar com clientes conectados separadamente
class ClienteHandler(QThread):
    def __init__(self, socket_cliente, servidor):
        super().__init__()
        self.socket_cliente = socket_cliente
        self.servidor_instance = servidor
    
    #função que lida com requisições do algoritmo de christian
    def handle_christian(self, data):
        t1 = self.servidor_instance.tempo_atual
        t2 = self.servidor_instance.tempo_atual
        self.socket_cliente.send(str.encode(f'{data}|{t1}|{t2}|'))
    
    #função que lida com requisições do algoritmo de berkley
    def handle_berkley(self, data):
        data = f'{self.socket_cliente}|{data}'
        self.servidor_instance.tempos_clientes.append(data)
        if len(self.servidor_instance.tempos_clientes) == len(self.servidor_instance.cliente_sockets):
            self.servidor_instance.algoritmo_berkley()

    #recebe dados enviados pelos clientes
    def run(self):
        while True:
            data = self.socket_cliente.recv(1024).decode()

            #caso o dado seja uma resposta ao ping do algoritmo de berkley
            if data.split('|')[0] == "RESPOSTA":
                self.handle_berkley(data.split('|')[1])
            else:
                self.handle_christian(data.split('|')[1])
            
            if not data:
                break
            
        self.socket_cliente.close()
    
    
        
#Thread com o relógio do servidor
class ThreadRelogio(QThread):
    sinal = pyqtSignal(str)

    def __init__(self, parent=None,):
        super().__init__(parent)
        self.h = 0
        self.m = 0
        self.s = 0

    #incrementa segundos e emite sinais para o servidor atualizar a interface
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
            if self.s >= 59:
                self.m+=1
                self.s = 0

            self.s += 1
            tempo = f'{self.h}:{self.m}:{self.s}' 
            self.sinal.emit(tempo)
            time.sleep(1)
    
    #retorna o tempo atual do relógio do servidor
    def get_tempo(self):
        tempo = f'{self.h}:{self.m}:{self.s}' 
        return tempo


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