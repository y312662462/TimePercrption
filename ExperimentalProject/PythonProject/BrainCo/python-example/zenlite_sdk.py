import abc
import os
import platform
import sys
from enum import IntEnum  # Enum declarations
from zen_logger import logwrap, ZLOG

from cffi import FFI

ffi = FFI()

# Defining SDK constants
_DEFAULT_DEVICE_SCAN_INTERVAL = 5  # Seconds
_ENABLE_SOCIAL_ENGAGEMENT = True


def load_library():
    lib_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "libzenlite")

    # 1. load header
    with open(os.path.join(lib_dir, "zenlite_sdk.h"), encoding='utf-8') as sdk_header:
        sdk_header = sdk_header.read() \
            .split("//CFFI_DEF_START")[1] \
            .split("//CFFI_DEF_END")[0] \
            .replace("SDK_EXTERN ", "") \
            .replace("#if defined(_WIN32) || TARGET_OS_OSX", "") \
            .replace("#endif", "")
        ffi.cdef(sdk_header)

    # 2. find library path and load
    arch = platform.architecture()[0]
    if platform.system() == "Darwin":
        return ffi.dlopen(os.path.join(lib_dir, "mac", "libzenlite.dylib"))

    elif platform.system() == "Windows" and arch == "64bit":
        # add path 'python/libzenlite/' to environment variable 'PATH' to load the dependent DLLs.
        os.environ["PATH"] += os.pathsep + os.path.join(lib_dir, "win")
        return ffi.dlopen(os.path.join(lib_dir, "win", "zenlite.dll"))
    else:
        raise Exception("Unsupported platform: " + platform.system() + ", arch: " + arch)


# load ZenLiteSDK library
libzenlite = load_library()


def get_sdk_version():
    return ffi.string(libzenlite.zl_get_sdk_version()).decode("utf-8")


class ZenLiteDeviceListener(abc.ABC):

    def on_device_info_ready(self, device_info):
        pass  # print("on_device_info_ready not implemented")

    def on_eeg_data(self, eeg_data):
        pass  # print("on_eeg_data not implemented")

    def on_imu_data(self, imu_data):
        pass  # print("on_imu_data not implemented")

    def on_ppg_data(self, ppg_data):
        pass  # print("on_ppg_data not implemented")

    def on_brain_wave(self, brain_wave):
        pass  # print("on_brain_wave not implemented")

    def on_error(self, error):
        pass  # print("on_error not implemented: %i" % error.code)

    def on_connectivity_change(self, connectivity):
        pass  # print("on_connection_change not implemented: %s" % connection_state.name)

    def on_contact_state_change(self, contact_state):
        pass  # print("on_contact_state_change not implemented: %s" % contact_state.name)

    def on_orientation_change(self, orientation):
        pass  # print("on_orientation_change not implemented: %s" % orientation.name)

    def on_event(self, event):
        pass  # print("on_event not implemented")

    def on_stress(self, stress):
        pass  # print("on_stress not implemented")

    def on_meditation(self, meditation):
        pass  # print("on_meditation not implemented")

    def on_sleep_stage(self, stage, conf, drowsiness):
        pass  # print("on_sleep_stage not implemented")

    def on_blink(self):
        pass  # print("on_blink not implemented")

    def on_event(self, event):
        pass  # print("on_event not implemented")

    def on_sleep_report(self, pose):
        pass  # print("on_sleep_report not implemented")

    # def fatal_error(msg):
    #     print("FATAL_ERROR:" + msg)
    #     sys.exit(1)


class EEGContactState(IntEnum):
    unknown = 0
    off = 1
    on = 2


class PPGContactState(IntEnum):
    unknown = 0
    off_skin = 1
    on_some_object = 2
    on_skin = 3


class ContactState(IntEnum):
    unknown = 0
    off = 1
    eeg = 2
    all = 3


class Orientation(IntEnum):
    unknown = 0
    upward = 1
    downward = 2


class Connectivity(IntEnum):
    connecting = 0
    connected = 1
    disconnecting = 2
    disconnected = 3


class ZLEvent(IntEnum):
    none = 0
    fall_asleep = 1
    wakeup = 2
    blink = 3


class SleepStage(IntEnum):
    unknown = -1
    awake = 0
    rem = 1
    light = 2
    deep = 3


class ImuPoseHead(IntEnum):
    unknown = 0
    left = 1
    right = 2
    face_up = 3
    face_down = 4


class ImuPoseBody(IntEnum):
    unknown = 0
    back = 1
    seated = 2
    forward = 3
    stomach = 4

class RespiratoryState(IntEnum):
    rest = 0
    rinward = 1
    outward = 2

class ZenLiteCommand(IntEnum):
    """
    Definition of 11 commands compatible in index with original in zenlite_protobuf

    Implementation of 14 commands in https://github.com/BrainCoTech/zenlite_protobuf/blob/main/proto/zenlite_common.proto
      SYSCFG_NONE               = 0;
      PAIR                      = 1;   // Used when device is in pairing mode
      VALIDATE_PAIR_INFO        = 2;   // Should be sent right after connection established
      START                     = 3;
      STOP                      = 4;
      SHUT_DOWN                 = 5;
      ENTER_OTA                 = 6;
      RESTORE_FACTORY_SETTINGS  = 7;
      SET_DEVICE_NAME           = 8;
      SET_SLEEP_IDLE_TIME       = 9;
      GET_SYSTEM_MONITOR        = 10;
      UPDATE_FILE_REQ           = 11;  // update ppg firmware data request
      UPDATE_TRANS_FRAME        = 12;
      UPDATE_TRANS_COMPLT       = 13;
    """
    none = 0
    pair = 1  # implemented
    check_pairing_status = 2  # implemented
    start_data_stream = 3  # implemented
    stop_data_stream = 4
    shutdown = 5
    enter_ota = 6
    reset = 7
    set_device_name = 8
    set_sleep_idle_time = 9
    get_system_info = 10


