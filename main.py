from kivy.app import App
from kivy.core.text import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.textinput import TextInput

from binance_utils import TrailingBot, PriceFetcher, get_balance

price_thread = None
bot_thread = None


class MenuScreen(Screen):
    wm = None
    live_price = Label()
    coin_label_1 = Label()
    coin_label_2 = Label()
    coin_balance_1 = Label()
    coin_balance_2 = Label()
    coin_pair = TextInput()
    status_label = Label()

    def open_trail_screen(self):
        global bot_thread
        if bot_thread is not None:
            bot_thread.running = False
            bot_thread.join()
        self.wm.transition.direction = 'left'
        self.wm.current = 'trail'

    def start_bot(self, trail_type, amount, val):
        coin1 = self.coin_pair.text.split("/")[0].upper()
        coin2 = self.coin_pair.text.split("/")[1].upper()

        global bot_thread
        if bot_thread is not None:
            bot_thread.running = False
            bot_thread.join()
        bot_thread = TrailingBot(trail_type, coin1 + coin2, float(amount), float(val), self.status_label,
                                 self.live_price)
        bot_thread.daemon = True
        bot_thread.start()

    def load(self):
        coin1 = self.coin_pair.text.split("/")[0].upper()
        coin2 = self.coin_pair.text.split("/")[1].upper()

        self.coin_label_1.text = coin1
        self.coin_label_2.text = coin2
        self.coin_balance_1.text = str(get_balance(coin1))
        self.coin_balance_2.text = str(get_balance(coin2))

        global price_thread
        if price_thread is not None:
            price_thread.running = False
            price_thread.join()
        price_thread = PriceFetcher(coin1 + coin2, self.live_price)
        price_thread.daemon = True
        price_thread.start()


class TrailScreen(Screen):
    wm = None

    def back_to_menu(self):
        self.wm.transition.direction = 'right'
        self.wm.current = 'menu'

    def start_bot(self, trail_type, amount, val):
        self.wm.transition.direction = 'right'
        self.wm.current = 'menu'
        self.wm.current_screen.start_bot(trail_type, amount, val)


class WindowManager(ScreenManager):
    pass


class MyApp(App):
    def build(self):
        self.wm = WindowManager()
        return self.wm

    def on_stop(self):
        if price_thread is not None:
            price_thread.final_closure = True
            price_thread.running = False
            price_thread.join()
        if bot_thread is not None:
            bot_thread.running = False
            bot_thread.join()
        return True


if __name__ == '__main__':
    MyApp().run()
