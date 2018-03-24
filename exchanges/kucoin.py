from kuconfig import key, secret

class Kucoin:

    def __init__(self, apikey=key, secret=secret):
        self.apikey = apikey
        self.secret = secret

    def balance(self, coin):
        print("coin balance")

    def buy(self, coin):
        print("buying coin")

    def sell(self, coin):
        print("selling coin")



if __name__ == '__main__':
    k = Kucoin()
    k.sell('derp')
    print(k.apikey)