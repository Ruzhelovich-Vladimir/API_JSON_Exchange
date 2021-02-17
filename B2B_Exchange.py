import http.client
from http.client import responses
import requests
import json
import os
import logging

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

REQUEST_PLAN = os.path.join(ROOT_DIR, ".conf", "request_plan.json")
LOG_FILE = os.path.join(ROOT_DIR, "api.log")


class JsonFile:

    __slots__ = ('file_pathname')

    def __init__(self, file_pathname):

        self.file_pathname = file_pathname

    @property
    def get_json_data(self):

        with open(self.file_pathname, "r", encoding='utf-8') as read_file:
            data = json.load(read_file)

        return data


class Api:

    _slots__ = (
        'conn', 'headers', 'supplier_data', 'request_plan_data', 'login', 'password', 'supplierId', 'outbox_path', 'current_token', 'protocol', 'server', 'login'
    )

    def __init__(self, supplier_filepath, ):

        self.supplier_data = JsonFile(supplier_filepath).get_json_data
        self.request_plan_data = JsonFile(REQUEST_PLAN).get_json_data

        self.protocol = self.request_plan_data["protocol"]
        self.catalog = self.request_plan_data["catalog"]
        self.server = self.request_plan_data["server"]
        self.conn = http.client.HTTPSConnection(self.server)

        self.login = self.supplier_data["login"]
        self.password = self.supplier_data["password"]
        self.supplierId = self.supplier_data["supplierId"]
        self.post_path = os.path.join(
            ROOT_DIR, self.supplier_data["post_path"])
        self.get_path = os.path.join(ROOT_DIR, self.supplier_data["get_path"])

        self.headers = {'accept': 'application/json',
                        'Content-type': 'application/json'}

        res, self.current_token = self.__token
        self.current_token = self.current_token[1:-1] if res == True else None

        self.headers["Authorization"] = f"Bearer {self.current_token}"

    @property
    def __token(self):
        r = {'login': self.login, 'password': self.password,
             "supplierId": self.supplierId}
        json_date = json.dumps(r)
        res, result = self.responce(
            self.request_plan_data["login"]["type"],
            f'{self.catalog}{self.request_plan_data["login"]["method"]}',
            "data", json_date)
        return res, result

    def responce(self, type_method, method, successful_execution, json_data={}, filename=''):

        method = method.replace('$supplierId$', f'{self.supplierId}')
        try:
            self.conn.request(type_method, method, json_data, self.headers)
            res = self.conn.getresponse()
            text_result = res.read().decode('utf-8')
        except Exception as err:
            logging.error(f'{method}: {err}')
            return False

        result = True if (successful_execution == text_result or successful_execution ==
                          "data") and res.status == 200 else False

        tt = "\n" if len(text_result) > 20 else ""
        msg = f'{type_method} {method.replace(self.catalog,"")} {str(res.status)}: {res.reason} {filename} {tt} {text_result}'

        if result:
            logging.info(msg)
        else:
            logging.error(msg)
            text_result = ""

        return result, text_result

    def send_file_responce(self, type_method, method, successful_execution, media_path):

        method = method.replace('$supplierId$', f'{self.supplierId}')
        _method = f'{self.protocol}://{self.server}/{method}'
        payload = {}
        files = [('uploadedFile', open(media_path, 'rb'))]
        headers = {'Authorization': f'Bearer {self.current_token}'}

        try:
            res = requests.request(type_method, _method,
                                   headers=headers, data=payload, files=files)
            text_result = res.content.decode('utf-8')
        except Exception as err:
            logging.error(f'{method}: {err}')
            return False

        result = True if '{"failed":{}}' == text_result or successful_execution == "date" and res.status_code == 200 else False

        tt = '\n' if len(text_result) > 20 else ''
        msg = f'{method.replace(self.catalog,"")} {str(res.status_code)}: {res.reason} {media_path} {tt} {text_result}'

        if result:
            logging.info(msg)
        else:
            logging.error(msg)
            text_result = ''

        return result, text_result

    @staticmethod
    def get_file_list(filename, path, ext, postfix='_'):
        # get filename without extention
        file_name = (filename.split('.'))[0] + postfix
        files_list = [os.path.join(path, f) for f in os.listdir(path) if f[0:len(
            file_name)] == file_name and f.endswith(f'.{ext}')]
        return files_list

    def run_request(self, request):

        if self.current_token is None:
            return

        res = []
        method_path = self.post_path if request["type"] == "POST" else self.get_path

        if "media_path" in request:
            zip_list = self.get_file_list(
                filename=request["media_path"], path=method_path, ext='zip')
            if len(zip_list) == 0:
                logging.warning(
                    f'{request["type"]} {request["method"]} - skip')
            for _file_name in zip_list:
                self.send_file_responce(request["type"], f'{self.catalog}{request["method"]}',
                                        request["successful_execution"], _file_name)
        elif request["type"] == "POST" and "json_data_path" in request:
            json_list = self.get_file_list(
                filename=request["json_data_path"], path=method_path, ext='json')
            if len(json_list) == 0:
                logging.warning(
                    f'{request["type"]} {request["method"]} - skip')

            for _file_name in json_list:
                with open(_file_name, "r", encoding='utf-8') as read_file:
                    try:
                        data = json.dumps(json.load(read_file))
                    except Exception as err:
                        logging.error(
                            f'Error of json format: {os.path.join(method_path, request["json_data_path"])} - {err.msg}: {err.doc}')
                        continue
                self.responce(
                    request["type"], f'{self.catalog}{request["method"]}', request["successful_execution"], data, _file_name)
        elif request["type"] == "GET" and "json_data_path" in request:
            res, result = False, []
            with open(os.path.join(os.getcwd(), method_path, request["json_data_path"]), "w", encoding='utf-8') as file:
                try:
                    res, result = self.responce(
                        request["type"], f'{self.catalog}{request["method"]}', request["successful_execution"])
                    if res:
                        file.write(result)
                    else:
                        logging.error(f'{request["method"]} : {result}')
                except Exception as err:
                    logging.error(f'{request["method"]} : {err}')

            return res, result

    @ property
    def run_requests_all(self):

        for request in self.request_plan_data["plan"]:
            self.run_request(request)


if __name__ == "__main__":

    # logging.basicConfig(
    #     format=u'[%(asctime)s] %(levelname)-8s %(message)s', level=logging.INFO)
    logging.basicConfig(
        format=u'%(levelname)-8s [%(asctime)s] %(message)s', level=logging.DEBUG, filename=LOG_FILE)
    Api(os.path.join(os.getcwd(), ".conf", "supplier.json")).run_requests_all
