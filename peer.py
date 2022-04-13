# Nome: Thiago Henrique Frois Menon Cunha
# RA: 2028080

import socket
import struct
import sys
import os
from _thread import *
import threading
from queue import Queue

# Estado possívels
RELEASED = "Released"
WANTED = "Wanted"
HELD  = "Held"

# Número de respostas recebidas
replies = 0

# Fila das requisições de acesso ao recurso
q = Queue()

# Estado inicial
state = RELEASED

# IP e porta do multicast
group = '224.1.1.1'
portGroup = 5004

# Argumento de entrada: IP
host = sys.argv[1]

#Argumento de entrada: Número total de processos na rede (contando com o próprio processo)
numPeers = sys.argv[2]

# Inicializa  e configura o socket para a comunicação multicast
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((group, portGroup))
mreq = struct.pack("4sl", socket.inet_aton(group), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


# Inicializa  e configura o socket para a comunicação unicast
sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock2.bind((host, 5005))

# Thread de recebimento/envio de mensagens com a comunicação multicast
def listen():
    global state
    while True:
        data  = sock.recv(1024)
        if data.decode().split()[0] != host: # Verifica se a mensagem que recebeu não é aquela que ele enviou

            if data.decode().split()[1] == '1': # Verifica se é um mensagem de requisição do recurso
                ms = "1"
                # Verifica se não estão usando o recurso
                # Se não: Responde a requisição
                # Se sim: Adiciona seu endereço na fila de requisições
                if state != HELD and state != WANTED:
                    sock2.sendto(ms.encode(), (data.decode().split()[0], 5005))
                else:
                    q.put(data.decode().split()[0])

# Inicia a thread do multicast
listener = threading.Thread(target=listen, daemon=True)
listener.start()

# Thread de recebimento/envio de mensagens com a comunicação unicast
def listen2():
    global replies
    global state
    global control
    while True:
        data2 = sock2.recv(1024)
        if data2.decode() == '1': # Verifica se houve resposta positiva da requisição enviada
            replies += 1

            if replies == int(numPeers) - 1: # Verifica se todos os outros processos responderam positivamente a requisição
                state = HELD
                replies = 0
        # Verifica se houve uma mensagem para a liberação do acesso a seção crítica
        # E por ser não ser o primeiro da fila mantém o estado WANTED
        elif data2.decode() == '0':
            #state = RELEASED
            replies = WANTED
        # Verifica se houve uma mensagem para a liberação do acesso a seção crítica
        # E por ser o primeiro da fila a resposta é para zera o número de requisição recebidas e alterar o estado para HELD
        elif data2.decode() == '2':
            state = HELD
            replies = 0

#Inicia a thread do unicast
listener2 = threading.Thread(target=listen2, daemon=True)
listener2.start()

# Menu de opções
while True:
    print("\nMenu:\nSair ----------- 0\nRequisitar ----- 1\nLiberar -------- 2\nAtualiza Tela -- 3\n")
    num = input("Sua escolha: ")
    os.system('clear')
    print("\n ------------------- O estado atual é {} ------------------".format(state))
    # Verifica se a opção escolhida é a requisição do recurso e o processo tem o estado REALEASED
    if num == '1' and state != HELD and state != WANTED:
        print("Requisitando o recurso...\n")
        m = host + ' ' + num # Mensagem composta: <IP> <Tipo mensagem>
        state = WANTED # O estado vira WANTED
        sock.sendto(m.encode(), (group, portGroup)) # Envia a mensagem por meio do multicast
    # Verifica se a opção escolhida é a liberação do recurso e o processo tem o estado HELD
    elif num == '2' and state == HELD:
        print("Liberando o recurso...\n")
        m = host + ' ' + num # Mensagem composta: <IP> <Tipo mensagem>
        state = RELEASED # O estado vira RELEASED
        ms = '2'
        ms2 = '0'
        if not q.empty():
            sock2.sendto(ms.encode(), (q.get(), 5005)) # Envia mensagem da liberação do recurso para o primeiro processo da fila
        while not q.empty():
            sock2.sendto(ms2.encode(), (q.get(), 5005)) # Envia a mensagem de liberação do recurso para o demais processos da fila
    elif num == '0':
        os.system('clear')
        print("Saindo...")
        break
    else:
        if num != '3': # Opção que controla a atualização da tela
            print("\nEscolha inválida!")



