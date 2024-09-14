#!/usr/bin/env python3
import shutil
import time
from pathlib import Path
from pprint import pprint
import json
from zte_utils import check_get_zte_alive, get_zte_login_cookie, get_raw_sms_list, make_ascii_safe, \
    decode_hex_sms_content_groups_of_4, create_scp_client

config = json.load(open("config.json"))

TMP_DIR = "/tmp"
HOST = config["HOST"]
PORT = config.get("PORT", 80)
WEB_UI_PASSWORD = config["WEB_UI_PASSWORD"]
COOKIE = config.get("COOKIE", None)
MSG_STORE_DIRECTORY = config.get("MSG_STORE_DIRECTORY", None)

TRANSFER_TO_HOST = config.get("TRANSFER_TO_HOST", None)
TRANSFER_TO_PORT = config.get("TRANSFER_TO_PORT", None)
TRANSFER_TO_USER = config.get("TRANSFER_TO_USER", None)
TRANSFER_TO_PATH = config.get("TRANSFER_TO_PATH", None)

SMS_CHECK_PERIOD_SECONDS = config.get("SMS_CHECK_PERIOD_SECONDS", 3600)


while True:
    assert check_get_zte_alive(host=HOST, port=PORT)
    if COOKIE is None:
        fetched_cookie = get_zte_login_cookie(host=HOST, port=PORT, password=WEB_UI_PASSWORD)
    else:
        # print("using cookie:", COOKIE)
        fetched_cookie = COOKIE

    # print("got a cookie:", fetched_cookie)

    result_sms_raw = get_raw_sms_list(host=HOST, port=PORT, cookie=fetched_cookie)
    result_sms_string_ascii = make_ascii_safe(input_bytes=result_sms_raw)
    result_sms_json = json.loads(s=result_sms_string_ascii)

    # pprint(result_sms_json)

    for message_data in result_sms_json["messages"]:
        content = message_data["content"]
        content_str = decode_hex_sms_content_groups_of_4(hex_content_str=content)
        message_data["content"] = content_str

    # pprint(result_sms_json)

    # store messages to directory
    if isinstance(MSG_STORE_DIRECTORY, str):
        msg_store_path = Path(__file__).parent.joinpath(MSG_STORE_DIRECTORY)
        assert not msg_store_path.is_file()
        if msg_store_path.exists():
            assert msg_store_path.is_dir()
        msg_store_path.mkdir(exist_ok=True, parents=True)
        # print(f"storing Messages to {msg_store_path}")
    else:
        print("not storing messages")
        exit(0)

    new_sms = 0
    for message_data in result_sms_json["messages"]:
        sms_id = message_data["id"]

        this_sms_path = msg_store_path / (sms_id + ".json")
        this_sms_tmp_path = Path(TMP_DIR) / (sms_id + ".json")

        if not this_sms_path.exists():
            print(f"got a new message with id {sms_id}!")
            with this_sms_tmp_path.open(mode="w") as f:
                json.dump(obj=message_data, fp=f)

            if TRANSFER_TO_PATH is not None and TRANSFER_TO_PORT is not None and TRANSFER_TO_HOST is not None and TRANSFER_TO_USER is not None:
                scp_client = create_scp_client(server=TRANSFER_TO_HOST, port=TRANSFER_TO_PORT, user=TRANSFER_TO_USER)
                scp_client.put(files=str(this_sms_tmp_path), remote_path=TRANSFER_TO_PATH + "/" + this_sms_path.name, recursive=True)
                scp_client.close()

            shutil.copy(src=this_sms_tmp_path, dst=this_sms_path, follow_symlinks=True)
            new_sms += 1

    if new_sms > 0:
        print(f"received and wrote {new_sms} new messages")
    else:
        print("no new messages")

    print(f"sleeping for {SMS_CHECK_PERIOD_SECONDS}")
    time.sleep(SMS_CHECK_PERIOD_SECONDS)

