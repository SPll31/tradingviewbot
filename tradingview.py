import os
import websockets
import uuid
import json
import re
from time import time


class TradingViewConnection:
    def __init__(self, symbol: str, timeframe: str):
        self._chart_session_key = self._generate_session_key("cs")
        self._symbol = symbol
        self._timeframe = timeframe

    @staticmethod
    def _generate_session_key(prefix):
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def _parse_websocket_message(message: str) -> list:
        segments = re.split(r'~m~\d+~m~', message)
        json_messages = []

        for segment in segments:
            if segment:
                json_data = json.loads(segment)
                json_messages.append(json_data)

        return json_messages

    @staticmethod
    def _timeframe_to_seconds(code):
        conversion = {
            "1": 60,          # 1 хвилина
            "3": 180,         # 3 хвилини
            "5": 300,         # 5 хвилин
            "15": 900,        # 15 хвилин
            "30": 1800,       # 30 хвилин
            "45": 2700,       # 45 хвилин
            "60": 3600,       # 1 година
            "120": 7200,      # 2 години
            "180": 10800,     # 3 години
            "240": 14400,     # 4 години
            "1D": 86400,      # 1 день
            "1W": 604800,     # 1 тиждень
            "1M": 2592000,    # 1 місяць (30 днів)
            "3M": 7776000,    # 3 місяці
            "6M": 15552000,   # 6 місяців
            "12M": 31536000   # 12 місяців
        }
        return conversion.get(code)

    @staticmethod
    def _build_message(json_msg):
        msg = json.dumps(json_msg, ensure_ascii=False, separators=(',', ':'))
        prefix = f"~m~{len(msg)}~m~"
        return prefix + msg

    def _prepare_messages(self):
        auth_token_message = self._build_message({
            "m": "set_auth_token",
            "p": [os.getenv("TR_VIEW_AUTH_TOKEN")]
        })

        chart_session_message = self._build_message({
            "m": "chart_create_session",
            "p": [self._chart_session_key, ""]
        })

        add_symbols_message = self._build_message({
                "m": "resolve_symbol",
                "p": [self._chart_session_key, "sds_sym_1",
                      f'={{"adjustment":"splits",'
                      f'"symbol":"{self._symbol}"}}']
        })

        create_series_message = self._build_message({
            "m": "create_series",
            "p": [self._chart_session_key, "sds_1", "s1", "sds_sym_1",
                  self._timeframe, 300, ""]
        })
        hueta_message = self._build_message({
            "m": "create_study",
            "p": [
                self._chart_session_key,
                "st7",
                "st1",
                "sds_1",
                "Script@tv-scripting-101!",
                {
                    "text": "bmI9Ks46_o2JPCHE64Wi9r2wKsxwHgg==_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",
                    "pineId": "PUB;b5decac5edce49b6b86bce93d4a3db0b",
                    "pineVersion": "1.0",
                    "pineFeatures": {
                        "v": '{\\"indicator\\":1,\\"plot\\":1,\\"array\\":1,\\"ta\\":1,\\"math\\":1,\\"alertcondition\\":1}',
                        "f": True,
                        "t": "text"
                    },
                    "in_0": {
                        "v": 8,
                        "f": True,
                        "t": "float"
                    },
                    "in_1": {
                        "v": 8,
                        "f": True,
                        "t": "float"
                    },
                    "in_2": {
                        "v": 25,
                        "f": True,
                        "t": "integer"
                    },
                    "in_3": {
                        "v": False,
                        "f": True,
                        "t": "bool"
                    },
                    "in_4": {
                        "v": 2,
                        "f": True,
                        "t": "integer"
                    },
                    "in_5": {
                        "v": 5,
                        "f": True,
                        "t": "integer"
                    },
                    "in_6": {
                        "v": 20,
                        "f": True,
                        "t": "integer"
                    },
                    "in_7": {
                        "v": 10,
                        "f": True,
                        "t": "integer"
                    },
                    "__profile": {
                        "v": False,
                        "f": True,
                        "t": "bool"
                    }
                }
            ]
        })

        return [
            auth_token_message,
            chart_session_message,
            add_symbols_message,
            create_series_message,
            hueta_message
        ]

    async def connect_and_send(self):
        headers = {
            "Host": "data.tradingview.com",
            "Connection": "Upgrade",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
            ),
            "Upgrade": "websocket",
            "Origin": "https://ru.tradingview.com",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ru"
        }
        ws_url = "wss://data.tradingview.com/socket.io/websocket?from=chart%2FyCgakbNi%2F&date=2024_12_25-14_03&type=chart"

        async with websockets.connect(
            ws_url, extra_headers=headers
        ) as websocket:
            self._websocket = websocket
            await websocket.recv()

            messages = self._prepare_messages()
            for message in messages:
                await websocket.send(message)
            await websocket.recv()

            try:
                prev_timestamp = {"timestamp": 0}
                last = 0
                while True:
                    data = await websocket.recv()

                    if "~~h" in data:
                        await websocket.send(data)
                        continue

                    parsed_data = self._parse_websocket_message(data)

                    print(parsed_data)
                    for msg in parsed_data:
                        if msg.get("m") == "du" and "st7" in msg["p"][1]:
                            values = msg["p"][1]["st7"]["st"][0]["v"]
                            short_v = values[-2]
                            long_v = values[-3]
                            close = values[-1]
                            if time() - prev_timestamp["timestamp"] < self._timeframe_to_seconds(self._timeframe):
                                continue
                            print(close)
                            if short_v == 300:
                                prev_timestamp["timestamp"] = time()
                                yield "Short", close
                            if long_v == 200:
                                prev_timestamp["timestamp"] = time()
                                yield "Long", close
            except Exception as e:
                print(e)

    async def end_connection(self):
        await self._websocket.close()
