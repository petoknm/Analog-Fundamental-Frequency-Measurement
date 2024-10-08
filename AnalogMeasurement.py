import numpy as np

from saleae.range_measurements import AnalogMeasurer

# code originally from endolith, https://gist.github.com/endolith/255291
def freq_from_autocorr(sig, fs):
    """
    Estimate frequency using autocorrelation
    """
    # Remove DC component
    sig -= np.mean(sig)
    
    # Calculate autocorrelation and throw away the negative lags
    corr = np.correlate(sig, sig, mode='full')
    corr = corr[len(corr)//2:]

    # Find the first low point
    d = np.diff(corr)
    non_zero = np.nonzero(d > 0)
    if len(non_zero) == 0 or len(non_zero[0]) == 0:
        return 0
    start = non_zero[0][0]

    # Find the next peak after the low point (other than 0 lag).  This bit is
    # not reliable for long signals, due to the desired peak occurring between
    # samples, and other peaks appearing higher.
    # Should use a weighting function to de-emphasize the peaks at longer lags.
    peak = np.argmax(corr[start:]) + start

    return fs / peak


class MyAnalogMeasurer(AnalogMeasurer):
    supported_measurements = ['fundamental']
    all_samples = None
    sample_rate = None

    # Initialize your measurement extension here
    # Each measurement object will only be used once, so feel free to do all per-measurement initialization here
    def __init__(self, requested_measurements):
        super().__init__(requested_measurements)

    # This method will be called one or more times per measurement with batches of data
    # data has the following interface
    #   * Iterate over to get Voltage values, one per sample
    #   * `data.samples` is a numpy array of float32 voltages, one for each sample
    #   * `data.sample_count` is the number of samples (same value as `len(data.samples)` but more efficient if you don't need a numpy array)
    def process_data(self, data):
        if self.sample_rate is None:
            delta = data.end_time - data.start_time
            sample_delta = float(delta) / data.sample_count
            self.sample_rate = 1.0 / sample_delta
        if self.all_samples is None:
            self.all_samples = data.samples
            return
        self.all_samples = np.concatenate((self.all_samples, data.samples))

    # This method is called after all the relevant data has been passed to `process_data`
    # It returns a dictionary of the request_measurements values
    def measure(self):
        f = freq_from_autocorr(self.all_samples, self.sample_rate)
        values = {'fundamental': f}
        return values
