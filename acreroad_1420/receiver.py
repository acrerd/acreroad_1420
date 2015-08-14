"""
acreroad_1420 Receiver software

Software designed to receive signals through the 1420MHz telescope at Acre Road observatory.

Parameters
----------

serial : str
   The serial number of the ettus device being used.


"""

# The large number of imports required for GNURadio
import os
import sys
sys.path.append(os.environ.get('GRC_HIER_PATH', os.path.expanduser('~/.grc_gnuradio')))

from PyQt4 import Qt
from PyQt4.QtCore import QObject, pyqtSlot
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import qtgui
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from gnuradio.qtgui import Range, RangeWidget
from optparse import OptionParser
from specflatfile import specflatfile  # grc-generated hier_block
from srt_integrator import srt_integrator  # grc-generated hier_block
from ts_ave import ts_ave  # grc-generated hier_block
import spectroscopy
import sip
import time

# Parse config files
import ConfigParser

class Receiver():
    def __init__(self, ettus_id=None, \
                 source_gain = None, \
                 freq_0=None, \
                 freq_offset=None, \
                 samp_rate=None, \
                 eq_file=None
    ):
        # Access the configuration file
        # TODO Move this to a better location within the entire package.

        config = ConfigParser.SafeConfigParser()
        config.read('settings.cfg')

        if not ettus_id:
            ettus_id = config.get('receiver', 'ettus_id')
        if not source_gain:
            source_gain = float(config.get('receiver', 'source_gain'))
        if not freq_0:
            freq_0 = float(config.get('receiver', 'centre_freq'))
        if not freq_offset:
            freq_offset = float(config.get('receiver', 'freq_offset'))
        if not samp_rate:
            samp_rate = int(config.get('receiver', 'samp_rate'))
            self.samp_rate = samp_rate
        if not samp_rate:
            samp_rate = int(config.get('receiver', 'equalisation_file'))
        self.eq_file = eq_file

        # Initialise the RX stream from UHD
        self._init_rx_connection(ettus_id, samp_rate, freq_0, freq_offset, gain)    

        


    def _init_rx_connection(self, ettus_id, samp_rate=self.samp_rate, freq_0, freq_offset, gain):
        """
        Establish a recieving connection to an Ettus device uing the UHD protocol.

        Parameters
        ----------
        ettus_id : str
           The serial number of the ettus device
        samp_rate : int
           The sample rate desired from the reciever.
        freq_0 : float
           The desired centre frequency of the passband
        freq_offset : float
           The local oscillator offset, used to remove the peak produced by the LO.
        gain : float
           The desired gain from the receiver.
        """
            
        #
        # We need to set up a connection to the Ettus receiver
        #    
        self.rx_con = uhd.usrp_source(  	",".join(("serial="+ettus_id, "")),
                                            uhd.stream_args(
                                                cpu_format="fc32",
                                                channels=range(1),
                                            )
        )
        
        self.rx_con.set_samp_rate(samp_rate)
        self.rx_con.set_center_freq(uhd.tune_request(freq_0 , -freq_offset), 0)
        self.rx_con.set_gain(gain, 0)

    def save_spectral_power(self, filepath, fft_len=2048, int_time=5, samp_rate=self.samp_rate, eq_file=self.eq_file):
        """
        Save the integrated spectrum from the telescope at regular intervals to an ASCI file

        Parameters
        ----------
        filepath : str
           The path to the file where the results should be output.
        fft_len : int
           The number of bins which the spectrum should be made of (i.e. the length of the
           FFT transform.) Defaults to 2048.
        int_time : float
           The number of seconds over which each output sample is integrated. Defaults to 5 seconds.
        samp_rate : int
           The input sample rate of the data. This defaults to the sample rate of the ettus
           device, which should be fine for most (all?!) circumstances.
        eq_file : str
           The file containing the equalisation profile. This defaults to the the profile
           used in the rest of the module.
        """

        self.specflatfile = specflatfile(fft_len=2**11,fft_size=2**11,flat_file=eq_file,samp_rate=samp_rate)
        self.integrator = srt_integrator(fft_len=fft_len, int_time=int_time, reset_flag=0, samp_rate=samp_rate)
        self.blocks_keep_one_in_n = blocks.keep_one_in_n(gr.sizeof_float*fft_len, int_time*int(samp_rate/fft_len))
        self.blocks_null = blocks.null_sink(gr.sizeof_float*fft_len)
        self.asci_sink = spectroscopy.asci_sink(fft_len, filepath)
        

        self.connect((self.rx_con, 0), (self.specflatfile, 0))
        self.connect((self.specflatfile, 0), (self.integrator, 0))
        self.connect((self.integrator,0), (self.blocks_null, 0)) 
        self.connect((self.integrator, 1), (self.blocks_keep_one_in_n, 0))
        self.connect((self.blocks_keep_one_in_n, 0), (self.asci_sink, 0))
        

        
    