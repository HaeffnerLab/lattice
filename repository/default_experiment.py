# This is a default experiment that runs when no other experiment is running.
# It sets the outputs to those for trapping correctly so that when experiments finish,
# the system automatically goes back to a stable state.

import time
from artiq.experiment import *

from acf.experiment import ACFExperiment
from acf_sequences.sequences import sequences

class DefaultExperiment(ACFExperiment):

    def build(self):
        self.setup(sequences)
        self.set_default_scheduling(priority=-99)

        # Get good cooling params
        self.freq_397_cooling = float(self.parameter_manager.get_param("frequency/397_cooling"))
        self.freq_866_cooling = float(self.parameter_manager.get_param("frequency/866_cooling"))
        self.freq_397_far_detuned = float(self.parameter_manager.get_param("frequency/397_far_detuned"))

    @kernel
    def run(self):
        self.setup_run()

        # Set good trapping parameters
        self.dds_397_dp.set(self.freq_397_cooling)
        self.dds_866_dp.set(self.freq_866_cooling)
        self.dds_397_far_detuned.set(self.freq_397_far_detuned)

        self.dds_397_dp.sw.on()
        self.dds_866_dp.sw.on()
        self.dds_397_far_detuned.sw.on()
        
        self.dds_729_dp.sw.off()
        self.dds_729_sp.sw.off()
        self.dds_854_dp.sw.off()
        self.dds_866_addressing.sw.off()

        # Loop forever. If an experiment is detected with higher priority, submit this
        # experiment again and exit
        while True:
            if self.scheduler.check_pause():
                self.scheduler.submit()
                break
            time.sleep(0.1)
