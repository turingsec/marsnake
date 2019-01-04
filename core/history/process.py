import socket
from ctypes import Structure, Union, c_char, c_int, c_uint, c_uint16, c_uint32, c_uint64, sizeof, cast, byref, POINTER

NLMSG_ALIGNTO = 4
NLMSG_DONE = 0x3

CONNECTOR_MAX_MSG_SIZE = 16384

NETLINK_CONNECTOR = 11
CN_IDX_PROC = 1
CN_VAL_PROC = 1

PROC_CN_MCAST_LISTEN = 1
PROC_CN_MCAST_IGNORE = 2

PROC_EVENT_NONE = 0x00000000
PROC_EVENT_FORK = 0x00000001
PROC_EVENT_EXEC = 0x00000002
PROC_EVENT_UID  = 0x00000004
PROC_EVENT_GID  = 0x00000040
PROC_EVENT_SID  = 0x00000080
PROC_EVENT_PTRACE = 0x00000100
PROC_EVENT_COMM = 0x00000200
PROC_EVENT_COREDUMP = 0x40000000
PROC_EVENT_EXIT = 0x80000000

def nlcn_msg_factory(type_of_data):
	class nlmsghdr(Structure):
		_fields_ = [
			("nlmsg_len", c_uint32),
			("nlmsg_type", c_uint16),
			("nlmsg_flags", c_uint16),
			("nlmsg_seq", c_uint32),
			("nlmsg_pid", c_uint32)
		]

	class cb_id(Structure):
		_fields_ = [
			("idx", c_uint32),
			("val", c_uint32)
		]

	class cn_msg(Structure):
		_fields_ = [
			("id", cb_id),
			("seq", c_uint32),
			("ack", c_uint32),
			("len", c_uint16),
			("flags", c_uint16),
			("data", type_of_data)
		]
		
	class nlcn_msg(Structure):
		_pack_ = NLMSG_ALIGNTO
		_fields_ = [
			("nl_hdr", nlmsghdr),
			("msg", cn_msg)
		]

	return nlcn_msg

class event_ack(Structure):
	_fields_ = [
		("err", c_uint32)
	]

class event_fork(Structure):
	_fields_ = [
		("parent_pid", c_int),
		("parent_tgid", c_int),
		("child_pid", c_int),
		("child_tgid", c_int)
	]

class event_exec(Structure):
	_fields_ = [
		("process_pid", c_int),
		("process_tgid", c_int)
	]

class event_id_r(Union):
	_fields_ = [
		("ruid", c_uint32),
		("rgid", c_uint32)
	]

class event_id_e(Union):
	_fields_ = [
		("euid", c_uint32),
		("egid", c_uint32)
	]

class event_id(Structure):
	_fields_ = [
		("process_pid", c_int),
		("process_tgid", c_int),
		("r", event_id_r),
		("e", event_id_e)
	]

class event_sid(Structure):
	_fields_ = [
		("process_pid", c_int),
		("process_tgid", c_int)
	]

class event_ptrace(Structure):
	_fields_ = [
		("process_pid", c_int),
		("process_tgid", c_int),
		("tracer_pid", c_int),
		("tracer_tgid", c_int)
	]

class event_comm(Structure):
	_fields_ = [
		("process_pid", c_int),
		("process_tgid", c_int),
		("comm", c_char * 16)
	]

class event_coredump(Structure):
	_fields_ = [
		("process_pid", c_int),
		("process_tgid", c_int),
		("parent_pid", c_int),
		("parent_tgid", c_int)
	]

class event_exit(Structure):
	_fields_ = [
		("process_pid", c_int),
		("process_tgid", c_int),
		("exit_code", c_uint32),
		("exit_signal", c_uint32),
		("parent_pid", c_int),
		("parent_tgid", c_int)
	]

class event_data(Union):
	_fields_ = [
		("ack", event_ack),
		("fork", event_fork),
		("exec", event_exec),
		("id", event_id),
		("sid", event_sid),
		("ptrace", event_ptrace),
		("comm", event_comm),
		("coredump", event_coredump),
		("exit", event_exit)
	]

class proc_event(Structure):
	_fields_ = [
		("what", c_uint),
		("cpu", c_uint32),
		("timestamp_ns", c_uint64),
		("event_data", event_data)
	]
	

class process():
	name = "process"

	def __init__(self):
		pass

	def init(self):
		try:
			self.nl_socket = socket.socket(socket.AF_NETLINK, socket.SOCK_DGRAM, NETLINK_CONNECTOR)
			self.nl_socket.bind((0, CN_IDX_PROC))
		except:
			return False

		proc_cn_msg = nlcn_msg_factory(c_int)()

		proc_cn_msg.nl_hdr.nlmsg_len = sizeof(proc_cn_msg)
		proc_cn_msg.nl_hdr.nlmsg_type = NLMSG_DONE
		proc_cn_msg.nl_hdr.nlmsg_flags = 0
		proc_cn_msg.nl_hdr.nlmsg_seq = 0
		proc_cn_msg.nl_hdr.nlmsg_pid = 0

		proc_cn_msg.msg.id.idx = CN_IDX_PROC
		proc_cn_msg.msg.id.val = CN_VAL_PROC
		proc_cn_msg.msg.seq = 0
		proc_cn_msg.msg.ack = 0
		proc_cn_msg.msg.len = sizeof(c_int)
		proc_cn_msg.msg.flags = 0
		proc_cn_msg.msg.data = PROC_CN_MCAST_LISTEN

		try:
			self.nl_socket.send(cast(byref(proc_cn_msg), POINTER(c_char * sizeof(proc_cn_msg))).contents.raw)
		except:
			return False

		return True

	def start(self):
		event_msg_t = nlcn_msg_factory(proc_event)

		while True:
			try:
				msgbuf = self.nl_socket.recv(CONNECTOR_MAX_MSG_SIZE)
				if len(msgbuf) == 0:
					break
			except:
				break

			event_msg = cast(msgbuf, POINTER(event_msg_t)).contents.msg.data

			if event_msg.what == PROC_EVENT_EXEC:
				try:
					with open("/proc/%d/comm" % (event_msg.event_data.exec.process_pid, ), "r") as f:
						comm = f.read()
					with open("/proc/%d/cmdline" % (event_msg.event_data.exec.process_pid, ), "r") as f:
						cmdline = f.read()
					with open("/proc/%d/stat" % (event_msg.event_data.exec.process_pid, ), "r") as f:
						stat = f.read()

					comm = comm.replace('\x00', ' ').strip()
					cmdline = cmdline.replace('\x00', ' ').strip()
					parent_pid = stat.split(' ', 4)[3]
				except:
					continue

				print("EXEC %s %d %s %s" % (parent_pid, event_msg.event_data.exec.process_pid, comm, cmdline))
