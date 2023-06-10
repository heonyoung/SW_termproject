import pymongo
from pymongo import MongoClient
import json, pytz
from flask import Flask, request, render_template, redirect, session, flash, jsonify, url_for, g
from datetime import datetime, timedelta
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'key'
cluster = MongoClient("mongodb+srv://royirene:xAndluojC4zCYCnq@heon.mwtmi5w.mongodb.net/?retryWrites=true&w=majority")
db = cluster["term_project"]
collection = db["info"]
history = db["trade_his"]
log_in = db["logged_in"]
coin_amount = db["market_coin_amount"]

@app.route('/coin_price_over_time', methods=['GET'])
def coin_price_over_time():
    # 현재 시간
    current_time = datetime.now(pytz.UTC)
    
    # 5시간 전 시간
    start_time = current_time - timedelta(hours=5)
    
    # 가격 데이터를 저장할 딕셔너리
    price_data = {}
    
    # 1시간씩 감소하며 가격 데이터 계산
    while current_time >= start_time:
        # 해당 시간 이전의 모든 거래 내역 조회
        transactions = list(history.find({'type': 'success', 'time': {'$lte': current_time}}))
        if len(transactions) > 0:
            total_price = sum(transaction['amount'] * transaction['ppc'] for transaction in transactions)
            coinsum = sum(transaction['amount'] for transaction in transactions)
            average_price = total_price / coinsum
            price_data[current_time.strftime('%H:%M')] = average_price
        else:
            # 거래 내역이 없는 경우 시장 가격으로 설정
            market_coin = coin_amount.find_one({})
            price_data[current_time.strftime('%H:%M')] = market_coin.get('market_coin', 100)  # 시장 가격
            
        # 1시간 감소
        current_time -= timedelta(hours=1)
    
    return json.dumps(price_data)



@app.route('/')
def main_():
    result = log_in.find()
    market_resulttmp = coin_amount.find()

    for i in result:
        logincheck = i["logged_in"]
    for i in market_resulttmp:
        market_result = i
    
    if logincheck == 1:
        sellings = list(history.find({"type": "sell", "user": g.user["_id"]}))
        transactions = list(history.find({"user": g.user["_id"]}))  # 모든 거래 내역 조회
        historys = list(history.find({}))

        return render_template('dashboard.html', logged_in=True, result=g.user, market_result=market_result, sellings=sellings,history=historys, transactions=transactions)
    else:
        return render_template('dashboard.html', logged_in=False)

@app.route('/deposits', methods=['GET'])
def show_deposit_form():
    return render_template('deposit.html')

@app.route('/deposit', methods=['POST'])
def handle_deposit():
    amount = int(request.form['amount'])

    user = collection.find_one({'id': session['user_id']})

    # 유저의 seedmoney를 입금액(amount)만큼 증가시킴
    collection.update_one({'_id': user['_id']}, {'$inc': {'seedmoney': amount}})

    #flash('입금이 완료되었습니다.')
    return redirect('/personal_info')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        g.user = collection.find_one({'id': username})
        if g.user and g.user['pw'] == password:
            session['user_id'] = g.user['id']
            log_in.update_one({}, {"$set": {"logged_in": 1}})
            return redirect('/')
        else:
            flash("Login failed")
            return redirect('/login')

    return render_template('login.html')

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)
    log_in.update_one({}, {"$set": {"logged_in": 0}})
    return redirect('/')

@app.route('/personal_info')
def personal_info():
    result = log_in.find()
    for i in result:
        logincheck = i["logged_in"]
    if logincheck == 1:
        return render_template('personal_info.html', logged_in=True, result=g.user)
    else:
        return render_template('personal_info.html', logged_in=False)

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    
    if request.method == 'POST':
        amount = int(request.form['amount'])

        user = collection.find_one({'id': session['user_id']})

        if amount > user['seedmoney']:
            flash('보유한 금액 이하의 금액을 입력해주세요.')
            return redirect('/withdraw')

        # 유저의 seedmoney를 출금액(amount)만큼 감소시킴
        collection.update_one({'_id': user['_id']}, {'$inc': {'seedmoney': -amount}})

        #flash('출금이 완료되었습니다.')
        return redirect('/personal_info')

    return render_template('withdraw.html')

@app.route('/open_withdraw')
def open_withdraw():
    flash("보유한 금액 이하의 금액을 입력해주세요.")
    return redirect('/withdraw')

