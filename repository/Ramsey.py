from acf.experiment import ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

class Ramsey(ACFExperiment):

    def build(self):
    
    	self.setup(sequences)
    	
    	self.add_arg_from_param("frequency/397_resonance")
    	self.add_arg_from_param("frequency/397_cooling")
    	self.add_arg_from_param("frequency/397_far_detuned")
    	self.add_arg_from_param("frequency/866_cooling")
    	self.add_arg_from_param("frequency/729_dp")
    	self.add_arg_from_param("frequency/729_sp")
    	self.add_arg_from_param("frequency/854_dp")
    	self.add_arg_from_param("attenuation/397")
    	self.add_arg_from_param("attenuation/397_far_detuned")
    	self.add_arg_from_param("attenuation/866")
    	self.add_arg_from_param("attenuation/729_dp")
    	self.add_arg_from_param("attenuation/729_sp")
    	self.add_arg_from_param("attenuation/854_dp")
    	self.add_arg_from_param("misc/pmt_sampling_time")
    	self.add_arg_from_param("doppler_cooling/cooling_time")



    	self.setattr_argument(
            "Ramsey_wait_time",
            Scannable(
                default=RangeScan(
                    start=0.1*us,
                    stop=10000*us,
                    npoints=100
                ),
                global_min=0*us,
                global_max=10000*us,
                global_step=10*us,
                unit="us"
            ),
            tooltip="Scan parameter for Ramsey wait time."
        )

        self.setattr_argument(
            "repump_854_time",
            NumberValue(default=100*us, min=5*us, max=1*ms, unit="us"),
            tooltip="Time to run 854 repump",
        )

        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=25, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )

        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=25, precision=0, step=1),
            tooltip="Threshold PMT counts",
        )

    @kernel
    def run(self):
        print("Running the script")
        self.setup_run()
        # Create datasets
        num_freq_samples = len(self.scan_rabi_t.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_time])
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("rabi_t", num_freq_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg_thresholded",
            x_data_name="rabi_t",
            pen=False,
        )

        # Init devices
        self.core.break_realtime()
        self.dds_397_dp.init()
        self.dds_397_far_detuned.init()
        self.dds_866_dp.init()
        self.dds_729_dp.init()
        self.dds_729_sp.init()
        self.dds_854_dp.init()

        # Set attenuations
        self.dds_397_dp.set_att(self.attenuation_397)
        self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
        self.dds_866_dp.set_att(self.attenuation_866)
        self.dds_729_dp.set_att(self.attenuation_729_dp)
        self.dds_729_sp.set_att(self.attenuation_729_sp)
        self.dds_854_dp.set_att(self.attenuation_854_dp)
        delay(1*ms)

        # Set frequencies
        self.dds_729_sp.set(self.freqency_729_sp)
        self.dds_729_dp.set(self.freqency_729_dp)
        self.dds_854_dp.set(self.freqency_854_dp)
        delay(1*ms)

        time_i = 0
        for rabi_t in self.scan_rabi_t.sequence: # scan the frequency



            total_thresh_count = 0
            for sample_num in range(self.samples_per_time): # repeat N times
                self.dds_854_dp.set_att(30*dB)
                
                # Cool
                self.seq.doppler_cool.run()
                
                # Set 397 freq here for count collection, so less delay between
                # end of cooling and beginning of detection
                self.dds_397_dp.set(self.freqency_397_resonance)
                delay(10*us)

                # Attempt Rabi flop
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()

                delay(rabi_t)

                self.dds_729_dp.sw.off()
                #self.dds_729_sp.sw.off()

                # Collect counts
                
                # leave 866 at cooling frequency
                self.dds_397_dp.sw.on()
                self.dds_866_dp.sw.on()

                num_pmt_pulses = self.ttl_pmt_input.count(
                    self.ttl_pmt_input.gate_rising(self.misc_pmt_sampling_time)
                )
                delay(10*us)

                # 854 repump
                self.dds_854_dp.set_att(self.attenuation_854_dp)
                self.dds_854_dp.sw.on()
                delay(self.repump_854_time)
                self.dds_854_dp.sw.off()
                self.dds_854_dp.set_att(30*dB)
                delay(10*us)

                # Update dataset
                self.experiment_data.insert_nd_dataset("pmt_counts",
                                            [time_i, sample_num],
                                            num_pmt_pulses)
                
                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count += 1

                delay(1*ms)
            
            self.experiment_data.append_list_dataset("rabi_t", rabi_t / us)
            self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_time)
            time_i += 1
            delay(30*ms)
            
    
 
