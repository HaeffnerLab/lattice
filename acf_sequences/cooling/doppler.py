from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz

class DopplerCool(Sequence):

    def __init__(self):
        super().__init__()

        self.add_parameter("frequency/397_cooling")
        self.add_parameter("frequency/866_cooling")
        self.add_parameter("frequency/397_far_detuned")
        self.add_parameter("attenuation/397")
        self.add_parameter("doppler_cooling/cooling_time")

        self.add_argument("interesting_arg", NumberValue(default=5*MHz, unit="MHz"))

    @kernel
    def run(self):
        self.sequence(self.frequency_397_cooling,
                      self.frequency_866_cooling,
                      self.frequency_397_far_detuned,
                      self.attenuation_397,
                      self.doppler_cooling_cooling_time)

    @kernel
    def sequence(self, freq_397_cooling,
                       freq_866_cooling,
                       freq_397_far_detuned,
                       attenuation_397,
                       doppler_cooling_time):

        self.dds_397_dp.set(freq_397_cooling)
        self.dds_397_far_detuned.set(freq_397_far_detuned)
        self.dds_866_dp.set(freq_866_cooling)
        
        self.dds_397_dp.sw.on()
        self.dds_397_far_detuned.sw.on()
        self.dds_866_dp.sw.on()
        print("My favorite number is:")
        print(self.interesting_arg)
        print("397 freq is:")
        print(self.frequency_397_cooling)
        
        delay(doppler_cooling_time * 0.6)
        
        self.dds_397_far_detuned.sw.off()
        
        delay(doppler_cooling_time * 0.2)

        self.dds_397_dp.set_att(15*dB)

        delay(doppler_cooling_time * 0.1)


        self.dds_397_dp.set_att(18*dB)

        delay(doppler_cooling_time * 0.1)
        
        self.dds_397_dp.set_att(attenuation_397)

        # self.dds_397_far_detuned.off()
        self.dds_397_dp.sw.off()
        delay(20*us)
        self.dds_866_dp.sw.off()

