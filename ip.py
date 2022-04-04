from iputils import *
from ipaddress import ip_address, ip_network

class IP:
    def __init__(self, enlace):
        """
        Inicia a camada de rede. Recebe como argumento uma implementação
        de camada de enlace capaz de localizar os next_hop (por exemplo,
        Ethernet com ARP).
        """
        self.callback = None
        self.enlace = enlace
        self.enlace.registrar_recebedor(self.__raw_recv)
        self.ignore_checksum = self.enlace.ignore_checksum
        self.meu_endereco = None
        self.meu_contador = 0

    def __raw_recv(self, datagrama):
        dscp, ecn, identification, flags, frag_offset, ttl, proto, \
           src_addr, dst_addr, payload = read_ipv4_header(datagrama)
       
        if dst_addr == self.meu_endereco:
            # atua como host
            if proto == IPPROTO_TCP and self.callback:
                self.callback(src_addr, dst_addr, payload)

        else:
            # atua como roteador
            # TODO: Trate corretamente o campo TTL do datagrama

            # verifica se o TTL vai chegaer a zero ou não
            if(ttl == 1):
                next_hop = self._next_hop(src_addr)
                checksum = calc_checksum(struct.pack('!BBHI', 11, 0, 0, 0) + datagrama[:28])
                ICMP = struct.pack('!BBHI', 11, 0, checksum, 0) + datagrama[:28]
                checksum = calc_checksum(struct.pack('!BBHHHBBH', 69, 0, 20+len(ICMP), self.meu_contador, 0, 64, IPPROTO_ICMP, 0) + str2addr(self.meu_endereco) + str2addr(src_addr))
                datagrama = struct.pack('!BBHHHBBH', 69, 0, 20+len(ICMP), self.meu_contador, 0, 64, IPPROTO_ICMP, checksum) + str2addr(self.meu_endereco) + str2addr(src_addr) + ICMP

            else:
                #Envia o datagrama para o destinatário
                next_hop = self._next_hop(dst_addr)
                ttl -= 1
                checksum = calc_checksum(struct.pack('!BBHHHBBH', 69, 0, 20+len(payload), self.meu_contador, 0, ttl, IPPROTO_TCP, 0) + str2addr(src_addr) + str2addr(dst_addr))
                datagrama = struct.pack('!BBHHHBBH', 69, 0, 20+len(payload), self.meu_contador, 0, ttl, IPPROTO_TCP, checksum) + str2addr(src_addr) + str2addr(dst_addr) + payload
            
            self.enlace.enviar(datagrama, next_hop)
                
    def _next_hop(self, dest_addr):
        # TODO: Use a tabela de encaminhamento para determinar o próximo salto
        # (next_hop) a partir do endereço de destino do datagrama (dest_addr).
        # Retorne o next_hop para o dest_addr fornecido.
        
        next_hop = None
        aux = 0        
        for currentHop in self.tabela:
            if ip_address(dest_addr) in ip_network(currentHop[0]):                
                splitItem = int(currentHop[0].split("/")[1])
                if  aux <= splitItem:
                    next_hop = currentHop[1]
                    aux = int(currentHop[0].split("/")[1])
        return next_hop
    
    def definir_endereco_host(self, meu_endereco):
        """
        Define qual o endereço IPv4 (string no formato x.y.z.w) deste host.
        Se recebermos datagramas destinados a outros endereços em vez desse,
        atuaremos como roteador em vez de atuar como host.
        """
        self.meu_endereco = meu_endereco

    def definir_tabela_encaminhamento(self, tabela):
        """
        Define a tabela de encaminhamento no formato
        [(cidr0, next_hop0), (cidr1, next_hop1), ...]
        
        Onde os CIDR são fornecidos no formato 'x.y.z.w/n', e os
        next_hop são fornecidos no formato 'x.y.z.w'.
        """
        # TODO: Guarde a tabela de encaminhamento. Se julgar conveniente,
        # converta-a em uma estrutura de dados mais eficiente.
        self.tabela = tabela

    def registrar_recebedor(self, callback):
        """
        Registra uma função para ser chamada quando dados vierem da camada de rede
        """
        self.callback = callback

    def enviar(self, segmento, dest_addr):
        """
        Envia segmento para dest_addr, onde dest_addr é um endereço IPv4
        (string no formato x.y.z.w).
        """
        next_hop = self._next_hop(dest_addr)
        # TODO: Assumindo que a camada superior é o protocolo TCP, monte o
        # datagrama com o cabeçalho IP, contendo como payload o segmento.

        #calcula checksum
        checksum = calc_checksum(struct.pack('!BBHHHBBH', 69, 0, 20+len(segmento), self.meu_contador, 0, 64, 6, 0) + str2addr(self.meu_endereco) + str2addr(dest_addr))
        #Montando o datagrama 
        datagrama = struct.pack('!BBHHHBBH', 69, 0, 20+len(segmento), self.meu_contador, 0, 64, 6, checksum) + str2addr(self.meu_endereco) + str2addr(dest_addr) + segmento

        self.meu_contador = self.meu_contador + 1

        self.enlace.enviar(datagrama, next_hop)