class EEGSampleRate(IntEnum):
    none = 0
    off = 1
    sr128 = 2
    sr256 = 3


class IMUSampleRate(IntEnum):
    none = 0
    off = 1
    sr25 = 2
    sr50 = 3
    sr100 = 4
    sr200 = 5
    sr400 = 6
    sr800 = 7


class IMUMode(IntEnum):
    none = 0
    acc = 1
    gyro = 2
    acc_gyro = 3
    euler = 4


class PPGReportRate(IntEnum):
    none = 0
    off = 1
    sr1 = 2
    sr5 = 3
    sr25 = 4
    sr50 = 5
    sr100 = 6


class PPGMode(IntEnum):
    none = 0
    raw_data = 1
    algo = 2
    spo2 = 3
    hr = 4
    hrv = 5


class ZenLitePpgRawSetReg(IntEnum):
    reg = 0
    value = 1


class AFEConfigError(IntEnum):
    none = 0
    unknown = 1
    afe_config_error = 2


class AFEConfigResponse:
    error = AFEConfigError.none

    def __init__(self, error):
        self.error = error

    def success(self):
        return self.error == AFEConfigError.none


class IMUConfigError(IntEnum):
    none = 0
    unknown = 1
    acc_config_error = 2
    gyro_config_error = 3


class IMUConfigResponse:
    error = IMUConfigError.none

    def __init__(self, error):
        self.error = error

    def success(self):
        return self.error == IMUConfigError.none


class SysConfigError(IntEnum):
    none = 0
    unknown = 1
    ota_failed_low_power = 2
    # Pairing related errors
    pair_error = 3
    validate_pair_info = 4
    allow_update = 5
    recv_ok = 6
    update_complete = 7


class SysConfigResponse:
    command = ZenLiteCommand.none
    error = SysConfigError.none

    def __init__(self, command, error):
        self.command = command
        self.error = error

    def success(self):
        return self.error == SysConfigError.none


class HardwareError(IntEnum):
    none = 0
    unknown = 1
    eeg_err = 2
    imu_err = 3
    mag_err = 4
    abnormal_battery_voltage = 5


class ZLErrorCode(IntEnum):
    none = 0
    unknown = -1
    invalid_params = -2
    invalid_data = -3
    bleDeviceUnreachable = -128
    bleDisabled = -129
    bleUnavailable = -130
    bleDataWriteFailure = -131
    device_not_connected = -160
    device_uuid_unavailable = -196
    # ZenLite error codes
    zenlite_eeg_init = -1002
    zenlite_imu_init = -1003
    zenlite_ppg_init = -1004
    zenlite_battery_voltage = -1005
    zenlite_battery_temperature = -1006
    zenlite_hardware_version = -1007
    zenlite_flash_init = -1008
    zenlite_ble_init = -1009


# Wrapper objects
class ZLError:
    code = None
    message = None

    def __init__(self, code):
        self.code = code
        c_msg = libzenlite.zl_err_code_to_msg(code)
        self.message = ffi.string(c_msg).decode("utf-8")


class DeviceInfo:
    manufacturer_name = None
    model_number = None
    serial_number = None
    hardware_revision = None
    firmware_revision = None

    def __init__(self, c_info):
        self.manufacturer_name = ffi.string(c_info.manufacturer, 16).decode("utf-8")
        self.model_number = ffi.string(c_info.model, 16).decode("utf-8")
        self.serial_number = ffi.string(c_info.serial, 16).decode("utf-8")
        self.hardware_revision = ffi.string(c_info.hardware, 16).decode("utf-8")
        self.firmware_revision = ffi.string(c_info.firmware, 16).decode("utf-8")


class EEGData:
    sequence_num = None
    sample_rate = None
    eeg_data = None

    def __init__(self, c_data):
        self.sequence_num = c_data.sequence_num
        self.sample_rate = c_data.sample_rate
        self.eeg_data = ffi.unpack(c_data.eeg_data, c_data.eeg_size)


class PPGAlgoData:
    hr = None
    hr_conf = None
    rr = None
    rr_conf = None
    activity = None
    spo2 = None
    spo2_r = None
    spo2_conf = None
    spo2_progress = None
    spo2_lsq_flag = None
    spo2_mt_flag = None
    spo2_lp_flag = None
    spo2_ur_flag = None
    spo2_state = None
    hrv = None
    hrv_stress = None
    stress = None
    contact_state = None

    def __init__(self, c_data):
        self.hr = c_data.hr
        self.hr_conf = c_data.hr_conf
        self.rr = c_data.rr
        self.rr_conf = c_data.rr_conf
        self.activity = c_data.activity
        self.spo2 = c_data.spo2
        self.spo2_conf = c_data.spo2_conf
        self.spo2_r = c_data.spo2_r
        self.spo2_progress = c_data.spo2_progress
        # self.spo2_lsq_flag = c_data.spo2_lsq_flag
        # self.spo2_mt_flag = c_data.spo2_mt_flag
        # self.spo2_lp_flag = c_data.spo2_lp_flag
        # self.spo2_ur_flag = c_data.spo2_ur_flag
        self.spo2_state = c_data.spo2_state
        self.hrv = c_data.hrv
        self.hrv_stress = c_data.hrv_stress
        self.stress = c_data.stress
        self.contact_state = PPGContactState(c_data.contact_state)

    def __str__(self):
        return "contact_state=%s, hr=%s, hr_conf=%s, rr=%s, rr_conf=%s, spo2=%s, spo2_conf=%s, spo2_state=%s" % (self.contact_state, self.hr, self.hr_conf, self.rr, self.rr_conf, self.spo2, self.spo2_conf, self.spo2_state)


