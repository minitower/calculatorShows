import openvpn_api.vpn
import os
import time


class OpenVPN:
    def __init__(self):
        """
        Class for init/reinit OVPN connection to the server
        """
        self.host = os.environ.get('HOST_OVPN')
        self.port = os.environ.get('PORT_OVPN')
        self.user = os.environ.get('USER_OVPN')
        self.passwd = os.environ.get('PASS_OVPN')

    def connect(self, check=True):
        """
        Func for connect to OVPN server
        """

        self.vpn = openvpn_api.vpn(self.host,
                                   self.port)
        self.vpn.connect()
        if check:
            status = self.vpn.state.desc_string
            if status == 'SUCCESS':
                return 0
            else:
                return 1
        return 2