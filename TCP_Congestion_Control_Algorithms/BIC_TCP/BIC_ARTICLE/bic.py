# this is the exact implementaion from the 
# pseudo code in the article.
import matplotlib.pyplot as plt
import threading, logging, time, random
import pandas as pd


class BICTCPCongestionControl:

    def __init__(self, Wmax:int, Wmin:int, Smax:int,
                Smin:int, Beta:float, low_window:int, 
                Cwnd:int
        ):
        self.Wmax = Wmax
        self.Wmin = Wmin
        self.Smax = Smax # constant
        self.Smin = Smin # constant
        self.cwnd = Cwnd
        self.low_window = low_window # constant
        self.Beta = Beta
        self.round_number = 1
        self.is_running = True

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
    
        # simulating packet loss functionlity with thread.
        self.packet_loss_thread = threading.Thread(target=self._packet_loss)
        self.packet_loss_thread.start()
        
    def run(self):
        if self.cwnd < self.low_window :
            logging.info(f"{self.round_number} -- cwnd({self.cwnd}) < low window({self.low_window})")
            self.cwnd = self.cwnd + (1 / self.cwnd)
            logging.info(f"{self.round_number} -- cwnd = {self.cwnd}")
            # everything is normal. DONE

        else:

            if self.cwnd < self.Wmax:
                logging.info(f"{self.round_number} -- cwnd({self.cwnd}) < Wmax({self.Wmax})")
                bic_increase = (self.Wmax - self.cwnd)/2
                         
            else:
                logging.info(f"{self.round_number} -- cwnd({self.cwnd}) >= Wmax({self.Wmax})")
                bic_increase = self.cwnd - self.Wmax
            
            if bic_increase > self.Smax:
                logging.info(f"{self.round_number} -- bic increase({bic_increase}) > Smax({self.Smax})")
                bic_increase = self.Smax

            elif bic_increase < self.Smin:
                logging.info(f"{self.round_number} -- bic increase({bic_increase}) < Smin({self.Smin})")
                bic_increase = self.Smin

            self.cwnd = self.cwnd + (bic_increase/self.cwnd)
            logging.info(f"{self.round_number} -- cwnd = {self.cwnd}")

        self.cwnd_values.append(self.cwnd)
        self.rounds.append(self.round_number)

        self.line.set_data(self.rounds, self.cwnd_values)
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def _packet_loss(self):
        while self.is_running:
            number = random.random() * 5
            time.sleep(number)
            logging.error('PACKET LOSS')
            self._fast_recovery()
    
    def _fast_recovery(self):
        if self.cwnd < self.low_window:
            logging.info(f'{self.round_number} -- FastRecovery: cwnd({self.cwnd}) < low window({self.low_window})')
            self.cwnd = self.cwnd * 0.5
            logging.info(f"{self.round_number} -- cwnd = {self.cwnd}")

        else:
            if self.cwnd < self.Wmax:
                logging.info(f"{self.round_number} -- FastRecovery: cwnd({self.cwnd}) < Wmax({self.Wmax})")
                self.Wmax = self.cwnd * ((2-self.Beta)/2)
                logging.info(f"{self.round_number} -- Wmax = {self.Wmax}")

            else:
                logging.info(f"{self.round_number} -- FastRecovery: cwnd({self.cwnd}) >= Wmax({self.Wmax})")
                self.Wmax = self.cwnd
                logging.info(f"{self.round_number} -- Wmax = {self.Wmax}")

            self.cwnd = self.cwnd * (1-self.Beta)
            logging.info(f"{self.round_number} -- cwnd = {self.cwnd}")

    def insert_paramaters_to_dataframe(self):
        data = [self.round_number, self.cwnd, self.Wmax, self.Wmin]
        self.dataframe.loc[len(self.dataframe)] = data

        
if __name__ == '__main__':
    bic_tcp = BICTCPCongestionControl(
        Wmax= 30, Wmin=5, Smin=1, Smax=5, low_window=4,
        Beta=0.125, Cwnd=10, 
    )
    for _ in range(1000):
        bic_tcp.run()
        bic_tcp.insert_paramaters_to_dataframe()
        bic_tcp.round_number += 1
        logging.info('')

    bic_tcp.is_running = False
    bic_tcp.dataframe.to_csv('bic_tcp_parameters.csv', index=False)
    plt.show(block=True)
