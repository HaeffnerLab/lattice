from acf.experiment import ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

class RabiFreqScan(ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.add_arg_from_param("frequency/397_resonance")
        self.add_arg_from_param("frequency/397_cooling")
        self.add_arg_from_param("frequency/397_far_detuned")
        self.add_arg_from_param("frequency/866_cooling")
        self.add_arg_from_param("frequency/729_sp")
        self.add_arg_from_param("frequency/854_dp")
        self.add_arg_from_param("attenuation/397")
        self.add_arg_from_param("attenuation/397_far_detuned")
        self.add_arg_from_param("attenuation/866")
        self.add_arg_from_param("attenuation/729_dp")
        self.add_arg_from_param("attenuation/729_sp")
        self.add_arg_from_param("attenuation/854_dp")
        self.add_arg_from_param("misc/pmt_sampling_time")
        
        self.setattr_argument(
            "rabi_t",
            NumberValue(default=7.34*us, min=5*us, max=5*ms, unit="us",precision=6)
        )

        self.setattr_argument(
            "repump_854_time",
            NumberValue(default=100*us, min=5*us, max=1*ms, unit="us",precision=6),
        )

        self.setattr_argument(
            "scan_freq_729_dp",
            Scannable(
                default=RangeScan(
                    start=190*MHz,
                    stop=220*MHz,
                    npoints=100
                ),
                global_min=150*MHz,
                global_max=250*MHz,
                global_step=1*kHz,
                unit="MHz",
                precision=6
            ),
            tooltip="Scan parameter for sweeping the 729 double pass laser."
        )

        self.setattr_argument(
            "samples_per_freq",
            NumberValue(default=5, precision=0, step=1),
            tooltip="Number of samples to take for each frequency",
        )
        
        
        self.setattr_argument("enable_thresholding", BooleanValue(False))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=25, precision=0, step=1),
            tooltip="Threshold PMT counts",
        )
        
        self.setattr_argument(
            "optical_pumping_times",
            NumberValue(default=0, precision=0, step=1),
            tooltip="optical pumping times",
            group='Optical Pumping'
        )
        self.setattr_argument(
            "optical_pumping_pulse",
            NumberValue(default=5*us, min=1*us, max=1*ms, unit="us"),
            tooltip="optical pumping pulse length", group='Optical Pumping'
        )
        
        self.setattr_argument(
            "op_729_freq",
            NumberValue(default=241.73*MHz, min=220*MHz, max=250*MHz, unit="MHz",precision=6),
            tooltip="optimal 729 frequency", group='Optical Pumping'
        )

    @kernel
    def run(self):

        self.setup_run()

        # Create datasets
        num_freq_samples = len(self.scan_freq_729_dp.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_freq])
        
        # Dataset mainly for plotting
        self.experiment_data.set_list_dataset("pmt_counts_avg", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("frequencies_729_dp_MHz", num_freq_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg",
            x_data_name="frequencies_729_dp_MHz",
            pen=True,
        )

        self.core.break_realtime()

        # Set attenuations
        self.dds_397_dp.set_att(self.attenuation_397)
        self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
        self.dds_866_dp.set_att(self.attenuation_866)
        self.dds_729_dp.set_att(self.attenuation_729_dp)
        self.dds_729_sp.set_att(self.attenuation_729_sp)
        self.dds_854_dp.set_att(self.attenuation_854_dp)
        delay(1*ms)

        # Set frequencies
        self.dds_729_sp.set(self.frequency_729_sp)
        self.dds_854_dp.set(self.frequency_854_dp)
        delay(1*ms)
	
	
	
        freq_i = 0
        for freq_729_dp in self.scan_freq_729_dp.sequence: # scan the frequency

            self.dds_729_dp.set(freq_729_dp)

            total_thresh_count = 0
            total_pmt_counts = 0
            
            for sample_num in range(self.samples_per_freq): # repeat N times
                delay(500*us)
                self.dds_854_dp.set_att(30*dB)
                self.dds_729_dp.sw.off()
                self.dds_729_sp.sw.off()
                self.dds_397_dp.sw.off()
                self.dds_854_dp.sw.off()
                delay(1*ms)
                
                # Cool
                self.seq.doppler_cool.run()

                # Set 397 freq here for count collection, so less delay between
                # end of cooling and beginning of detection
                self.dds_397_dp.set(self.frequency_397_resonance)
                delay(10*us)

                # Attempt Rabi flop
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on() 

                delay(self.rabi_t)
                self.dds_729_dp.sw.off()
                #self.dds_729_sp.sw.off()

                # Collect counts
                
                # leave 866 at cooling frequency
                self.dds_397_dp.sw.on()
                self.dds_866_dp.sw.on()

                num_pmt_pulses = self.ttl_pmt_input.count(
                    self.ttl_pmt_input.gate_rising(self.misc_pmt_sampling_time)
                )
                delay(5*us)

                self.dds_397_dp.sw.off()
                self.dds_866_dp.sw.off()
                
                delay(5*us)

                # 854 repump
                self.dds_854_dp.set_att(self.attenuation_854_dp)
                self.dds_854_dp.sw.on()
                delay(self.repump_854_time)
                self.dds_854_dp.sw.off()
                self.dds_854_dp.set_att(30*dB)
                delay(10*us)

                # Update dataset
                self.experiment_data.insert_nd_dataset("pmt_counts",
                                            [freq_i, sample_num],
                                            num_pmt_pulses)
                                            
                #update the total count & thresolded events
                total_pmt_counts += num_pmt_pulses
                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count += 1

                delay(2*ms)
                
                #optical pumping
                self.dds_729_dp.set(self.op_729_freq)
                self.dds_729_dp.set_att(20*dB)
                for op_i in range(self.optical_pumping_times):
                	self.dds_729_dp.sw.on()
                	#self.dds_729_sp.sw.on()
                	delay(7*us)
                	self.dds_729_dp.sw.off()
                	delay(1*us)
                	self.dds_854_dp.sw.on()
                	self.dds_866_dp.sw.on()
                	
                	delay(self.optical_pumping_pulse)
                	
                	self.dds_854_dp.sw.off()
                	self.dds_866_dp.sw.off()
                	delay(1*us)
                delay(2*us)
                self.dds_729_dp.set(freq_729_dp)
                self.dds_729_dp.set_att(self.attenuation_729_dp)
                     
            
            self.experiment_data.append_list_dataset("frequencies_729_dp_MHz", freq_729_dp / MHz)
            if not self.enable_thresholding:
            	self.experiment_data.append_list_dataset("pmt_counts_avg",
                                          float(total_pmt_counts) / self.samples_per_freq)
            else:
            	self.experiment_data.append_list_dataset("pmt_counts_avg",
                                          float(total_thresh_count) / self.samples_per_freq)
            freq_i += 1
            delay(40*ms)
            self.dds_854_dp.sw.on()
            self.dds_397_far_detuned.sw.on()

