'''
from scapy.all import sniff, UDP, TCP

# simply use scapy to capture and parse dns

def pkt_callback(pkt):
    pkt[DNS].show()
    #print "src %s, src_ip %s" % (pkt[DNS].hwsrc, pkt[ARP].psrc)
    
sniff(prn = pkt_callback, store = 0, filter = "udp port 53 or tcp port 53")
'''

import pcapy
import struct

class udp_traffic():
    def __init__(self, dns_captured_cb):
        self.name = "UDP traffic"
        
        self.dns_captured_cb = dns_captured_cb
        
    def init(self):
        try:
            self.device = pcapy.open_live(pcapy.lookupdev(), 65535, 0, 0)
            self.device.setfilter("udp port 53")
        except Exception as e:
            print(e)
            return False
            
        return True
        
    def do(self):
        while True:
            try:
                src_ip, dst_ip, src_port, dst_port, data = self.get_udp(self.device.next()[1])
                result = self.dns_parse(data)

                if not result is None:
                    print str(int(src_port.encode("hex"),16)) + " " + str(int(dst_port.encode("hex"),16))
                    print result
            except:
                continue

    def get_name(self, data, start_offset):
        offset = start_offset
        name = ''
        
        i = 0
        try:
            while True:
                if (ord(data[offset]) >> 6) == 0b11:
                    (tmp_offset,) = struct.unpack(">H", data[offset : offset + 2])
                    tmp_offset &= 0x3fff
                    _, tmp_name = self.get_name(data, tmp_offset)
                    name += tmp_name
                    offset += 2
                    break
                elif data[offset] == '\x00':
                    offset += 1
                    break
                else:
                    j = ord(data[offset])
                    offset += 1
                    name += (data[offset : offset + j] + ".")
                    offset += j
        except:
            return None

        if name[-1] == '.':
            name = name[:-1]
        return (offset, name)

    def dns_parse(self, data):
        result = {}

        if len(data) < 12:
            return None

        (hdr_id, hdr_flags, hdr_questions, hdr_AnswerRR, hdr_AuthorityRR, hdr_AdditionalRR) = struct.unpack(">HHHHHH", data[:12])

        result['is_response'] = (hdr_flags >> 15 == 1)
        result['opcode'] = (hdr_flags >> 11) & 0b1111
        result['questions'] = hdr_questions
        result['answer_rrs'] = hdr_AnswerRR
        result['authority_rrs'] = hdr_AuthorityRR
        result['additional_rrs'] = hdr_AdditionalRR

        offset = 12

        querys = []
        i = 0
        while i < hdr_questions:
            try:
                offset, query_name = self.get_name(data, offset)
                (query_type, query_class) = struct.unpack(">HH", data[offset : offset + 4])
                offset += 4
            except:
                return None

            querys.append({"name":query_name, "type":query_type, "class":query_class})
            i += 1

        answers = []
        i = 0
        while i < hdr_AnswerRR:
            try:
                offset, answer_name = self.get_name(data, offset)
                (answer_type, answer_class, answer_ttl, answer_length) = struct.unpack(">HHIH", data[offset : offset + 10])
                offset += 10

                answer_data = data[offset : offset + answer_length]
            except:
                return None

            answers.append({"name":answer_name, "type":answer_type, "class":answer_class, "ttl":answer_ttl, "data":answer_data})
            i += 1

        authorities = []
        i = 0
        while i < hdr_AuthorityRR:
            try:
                offset, authority_name = self.get_name(data, offset)
                (authority_type, authority_class, authority_ttl, authority_length) = struct.unpack(">HHIH", data[offset : offset + 10])
                offset += 10

                authority_data = data[offset : offset + authority_length]
            except:
                return None

            authorities.append({"name":authority_name, "type":authority_type, "authority_class":authority_class, "authority_ttl":authority_ttl, "authority_data":authority_data})
            i += 1

        result['querys'] = querys
        result['answers'] = answers
        result['authorities'] = authorities

        return result

    def get_udp(self, data):
        if len(data) < 14:
            return None

        offset = 0

        # if ipv4
        if data[offset + 12 : offset + 14] == '\x08\x00':
            offset += 14
        # if pppoe
        elif data[offset + 12 : offset + 14] == '\x88\x64':
            offset += (14 + 6 + 2)
        else:
            return None

        if len(data) < offset + 20:
            return None

        # ip version
        if ((ord(data[offset + 0]) >> 4) & 0xf) != 4:
            return None

        header_len = (ord(data[offset + 0]) & 0xf) << 2
        protocol = ord(data[offset + 9])
        sequence = data[offset + 4 : offset + 6]
        src_ip = data[offset + 12 : offset + 16]
        dst_ip = data[offset + 16 : offset + 20]

        # is udp?
        if protocol != 0x11:
            return None

        offset += header_len

        if len(data) < offset + 8:
            return None

        src_port = data[offset + 0 : offset + 2]
        dst_port = data[offset + 2 : offset + 4]

        offset += 8;

        return (src_ip, dst_ip, src_port, dst_port, data[offset:])
