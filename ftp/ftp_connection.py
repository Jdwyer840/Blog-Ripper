import paramiko
from ftplib import FTP

class FTPInterface:
    def __init__(self, host: str, username: str, password: str, port: int = 21):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.ftp = FTP()

    def connect(self):
        self.ftp.connect(self.host, self.port)
        self.ftp.login(self.username, self.password)

    def upload(self, local_path: str, remote_path: str):
        with open(local_path, 'rb') as file:
            self.ftp.storbinary(f'STOR {remote_path}', file)

    def download(self, remote_path: str, local_path: str):
        with open(local_path, 'wb') as file:
            self.ftp.retrbinary(f'RETR {remote_path}', file.write)

    def list_files(self, path: str = ''):
        return self.ftp.nlst(path)

    def delete(self, remote_path: str):
        self.ftp.delete(remote_path)

    def close(self):
        self.ftp.quit()


class SFTPInterface:
    def __init__(self, host: str, username: str, password: str, port: int = 22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.client = None
        self.sftp = None

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.host, port=self.port, username=self.username, password=self.password)
        self.sftp = self.client.open_sftp()

    def upload(self, local_path: str, remote_path: str):
        self.sftp.put(local_path, remote_path)

    def download(self, remote_path: str, local_path: str):
        self.sftp.get(remote_path, local_path)

    def list_files(self, path: str = '.'):
        return self.sftp.listdir(path)

    def delete(self, remote_path: str):
        self.sftp.remove(remote_path)

    def close(self):
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()


class SSHFTPInterface:
    def __init__(self, host: str, username: str, password: str, port: int = 22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.client = None
        self.ftp = None

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.host, port=self.port, username=self.username, password=self.password)
        transport = self.client.get_transport()
        self.ftp = FTP()
        self.ftp.connect(self.host)
        self.client.connect(self.host, port=self.port, username=self.username, key_filename='/path/to/private/key')

        self.ftp.login(self.username, self.password)

    def upload(self, local_path: str, remote_path: str):
        with open(local_path, 'rb') as file:
            self.ftp.storbinary(f'STOR {remote_path}', file)

    def download(self, remote_path: str, local_path: str):
        with open(local_path, 'wb') as file:
            self.ftp.retrbinary(f'RETR {remote_path}', file.write)

    def list_files(self, path: str = ''):
        return self.ftp.nlst(path)

    def delete(self, remote_path: str):
        self.ftp.delete(remote_path)

    def close(self):
        if self.ftp:
            self.ftp.quit()
        if self.client:
            self.client.close()
