import paramiko


class UGConnection:
    """ SSH connection for communication between the client and the remote server
    >>> # DONE_TODO: remove credentials before commit
    >>> HOSTNAME = ""
    >>> USERNAME = ""
    >>> PASSWD = ""
    >>> KEY_FILENAME = "../profile/id_rsa"
    >>> # supply only passwd
    >>> conn = UGConnection()
    >>> conn.connect(HOSTNAME, USERNAME, passwd=PASSWD)
    >>> _, stdout, _ = conn.exec_command("ls")
    >>> for line in stdout:
    ...     print(line) # doctest: +ELLIPSIS
    total...
    >>> # reuse conn
    >>> conn.connect(HOSTNAME, USERNAME, passwd=PASSWD) # doctest: +ELLIPSIS
    Connection already established on ...
    >>> # save keys
    >>> import os
    >>> from os import path
    >>> if path.isfile(KEY_FILENAME):
    ...     os.remove(KEY_FILENAME)
    >>> conn.save_keys(KEY_FILENAME)
    >>> path.isfile(KEY_FILENAME)
    True
    >>> # disconnect conn
    >>> conn.disconnect()
    >>> # supply invalid credentials
    >>> try:
    ...     conn.connect(HOSTNAME, USERNAME, passwd="1234")
    ... except paramiko.ssh_exception.AuthenticationException as e:
    ...     print(e)
    Authentication failed.
    >>> # supply invalid hostname
    >>> import socket
    >>> try:
    ...     conn.connect("invalid_host", USERNAME, PASSWD)
    ... except socket.gaierror as e:
    ...     print(e)
    [Errno 8] nodename nor servname provided, or not known
    >>> # supply key_filename
    >>> conn.connect(HOSTNAME, USERNAME, key_filename=KEY_FILENAME)
    >>> _, stdout, _ = conn.exec_command("ls")
    >>> for line in stdout: # doctest: +ELLIPSIS
    ...     print(line)
    total...
    """

    def __init__(self):
        self.connected = False

        self.hostname = None
        self.username = None

        self.client = paramiko.SSHClient()
        # TODO: should prompt the user to confirm the host key if missing
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self, hostname, username, passwd=None, key_filename=None):
        """ Connect to the remote server

        :param hostname: remote server host name
        :param username: user name on the remote server
        :param passwd: password for user authentication
        :param key_filename: (unused if passwd is not None) private RSA key for user authentication
        :return: None
        """
        # if the client is already connected, we should attempt to reuse the connection
        if self.connected:
            if hostname == self.hostname and username == self.username:
                # the hostname and username match what we have right now
                # reuse the connection
                print("Connection already established on %s@%s" % (username, hostname))
                return
            else:
                # the hostname and username don't match what we have right now
                print("Hostname or credential mismatch. Disconnect that connection. ")

        # if the client is not connected or can't be reused
        self.disconnect()
        try:
            # assume connect() is called correctly (only passwd or key_filename is supplied):
            #   1) if passwd is not None, use password to login
            #   2) if passwd is None and key_filename is not None, use key to login
            #   3) if passwd is None and key_filename is None, raise an invalid-argument exception
            if passwd is not None:
                # try connecting to the host
                self.client.connect(hostname,
                                    username=username,
                                    password=passwd)
            elif key_filename is not None:
                self.client.connect(hostname,
                                    username=username,
                                    key_filename=key_filename)
            else:
                raise ValueError("Invalid arguments: Both passwd and key_filename are None. ")
            # save the hostname and username
            #  for checking whether the connection can be reused
            self.hostname = hostname
            self.username = username
            self.connected = True
        except Exception as e:
            # common exceptions include
            #   1) Authentication Error
            #       paramiko.ssh_exception.AuthenticationException: Authentication failed.
            #   2) Hostname Error
            #       socket.gaierror: [Errno 8] nodename nor servname provided, or not known
            raise e

    def disconnect(self):
        """ Disconnect the SSH client "client"

        :return: None
        """
        self.client.close()

        self.hostname = None
        self.username = None
        self.connected = False

    @staticmethod
    def ssh_keygen(key_filename):
        """ Generate and save an RSA SSH private key on the local machine, return a public key

        :param key_filename: path to where the private key should be saved
        :return: passphrase of the public key
        """
        # 2048 is the default size of RSA keys
        rsa_key = paramiko.RSAKey.generate(2048)

        # save the private key
        rsa_key.write_private_key_file(key_filename)

        # get the username and hostname for saving those on the remote server
        import getpass
        import socket
        os_username = getpass.getuser()
        os_hostname = socket.gethostname()

        # ssh-rsa: key type
        # rsa_key.get_base64(): key phrase
        # os_username + "@" + os_hostname: for identification on the remote server
        return "ssh-rsa " + rsa_key.get_base64() + " " + os_username + "@" + os_hostname

    def save_keys(self, key_filename):
        """ Generate an RSA SSH key. Save the private key on the local machine, and save the public one on the remote.

        :param key_filename: path to where the private key should be saved
        :return: None
        """
        if not self.connected:
            raise PermissionError("Misuse: Client not connected.")

        # generate and save the private key on the local machine
        pub_key = UGConnection.ssh_keygen(key_filename)
        # save the public key onto the remote server
        exit_status, _, _, _ = self.exec_command_blocking(
            "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '%s' >>  ~/.ssh/authorized_keys" % pub_key)
        if exit_status != 0:
            raise SystemError("Not able to save pub key on the remote, exit_status=%d" % exit_status)

    def exec_command(self, command):
        """ Execute some command on the remote and return the outputs.
        NOTE: This function is non-blocking. If blocking is required, call recv_exit_status() on the channel. e.g.
            stdout.channel.recv_exit_status()

        :param command: command to be executed
        :return: stdin, stdout, stderr of the executed command
        """
        return self.client.exec_command(command)

    def exec_command_blocking(self, command):
        """ Execute some command on the remote and return the exit_status and the outputs of the execution.
        NOTE: This function is blocking.

        :param command: command to be executed
        :return: exit_status, stdin, stdout, stderr of the executed command
        """
        stdin, stdout, stderr = self.client.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()

        return exit_status, stdin, stdout, stderr