class PPGRawData:
    green1_count = None
    green2_count = None
    ir_count = None
    red_count = None

    def __init__(self, c_data):
        self.green1_count = c_data.green1_count
        self.green2_count = c_data.green2_count
        self.ir_count = c_data.ir_count
        self.red_count = c_data.red_count

    def __str__(self):
        return "green1=%s green2=%s ir=%s, red=%d" % (self.green1_count, self.green2_count, self.ir_count, self.red_count)


class PPGData:
    sequence_num = None
    sample_rate = None
    raw_data = None
    algo_data = None
    respiratory_rate = None
    respiratory_curve = None
    respiratory_state = None

    def __init__(self, c_data):
        self.sequence_num = c_data.sequence_num
        self.sample_rate = c_data.report_rate

        if c_data.raw_data != ffi.NULL and c_data.raw_data_size > 0:
            raw_data = ffi.unpack(c_data.raw_data, c_data.raw_data_size)
            self.raw_data = []  # * c_data.raw_data_size
            for i in range(0, c_data.raw_data_size):
                self.raw_data.append(PPGRawData(raw_data[i]))
            if c_data.respiratory_curve != ffi.NULL and c_data.respiratory_curve_size > 0:
                self.respiratory_curve = ffi.unpack(c_data.respiratory_curve, c_data.respiratory_curve_size)
                self.respiratory_rate = c_data.respiratory_rate
                self.respiratory_state = RespiratoryState(c_data.respiratory_state)
                
        if c_data.algo_data != ffi.NULL and c_data.algo_data_size > 0:
            algo_data = ffi.unpack(c_data.algo_data, c_data.algo_data_size)
            self.algo_data = []
            for i in range(0, c_data.algo_data_size):
                self.algo_data.append(PPGAlgoData(algo_data[i]))
        
    def __str__(self):
        if self.raw_data is not None:
            return "seq_num=%s raw_data=%s" % (self.sequence_num, self.raw_data[0])
        if self.algo_data is not None:
            return "seq_num=%s raw_data=%s" % (self.sequence_num, self.algo_data[0])


class ACCData:
    sequence_num = None
    x = None
    y = None
    z = None

    def __init__(self, c_data):
        self.sequence_num = c_data.sequence_num
        points = ffi.unpack(c_data.data, c_data.size)
        self.x = [0.0] * c_data.size
        self.y = [0.0] * c_data.size
        self.z = [0.0] * c_data.size
        for i in range(0, c_data.size):
            self.x[i] = points[i].x
            self.y[i] = points[i].y
            self.z[i] = points[i].z

    def __str__(self):
        return "sn=%s, x=%s, y=%s, z=%s" % (self.sequence_num, self.x, self.y, self.z)


class GyroData:
    sequence_num = None
    x = None
    y = None
    z = None

    def __init__(self, c_data):
        self.sequence_num = c_data.sequence_num
        points = ffi.unpack(c_data.data, c_data.size)

        self.x = [0.0] * c_data.size
        self.y = [0.0] * c_data.size
        self.z = [0.0] * c_data.size
        for i in range(0, c_data.size):
            self.x[i] = points[i].x
            self.y[i] = points[i].y
            self.z[i] = points[i].z


class EulerAngleData:
    yaw = None
    pitch = None
    roll = None

    def __init__(self, c_data):
        self.yaw = ffi.unpack(c_data.yaw, c_data.size)
        self.pitch = ffi.unpack(c_data.pitch, c_data.size)
        self.roll = ffi.unpack(c_data.roll, c_data.size)


class IMUData:
    acc_data = None
    gyro_data = None
    euler_angle_data = None
    sample_rate = None
    head = None
    body = None

    def __init__(self, c_data):
        self.sample_rate = c_data.sample_rate
        self.head = ImuPoseHead(c_data.head)
        self.body = ImuPoseBody(c_data.body)

        if c_data.acc_data != ffi.NULL:
            self.acc_data = ACCData(c_data.acc_data)

        if c_data.gyro_data != ffi.NULL:
            self.gyro_data = GyroData(c_data.gyro_data)

        if c_data.euler_angle_data != ffi.NULL:
            self.euler_angle_data = EulerAngleData(c_data.euler_angle_data)


class SleepReport:
    beginTime = None
    endTime = None
    fallAsleepTime = None

    def __init__(self, c_data):
        if c_data != ffi.NULL:
            self.beginTime = c_data.beginTime
            self.endTime = c_data.endTime
            self.fallAsleepTime = c_data.fallAsleepTime


class SysInfoData:
    firmware_info = None
    hardware_errors = None

    def __init__(self, firmware_info, hardware_errs):
        self.firmware_info = firmware_info
        self.hardware_errors = hardware_errs


class BrainWave:
    delta = 0
    theta = 0
    alpha = 0
    low_beta = 0
    high_beta = 0
    gamma = 0

    def __init__(self, c_stats):
        self.delta = c_stats.delta
        self.theta = c_stats.theta
        self.alpha = c_stats.alpha
        self.low_beta = c_stats.low_beta
        self.high_beta = c_stats.high_beta
        self.gamma = c_stats.gamma


