import math
import struct
from dataclasses import dataclass, field, fields

# Using dataclasses to create structured objects for parameters, similar to MATLAB structs.
# This makes attribute access clean (e.g., params.profileCfg.startFreq)

@dataclass
class ProfileCfg:
    startFreq: float = 0.0
    idleTime: list = field(default_factory=lambda: [0.0, 0.0])
    rampEndTime: float = 0.0
    freqSlopeConst: float = 0.0
    numAdcSamples: int = 0
    digOutSampleRate: float = 0.0

@dataclass
class DataPath:
    numTxAnt: int = 0
    numRxAnt: int = 0
    numChirpsPerFrame: int = 0
    numDopplerChirps: int = 0
    numDopplerBins: int = 0
    numRangeBins: int = 0
    numValidRangeBins: int = 0
    rangeResolutionMeters: float = 0.0
    rangeIdxToMeters: float = 0.0
    dopplerResolutionMps: float = 0.0

@dataclass
class FrameCfg:
    numLoops: int = 0
    chirpStartIdx: int = 0
    chirpEndIdx: int = 0
    framePeriodicity: float = 0.0

# Main parameter class
@dataclass
class RadarParams:
    profileCfg: ProfileCfg = field(default_factory=ProfileCfg)
    dataPath: DataPath = field(default_factory=DataPath)
    frameCfg: FrameCfg = field(default_factory=FrameCfg)
    channelCfg: dict = field(default_factory=dict)
    chirpComnCfg: dict = field(default_factory=dict)
    chirpTimingCfg: dict = field(default_factory=dict)
    trackingCfg: list = field(default_factory=list)
    guiMonitor: dict = field(default_factory=dict)
    sensorPosition: dict = field(default_factory=dict)
    boundaryBox: list = field(default_factory=list)

def read_cfg(filename):
    """
    Reads a text-based radar configuration file line by line.

    Args:
        filename (str): The full path to the .cfg file.

    Returns:
        list: A list where each element is one line (command) from the file.
    """
    config = []
    try:
        with open(filename, 'r') as f:
            print(f'--- Opening configuration file {filename} ... ---')
            for line in f:
                # Ignore comments and empty lines
                if line.strip() and not line.strip().startswith('%'):
                    config.append(line.strip())
    except FileNotFoundError:
        print(f'ERROR: File {filename} not found!')
        return []
    return config

