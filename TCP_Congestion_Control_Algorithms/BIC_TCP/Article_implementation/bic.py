import matplotlib.pyplot as plt
import threading, logging, time, random
import pandas as pd


class BICTCPCongestionControl:

    def __init__(self, wmax:int, wmin:int, Smax:int,
                Smin:int, Beta:float, low_window:int, 
                cwnd:int
        ):
        self.wmax = wmax
        self.wmin = wmin
        self.smax = Smax # constant
        self.smin = Smin # constant
        self.cwnd = cwnd
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
            # everything is normal.

        else:

            if self.cwnd < self.wmax:
                logging.info(f"{self.round_number} -- cwnd({self.cwnd}) < wmax({self.wmax})")
                bic_increase = (self.wmax - self.cwnd) / 2
                         
            else:
                # if window exceeds maximum increment.
                logging.info(f"{self.round_number} -- cwnd({self.cwnd}) >= wmax({self.wmax})")
                bic_increase = self.cwnd - self.wmax
            
            if bic_increase > self.smax:
                # additve increase to prevent pressure to the network.
                logging.info(f"{self.round_number} -- bic increase({bic_increase}) > Smax({self.smax})")
                bic_increase = self.smax

            elif bic_increase < self.smin:
                logging.info(f"{self.round_number} -- bic increase({bic_increase}) < Smin({self.smin})")
                bic_increase = self.smin

            self.cwnd += (bic_increase/self.cwnd)
            logging.info(f"{self.round_number} -- cwnd = {self.cwnd}")

        self.cwnd_values.append(self.cwnd)
        self.rounds.append(self.round_number)

        self.line.set_data(self.rounds, self.cwnd_values)
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def _packet_loss(self):
        """
            Another Thread is running and waiting until the random time(*5)
            and then it invokes fast recovery method.
        """
        while self.is_running:
            number = random.random() * 5
            time.sleep(number)
            logging.error(f'{self.round_number} -- PACKET LOSS')
            self._fast_recovery()
    
    def _fast_recovery(self):
        """
            it changes cnwd, wmax parameters.
        """
        if self.cwnd < self.low_window:
            logging.info(f'{self.round_number} -- FastRecovery: cwnd({self.cwnd}) < low window({self.low_window})')
            self.cwnd = self.cwnd * 0.5
            logging.info(f"{self.round_number} -- cwnd = {self.cwnd}")

        else:
            
            if self.cwnd < self.wmax:
                logging.info(f"{self.round_number} -- FastRecovery: cwnd({self.cwnd}) < wmax({self.wmax})")
                self.wmax = self.cwnd * ((2-self.Beta)/2)
                logging.info(f"{self.round_number} -- wmax = {self.wmax}")

            else:
                logging.info(f"{self.round_number} -- FastRecovery: cwnd({self.cwnd}) >= wmax({self.wmax})")
                self.wmax = self.cwnd
                logging.info(f"{self.round_number} -- wmax = {self.wmax}")

            self.cwnd = self.cwnd * (1-self.Beta)
            logging.info(f"{self.round_number} -- cwnd = {self.cwnd}")

    def insert_paramaters_to_dataframe(self):
        data = [self.round_number, self.cwnd, self.wmax, self.wmin]
        self.dataframe.loc[len(self.dataframe)] = data

        
if __name__ == '__main__':
    bic_tcp = BICTCPCongestionControl(
        wmax= 30, wmin=5, Smin=1, Smax=5, low_window=4,
        Beta=0.125, cwnd=10, 
    )
    for _ in range(1000):
        bic_tcp.run()
        bic_tcp.insert_paramaters_to_dataframe()
        bic_tcp.round_number += 1
        logging.info('')

    bic_tcp.is_running = False
    bic_tcp.dataframe.to_csv('bic_tcp_parameters.csv', index=False)
    plt.show(block=True)
