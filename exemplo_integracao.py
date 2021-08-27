#!/usr/bin/env python3
# Antes de usar, execute o seguinte comando para evitar que o Linux feche
# as conexões TCP que o seu programa estiver tratando:
#
# sudo iptables -I OUTPUT -p tcp --tcp-flags RST RST -j DROP


# Este é um exemplo de um programa que faz eco, ou seja, envia de volta para
# o cliente tudo que for recebido em uma conexão.

import asyncio
from camadaenlace import CamadaEnlaceLinux
from tcp import Servidor   # copie o arquivo do Trabalho 2
from ip import IP

states = {}
nicks = {}
buffers = {}
lista = []

def send_all(msg):
    for sock in lista:
        sock.enviar(msg)

def dados_recebidos(conexao, dados):
    print(conexao, dados)
    if dados == b'':
        lista.remove(conexao)
        if states[conexao] == 2:
            send_all(b'/quit %s\n' % nicks[conexao])
        del states[conexao]
        del nicks[conexao]
        del buffers[conexao]
        conexao.fechar()
    else:
        buffers[conexao] += dados
        linhas = buffers[conexao].split(b'\n')
        buffers[conexao] = linhas[-1]
        for msg in linhas[:-1]:
            if msg.startswith(b'/nick '):
                oldnick = nicks[conexao]
                _, newnick = msg.split(b' ', 1)
                if newnick in nicks.values():
                    conexao.enviar(b'/error\n')
                else:
                    nicks[conexao] = newnick
                    if states[conexao] == 1:
                        send_all(b'/joined %s\n' % nicks[conexao])
                    elif states[conexao] == 2:
                        send_all(b'/renamed %s %s\n' % (oldnick, nicks[conexao]))
                    states[conexao] = 2
            else:
                if states[conexao] == 1:
                    conexao.enviar(b'/error\n')
                elif states[conexao] == 2:
                    send_all(b'%s: %s\n' % (nicks[conexao], msg))

def conexao_aceita(conexao):
    print(conexao)
    lista.append(conexao)
    states[conexao] = 1
    nicks[conexao] = b''
    buffers[conexao] = b''
    conexao.registrar_recebedor(dados_recebidos)   # usa esse mesmo recebedor para toda conexão aceita

enlace = CamadaEnlaceLinux()
rede = IP(enlace)
rede.definir_endereco_host('192.168.88.235')  # consulte o endereço IP da sua máquina com o comando: ip addr
rede.definir_tabela_encaminhamento([
    ('192.168.88.231/32', '192.168.88.231'),
    ('0.0.0.0/0', '192.168.88.1')  # consulte sua rota padrão com o comando: ip route | grep default
])
servidor = Servidor(rede, 7000)
servidor.registrar_monitor_de_conexoes_aceitas(conexao_aceita)
asyncio.get_event_loop().run_forever()
