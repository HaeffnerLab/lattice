from acf.sequences_container import SequencesContainer
from acf_sequences.cooling.doppler import DopplerCool
from acf_sequences.misc.print_hi import PrintHi

sequences = SequencesContainer()

sequences.add_sequence("doppler_cool", DopplerCool())
sequences.add_sequence("print_hi", PrintHi())