def parse_cfg(cli_cfg):
    """
    Parses the list of config commands into a structured RadarParams object.
    It also calculates many derived radar parameters needed for processing.

    Args:
        cli_cfg (list): A list of configuration command strings.

    Returns:
        RadarParams: A dataclass object containing all radar parameters.
    """
    params = RadarParams()
    
    for line in cli_cfg:
        parts = line.split()
        command = parts[0]
        
        if command == 'channelCfg':
            params.channelCfg['rxChannelEn'] = int(parts[1])
            params.channelCfg['txChannelEn'] = int(parts[2])
            params.dataPath.numRxAnt = bin(params.channelCfg['rxChannelEn']).count('1')
            params.dataPath.numTxAnt = bin(params.channelCfg['txChannelEn']).count('1')
        
        elif command == 'chirpComnCfg':
            params.chirpComnCfg['digOutputSampRate'] = 100 / float(parts[1]) # in MHz
            params.chirpComnCfg['numAdcSamples'] = int(parts[4])
            params.chirpComnCfg['chirpRampEndTime'] = float(parts[6]) # in us

        elif command == 'chirpTimingCfg':
            params.chirpTimingCfg['idleTime'] = float(parts[1]) # in us
            params.chirpTimingCfg['chirpSlope'] = float(parts[4]) # in MHz/us
            params.chirpTimingCfg['startFreq'] = float(parts[5]) # in GHz

        elif command == 'frameCfg':
            chirp_start_idx = int(parts[1])
            chirp_end_idx = int(parts[2])
            num_loops = int(parts[3])
            params.frameCfg.numLoops = num_loops
            params.frameCfg.chirpStartIdx = chirp_start_idx
            params.frameCfg.chirpEndIdx = chirp_end_idx
            params.frameCfg.framePeriodicity = float(parts[5]) # in ms
            
        elif command == 'guiMonitor':
            params.guiMonitor['pointCloud'] = int(parts[1])
            params.guiMonitor['rangeProfileMask'] = int(parts[2])
            params.guiMonitor['heatMapMask'] = int(parts[4])
            params.guiMonitor['statsInfo'] = int(parts[6])
        
        elif command == 'trackingCfg':
            # Example: trackingCfg 1 2 100 16 400 50 50
            params.trackingCfg = [float(p) for p in parts[1:]]

        elif command == 'boundaryBox':
            # Example: boundaryBox -20 20 0 120
            params.boundaryBox = [float(p) for p in parts[1:]]
        
        elif command == 'sensorPosition':
            params.sensorPosition['xOffset'] = float(parts[1])
            params.sensorPosition['yOffset'] = float(parts[2])
            params.sensorPosition['zOffset'] = float(parts[3])
            params.sensorPosition['azimuthTilt'] = float(parts[4])
            params.sensorPosition['elevationTilt'] = float(parts[5])

    # --- Derived Parameter Calculations ---
    
    # Profile Config
    params.profileCfg.startFreq = params.chirpTimingCfg['startFreq']
    params.profileCfg.idleTime = [params.chirpTimingCfg['idleTime'], params.chirpTimingCfg['idleTime']]
    params.profileCfg.rampEndTime = params.chirpComnCfg['chirpRampEndTime']
    params.profileCfg.freqSlopeConst = params.chirpTimingCfg['chirpSlope']
    params.profileCfg.numAdcSamples = params.chirpComnCfg['numAdcSamples']
    params.profileCfg.digOutSampleRate = 1000 * params.chirpComnCfg['digOutputSampRate']
    
    # Data Path
    params.dataPath.numChirpsPerFrame = (params.frameCfg.chirpEndIdx - params.frameCfg.chirpStartIdx + 1) * params.frameCfg.numLoops
    params.dataPath.numDopplerChirps = params.dataPath.numChirpsPerFrame / params.dataPath.numTxAnt
    params.dataPath.numDopplerBins = 1 << (params.dataPath.numDopplerChirps - 1).bit_length() # pow2roundup
    params.dataPath.numRangeBins = 1 << (params.profileCfg.numAdcSamples - 1).bit_length() # pow2roundup
    params.dataPath.numValidRangeBins = params.dataPath.numRangeBins // 2

    # Range Resolution
    params.dataPath.rangeResolutionMeters = (3e8 * params.profileCfg.digOutSampleRate * 1e3) / \
                                            (2 * abs(params.profileCfg.freqSlopeConst) * 1e12 * params.profileCfg.numAdcSamples)
    
    # Doppler Resolution
    c = 3e8
    start_freq_hz = params.profileCfg.startFreq * 1e9
    wavelength_m = c / start_freq_hz
    chirp_time_s = (params.profileCfg.idleTime[0] + params.profileCfg.rampEndTime) * 1e-6
    
    params.dataPath.dopplerResolutionMps = wavelength_m / (2 * params.dataPath.numDopplerChirps * chirp_time_s * params.dataPath.numTxAnt)

    return params


def get_byte_length_from_struct(struct_def):
    """
    Calculates the total byte length of a structure definition template.
    Args:
        struct_def (dict): A dict where each key is a field name and each value is a
                           tuple of ('format_char', num_bytes).
    Returns:
        int: The total number of bytes.
    """

    return sum(item[1] for item in struct_def.values())

def read_to_struct(byte_array, struct_def):
    """
    Converts a raw byte array into a Python dictionary using a template.
    This is the Python equivalent of readToStruct using the `struct` module.

    Args:
        byte_array (bytes): The raw byte data.
        struct_def (dict): The structure definition template.
    
    Returns:
        dict: A dictionary populated with the parsed data.
    """
    result = {}
    offset = 0
    # Create the format string for the entire struct
    # Note: Assumes little-endian ('<') format, which is common for sensors.
    format_string = '<' + ''.join(item[0] for item in struct_def.values())
    
    try:
        unpacked_data = struct.unpack(format_string, byte_array)
        
        i = 0
        for field_name in struct_def.keys():
            result[field_name] = unpacked_data[i]
            i += 1
            
    except struct.error as e:
        print(f"ERROR: Failed to unpack byte array. Struct definition might not match data length. {e}")
        return None
        
    return result