import json, config
import math
from flask import Flask, request, jsonify, render_template
# from binance.client import Client
# from binance.enums import *
import logging
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError

app = Flask(__name__)

um_futures_client = UMFutures(config.API_KEY, config.API_SECRET)

accBalance = 0


def getBalance():
    # get_account
    try:
        response = um_futures_client.account(recvWindow=6000)
        logging.info(response)
        # print(response)

        global accBalance
        accBalance = response['availableBalance']
        accBalance = round(float(accBalance), 0)-1
        # print("accBalance= ", accBalance)

    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )


getBalance()


# def changeLeverangeMode():
#     try:
#         response = um_futures_client.change_margin_type(
#             symbol="BTCUSDT", marginType="ISOLATED", recvWindow=6000
#         )
#         logging.info(response)
#         # print(response)
#     except ClientError as error:
#         logging.error(
#             "Found error. status: {}, error code: {}, error message: {}".format(
#                 error.status_code, error.error_code, error.error_message
#             )
#         )


# changeLeverangeMode()


# def changeLeverange(x=10):
#     try:
#         response = um_futures_client.change_leverage(
#             symbol="ETHUSDT", leverage=x, recvWindow=6000
#         )
#         logging.info(response)
#         # print(response)
#     except ClientError as error:
#         logging.error(
#             "Found error. status: {}, error code: {}, error message: {}".format(
#                 error.status_code, error.error_code, error.error_message
#             )
#         )

# changeLeverange(10)
def cancelOrder():
    try:
        response = um_futures_client.cancel_open_orders(symbol="ETHUSDT", recvWindow=2000)
        logging.info(response)
    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )


# checkOpenedPosition()

positionAmt = 0


def getPosition(symbol):
    # cancelOrder()
    try:
        response = um_futures_client.get_position_risk(recvWindow=6000)
        logging.info(response)
        posiblePosition = response

        for i in range(len(posiblePosition)):
            if response[i]["symbol"] == symbol:
                print(response[i])
                global positionAmt
                positionSymbol = response[i]['symbol']
                positionAmt = float(response[i]['positionAmt'])
                positionAmt = round(positionAmt, 3)
                positionEntryPrice = response[i]['entryPrice']
                # print(positionSymbol)
                print(positionAmt)
                # print(positionEntryPrice)
        else:
            i += 1

        # print(response)
        # print(posiblePosition)
    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )


# getPosition("ETHUSDT")


def closePosition(symbol, qty):
    try:
        # markPrice = um_futures_client.mark_price(symbol)["markPrice"]
        # markPrice = round(float(markPrice), 2)
        response = um_futures_client.new_order(
            symbol=symbol,
            side="BUY",
            type="MARKET",
            reduceOnly="true",
            quantity=qty,
            # timeInForce="GTC",
            # price=cl,
            # stopPrice=markPrice
        )
        print("close Position ", symbol)
        print("close Qty ", qty)
    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

    try:
        markPrice = um_futures_client.mark_price(symbol)["markPrice"]
        markPrice = round(float(markPrice), 2)
        response = um_futures_client.new_order(
            symbol=symbol,
            side="SELL",
            type="MARKET",
            reduceOnly="true",
            quantity=qty,
            # timeInForce="GTC",
            # price=cl,
            # stopPrice=markPrice
        )
        print("close Position ", symbol)
        print("close Qty ", qty)
    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )


# closePosition("ETHUSDT", positionAmt)
# markPrice = um_futures_client.mark_price("ETHUSDT")["markPrice"]
# markPrice = round(float(markPrice), 3)
# print(markPrice)


positionQty = 0.00


def calculateMargin(price, side):
    global accBalance
    getBalance()
    # position use 90% of acc balance available
    if side == "BUY":
        # Long margin 2.5% cl
        positionSize = (10 / 2.5) * float(accBalance * (1 - 0.1))
    else:
        # Short margin 3% cl
        positionSize = (10 / 3) * float(accBalance * (1 - 0.1))

    return positionSize


def order(symbol, side, price):
    print("Place new order")
    cancelOrder()
    global positionQty
    # position use 90% of acc balance available

    positionQty = round(float(accBalance * (1 - 0.1)), 0) / price
    positionQty = round(positionQty, 3)
    clQty = positionQty

    if side == "BUY":
        cl = round(price * (1 - 0.015), 2)  # 1min scalp
        # cl = price * (1 - 0.025)
    else:
        cl = round(price * (1 + 0.02), 2)  # 1min scalp
        # cl = price * (1 + 0.03)

    try:
        response = um_futures_client.new_order(
            symbol=symbol,
            side=side,
            type="LIMIT",
            quantity=positionQty,
            timeInForce="GTC",
            price=price,
        )

        logging.info(response)
        print("Entry Order")
        print(response["symbol"])
        print("Side: ", response["side"])
        print("Order type: ", response["type"])
        print("Position Qty: ", positionQty)
        print("Order price: ", response["price"])
        print("")
        # place stoploss order
        if side == "BUY":
            clSide = "SELL"
        else:
            clSide = "BUY"

        def stoplossOrder(symbol, side, clQty):
            # place stoploss order
            print("place stoploss order")
            if side == "BUY":
                clSide = "SELL"
            else:
                clSide = "BUY"
            try:
                response = um_futures_client.new_order(
                    symbol=symbol,
                    side=clSide,
                    type="STOP_MARKET",
                    reduceOnly="true",
                    quantity=clQty,
                    timeInForce="GTC",
                    # price=cl,
                    stopPrice=cl
                )
                logging.info(response)
                print("Stoploss Order")
                print(response["symbol"])
                print("Side: ", response["side"])
                print("Order type: ", response["type"])
                print("Position Qty: ", clQty)
                print("Order price: ", response["stopPrice"])
                print("")
            except ClientError as error:
                logging.error(
                    "Found error. status: {}, error code: {}, error message: {}".format(
                        error.status_code, error.error_code, error.error_message
                    )
                )
                return False

        stoplossOrder(symbol, side, clQty)
    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
        return False
    return order


#
# order(side="BUY", price=800) test


# def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
#     try:
#         print(f"sending order {order_type} - {side} {quantity} {symbol}")
#         order = um_futures_client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
#     except Exception as e:
#         print("an exception occured - {}".format(e))
#         return False
#
#     return order


@app.route('/')
def welcome():
    return render_template('index.html')


order_response = ""


@app.route('/webhook', methods=['POST'])
def webhook():
    global order_response

    data = json.loads(request.data)
    if data["passphrase"] != config.WEBHOOK_PASSPHRASE:
        return {
            "code": "error",
            "message": "Nice try, invalid passphrase"
        }

    symbol = data["ticker"]
    side = data["strategy"]["order_id"]
    price = data["strategy"]["order_price"]

    if side == "BUY" or side == "SELL":
        order_response = order(symbol, side, price)
    elif side == "Close entry(s) order SELL" or side == "Close entry(s) order BUY":
        closePosition(symbol, positionAmt)
    else:
        return "wrong order_id"

    # return {
    #     "code": "success",
    #     "message": str(data)
    # }

    if order_response:
        return {
            "code": "success",
            "message": "order executed"
        }
    else:
        print("order failed")

        return {
            "code": "error",
            "message": "order failed"
        }
