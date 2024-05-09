from acf.experiment import ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *


class RabiTimeScannThresholded_withOP(ACFExperiment):

    def build(self):
        
        self.setup(sequences)
        
        self.add_arg_from_param("frequency/397_resonance")
        self.add_arg_from_param("frequency/397_cooling")
        self.add_arg_from_param("frequency/397_far_detuned")
        self.add_arg_from_param("frequency/866_cooling")
        #self.add_arg_from_param("frequency/729_dp")
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
            "scan_rabi_t",
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
            tooltip="Scan parameter for sweeping the 729 double pass on time."
        )


        self.setattr_argument(
            "repump_854_time",
            NumberValue(default=100*us, min=5*us, max=1*ms, unit="us"),
            tooltip="Time to run 854 repump",
        )
	
        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=233.48*MHz, min=200*MHz, max=250*MHz, unit="MHz", ndecimals=3),
            tooltip="729 double pass frequency",
        )


        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=25, ndecimals=0, step=1),
            tooltip="Number of samples to take for each time",
        )

        self.setattr_argument(
            "OP_cycle",
            NumberValue(default=20, ndecimals=0, step=1),
            tooltip="Threshold PMT counts",
        )


        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=25, ndecimals=0, step=1),
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

        #axialmodes = np.array([0.089,0.153,0.214,0.272,0.326,0.380,0.432,0.482,0.532])
        sbc_freq = (239.74)
        freq_offset = (0.26)
        op_freq = (241.753)

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
        self.dds_729_dp.set(self.freq_729_dp)
        self.dds_854_dp.set(self.frequency_854_dp)
        delay(1*ms)

        time_i = 0

        for rabi_t in self.scan_rabi_t.sequence: # scan the frequency
            total_thresh_count = 0
            total_pmt_counts = 0
            for sample_num in range(self.samples_per_time): # repeat N times
                
                #  Cool
                self.seq.doppler_cool.run()

                # Set 397 freq here for count collection, so less delay between
                # end of cooling and beginning of detection
                
                self.dds_397_dp.set(self.frequency_397_resonance)
                delay(10*us)

                #OP
                self.dds_729_dp.set(241.91*MHz)
                self.dds_729_dp.set(op_freq*MHz)
                self.dds_729_dp.set_att(15*dB)
                self.dds_854_dp.set_att(3*dB)
                
                #state prep S 1/2,1/2->D 5/2,-3/2 + repump
                for OP_num in range(self.OP_cycle):
                    self.dds_729_dp.sw.on()
                    self.dds_729_sp.sw.on()
                    delay(5*us)
                    self.dds_729_dp.sw.off()
                    self.dds_854_dp.sw.on()
                    delay(5*us)
                    self.dds_854_dp.sw.off()
			
		# ground state cooling S 1/2,-1/2->D 5/2,-5/2 + repump
                for GSC in range(30):
                    self.dds_729_dp.set((sbc_freq+freq_offset*2)*MHz)
                    self.dds_729_dp.set_att(15*dB)
                    self.dds_729_dp.sw.on()
                    self.dds_729_sp.sw.on()
                    delay(7*us)
                    self.dds_729_dp.sw.off()
                    self.dds_854_dp.sw.on()
                    self.dds_866_dp.sw.on()
                    delay(5*us)
                    self.dds_854_dp.sw.off()
                    self.dds_866_dp.sw.off()
                    
                                  # OP on resonant
                self.dds_729_dp.set(op_freq*MHz)
                self.dds_729_dp.set_att(18*dB)

                for OP_num in range(20):
            
                    self.dds_729_dp.sw.on()
                    self.dds_729_sp.sw.on()
                    delay(7*us)
                    self.dds_729_dp.sw.off()
                    self.dds_854_dp.sw.on()
                    self.dds_866_dp.sw.on()
                    delay(4*us)
                    self.dds_854_dp.sw.off()
                    self.dds_866_dp.sw.off()




                for GSC in range(50):
                    self.dds_729_dp.set((sbc_freq+freq_offset)*MHz)
                    self.dds_729_dp.set_att(20*dB)
                    self.dds_729_dp.sw.on()
                    self.dds_729_sp.sw.on()
                    delay(12*us)
                    self.dds_729_dp.sw.off()
                    self.dds_854_dp.sw.on()
                    self.dds_866_dp.sw.on()
                    delay(5*us)
                    self.dds_854_dp.sw.off()
                    self.dds_866_dp.sw.off()
                    
                                  # OP on resonant
                self.dds_729_dp.set(op_freq*MHz)
                self.dds_729_dp.set_att(18*dB)

                for OP_num in range(30):
            
                    self.dds_729_dp.sw.on()
                    self.dds_729_sp.sw.on()
                    delay(7*us)
                    self.dds_729_dp.sw.off()
                    self.dds_854_dp.sw.on()
                    self.dds_866_dp.sw.on()
                    delay(4*us)
                    self.dds_854_dp.sw.off()
                    self.dds_866_dp.sw.off()


                for GSC in range(30):
                    self.dds_729_dp.set((sbc_freq+freq_offset*2)*MHz)
                    self.dds_729_dp.set_att(15*dB)
                    self.dds_729_dp.sw.on()
                    self.dds_729_sp.sw.on()
                    delay(7*us)
                    self.dds_729_dp.sw.off()
                    self.dds_854_dp.sw.on()
                    self.dds_866_dp.sw.on()
                    delay(5*us)
                    self.dds_854_dp.sw.off()
                    self.dds_866_dp.sw.off()
                    
                                  # OP on resonant
                self.dds_729_dp.set(op_freq*MHz)
                self.dds_729_dp.set_att(18*dB)

                for OP_num in range(20):
            
                    self.dds_729_dp.sw.on()
                    self.dds_729_sp.sw.on()
                    delay(7*us)
                    self.dds_729_dp.sw.off()
                    self.dds_854_dp.sw.on()
                    self.dds_866_dp.sw.on()
                    delay(4*us)
                    self.dds_854_dp.sw.off()
                    self.dds_866_dp.sw.off()
                for GSC in range(30):
                    self.dds_729_dp.set((sbc_freq+freq_offset*2)*MHz)
                    self.dds_729_dp.set_att(15*dB)
                    self.dds_729_dp.sw.on()
                    self.dds_729_sp.sw.on()
                    delay(7*us)
                    self.dds_729_dp.sw.off()
                    self.dds_854_dp.sw.on()
                    self.dds_866_dp.sw.on()
                    delay(5*us)
                    self.dds_854_dp.sw.off()
                    self.dds_866_dp.sw.off()
                    
                                  # OP on resonant
                self.dds_729_dp.set(op_freq*MHz)
                self.dds_729_dp.set_att(18*dB)

                for OP_num in range(20):
            
                    self.dds_729_dp.sw.on()
                    self.dds_729_sp.sw.on()
                    delay(7*us)
                    self.dds_729_dp.sw.off()
                    self.dds_854_dp.sw.on()
                    self.dds_866_dp.sw.on()
                    delay(4*us)
                    self.dds_854_dp.sw.off()
                    self.dds_866_dp.sw.off()


                for Iterate in range(5):
                    for GSC in range(30):
                        self.dds_729_dp.set((sbc_freq+freq_offset)*MHz)
                        self.dds_729_dp.set_att(20*dB)
                        self.dds_729_dp.sw.on()
                        self.dds_729_sp.sw.on()
                        delay(12*us)
                        self.dds_729_dp.sw.off()
                        self.dds_854_dp.sw.on()
                        self.dds_866_dp.sw.on()
                        delay(5*us)
                        self.dds_854_dp.sw.off()
                        self.dds_866_dp.sw.off()
                    
                                  # OP on resonant
                    self.dds_729_dp.set(op_freq*MHz)
                    self.dds_729_dp.set_att(18*dB)

                    for OP_num in range(8):
                
                        self.dds_729_dp.sw.on()
                        self.dds_729_sp.sw.on()
                        delay(7*us)
                        self.dds_729_dp.sw.off()
                        self.dds_854_dp.sw.on()
                        self.dds_866_dp.sw.on()
                        delay(4*us)
                        self.dds_854_dp.sw.off()
                        self.dds_866_dp.sw.off()

                for OP_num in range(10):
                
                        self.dds_729_dp.sw.on()
                        self.dds_729_sp.sw.on()
                        delay(7*us)
                        self.dds_729_dp.sw.off()
                        self.dds_854_dp.sw.on()
                        self.dds_866_dp.sw.on()
                        delay(4*us)
                        self.dds_854_dp.sw.off()
                        self.dds_866_dp.sw.off()


                self.dds_854_dp.sw.on()

                #self.ttl_awg_trigger.pulse(1*us)
                #delay(500*us)

                self.dds_854_dp.sw.off()

                # Attempt Rabi flop
                self.dds_729_dp.set(self.freq_729_dp)
                self.dds_729_dp.set_att(self.attenuation_729_dp)
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

                #total_pmt_counts += num_pmt_pulses

                delay(3*ms)
            
            self.experiment_data.append_list_dataset("rabi_t", rabi_t / us)
            self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_time)
            #self.data.append_list_dataset("pmt_counts_avg_thresholded",
            #                              float(total_pmt_counts) / self.samples_per_time)
            time_i += 1
            delay(30*ms)

        self.dds_729_dp.sw.off()
        self.dds_729_sp.sw.off()
        self.dds_854_dp.set_att(10*dB)
        self.dds_854_dp.sw.on()

        self.dds_397_dp.set(self.frequency_397_cooling)
        self.dds_397_dp.sw.on()
        self.dds_397_far_detuned.sw.on()
        self.dds_866_dp.sw.on()
            
