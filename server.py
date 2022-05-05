import socket
import time
import json

FORMAT = 'utf-8'


class Server:

    def __init__(self, list_of_records):
        self.status_request: str = '^0?RS'
        self.mailing_request: str = '0?SM'
        self.start_print_request: str = '^!GO'
        self.mailing_record_request: str = '^0=MR'
        self.records = list()
        self.host_ip: str = '127.0.0.1'
        self.port: int = 8000
        self.printer_status = str()
        self.max_record = str()
        self.buffer = str()

        self.list_of_records: list = list_of_records

    def send_parameters(self, _socket: socket.socket) -> None:

        parameter = len(self.list_of_records)
        request = json.dumps({'parameter': f'^0=CM{parameter}'})
        _socket.send(request.encode(FORMAT))

    def acknowledge_status(self, status_of_printer: str, kind_of_status: str) -> None:

        list_of_statuses = list(status_of_printer.split(' '))

        if kind_of_status == self.status_request:
            print(f'{list_of_statuses=}')
            self.printer_status = list_of_statuses[1]

        elif kind_of_status == self.mailing_request:
            print(f'{list_of_statuses=}')
            m_index = list_of_statuses[0].find('M')
            self.max_record = list_of_statuses[0][m_index:]
            self.buffer = list_of_statuses[1]

        print(f'{list_of_statuses=}')

    def send_part(self, _socket: socket.socket) -> None:
        try:
            part = self.list_of_records[0:50]
            for index, item in enumerate(part):
                request = json.dumps(
                    {f'{self.mailing_record_request}':
                         f'{self.mailing_record_request}{index + 1} {item}'}
                )
                _socket.send(request.encode(FORMAT))
                time.sleep(0.1)
            self.list_of_records = self.list_of_records[50:]
            print(f'{len(self.list_of_records)}')
        except IndexError:
            for index, item in enumerate(self.list_of_records):
                request = json.dumps(
                    {f'{self.mailing_record_request}':
                         f'{self.mailing_record_request}{index + 1} {item}'}
                )
                _socket.send(request.encode(FORMAT))
                time.sleep(0.1)
            self.list_of_records.clear()

    def status_check(self, _socket: socket.socket, kind_of_status: str) -> None:

        request = json.dumps({kind_of_status: kind_of_status})

        _socket.send(request.encode(FORMAT))
        status_of_printer = _socket.recv(1024).decode(FORMAT)
        self.acknowledge_status(status_of_printer, kind_of_status)

    def send_first_set(self, _socket: socket.socket) -> None:
        print('Отправляю первую часть данных')

        for index, item in enumerate(self.list_of_records[0:255]):
            request = json.dumps(
                {f'{self.mailing_record_request}':
                     f'{self.mailing_record_request}{index + 1} {item}'}
            )
            _socket.send(request.encode(FORMAT))
            time.sleep(0.5)

        self.list_of_records = self.list_of_records[255:]

    def send_start(self, _socket: socket.socket) -> None:
        print('Отправляю запрос на начало печати')

        request = json.dumps({self.start_print_request: self.start_print_request})

        _socket.send(request.encode(FORMAT))

    def start(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host_ip, self.port))
            server_socket.listen()
            connection, address = server_socket.accept()
            with connection:
                print(f"Соединился с {address}")

                self.status_check(connection, self.status_request)
                if self.printer_status == '5':
                    self.status_check(connection, self.mailing_request)
                    self.send_parameters(connection)
                    print('Параметр отправлен')
                else:
                    raise KeyError

                self.status_check(connection, self.status_request)

                self.send_first_set(connection)
                self.status_check(connection, self.mailing_request)
                print(f'{self.buffer=}')

                self.send_start(connection)
                while self.list_of_records:
                    self.status_check(connection, self.mailing_request)
                    self.status_check(connection, self.status_request)

                    if 255 - int(self.buffer) >= 50:
                        self.send_part(connection)
                    time.sleep(1)

                print('Все данные отправлены')


if __name__ == '__main__':
    list_of_texts = [str(i) for i in range(1, 401)]
    server = Server(list_of_texts)
    server.start()