class ZenLiteDevice(ZenLiteDeviceListener):
    _device_pointer_map = {}
    _device_map = {}
    _config_response_callbacks = {}
    _sys_info_cb = None

    __address = 0
    __uuid = None
    __name = None
    __broadcast_battery_level = 0
    rssi = 0.0
    __in_pairing_mode = False

    __listener = None

    def __init__(self, uuid, name, address, broadcast_battery_level):
        self.__uuid = uuid
        self.__name = name
        self.__address = address
        self.__broadcast_battery_level = broadcast_battery_level

    @property
    def uuid(self):
        return self.__uuid

    @property
    def addr(self):
        return self.__address

    @property
    def name(self):
        return self.__name

    @property
    def connectivity(self):
        if self.__uuid in ZenLiteDevice._device_pointer_map:
            return Connectivity(libzenlite.zl_get_ble_connectivity(ZenLiteDevice._device_pointer_map[self.__uuid]))
        return Connectivity.disconnected

    @property
    def contact_state(self):
        if self.__uuid in ZenLiteDevice._device_pointer_map:
            return ContactState(libzenlite.zl_get_contact_state(ZenLiteDevice._device_pointer_map[self.__uuid]))
        return ContactState.unknown

    @property
    def battery_level(self):
        if self.__uuid in ZenLiteDevice._device_pointer_map:
            return libzenlite.zl_get_battery_level(ZenLiteDevice._device_pointer_map[self.__uuid])
        return self.__broadcast_battery_level

    @property
    def hardware_revision(self):
        if self.__uuid in ZenLiteDevice._device_pointer_map:
            hardware_rev = libzenlite.zl_get_hardware_revision(ZenLiteDevice._device_pointer_map[self.__uuid])
            return ffi.string(hardware_rev, 64).decode("utf-8")
        print("Never connected to the device; hardware revision is not available")
        return None

    @property
    def firmware_revision(self):
        if self.__uuid in ZenLiteDevice._device_pointer_map:
            firmware_rev = libzenlite.zl_get_firmware_revision(ZenLiteDevice._device_pointer_map[self.__uuid])
            return ffi.string(firmware_rev, 64).decode("utf-8")
        print("Never connected to the device; firmware revision is not available")
        return None

    @property
    def in_pairing_mode(self):
        return self.__in_pairing_mode

    # ZenLite msg
    def zl_config_afe(self, sample_rate, cb=None):
        if self.__uuid in ZenLiteDevice._device_pointer_map:
            res = libzenlite.zl_config_afe(ZenLiteDevice._device_pointer_map[self.__uuid], sample_rate, ZenLiteDevice.__on_afe_config_response_internal)
            if res > 0:  # res is now msg_id
                if cb is not None:
                    ZenLiteDevice._config_response_callbacks[res] = cb
                return ZLError(ZLErrorCode.none)
            else:
                return ZLError(res)
        else:
            fatal_error("Calling zl_config_afe before connecting to device")

    def zl_config_imu(self, sample_rate, mode=0, cb=None):
        if self.__uuid in ZenLiteDevice._device_pointer_map:
            res = libzenlite.zl_config_imu(ZenLiteDevice._device_pointer_map[self.__uuid], sample_rate, mode, ZenLiteDevice.__on_imu_config_response_internal)
            if res > 0:  # res is now msg_id
                if cb is not None:
                    ZenLiteDevice._config_response_callbacks[res] = cb
                return ZLError(ZLErrorCode.none)
            else:
                return ZLError(res)
        else:
            fatal_error("Calling zl_config_imu before connecting to device")

    def zl_config_ppg(self, sample_rate, mode, raw_set_reg=0, raw_set_value=0, cb=None):
        if self.__uuid in ZenLiteDevice._device_pointer_map:
            res = libzenlite.zl_config_ppg(ZenLiteDevice._device_pointer_map[self.__uuid], sample_rate, mode, raw_set_reg, raw_set_value, ZenLiteDevice.__on_afe_config_response_internal)
            if res > 0:  # res is now msg_id
                if cb is not None:
                    ZenLiteDevice._config_response_callbacks[res] = cb
                return ZLError(ZLErrorCode.none)
            else:
                return ZLError(res)
        else:
            fatal_error("Calling zl_config_ppg before connecting to device")

    def zl_sys_cmd(self, cmd, cb=None):
        print("cmd:", cmd)
        if self.__uuid in ZenLiteDevice._device_pointer_map:
            res = libzenlite.zl_sys_cmd(ZenLiteDevice._device_pointer_map[self.__uuid], cmd, ZenLiteDevice.__on_afe_config_response_internal)
            print("res:", res)
            if res > 0:  # res is now msg_id
                if cb is not None:
                    ZenLiteDevice._config_response_callbacks[res] = cb
                return ZLError(ZLErrorCode.none)
            else:
                return ZLError(res)
        else:
            fatal_error("Calling zl_sys_cmd before connecting to device")

    def zl_pair(self, in_pairing_mode, cb=None):
        if self.__uuid in ZenLiteDevice._device_pointer_map:
            res = libzenlite.zl_pair(ZenLiteDevice._device_pointer_map[self.__uuid], in_pairing_mode, ZenLiteDevice.__on_afe_config_response_internal)
            if res > 0:  # res is now msg_id
                if cb is not None:
                    ZenLiteDevice._config_response_callbacks[res] = cb
                return ZLError(ZLErrorCode.none)
            else:
                return ZLError(res)
        else:
            fatal_error("Calling zl_pair before connecting to device")

    def zl_set_device_name(self, name, cb=None):
        if self.__uuid in ZenLiteDevice._device_pointer_map:
            res = libzenlite.zl_set_device_name(ZenLiteDevice._device_pointer_map[self.__uuid], name, ZenLiteDevice.__on_afe_config_response_internal)
            if res > 0:  # res is now msg_id
                if cb is not None:
                    ZenLiteDevice._config_response_callbacks[res] = cb
                return ZLError(ZLErrorCode.none)
            else:
                return ZLError(res)
        else:
            fatal_error("Calling zl_set_device_name before connecting to device")

    def zl_set_sleep_idle_time(self, sec, cb=None):
        if self.__uuid in ZenLiteDevice._device_pointer_map:
            res = libzenlite.zl_set_sleep_idle_time(ZenLiteDevice._device_pointer_map[self.__uuid], sec, ZenLiteDevice.__on_sys_config_response_internal)
            if res > 0:  # res is now msg_id
                if cb is not None:
                    ZenLiteDevice._config_response_callbacks[res] = cb
                return ZLError(ZLErrorCode.none)
            else:
                return ZLError(res)
        else:
            fatal_error("Calling zl_set_sleep_idle_time before connecting to device")

    def zl_set_sleep_mode(self, enabled, cb=None):
        if self.__uuid in ZenLiteDevice._device_pointer_map:
            res = libzenlite.zl_set_sleep_mode(ZenLiteDevice._device_pointer_map[self.__uuid], enabled, ZenLiteDevice.__on_afe_config_response_internal)
            if res > 0:  # res is now msg_id
                if cb is not None:
                    ZenLiteDevice._config_response_callbacks[res] = cb
                return ZLError(ZLErrorCode.none)
            else:
                return ZLError(res)
        else:
            fatal_error("Calling zl_set_sleep_mode before connecting to device")

    def zl_get_sys_info(self, sys_info_cb, cb=None):
        if self.__uuid in ZenLiteDevice._device_pointer_map:
            self._sys_info_cb = sys_info_cb
            res = libzenlite.zl_get_sys_info(ZenLiteDevice._device_pointer_map[self.__uuid], ZenLiteDevice.__on_afe_config_response_internal, ZenLiteDevice.__on_sys_info_internal)
            if res > 0:  # res is now msg_id
                if cb is not None:
                    ZenLiteDevice._config_response_callbacks[res] = cb
                return ZLError(ZLErrorCode.none)
            else:
                return ZLError(res)
        else:
            fatal_error("Calling zl_get_sys_info before connecting to device")

    def set_listener(self, listener):
        if isinstance(listener, ZenLiteDeviceListener):
            self.__listener = listener
            if self.__uuid in ZenLiteDevice._device_pointer_map:
                device_ptr = ZenLiteDevice._device_pointer_map[self.__uuid]
                libzenlite.zl_set_signal_quality_warning_callback(device_ptr, ZenLiteDevice.__on_signal_quality_warning_internal)

                if listener is not None:
                    libzenlite.zl_set_sleep_report_callback(device_ptr, ZenLiteDevice.__on_sleep_report_internal)
                    libzenlite.zl_set_sleep_stage_callback(device_ptr, ZenLiteDevice.__on_sleep_stage_internal)
                    libzenlite.zl_set_event_callback(device_ptr, ZenLiteDevice.__on_event_internal)
                    libzenlite.zl_set_stress_callback(device_ptr, ZenLiteDevice.__on_stress_internal)
                    libzenlite.zl_set_meditation_callback(device_ptr, ZenLiteDevice.__on_meditation_internal)
                    libzenlite.zl_set_eeg_data_callback(device_ptr, ZenLiteDevice.__on_eeg_data_internal)
                    libzenlite.zl_set_imu_data_callback(device_ptr, ZenLiteDevice.__on_imu_data_internal)
                    libzenlite.zl_set_ppg_data_callback(device_ptr, ZenLiteDevice.__on_ppg_data_internal)
                    libzenlite.zl_set_eeg_stats_callback(device_ptr, ZenLiteDevice.__on_eeg_stats_internal)
                    libzenlite.zl_set_error_callback(device_ptr, ZenLiteDevice.__on_error_internal)
                    libzenlite.zl_set_connectivity_change_callback(device_ptr, ZenLiteDevice.__on_connectivity_change_internal)
                    libzenlite.zl_set_contact_state_change_callback(device_ptr, ZenLiteDevice.__on_contact_state_change_internal)
                    libzenlite.zl_set_orientation_change_callback(device_ptr, ZenLiteDevice.__on_orientation_change_internal)
                    libzenlite.zl_set_blink_callback(device_ptr, ZenLiteDevice.__on_blink_internal)
                    libzenlite.zl_set_device_info_callback(device_ptr, ZenLiteDevice.__on_device_info_internal)
                else:
                    libzenlite.zl_set_sleep_report_callback(device_ptr, ffi.NULL)
                    libzenlite.zl_set_sleep_stage_callback(device_ptr, ffi.NULL)
                    libzenlite.zl_set_event_callback(device_ptr, ffi.NULL)
                    libzenlite.zl_set_stress_callback(device_ptr, ffi.NULL)
                    libzenlite.zl_set_meditation_callback(device_ptr, ffi.NULL)
                    libzenlite.zl_set_eeg_data_callback(device_ptr, ffi.NULL)
                    libzenlite.zl_set_imu_data_callback(device_ptr, ffi.NULL)
                    libzenlite.zl_set_ppg_data_callback(device_ptr, ffi.NULL)
                    libzenlite.zl_set_eeg_stats_callback(device_ptr, ffi.NULL)
                    libzenlite.zl_set_error_callback(device_ptr, ffi.NULL)
                    libzenlite.zl_set_connectivity_change_callback(device_ptr, ffi.NULL)
                    libzenlite.zl_set_contact_state_change_callback(device_ptr, ffi.NULL)
                    libzenlite.zl_set_orientation_change_callback(device_ptr, ffi.NULL)
                    libzenlite.zl_set_blink_callback(device_ptr, ffi.NULL)
                    libzenlite.zl_set_device_info_callback(device_ptr, ffi.NULL)

        else:
            fatal_error("Listener does not conform to ZenLiteDeviceListener interface")

    def clamp(self, num, min_value, max_value):
        return max(min(num, max_value), min_value)

    def __get_c_ble_info(self):
        print(f'uuid={self.__uuid}, name={self.__name}')
        print(f'rssi={self.rssi}, broadcast_battery_level={self.__broadcast_battery_level}, in_pairing_mode=${self.__in_pairing_mode}')
        uuid_fld = ffi.new("char[40]", self.__uuid.encode('utf-8'))
        name_fld = ffi.new("char[40]", self.__name.encode('utf-8'))
        battery_level = self.clamp(self.__broadcast_battery_level, 0, 100)
        battery_level = chr(battery_level).encode()
        c_info = ffi.new("BLEScanResult *", (uuid_fld, name_fld, float(self.rssi), self.__address, self.__in_pairing_mode, battery_level))
        return c_info[0]

    def connect(self):
        libzenlite.stop_scan()

        if self.connectivity == Connectivity.disconnected:
            print("ZenLiteDevice:connecting...")
            device_ptr = libzenlite.zl_connect_ble(self.__get_c_ble_info())
            if device_ptr is not ffi.NULL:
                ZenLiteDevice._device_pointer_map[self.__uuid] = device_ptr
        # Make sure listeners are set to the C core
        if self.__listener is not None:
            self.set_listener(self.__listener)

    def disconnect(self):
        if self.connectivity is not Connectivity.disconnected or self.connectivity is not Connectivity.disconnecting:
            print("ZenLiteDevice:disconnecting...")
            if self.__uuid in self._device_pointer_map:
                device_ptr = ZenLiteDevice._device_pointer_map[self.__uuid]
                libzenlite.zl_disconnect_ble(device_ptr)
            else:
                fatal_error("ZenLiteDevice: Device map already cleared this device")

        else:
            print("ZenLiteDevice:Device is already disconnected...")

    @classmethod
    def create_device_with_scan_result(cls, result):
        uuid = ffi.string(result.uuid, 40).decode("utf-8")
        name = ffi.string(result.name, 16).decode("utf-8")
        rssi = result.rssi
        address = result.address
        in_pairing_mode = result.in_pairing_mode
        broadcast_battery_level = result.battery_level[0]
        return cls.create_zl_device(address, uuid, name, rssi, in_pairing_mode, broadcast_battery_level)

    @classmethod
    def create_zl_device(cls, address, uuid, name, rssi, in_pairing_mode, broadcast_battery_level):
        if uuid in cls._device_map:
            device = cls._device_map.get(uuid)
            device.__name = name
            device.__in_pairing_mode = in_pairing_mode
            device.__broadcast_battery_level = broadcast_battery_level
            device.__rssi = rssi
            if device.connectivity == Connectivity.connected or device.connectivity == Connectivity.connecting:
                device.connect()
            return device
        device = ZenLiteDevice(uuid, name, address, broadcast_battery_level)
        device.__rssi = rssi
        device.__in_pairing_mode = in_pairing_mode
        cls._device_map[uuid] = device
        return device

    # Callback internal methods implementation
    @staticmethod
    @ffi.callback("void(char*, unsigned int, ConfigResp*)")
    def __on_afe_config_response_internal(uuid_ptr, msg_id, c_resp):
        uuid = ffi.string(uuid_ptr, 40).decode("utf-8")
        if msg_id in ZenLiteDevice._config_response_callbacks:
            if uuid in ZenLiteDevice._device_map:
                device = ZenLiteDevice._device_map[uuid]
                err = AFEConfigError.none
                if c_resp.n_errors > 0:
                    err = AFEConfigError(ffi.unpack(c_resp.errors, c_resp.n_errors)[0])

                cb = ZenLiteDevice._config_response_callbacks[msg_id]
                cb(device, AFEConfigResponse(err))
                del ZenLiteDevice._config_response_callbacks[msg_id]

    @staticmethod
    @ffi.callback("void(char*, unsigned int, ConfigResp*)")
    def __on_imu_config_response_internal(uuid_ptr, msg_id, c_resp):
        uuid = ffi.string(uuid_ptr, 40).decode("utf-8")
        if msg_id in ZenLiteDevice._config_response_callbacks:
            if uuid in ZenLiteDevice._device_map:
                device = ZenLiteDevice._device_map[uuid]
                err = IMUConfigError.none
                if c_resp.n_errors > 0:
                    err = IMUConfigError(ffi.unpack(c_resp.errors, c_resp.n_errors)[0])

                cb = ZenLiteDevice._config_response_callbacks[msg_id]
                cb(device, IMUConfigResponse(err))
                del ZenLiteDevice._config_response_callbacks[msg_id]

    @staticmethod
    @ffi.callback("void(char*, unsigned int, ConfigResp*)")
    def __on_sys_config_response_internal(uuid_ptr, msg_id, c_resp):
        uuid = ffi.string(uuid_ptr, 40).decode("utf-8")
        if msg_id in ZenLiteDevice._config_response_callbacks:
            if uuid in ZenLiteDevice._device_map:
                device = ZenLiteDevice._device_map[uuid]
                cmd = ffi.unpack(c_resp.cmds, c_resp.n_errors)[0]
                err = ffi.unpack(c_resp.errors, c_resp.n_errors)[0]
                cb = ZenLiteDevice._config_response_callbacks[msg_id]
                if cb is not None:
                    cb(device, SysConfigResponse(ZenLiteCommand(cmd), SysConfigError(err)))

                del ZenLiteDevice._config_response_callbacks[msg_id]

    @staticmethod
    @ffi.callback("void(char*, unsigned int, SysInfoData*)")
    def __on_sys_info_internal(uuid_ptr, msg_id, c_data):
        uuid = ffi.string(uuid_ptr, 40).decode("utf-8")
        if uuid in ZenLiteDevice._device_map:
            device = ZenLiteDevice._device_map[uuid]
            if device._sys_info_cb is not None:
                firmware_info = ffi.string(c_data.firmware_info).decode("utf-8")  # TODO: Validate firmware info is properly unpacked
                c_errors = ffi.unpack(c_data.hardware_errors, c_data.n_errors)
                hardware_errors = []
                for err in c_errors:
                    hardware_errors.append(HardwareError(err))
                device._sys_info_cb(device, SysInfoData(firmware_info, hardware_errors))
                device._sys_info_cb = None

    @staticmethod
    @ffi.callback("void(char*, int)")
    def __on_signal_quality_warning_internal(uuid_ptr, signal_quality):
        print("Signal quality warning:%i, starting lead off detection" % signal_quality)

    @staticmethod
    @ffi.callback("void(char*, BLEConnectivity)")
    def __on_connectivity_change_internal(uuid_ptr, connectivity):
        uuid = ffi.string(uuid_ptr, 40).decode("utf-8")
        if uuid in ZenLiteDevice._device_map:
            device = ZenLiteDevice._device_map[uuid]
            connectivity_enum = Connectivity(connectivity)
            if device.__listener is not None:
                device.__listener.on_connectivity_change(connectivity_enum)
            if connectivity_enum == Connectivity.disconnected:
                if device.__uuid in ZenLiteDevice._device_pointer_map:
                    del ZenLiteDevice._device_pointer_map[device.__uuid]
        else:
            fatal_error("__on_connection_change_internal:device unavailable for:" + uuid)

    @staticmethod
    @ffi.callback("void(char*, EEGData*)")
    def __on_eeg_data_internal(uuid_ptr, eeg_data_ptr):
        uuid = ffi.string(uuid_ptr, 40).decode("utf-8")
        if uuid in ZenLiteDevice._device_map:
            device = ZenLiteDevice._device_map[uuid]
            if device.__listener is not None:
                device.__listener.on_eeg_data(EEGData(eeg_data_ptr[0]))
        else:
            fatal_error("__eeg_data_internal:device unavailable for:" + uuid)

    @staticmethod
    @ffi.callback("void(char*, IMUData*)")
    def __on_imu_data_internal(uuid_ptr, imu_data_ptr):
        uuid = ffi.string(uuid_ptr, 40).decode("utf-8")
        if uuid in ZenLiteDevice._device_map:
            device = ZenLiteDevice._device_map[uuid]
            if device.__listener is not None:
                device.__listener.on_imu_data(IMUData(imu_data_ptr[0]))
        else:
            fatal_error("__on_imu_data_internal:device unavailable for:" + uuid)

    @staticmethod
    @ffi.callback("void(char*, PPGData*)")
    def __on_ppg_data_internal(uuid_ptr, ppg_data_ptr):
        uuid = ffi.string(uuid_ptr, 40).decode("utf-8")
        if uuid in ZenLiteDevice._device_map:
            device = ZenLiteDevice._device_map[uuid]
            if device.__listener is not None:
                device.__listener.on_ppg_data(PPGData(ppg_data_ptr[0]))
        else:
            fatal_error("__ppg_data_internal:device unavailable for:" + uuid)

    @staticmethod
    @ffi.callback("void(char*, SleepReport*)")
    def __on_sleep_report_internal(uuid_ptr, data_str):
        uuid = ffi.string(uuid_ptr, 40).decode("utf-8")
        if uuid in ZenLiteDevice._device_map:
            device = ZenLiteDevice._device_map[uuid]
            if device.__listener is not None:
                device.__listener.on_sleep_report(SleepReport(data_str[0]))
        else:
            fatal_error("__sleep_report_internal:device unavailable for:" + uuid)

    @staticmethod
    @ffi.callback("void(char*, int)")
    def __on_event_internal(uuid_ptr, event):
        uuid = ffi.string(uuid_ptr, 40).decode("utf-8")
        if uuid in ZenLiteDevice._device_map:
            device = ZenLiteDevice._device_map[uuid]
            if device.__listener is not None:
                device.__listener.on_event(ZLEvent(event))
        else:
            fatal_error("__event_internal:device unavailable for:" + uuid)

    @staticmethod
    @ffi.callback("void(char*, float)")
    def __on_stress_internal(uuid_ptr, stress):
        uuid = ffi.string(uuid_ptr, 40).decode("utf-8")
        if uuid in ZenLiteDevice._device_map:
            device = ZenLiteDevice._device_map[uuid]
            if device.__listener is not None:
                device.__listener.on_stress(stress)
        else:
            fatal_error("__stress_internal:device unavailable for:" + uuid)

    @staticmethod
    @ffi.callback("void(char*, float)")
    def __on_meditation_internal(uuid_ptr, meditation):
        uuid = ffi.string(uuid_ptr, 40).decode("utf-8")
        if uuid in ZenLiteDevice._device_map:
            device = ZenLiteDevice._device_map[uuid]
            if device.__listener is not None:
                device.__listener.on_meditation(meditation)
        else:
            fatal_error("__meditation_internal:device unavailable for:" + uuid)

    @staticmethod
    @ffi.callback("void(char*, SleepStage, float, float)")
    def __on_sleep_stage_internal(uuid_ptr, stage, conf, drowsiness):
        uuid = ffi.string(uuid_ptr, 40).decode("utf-8")
        if uuid in ZenLiteDevice._device_map:
            device = ZenLiteDevice._device_map[uuid]
            if device.__listener is not None:
                device.__listener.on_sleep_stage(SleepStage(stage), conf, drowsiness)
        else:
            fatal_error("__meditation_internal:device unavailable for:" + uuid)

    @staticmethod
    @ffi.callback("void(char*, EEGStats*)")
    def __on_eeg_stats_internal(uuid_ptr, eeg_stats_ptr):
        uuid = ffi.string(uuid_ptr, 40).decode("utf-8")
        if uuid in ZenLiteDevice._device_map:
            device = ZenLiteDevice._device_map[uuid]
            if device.__listener is not None:
                device.__listener.on_brain_wave(BrainWave(eeg_stats_ptr[0]))
        else:
            fatal_error("__eeg_stats_internal:device unavailable for:" + uuid)

    @staticmethod
    @ffi.callback("void(char*, int)")
    def __on_error_internal(uuid_ptr, error_code):
        uuid = ffi.string(uuid_ptr, 40).decode("utf-8")
        if uuid in ZenLiteDevice._device_map:
            device = ZenLiteDevice._device_map[uuid]
            if device.__listener is not None:
                device.__listener.on_error(ZLError(error_code))
        else:
            fatal_error("__on_error_internal:device unavailable for:" + uuid)

    @staticmethod
    @ffi.callback("void(char*, ContactState)")
    def __on_contact_state_change_internal(uuid_ptr, contact_state):
        uuid = ffi.string(uuid_ptr, 40).decode("utf-8")
        if uuid in ZenLiteDevice._device_map:
            device = ZenLiteDevice._device_map[uuid]
            if device.__listener is not None:
                device.__listener.on_contact_state_change(ContactState(contact_state))
        else:
            fatal_error("__on_contact_state_change_internal:device unavailable for:" + uuid)

    @staticmethod
    @ffi.callback("void(char*, DeviceOrientation)")
    def __on_orientation_change_internal(uuid_ptr, orientation):
        uuid = ffi.string(uuid_ptr, 40).decode("utf-8")
        if uuid in ZenLiteDevice._device_map:
            device = ZenLiteDevice._device_map[uuid]
            if device.__listener is not None:
                device.__listener.on_orientation_change(Orientation(orientation))
        else:
            fatal_error("__on_orientation_change_internal:device unavailable for:" + uuid)

    @staticmethod
    @ffi.callback("void(char*)")
    def __on_blink_internal(uuid_ptr):
        uuid = ffi.string(uuid_ptr, 40).decode("utf-8")
        if uuid in ZenLiteDevice._device_map:
            device = ZenLiteDevice._device_map[uuid]
            if device.__listener is not None:
                device.__listener.on_blink()
        else:
            fatal_error("__on_blink_internal:device unavailable for:" + uuid_ptr)

    @staticmethod
    @ffi.callback("void(char*, BLEDeviceInfo*)")
    def __on_device_info_internal(uuid_ptr, c_info):
        uuid = ffi.string(uuid_ptr, 40).decode("utf-8")
        if uuid in ZenLiteDevice._device_map:
            device = ZenLiteDevice._device_map[uuid]
            if device.__listener is not None:
                device.__listener.on_device_info_ready(DeviceInfo(c_info))
        else:
            fatal_error("__on_device_info_ready_internal:device unavailable for:" + uuid_ptr)


