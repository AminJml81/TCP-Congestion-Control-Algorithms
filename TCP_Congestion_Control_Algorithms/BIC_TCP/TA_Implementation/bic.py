# this is the exact implementaion from the 
# TA Code in the Lecture which is in the materials folder.
import matplotlib.pyplot as plt
import logging, random
import pandas as pd


class BICTCPCongestionControl:

    def __init__(self, wmax:int, wmin:int, smax:int,
                smin:int, low_window:int, 
                cwnd:int
        ):
        self.wmax = wmax
        self.wmin = wmin
        self.smax = smax # constant
        self.smin = smin # constant
        self.cwnd = cwnd
        self.low_window = low_window # constant
        self.round_number = 1

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

        # setting up Pandas dataFrame.
        self.dataframe = pd.DataFrame(columns=['round', 'cwnd', 'wmax', 'wmin'])

        # setting up logging.
        logging.basicConfig(
            level=logging.INFO, format='%(message)s',
            filename='log.log', filemode='w',
        )
            
    def run(self):
        if self.cwnd < self.low_window :
            logging.info(f"{self.round_number} -- cwnd({self.cwnd}) < low window({self.low_window})")
            self.cwnd *= 0.5
            logging.info(f"{self.round_number} -- cwnd = {self.cwnd}")

        else:
            self._binary_search_increase()
    
            if self.wmax - self.cwnd > self.smax:
                logging.info(f"{self.round_number} -- wmax({self.wmax}) - cwnd({self.cwnd}) > smax({self.smax})")
                self._additive_increase()

            if self.cwnd > self.wmax:
                logging.info(f"{self.round_number} -- cwnd({self.cwnd}) > wmax({self.wmax})")
                self._slow_start()

        self.cwnd_values.append(self.cwnd)
        self.rounds.append(self.round_number)

        self.line.set_data(self.rounds, self.cwnd_values)
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    
    def _binary_search_increase(self):
        logging.info(f"{self.round_number} -- Binary Search Increase")
        midpoint = (self.wmax + self.wmin) / 2
        logging.info(f"{self.round_number} -- midpoint = {midpoint}")
        if self.wmax - self.wmin < self.smin:
            logging.info(f"{self.round_number} -- wmax({self.wmax}) - wmin({self.wmin}) < smin({self.smin})")
            self.cwnd = midpoint
        else:
            if self._is_packet_loss():
                logging.error('PACKET LOSS')
                self.wmax = midpoint
                logging.info(f'{self.round_number} -- wmax = {self.wmax}')
            else:
                self.wmin = midpoint
                logging.info(f'{self.round_number} -- wmin = {self.wmin}')
        
    def _additive_increase(self):
        logging.info(f'{self.round_number} -- Additive Increase')
        if self.wmax - self.cwnd > self.smax:
            logging.info(f'{self.round_number} -- wmax({self.wmax}) - cwnd({self.cwnd}) > smax({self.smax})')
            self.cwnd += self.smax
            logging.info(f'{self.round_number} -- cwnd = {self.cwnd}')
        else:
            self.cwnd = self.wmax
            logging.info(f'{self.round_number} -- cwnd = {self.cwnd}')


    def _slow_start(self):
        logging.info(f'{self.round_number} -- Slow Start')
        while self.cwnd < self.wmax + self.smax:
            self.cwnd += self.smax
            logging.info(f'{self.round_number} -- cwnd = {self.cwnd}')

    def _is_packet_loss(self):
        return random.random() > 0.7
        
    def insert_paramaters_to_dataframe(self):
        data = [self.round_number, self.cwnd, self.wmax, self.wmin]
        self.dataframe.loc[len(self.dataframe)] = data

        
if __name__ == '__main__':
    bic_tcp = BICTCPCongestionControl(
        wmax= 30, wmin=5, smin=1, smax=5, 
        low_window=4,cwnd=10)
    
    for _ in range(20):
        bic_tcp.run()
        bic_tcp.insert_paramaters_to_dataframe()
        bic_tcp.round_number += 1
        logging.info('')

    bic_tcp.is_running = False
    bic_tcp.dataframe.to_csv('bic_tcp_parameters.csv', index=False)
    plt.show(block=True)
