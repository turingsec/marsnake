import pcapy
import struct
import tempfile
import time
import os
import re

# constants
TCP_ACK =  0b00010000
TCP_PUSH = 0b00001000
TCP_RST =  0b00000100
TCP_SYN =  0b00000010
TCP_FIN =  0b00000001

FILE_IN_MEMORY_MAXSIZE = 65536
FILE_SIZE_JUDGE_THRESHOLD = 67108864    # 64MB
FILE_SAVE_PATH = "d:\\test"

class tcp_traffic():
    def __init__(self, pe_captured_cb, elf_captured_cb, http_captured_cb):
        self.name = "TCP traffic"
        
        self.connections = []
        self.http_pattern = re.compile("(?:GET|POST) \S+? HTTP/1.1\x0d\x0a|HTTP/1.1 \d+? \w+?\x0d\x0a")
        
        self.pe_captured_cb = pe_captured_cb
        self.elf_captured_cb = elf_captured_cb
        self.http_captured_cb = http_captured_cb

    def init(self):
        try:
            self.device = pcapy.open_live(pcapy.lookupdev(), 65535, 0, 0)
            self.device.setfilter("tcp port 80")
        except Exception as e:
            print(e)
            return False
            
        return True

    def do(self):
        while True:
            pkt = self.parse_pkt(self.device.next()[1])
            #print pkt
            if pkt is None:
                continue
            else:
                (src, dest, src_port, dest_port, sequence, acknowledgement, flags, payload) = pkt

            if flags & TCP_SYN != 0:
                # tcp handshake
                # at this time, there should be not any data in pkt

                f = tempfile.TemporaryFile()

                i = 0
                while i < len(self.connections):
                    if self.connections[i][0] == src and self.connections[i][1] == dest and self.connections[i][2] == src_port and self.connections[i][3] == dest_port:
                        if self.connections[i][4] != sequence + 1:
                            print "syn: double self.connections, try to recover!!!"
                            # judge?
                            self.connections[i][4:] = [sequence + 1, f, time.time(), time.time()]
                        break
                    i += 1

                if i >= len(self.connections):
                    self.connections.append([src, dest, src_port, dest_port, sequence + 1, f, time.time(), time.time()])

            elif flags & TCP_RST != 0:
                # tcp reset
                # at this time, there should be not any data in pkt and connection in both direction should close

                i = 0
                while i < len(self.connections):
                    if self.connections[i][0] == src and self.connections[i][1] == dest and self.connections[i][2] == src_port and self.connections[i][3] == dest_port:
                        file_size = (sequence - self.connections[i][4]) if sequence >= self.connections[i][4] else (0xffffffff - self.connections[i][4] + sequence)
                        if file_size > 0:
                            self.connections[i][5].truncate(file_size)
                            self.judge(self.connections[i][5])
                            
                        self.connections.remove(self.connections[i])
                        continue

                    if self.connections[i][0] == dest and self.connections[i][1] == src and self.connections[i][2] == dest_port and self.connections[i][3] == src_port:
                        if flags & TCP_ACK != 0:
                            file_size = (acknowledgement - self.connections[i][4]) if acknowledgement >= self.connections[i][4] else (0xffffffff - self.connections[i][4] + acknowledgement)
                        else:
                            file_size = self.connections[i][5].tell()

                        if file_size > 0:
                            self.connections[i][5].truncate(file_size)
                            self.judge(self.connections[i][5])
                            
                        self.connections.remove(self.connections[i])
                        continue

                    i += 1

            else:
                # tcp data payload
                # at this time, there probably contains data in pkt

                i = 0
                while i < len(self.connections):
                    if self.connections[i][0] == src and self.connections[i][1] == dest and self.connections[i][2] == src_port and self.connections[i][3] == dest_port:
                        break
                    i += 1

                if i >= len(self.connections):
                    print "connection not found"
                    continue

                self.connections[i][7] = time.time()

                if sequence == self.connections[i][4] - 1:
                    # tcp keepalive
                    if len(payload) == 0 or (len(payload) == 1 and payload == '\x00'):
                        continue

                if sequence < self.connections[i][4] and (sequence + 0x80000000 > self.connections[i][4]):
                    # maybe a resend pkt after we rewrap the file
                    print "resend pkt after file rewrap"
                    continue

                f = self.connections[i][5]
                if len(payload) != 0:
                    # solve sequence wrap
                    fpos = (sequence - self.connections[i][4]) if sequence >= self.connections[i][4] else (0xffffffff - self.connections[i][4] + sequence)

                    f.seek(fpos)
                    f.write(payload)

                if flags & TCP_PUSH != 0:
                    # if there is a push, perform a judge and rewrap the file to header

                    file_size = (sequence + len(payload) - self.connections[i][4]) if sequence >= self.connections[i][4] else (0xffffffff - self.connections[i][4] + sequence + len(payload))
                    
                    if file_size >= FILE_SIZE_JUDGE_THRESHOLD:
                        self.connections[i][5].truncate(file_size)
                        self.judge(self.connections[i][5])
                        
                        self.connections[i][4] = sequence + len(payload)

                if flags & TCP_FIN != 0:
                    # close the connection
                    
                    file_size = (sequence + len(payload) - self.connections[i][4]) if sequence >= self.connections[i][4] else (0xffffffff - self.connections[i][4] + sequence + len(payload))
                    if file_size > 0:
                        self.connections[i][5].truncate(file_size)
                        self.judge(self.connections[i][5])
                        
                    self.connections.remove(self.connections[i])

    def parse_pkt(self, data):
        offset = 0
        
        # parsing ethernet header
        if len(data) < offset + 14:
            return None

        L2_destination = data[offset + 0 : offset + 6]
        L2_source = data[offset + 6 : offset + 12]
        L2_type = data[offset + 12 : offset + 14]

        if L2_type == '\x08\x00':
            offset += 14
        else:
            return None

        # parsing ip header
        if len(data) < offset + 20:
            return None
        
        L3_version = (ord(data[offset]) & 0b11110000) >> 4
        L3_header_length = ord(data[offset]) & 0b1111
        (L3_total_length,) = struct.unpack(">H", data[offset + 2 : offset + 4])
        L3_identification = data[offset + 4 : offset + 6]
        L3_flags = data[offset + 6]
        L3_ttl = ord(data[offset + 8])
        L3_protocol = data[offset + 9]
        L3_source = data[offset + 12 : offset + 16]
        L3_destination = data[offset + 16 : offset + 20]

        if L3_version != 4 or L3_protocol != '\x06':
            return None

        offset += L3_header_length << 2

        # parsing tcp header
        if len(data) < offset + 20:
            return None

        (L4_src_port, L4_dest_port, L4_sequence, L4_acknowledgement, L4_header_length, L4_flags, L4_window_size) = struct.unpack(">HHIIBBH", data[offset + 0 : offset + 16])
        L4_header_length = L4_header_length >> 4

        offset += L4_header_length << 2

        # retrive and check payload
        if L3_total_length > 0:
            payload_length = L3_total_length - (L3_header_length << 2) - (L4_header_length << 2)
            try:
                payload = data[offset : offset + payload_length]
            except:
                print "malform pkt"
                return None
        else:
            # TCP segment offload
            payload = data[offset:]

        return (L3_source, L3_destination, L4_src_port, L4_dest_port, L4_sequence, L4_acknowledgement, L4_flags, payload)

    def http_parse(self, f):
        flag = False
        results = []

        f.seek(0, 2)
        file_size = f.tell()

        f.seek(0, 0)

        while True:
            data = f.read(65536)
            if len(data) < 16:
                break

            m = self.http_pattern.search(data)
            if m is None:
                f.seek(-15, 1)
                continue
            else:
                if m.start() != 0:
                    f.seek(f.tell() - len(data) + m.start())
                    continue
                
            header = data[:m.end()].strip()

            try:
                options_end = data.index("\x0d\x0a\x0d\x0a", m.end())
                options = data[m.end() : options_end].split("\x0d\x0a")
            except:
                f.seek(f.tell() - len(data) + m.end())
                continue

            results.append((header, options))

            f.seek(f.tell() - len(data) + options_end)
            flag = True

        if len(results) != 0:
            print results

        return flag

    def windows_pe(self, f):
        flag = False
        
        f.seek(0, 2)
        file_size = f.tell()

        f.seek(0, 0)

        while True:
            data = f.read(1024*1024*8)
            if len(data) < 2:
                break

            try:
                i = data.index("MZ")
                pe_start = f.tell() - len(data) + i
                pe_size = 0
            except:
                f.seek(-1, 1)
                continue

            f.seek(pe_start, 0)
            
            dos_header = f.read(64)
            if len(dos_header) != 64:
                f.seek(pe_start + 1, 0)
                continue
            else:
                pe_size = f.tell() - pe_start

            (nt_header_offset,) = struct.unpack("<I", dos_header[-4:])
            if pe_start + nt_header_offset >= file_size:
                f.seek(pe_start + 1, 0)
                continue

            f.seek(pe_start + nt_header_offset, 0)

            nt_header = f.read(24)
            if len(nt_header) != 24:
                f.seek(pe_start + 1, 0)
                continue
            else:
                pe_size = (f.tell() - pe_start) if (f.tell() - pe_start) > pe_size else pe_size

            if nt_header[:4] != '\x50\x45\x00\x00':
                f.seek(pe_start + 1, 0)
                continue

            (number_of_sections, _, _, _, sizeof_optional_header) = struct.unpack("<HIIIH", nt_header[6:22])

            optional_header = f.read(sizeof_optional_header)
            if len(optional_header) != sizeof_optional_header:
                f.seek(pe_start + 1, 0)
                continue
            else:
                pe_size = (f.tell() - pe_start) if (f.tell() - pe_start) > pe_size else pe_size

            if optional_header[:2] != '\x0b\x01' and optional_header[:2] != '\x0b\x02':
                f.seek(pe_start + 1, 0)
                continue

            sections_headers = f.read(number_of_sections * 0x28)
            if len(sections_headers) != number_of_sections * 0x28:
                f.seek(pe_start + 1, 0)
                continue
            else:
                pe_size = (f.tell() - pe_start) if (f.tell() - pe_start) > pe_size else pe_size

            i = 0
            while i < number_of_sections:
                (sizeof_rawdata, pointer_to_rawdata) = struct.unpack("<II", sections_headers[i * 0x28 + 16 : i * 0x28 + 24])
                if pointer_to_rawdata + sizeof_rawdata > file_size:
                    break

                pe_size = (pointer_to_rawdata + sizeof_rawdata) if (pointer_to_rawdata + sizeof_rawdata) > pe_size else pe_size
                i += 1

            if i < number_of_sections:
                f.seek(pe_start + 1, 0)
                continue

            print "!!! windows_pe found, start " + str(pe_start) + " size " + str(pe_size) + " streamsize " + str(file_size - pe_start)

            out = tempfile.mkstemp(dir = FILE_SAVE_PATH)
            
            f.seek(pe_start, 0)
            i = 0
            b = pe_size / (1024*1024*16)
            while i < b:
                out_data = f.read(1024*1024*16)
                os.write(out[0], out_data)
                i += 1

            remain = pe_size - (1024*1024*16*b)
            out_data = f.read(remain)
            os.write(out[0], out_data)

            os.close(out[0])

            print "file save to " + out[1]

            flag = True

        return flag

    def linux_elf(self, f):
        flag = False
        
        f.seek(0, 2)
        file_size = f.tell()

        f.seek(0, 0)

        while True:
            data = f.read(65536)
            if len(data) < 4:
                break

            try:
                i = data.index("\x7f\x45\x4c\x46")
                pe_start = f.tell() - len(data) + i
                pe_size = 0
            except:
                f.seek(-3, 1)
                continue

            f.seek(pe_start, 0)

            elf_ident = f.read(16)
            if len(elf_ident) != 16:
                f.seek(pe_start + 1, 0)
                continue
            else:
                pe_size = f.tell() - pe_start

            if (elf_ident[4] == '\x01' or elf_ident[4] == '\x02') and elf_ident[5] == '\x01':
                is_64 = elf_ident[4] == '\x02'
            else:
                f.seek(pe_start + 1, 0)
                continue

            elf_header = f.read(48 if is_64 == True else 36)
            if len(elf_header) != (48 if is_64 == True else 36):
                f.seek(pe_start + 1, 0)
                continue
            else:
                pe_size = (f.tell() - pe_start) if (f.tell() - pe_start) > pe_size else pe_size

            if is_64 == True:
                (e_type, _, e_version, _, e_phoff, e_shoff, _, e_ehsize, e_phentsize, e_phnum, e_shentsize, e_shnum) = \
                     struct.unpack("<HHIQQQIHHHHH", elf_header[:46])
            else:
                (e_type, _, e_version, _, e_phoff, e_shoff, _, e_ehsize, e_phentsize, e_phnum, e_shentsize, e_shnum) = \
                     struct.unpack("<HHIIIIIHHHHH", elf_header[:34])

            if e_type < 1 or e_type > 3 or e_version != 1 or (e_ehsize != 64 and e_ehsize != 52) or (e_phentsize != 32 and e_phentsize != 56) or (e_shentsize != 40 and e_shentsize != 64):
                f.seek(pe_start + 1, 0)
                continue

            if e_phoff != 0 and e_phnum != 0:
                if e_phoff + e_phentsize * e_phnum > file_size:
                    f.seek(pe_start + 1, 0)
                    continue

                f.seek(pe_start + e_phoff, 0)
                program_header = f.read(e_phentsize * e_phnum)
                pe_size = (f.tell() - pe_start) if (f.tell() - pe_start) > pe_size else pe_size
                
                i = 0
                while i < e_phnum:
                    if is_64 == True:
                        (ph_offset, _, _, ph_filesz) = struct.unpack("<QQQQ", program_header[i * e_phentsize + 8 : i * e_phentsize + 40])
                    else:
                        (ph_offset, _, _, ph_filesz) = struct.unpack("<IIII", program_header[i * e_phentsize + 4 : i * e_phentsize + 20])

                    if ph_offset + ph_filesz > file_size:
                        break

                    pe_size = (ph_offset + ph_filesz - pe_start) if (ph_offset + ph_filesz - pe_start) > pe_size else pe_size

                    i += 1

                if i < e_phnum:
                    f.seek(pe_start + 1, 0)
                    continue

            if e_shoff != 0 and e_shnum != 0:
                if e_shoff + e_shentsize * e_shnum > file_size:
                    f.seek(pe_start + 1, 0)
                    continue

                f.seek(pe_start + e_shoff, 0)
                section_header = f.read(e_shentsize * e_shnum)
                pe_size = (f.tell() - pe_start) if (f.tell() - pe_start) > pe_size else pe_size

                i = 0
                while i < e_shnum:
                    if is_64 == True:
                        (sh_type, _, _, sh_offset, sh_size) = struct.unpack("<IQQQQ", section_header[i * e_shentsize + 4 : i * e_shentsize + 40])
                    else:
                        (sh_type, _, _, sh_offset, sh_size) = struct.unpack("<IIIII", section_header[i * e_shentsize + 4 : i * e_shentsize + 24])

                    # sht_null and sht_nobits
                    if sh_type != 0 and sh_type != 8:
                        if sh_offset + sh_size > file_size:
                            break

                        pe_size = (sh_offset + sh_size - pe_start) if (sh_offset + sh_size - pe_start) > pe_size else pe_size

                    i += 1

                if i < e_shnum:
                    f.seek(pe_start + 1, 0)
                    continue

            print "!!! linux_elf found, start " + str(pe_start) + " size " + str(pe_size) + " streamsize " + str(file_size - pe_start)

            out = tempfile.mkstemp(dir = FILE_SAVE_PATH)
            
            f.seek(pe_start, 0)
            i = 0
            b = pe_size / (1024*1024*16)
            while i < b:
                out_data = f.read(1024*1024*16)
                os.write(out[0], out_data)
                i += 1

            remain = pe_size - (1024*1024*16*b)
            out_data = f.read(remain)
            os.write(out[0], out_data)

            os.close(out[0])

            print "file save to " + out[1]

            flag = True
            
        return flag
        
    def judge(self, f):
        return http_parse(f) or windows_pe(f) or linux_elf(f)