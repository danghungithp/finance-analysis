from flask import Flask, render_template, request
import pandas as pd
import requests
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

API_KEY = '71GU24NSRGWPV28C'
BASE_URL = 'https://www.alphavantage.co/query'

def get_stock_data(symbol):
    params = {
        'function': 'TIME_SERIES_DAILY_ADJUSTED',
        'symbol': symbol,
        'outputsize': 'full',
        'apikey': API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    return data['Time Series (Daily)']

def parse_time_series(data):
    df = pd.DataFrame.from_dict(data, orient='index')
    df = df.astype(float)
    df.index = pd.to_datetime(df.index)
    df = df.rename(columns={
        '1. open': 'Open',
        '2. high': 'High',
        '3. low': 'Low',
        '4. close': 'Close',
        '5. adjusted close': 'Adjusted Close',
        '6. volume': 'Volume'
    })
    return df

def calculate_money_flow(df):
    df['Typical Price'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['Money Flow'] = df['Typical Price'] * df['Volume']
    df['Positive Money Flow'] = df.apply(lambda row: row['Money Flow'] if row['Typical Price'] > row['Typical Price'].shift(1) else 0, axis=1)
    df['Negative Money Flow'] = df.apply(lambda row: row['Money Flow'] if row['Typical Price'] < row['Typical Price'].shift(1) else 0, axis=1)
    return df

@app.route('/', methods=['GET', 'POST'])
def index():
    plot_url = None
    if request.method == 'POST':
        symbol = request.form['symbol']
        try:
            data = get_stock_data(symbol)
            df = parse_time_series(data)
            df = calculate_money_flow(df)

            # Vẽ đồ thị
            plt.figure(figsize=(14, 7))
            plt.plot(df.index, df['Positive Money Flow'], label='Positive Money Flow', color='g')
            plt.plot(df.index, df['Negative Money Flow'], label='Negative Money Flow', color='r')
            plt.fill_between(df.index, df['Positive Money Flow'], color='g', alpha=0.5)
            plt.fill_between(df.index, df['Negative Money Flow'], color='r', alpha=0.5)
            plt.title(f'Money Flow for {symbol}')
            plt.xlabel('Date')
            plt.ylabel('Money Flow')
            plt.legend()

            # Chuyển đồ thị thành hình ảnh
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode()

            plt.close()
        except Exception as e:
            print(f"Error: {e}")

    return render_template('index.html', plot_url=plot_url)

if __name__ == '__main__':
    app.run(debug=True)