@app.route('/registering')
def registering():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json  # request.form 대신 request.json 사용
    id = data['id']
    pw = data['pw']
    name = data['name']
    birth = data['birth']
    number = data['number']
    email = data['email']

    user = {
        'id': id,
        'pw': pw,
        'name': name,
        'birth': birth,
        'number':number,
        'email': email,
        'seedmoney' : 0,
        'coin': 0
    }
    collection.insert_one(user)
    # 회원가입이 완료되었다는 메시지와 함께 dashboard.html로 리다이렉트
    message = "회원가입이 완료되었습니다!"
    return jsonify(message=message, redirect='/')  # dashboard.html로 리다이렉트

@app.before_request
def load_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = collection.find_one({'id': user_id})

@app.route('/buy', methods=['POST'])
def buy_coin():
    data = request.get_json()
    user = g.user
    coin_id = data.get('coinId')
    quantity = int(data.get('quantity'))
    market_price = float(data.get('marketPrice'))

    market_coin = coin_amount.find_one({})

    if market_coin['market_coin'] < quantity:
        return jsonify(status='failed', message='Not enough coins available in the market.')

    total_price = market_price * quantity

    if user['seedmoney'] < total_price:
        return jsonify(status='failed', message='Not enough seed money.')

    collection.update_one({'_id': user['_id']}, {'$inc': {'seedmoney': -total_price}})
    collection.update_one({'_id': user['_id']}, {'$inc': {'coin': quantity}})
    coin_amount.update_one({}, {'$inc': {'market_coin': -quantity}})
    history.insert_one({
        "type": "buy",
        "user": user['_id'],
        "amount": quantity,
        "ppc": market_price,
        "time": datetime.now()
    })

    return jsonify(status='success')


@app.route('/check-user-id/<user_id>', methods=['GET'])
def check_user_id(user_id):
    user = collection.find_one({"id": user_id})
    if user:
        return jsonify(valid=False, message="아이디가 이미 존재합니다.")
    else:
        return jsonify(valid=True, message="사용 가능한 아이디입니다.")

@app.route('/sell', methods=['POST'])
def sell_coin():
    if g.user is None:
        return jsonify({'status': 'fail', 'message': '로그인하지 않았습니다.'})

    data = request.get_json()
    sell_amount = int(data.get('amount'))
    sell_quantity = int(data.get('quantity'))

    if g.user["coin"] < sell_quantity:
        return jsonify({'status': 'fail', 'message': '판매할 코인이 부족합니다.'})

    collection.update_one({'_id': g.user['_id']}, {'$inc': {'coin': -sell_quantity}})
    history.insert_one({
        "type": "sell",
        "user": g.user['_id'],
        "amount": sell_quantity,
        "ppc": sell_amount,
        "time": datetime.now()
    })

    return jsonify({'status': 'success'})

@app.route('/cancel-sell', methods=['POST'])
def cancel_sell():
    data = request.get_json()
    transaction_id = data.get('transaction_id')

    transaction = history.find_one({"_id": ObjectId(transaction_id)})

    if not transaction:
        return jsonify(status='failed', message='거래를 찾을 수 없습니다.')

    user = collection.find_one({"_id": transaction['user']})
    collection.update_one({'_id': user['_id']}, {'$inc': {'coin': transaction['amount']}})

    history.insert_one({
        "type": "cancel_sell",
        "user": user['_id'],
        "amount": transaction['amount'],
        "ppc": transaction['ppc'],
        "time": datetime.now()
    })

    history.delete_one({"_id": ObjectId(transaction_id)})

    return jsonify(status='success')

@app.route('/buy-market', methods=['POST'])
def buy_market_coin():
    data = request.get_json()
    user = g.user
    coin_id = data.get('coinId')

    # coinId를 기반으로 시장에서 코인을 찾습니다.
    coin = history.find_one({"_id": ObjectId(coin_id)})

    if not coin:
        return jsonify(status='failed', message='시장에서 코인을 찾을 수 없습니다.')

    # 총 구매 가격을 계산합니다.
    total_price = coin['ppc'] * coin['amount']

    if user['seedmoney'] < total_price:
        return jsonify(status='failed', message='가진 자금이 구매에 부족합니다.')

    # 사용자의 자금에서 가격을 차감합니다.
    collection.update_one({'_id': user['_id']}, {'$inc': {'seedmoney': -total_price}})

    # 사용자의 코인 수량을 업데이트합니다.
    collection.update_one({'_id': user['_id']}, {'$inc': {'coin': coin['amount']}})

    # 판매한 사용자의 돈을 증가시킵니다.
    seller = collection.find_one({'_id': coin['user']})
    collection.update_one({'_id': seller['_id']}, {'$inc': {'seedmoney': total_price}})

    # 시장에서 구매한 코인을 'success'로 업데이트하고 시간을 업데이트합니다.
    history.update_one({"_id": ObjectId(coin_id)}, {'$set': {'type': 'success'}, '$currentDate': {'time': True}})

    return jsonify(status='success')


if __name__ == '__main__':
    app.run()
