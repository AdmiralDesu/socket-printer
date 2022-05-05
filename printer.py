import json
import socket
import threading
import time

FORMAT = 'utf-8'


class Printer:

    def __init__(self):
        self.host_ip: str = '127.0.0.1'
        self.port: int = 8000
        self.list_of_text = list()

        self.status_request: str = '^0?RS'
        self.mailing_request: str = '0?SM'
        self.start_print_request: str = '^!GO'
        self.mailing_record_request: str = '^0=MR'
        self.nozzle: int = 2
        self.ready_to_print: int = 5
        self.errors: int = 0
        self.head_cover: int = 0
        self.speed: int = 9
        self.changes: int = 1
        self.max_records: int = 256
        self.buffer: int = 0
        self.last_printed: int = 0
        self.stop_record: int = 0
        self.print_go: int = 1

    def get_status_string(self, kind_of_status: str) -> str:

        status_string = str()

        if kind_of_status == self.status_request:
            status_string = f'^0RS{self.nozzle} ' \
                            f'{self.ready_to_print} ' \
                            f'{self.errors} ' \
                            f'{self.head_cover} ' \
                            f'{self.speed} ' \
                            f'{self.changes}'

        elif kind_of_status == self.mailing_request:
            status_string = f'^0=SM{self.max_records} ' \
                           f'{self.buffer} ' \
                           f'{self.last_printed} ' \
                           f'{self.stop_record} ' \
                           f'{self.print_go}'

        if status_string:
            return status_string
        else:
            print('Статус не отправлен')
            raise KeyError

    def print_text(self) -> None:
        while self.buffer != 0:
            print(f'Текст {self.list_of_text.pop(0)} напечатан')
            print(f'{self.buffer=}')
            self.buffer -= 1
            self.last_printed += 1
            self.print_go += 1
            time.sleep(0.5)

        self.last_printed = 0
        print('Печать окончена')

    def start(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((self.host_ip, self.port))
            while True:
                data = client_socket.recv(4096).decode(FORMAT)
                print(f'{data=}')
                if not data:
                    break
                data = json.loads(data)

                if self.status_request in data.keys():
                    status_string = self.get_status_string(self.status_request)
                    client_socket.sendall(status_string.encode(FORMAT))
                elif self.mailing_request in data.keys():
                    status_string = self.get_status_string(self.mailing_request)
                    client_socket.sendall(status_string.encode(FORMAT))
                elif 'parameter' in data.keys():
                    parameter = data['parameter']
                    self.stop_record = parameter[parameter.find('M') + 1:]
                elif self.mailing_record_request in data.keys():
                    item = data[self.mailing_record_request]
                    self.list_of_text.append(item[item.find(' ')+1:])
                    self.buffer = len(self.list_of_text)
                # elif 'part' in data.keys():
                #     part = eval(data['part'])
                #     self.list_of_text = self.list_of_text + part
                #     self.buffer += len(part)
                elif self.start_print_request in data.keys():
                    threading.Thread(target=self.print_text).start()
                    print('Печать включена')

            print('Все данные приняты')


if __name__ == '__main__':
    printer = Printer()
    printer.start()


