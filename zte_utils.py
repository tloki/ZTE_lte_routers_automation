import base64
import time

import requests


def get_encoded_password(ascii_password: str) -> str:
    encoded_bytes = base64.b64encode(ascii_password.encode('utf-8'))
    # Convert the bytes back to a string
    encoded_string = encoded_bytes.decode('utf-8')

    return encoded_string

def check_get_zte_alive(host: str, port: int) -> bool:
    scheme = "http"
    path = "/goform/goform_set_cmd_process"

    # URL to which the request is to be sent
    url = f'{scheme}://{host}:{port}'
    response = requests.get(url)

    # Reading the response
    if response.status_code == 200:
        # print(response.text)
        return True
    else:
        print('Failed:', response.status_code, response.text)
        return False

def get_zte_login_cookie(host: str, port: int, password: str) -> dict[str, str]:
    scheme = "http"
    path = "/goform/goform_set_cmd_process"

    # URL to which the request is to be sent
    url = f'{scheme}://{host}:{port}{"/" if not path.startswith("/") else ""}{path}'

    # Data to be sent in the POST request
    data = {
        "isTest": "false",
        "goformId": "LOGIN",
        "password": get_encoded_password(password),
    }

    headers = {
        "Host": host,
        "Referer": f"http://{host}/index.html",
    }

    response = requests.post(url=url, data=data, headers=headers)

    if response.status_code == 200:
        response_json = response.json()
        assert "result" in response_json
        assert response_json["result"] == "0"
        response_cookies = response.cookies
        response_cookie_items = response_cookies.items()
        assert len(response_cookie_items) == 1
        response_cookie_item = response_cookie_items[0]
        assert response_cookie_item[0] == "zwsd"

        cookie_value = response_cookie_item[1]
        if cookie_value.startswith('"') and cookie_value.endswith('"'):
            cookie_value = cookie_value[1:-1]
        else:
            raise ValueError("unexpected cookie")

        return dict([("zwsd", cookie_value)])
    else:
        print('Failed:', response.status_code, response.text)
        raise RuntimeError()

def get_raw_sms_list(host: str, port: int, cookie: dict[str, str]) -> bytes:
    scheme = "http"

    unix_time_now = int(round(time.time() * 1000))

    path = (
        "/goform/goform_get_cmd_process?"
            "isTest=false&"
            "cmd=sms_data_total&"
            "page=0&"
            "data_per_page=500&"
            "mem_store=1&"
            "tags=10&"
            "order_by=order+by+id+desc&"
            f"_={unix_time_now}"
    )
    headers = {
        "Host": host,
        "User-Agent": 'Mozilla/5.0 Gecko/20100101 Firefox/131.0',
        "Accept": 'application/json, text/javascript, */*; q=0.01',
        "Accept-Language": 'en-US,en;q=0.5',
        "Accept-Encoding": 'gzip, deflate',
        "X-Requested-With": 'XMLHttpRequest',
        "Connection": 'keep-alive',
        "Referer": f'{scheme}://{host}/index.html',
        "Cookie": f'zwsd="{cookie["zwsd"]}"',
    }

    # URL to which the request is to be sent.
    url = f'{scheme}://{host}:{port}{"/" if not path.startswith("/") else ""}{path}'

    response = requests.get(url=url, headers=headers)

    assert response.status_code == 200
    response_content = response.content

    return response_content

def make_ascii_safe(input_bytes: bytes) -> str:
    output = ""
    for i, letter in enumerate(input_bytes):

        if letter in range(32, 126 + 1): # only ascii characters, nothing else please here!
            output += chr(letter)
        else:
            # print(f"{i:6d}. char id: '{letter}', byte(s): '{input_bytes[i:i+1]}', would translate to: '{chr(letter)}'")
            output += "?"
    return output

def decode_hex_sms_content_groups_of_4(hex_content_str: str) -> str:
    assert len(hex_content_str) % 4 == 0

    content_grouped = [hex_content_str[4 * i:4 * (i + 1)] for i in range(len(hex_content_str) // 4)]

    content_grouped_str_ascii = [chr(int("0x" + e.lower(), base=16)) for e in content_grouped]

    return "".join(content_grouped_str_ascii)



def create_scp_client(server: str, port: int, user: str):
    import paramiko
    from scp import SCPClient

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(hostname=server, port=port, username=user)

    scp = SCPClient(client.get_transport())
    return scp

