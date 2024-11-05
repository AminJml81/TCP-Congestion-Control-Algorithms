import pandas as pd
import matplotlib.pyplot as plt
import time, threading, logging, random


class CubicTCPCongestionControl:

    def __init__(self, beta:float, c:float, cwnd:int,
                tcp_friendliness:bool, fast_convergence:bool):
        """
        Args:
            beta (float): window decrease constant.
            c (float): cubic parameter.
            cwnd (int): current window size(here initial window size).

        Instance Variables:
            wlast_max(float): The last value of wmax.

            k(float): The time period it takes to increase the cwnd from its current value
                          to the wlast_max without encountering further packet loss.

            epoch_start(float): The timestamp marking the beginning
                                    of the current congestion epoch.

            origin_point(float): The congestion window value at the beginning
                                    of the current congestion epoch.

            ack_cnt(int): The number of acknowledgements received since the beginning
                              of the current congestion epoch.

            wtcp(float): The target congestion window during
                             TCP-friendliness calculations.

            ssthresh(float): The slow-start threshold, which determines
                                 the maximum congestion window size during
                                 the slow-start phase.

            tcp_timestamp(float): A timestamp representing the current time.
        """
        self.c = c
        self.beta = beta 
        self.cwnd = cwnd
        self.tcp_friendliness = tcp_friendliness
        self.fast_convergence = fast_convergence

        self.wlast_max = 30
        self.k = 0
        self.origin_point = 0
        self.ack_cnt = 0
        self.cwnd_cnt = 0
        self.wtcp = 0
        self.ssthresh = 30
        self.epoch_start = 0
        self.round_number = 1
        self.dMin = 0 

        # setting up logging 
        logging.basicConfig(
            level=logging.INFO, format='%(message)s',
            filename='log.log', filemode='w',
        )

        # setting up Pandas dataFrame.
        self.dataframe = pd.DataFrame(columns=['round', 'cwnd', 'wlast_max', 'wtcp', 'epoch_start', 'origin_point', 'dMin', 'ack_cnt'])

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
        
        # setting up thread for timeout.
        timeout_thread = threading.Thread(target=self._timeout, daemon=True)
        timeout_thread.start()

    def run(self):
        rtt = random.uniform(0,1)
        if self.dMin != 0:
            self.dMin = min(self.dMin, rtt)
        else:
            self.dMin = rtt
        logging.info(f'{self.round_number} -- dmin: {self.dMin}')
        if self.cwnd < self.ssthresh:
            logging.info(f'{self.round_number} -- cnwd({self.cwnd}) < ssthresh({self.ssthresh})')
            self.cwnd += 1
            logging.info(f'{self.round_number} -- cnwd: {self.cwnd}')

        else:
            logging.info(f'{self.round_number} -- cnwd({self.cwnd}) > ssthresh({self.ssthresh})')
            self._cubic_update()
            if self.cwnd_cnt > self.cnt:
                logging.info(f'{self.round_number} -- cwnd_cnt({self.cwnd_cnt}) > cnt: ({self.cnt})')
                self.cwnd += 1
                self.cwnd_cnt = 0
            else:
                logging.info(f'{self.round_number} -- cwnd_cnt({self.cwnd_cnt}) < cnt: ({self.cnt})')
                self.cwnd_cnt += 1
                logging.info(f'{self.round_number} -- cwnd_cnt: {self.cwnd_cnt}')

        self.cwnd_values.append(self.cwnd)
        self.rounds.append(self.round_number)

        self.line.set_data(self.rounds, self.cwnd_values)
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def _packet_loss(self):
        while self.is_running:
            number = random.random() * 3
            time.sleep(number)
            logging.error(f'{self.round_number} -- PACKET LOSS')
            self.epoch_start = 0
            if self.fast_convergence and self.cwnd < self.wlast_max:
                logging.info(f'{self.round_number} -- fast_convergence({self.fast_convergence}) and cwnd({self.cwnd}) < wlast_max({self.wlast_max})')
                self.wlast_max = self.cwnd * (2-self.beta)/2
            else:
                logging.info(f'{self.round_number} -- fast_convergence({self.fast_convergence}) and cwnd({self.cwnd}) < wlast_max({self.wlast_max})')
                self.wlast_max = self.cwnd
            
            self.ssthresh = self.cwnd
            self.cwnd *= (1-self.beta)
            logging.info(f'{self.round_number} -- ssthresh:{self.ssthresh}, cwnd:{self.cwnd}')

    def _timeout(self):
        while self.is_running:
            number = random.random() * 6
            time.sleep(number)
            logging.error(f'{self.round_number} -- TIMEOUT')
        self._cubic_reset()

    def _cubic_update(self):
        logging.info(f'{self.round_number} -- Cubic Update')
        self.ack_cnt += 1
        logging.info(f'{self.round_number} -- ack_cnt: {self.ack_cnt}')
        if self.epoch_start <= 0:
            logging.info(f'{self.round_number} -- epoch_start({self.epoch_start}) <= 0')
            self.epoch_start = time.time()
            logging.info(f'{self.round_number} -- epoch_start: {self.epoch_start}')
            if self.cwnd < self.wlast_max:
                logging.info(f'{self.round_number} -- cwnd({self.cwnd}) < wlast_max({self.wlast_max})')
                self.k = ((self.wlast_max - self.cwnd) / self.c) ** (1/3)
                self.origin_point = self.wlast_max
            else:
                logging.info(f'{self.round_number} -- cwnd({self.cwnd}) < wlast_max({self.wlast_max})')
                self.k = 0
                self.origin_point = self.cwnd
            logging.info(f'{self.round_number} -- k: {self.k}, origin_point: {self.origin_point}')
            self.ack_cnt = 1
            self.wtcp = self.cwnd
            logging.info(f'{self.round_number} -- ack_cnt: {self.ack_cnt}, wtcp: {self.wtcp}')

        t = time.time() + self.dMin - self.epoch_start
        target = self.origin_point + self.c * (t-self.k)**3
        logging.info(f'{self.round_number} -- t: {t}, target: {target}, cwnd: {self.cwnd}')
        if target > self.cwnd:
            logging.info(f'{self.round_number} -- target({target}) > cwnd({self.cwnd})')
            self.cnt = self.cwnd / (target - self.cwnd)
        else:
            logging.info(f'{self.round_number} -- target({target}) < cwnd({self.cwnd})')
            self.cnt = 100 * self.cwnd
        logging.info(f"{self.round_number} -- cnt: {self.cnt}")
        if self.tcp_friendliness:
            self._cubic_tcp_friendliness()
        
    def _cubic_tcp_friendliness(self):
        logging.info(f'{self.round_number} -- TCP Friendliness')
        self.wtcp = self.wtcp + (3*self.beta)/(2-self.beta) * (self.ack_cnt/self.cwnd)
        self.ack_cnt = 0
        logging.info(f'{self.round_number} -- wtcp: {self.wlast_max}, ack_cnt: {self.ack_cnt}')
        if self.wtcp > self.cwnd:
            logging.info(f'{self.round_number} -- wtcp({self.wtcp}) > cwnd({self.cwnd})')
            max_cnt = (self.cwnd)/(self.wtcp-self.cwnd)
            if self.cnt > max_cnt:
                logging.info(f'{self.round_number} -- cnt({self.cnt}) > max_cnt({max_cnt})')
                self.cnt = max_cnt
            logging.info(f'{self.round_number} -- max_cnt: {max_cnt}, cnt: {self.cnt}')

    def _cubic_reset(self):
        self.wlast_max, self.epoch_start, self.origin_point = 0, 0, 0 
        self.dMin, self.wtcp, self.k ,self.ack_cnt = 0, 0, 0, 0 

    def insert_paramaters_to_dataframe(self):
        data = [self.round_number, self.cwnd, self.wlast_max, self.wtcp, self.epoch_start, self.origin_point, self.dMin, self.ack_cnt]
        self.dataframe.loc[len(self.dataframe)] = data


if __name__ == '__main__':
    cubic_tcp = CubicTCPCongestionControl(
        beta=0.2 , c=0.4, cwnd=10, tcp_friendliness=True, fast_convergence=True
    )
    for _ in range(1000):
        cubic_tcp.run()
        cubic_tcp.insert_paramaters_to_dataframe()
        cubic_tcp.round_number += 1
        logging.info('')
    
    cubic_tcp.is_running = False
    cubic_tcp.dataframe.to_csv('cubic_tcp_parameters.csv', index=False)
    plt.show(block=True)