class ZenLiteSDK:
    _on_found_device = None
    _on_scan_error = None

    @staticmethod
    def dispose():
        ffi.dlclose(libzenlite)
        # os.kill(os.getpid(), signal.SIGKILL)

    @staticmethod
    @ffi.callback("void(BLEScanResult*)")
    def _on_found_device_internal(result):
        if ZenLiteSDK._on_found_device is not None:
            if result is not None:
                device = ZenLiteDevice.create_device_with_scan_result(result)
                ZenLiteSDK._on_found_device(device)
            else:
                fatal_error("Device found but is None")

    @classmethod
    def start_scan(cls, on_finish):
        cls._on_found_device = on_finish
        # cls._on_search_error = on_error
        ZLOG.LOG_INFO(msg="zenlite_sdk.py:start_scan:scanning ...")
        libzenlite.start_scan(ZenLiteSDK._on_found_device_internal)

    @classmethod
    def stop_scan(cls):
        print("zenlite_sdk.py:stop_scan:stop")
        cls._on_found_device = None
        libzenlite.stop_scan()

    @classmethod
    def create_sdk_filter(cls):
        return libzenlite.dev_create_sdk_filter()

    @classmethod
    def filter(cls, sdk_filter, signal):
        return libzenlite.dev_filter(sdk_filter, signal)

    # TEST Methods
    @classmethod
    def zl_create_device(cls, uuid):
        uuid_str = ffi.new("char[]", uuid.encode('utf-8'))
        return libzenlite.zl_create_device(uuid_str)

    @classmethod
    def dev_analyze_eeg(cls, device, eeg_data, seg_finished):
        libzenlite.dev_analyze_eeg(device, ffi.cast("float(*)", eeg_data.ctypes.data), len(eeg_data), seg_finished)
