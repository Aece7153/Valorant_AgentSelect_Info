from pynput import *

def main(x,y):
    print("Now at: {}".format((x,y)))

with mouse.Listener(on_move = main) as listen:
    listen.join()
