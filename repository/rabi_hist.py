from artiq.experiment import *
from acf.experiment import ACFExperiment
from acf_config.arguments_definition import argument_manager

from acf_sequences.sequences import sequences

import numpy as np

class RabiHist(ACFExperiment):

    def build(self):
        self.setup(sequences)
    	
        self.add_arg_from_param("frequency/397_resonance")
        self.add_arg_from_param("frequency/397_cooling")
        self.add_arg_from_param("frequency/397_far_detuned")
        self.add_arg_from_param("frequency/866_cooling")
        self.add_arg_from_param("attenuation/397")
        self.add_arg_from_param("attenuation/397_far_detuned")
        self.add_arg_from_param("attenuation/866")
        self.add_arg_from_param("misc/pmt_sampling_time")

        self.setattr_argument(
            "samples",
            NumberValue(default=1000, ndecimals=0, step=1),
        )

        self.setattr_argument(
            "bin_width",
            NumberValue(default=1, ndecimals=0, step=1),
        )

        self.setattr_argument(
            "bin_val_max",
            NumberValue(default=300, ndecimals=0, step=1),
        )

    @kernel
    def run(self):
        # Create datasets
        num_bins = int(self.bin_val_max / self.bin_width) + 1
        hist_counts = [0] * num_bins

        # Start value of each bin
        self.experiment_data.set_list_dataset("rabi_hist_bins", num_bins + 1, broadcast=True)
        for bin_i in range(num_bins + 1):
            self.experiment_data.append_list_dataset("rabi_hist_bins", bin_i * self.bin_width)

        # Number of counts in each bin
        self.experiment_data.set_list_dataset("rabi_hist_counts", num_bins, broadcast=True)
        for i in range(num_bins):
            self.experiment_data.append_list_dataset("rabi_hist_counts", 0)
        
        self.setup_run()

        # Set attenuations
        self.dds_397_dp.set_att(self.attenuation_397)
        self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
        self.dds_866_dp.set_att(self.attenuation_866)
        delay(1*ms)

        # Set 397 far detuned and 866 frequencies
        self.dds_397_far_detuned.set(self.frequency_397_far_detuned)
        self.dds_866_dp.set(self.frequency_866_cooling)

        #self.dds_397_dp.sw.on()
        #self.dds_397_far_detuned.sw.on()
        #self.dds_866_dp.sw.on()
        delay(1*ms)

        for i in range(2):
            for _ in range(self.samples):
                self.seq.doppler_cool.run()
                self.dds_397_dp.set(self.frequency_397_resonance)
                self.dds_397_dp.sw.on()
                self.dds_866_dp.sw.on()
                delay(10*us)

                num_pmt_pulses = self.ttl_pmt_input.count(
                    self.ttl_pmt_input.gate_rising(self.misc_pmt_sampling_time)
                )

                for bin_i in range(num_bins - 1):
                    
                    if num_pmt_pulses < (bin_i + 1) * self.bin_width:
                        hist_counts[bin_i] += 1
                        self.experiment_data.insert_nd_dataset("rabi_hist_counts", bin_i, hist_counts[bin_i])
                        break
                
                delay(10*ms)
            
            if i == 0:
                print("QIMING PLEASE THROW OUT THE IONS, THE WORLD DEPENDS ON YOUUUU")
                print("CONTINUING IN 10 SECONDS")
                delay(10*s)

