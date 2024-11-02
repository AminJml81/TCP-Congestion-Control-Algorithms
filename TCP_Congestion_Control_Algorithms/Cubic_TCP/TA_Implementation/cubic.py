import matplotlib.pyplot as plt
import pandas as pd
import random, logging, threading, time


class CubicTCPCongestionControl:

    def __init__(self, cwnd: float, wmax:float, c:float, low_window:float):
        self.cwnd = cwnd
        self.wmax = wmax
        self.c = c
        self.low_window = low_window
        self.k = 0
        self.t = 1 # same as round number in previous implementations.
        self.t_last_loss = 0

        # setting up logging 
        logging.basicConfig(
            level=logging.INFO, format='%(message)s',
            filename='log.log', filemode='w',
        )

        # setting up Pandas dataFrame.
        self.dataframe = pd.DataFrame(columns=['t', 'cwnd', 'wmax',  'k', 't_lastloss'])

        # setting up plot
        plt.ion()
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [])
        plt.xlabel('Round Number')
        plt.ylabel('Congestion Window (cwnd)')
        plt.title('Congestion Window Evolution')
        plt.grid(True)
        plt.show()
        self.rounds, self.cwnd_values = [], []

        self.is_running = True
        # setting up thread for packet loss.
        packet_loss_thread = threading.Thread(target=self._packet_loss, daemon=True)
        packet_loss_thread.start()

    def run(self):
        if self.cwnd < self.low_window:
            logging.info(f't{self.t} -- cwnd({self.cwnd}) < low_window({self.low_window})')
            self.cwnd *= 0.5
            
        time_since_loss = self.t - self.t_last_loss
        self.target_cwnd = self._cubic_function(time_since_loss)
        logging.info(f'{self.t} -- time_since_loss: {time_since_loss}, target_cwnd: {self.target_cwnd}')

        if self.cwnd < self.target_cwnd:
            logging.info(f'{self.t} -- cwnd({self.cwnd}): < target_cwnd({self.target_cwnd})')
            self.cwnd += self._cubic_increase()
            logging.info(f'{self.t} -- cwnd: {self.cwnd}')

        if self.cwnd > self.target_cwnd:
            logging.info(f'{self.t} -- cwnd: ({self.cwnd}) > target_cwnd: ({self.target_cwnd})')
            self.cwnd = self.target_cwnd
            logging.info(f'{self.t} -- cwnd: {self.cwnd}')

        self.cwnd_values.append(self.cwnd)
        self.rounds.append(self.t)

        self.line.set_data(self.rounds, self.cwnd_values)
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def _cubic_function(self, time_since_loss):
        logging.info(f'{self.t} -- Cubic Function')
        self.k = ((self.wmax -1) / self.c) ** (1/3)

        logging.info(f'{self.t} -- k: {self.k}')
        return self.wmax + self.c * (time_since_loss-self.k) ** 3

    def _cubic_increase(self):
        logging.info(f'{self.t} -- Cubic Increase')
        return (self.target_cwnd - self.cwnd) / self.cwnd

    def _packet_loss(self):
        while self.is_running:
            number = random.random() * 10
            time.sleep(number)
            self.t_last_loss = self.t
            logging.error(f'{self.t} -- PACKET LOSS')

    def insert_paramaters_to_dataframe(self):
        data = [self.t, self.cwnd, self.k, self.wmax, self.t_last_loss]
        self.dataframe.loc[len(self.dataframe)] = data
    

if __name__ == '__main__':
    cubic_tcp = CubicTCPCongestionControl(
        cwnd=10, wmax=30, c=0.4, low_window=4 
    )
    for _ in range(1000):
        cubic_tcp.run()
        logging.info('')
        cubic_tcp.insert_paramaters_to_dataframe()
        cubic_tcp.t += 1
    
    cubic_tcp.is_running = False
    cubic_tcp.dataframe.to_csv('cubic_tcp_parameters.csv', index=False)
    plt.show(block=True)
