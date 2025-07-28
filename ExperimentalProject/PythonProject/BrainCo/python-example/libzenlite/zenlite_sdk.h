#ifndef ZENLITE_SDK_H
#define ZENLITE_SDK_H

#ifdef __cplusplus
extern "C" {
#endif

#ifdef _WIN32
#ifdef BUILDING_ZL_SHARED
#define SDK_EXTERN __declspec(dllexport)
#elif USING_ZL_SHARED
#define SDK_EXTERN __declspec(dllimport)
#else
#define SDK_EXTERN
#endif
#else
#define SDK_EXTERN
#endif

#if __APPLE__
#include <TargetConditionals.h>
#endif

#include <stdbool.h>

//CFFI_DEF_START

// 1. ZenLiteDevice and related struct definitions
// ==============================================================================
typedef struct ZenLiteDevice ZenLiteDevice;
typedef struct SleepReport SleepReport;

typedef enum {
    LOG_LEVEL_DEBUG = 0,
    LOG_LEVEL_INFO = 1,
    LOG_LEVEL_WARNING= 2,
    LOG_LEVEL_ERROR= 3,
    LOG_LEVEL_NONE= 4,
} LogLevel;

typedef enum {
    PROJECT_ID_DEFAULT = 0,
    PROJECT_ID_ZENLITE = 1,
    PROJECT_ID_MORPHEUS = 2,
    PROJECT_ID_MOBUIS = 3,
} ProjectID;

typedef enum {
    CONTACT_STATE_UNKNOWN = 0,
    CONTACT_STATE_OFF = 1,
    CONTACT_STATE_EEG = 2,
    CONTACT_STATE_ALL = 3
} ContactState;

typedef enum {
    EEG_CONTACT_STATE_UNKNOWN = 0,
    EEG_CONTACT_STATE_OFF = 1,
    EEG_CONTACT_STATE_ON = 2
} EEGContactState;

typedef enum {
    PPG_CONTACT_STATE_UNKNOWN = 0,
    PPG_CONTACT_STATE_OFF_SKIN = 1,
    PPG_CONTACT_STATE_ON_SOME_OBJECT = 2,
    PPG_CONTACT_STATE_ON_SKIN = 3
} PPGContactState;

typedef enum {
    WORKING_MODE_NORMAL = 0,
    WORKING_MODE_SLEEP  = 1
} WorkingMode;

typedef struct {
    int sequence_num;
    float sample_rate;
    float* eeg_data;
    int eeg_size;
    WorkingMode working_mode;
} EEGData;

typedef enum {
    ORIENTATION_UNKNOWN = 0,
    ORIENTATION_UPWARD = 1,
    ORIENTATION_DOWNWARD = 2 //UPSIDEDOWN
} DeviceOrientation;

typedef struct {
    float x;
    float y;
    float z;
} Point3D;

typedef struct {
    int     sequence_num;
    Point3D *  data;
    int     size;
} ACCData;

typedef struct {
    int     sequence_num;
    Point3D*  data;
    int     size;
} GyroData;

typedef struct {
    float*    yaw; // (-180 ~ 180) int value
    float*    pitch;
    float*    roll;
    int     size;
} EulerAngleData;

typedef enum {
    BODY_POSE_INVALID=0,
    BODY_POSE_NORM_BACK=1, //正常平躺
    BODY_POSE_SEATED=2,  //坐
    BODY_POSE_LEAN_FORWARD=3, //前倾
    BODY_POSE_STOMACH=4 //趴睡
} BodyPose;

typedef enum {
    HEAD_ROTATION_INVALID = 0,
    HEAD_ROTATION_LEFT = 1,
    HEAD_ROTATION_RIGHT = 2,
    HEAD_ROTATION_FACE_UP = 3,
    HEAD_ROTATION_FACE_DOWN = 4
} HeadRotation;  

typedef struct {
    ACCData*           acc_data;
    GyroData*          gyro_data;
    EulerAngleData*    euler_angle_data;
    float              sample_rate;
    HeadRotation       head;
    BodyPose           body;
} IMUData;

typedef enum {
    PPG_ACTIVITY_REST = 0,
    PPG_ACTIVITY_OTHER = 1,
    PPG_ACTIVITY_WALK = 2,
    PPG_ACTIVITY_RUN = 3,
    PPG_ACTIVITY_BIKE = 4
} PPGActivity;

typedef enum {
    PPG_STATE_ADJUSTING_LED = 0,
    PPG_STATE_COMPUTING = 1,
    PPG_STATE_SUCCESS = 2,
    PPG_STATE_TIMEOUT = 3,
} SPO2State;
// https://github.com/BrainCoTech/zenlite_protobuf/blob/main/proto/dev_ppg.proto
typedef struct { // int     op_mode;
    float        hr;            // bpm
    int          hr_conf;       // %
    float        rr;            // ms
    int          rr_conf;       // %
    PPGActivity  activity;
    float        spo2;          // %
    float        spo2_r;
    int          spo2_conf;     //%
    int          spo2_progress; //%
    bool         spo2_lsq_flag;
    bool         spo2_mt_flag;
    bool         spo2_lp_flag;
    bool         spo2_ur_flag;
    float        hrv;
    float        hrv_stress;
    float        stress;
    SPO2State       spo2_state;
    PPGContactState contact_state; //scd_state
} PPGAlgoData;

typedef struct {
    int green1_count;
    int green2_count;
    int ir_count;
    int red_count;
} PPGRawData;

typedef enum {
    RESPIRATORY_STATE_REST = 0,
    RESPIRATORY_STATE_IN = 1,
    RESPIRATORY_STATE_OUT = 2,
} RespiratoryState;

typedef struct {
    int            sequence_num;
    float          report_rate;
    int            raw_data_size;
    PPGRawData *   raw_data;
    int            algo_data_size;
    PPGAlgoData *  algo_data;
    float        respiratory_rate;
    float *      respiratory_curve;
    int          respiratory_curve_size;
    RespiratoryState respiratory_state;
} PPGData;

typedef struct {
    char* firmware_info;      // Firmware information
    int * hardware_errors;    // Hardware errors
    int   n_errors;    // Number of hardware errors
    int   sleep_idle_time_sec; //最小不能小于30秒 0表示不休眠
    int   vibration_intensity; //0~100
} SysInfoData;

typedef struct {
    int success;
    int* cmds;
    int* errors;
    int n_errors;
} ConfigResp;

typedef struct {
    double delta;
    double theta;
    double alpha;
    double low_beta;
    double high_beta;
    double gamma;
} EEGStats;

typedef enum {
    SLEEP_STAGE_UNKNOWN = -1,
    SLEEP_STAGE_AWAKE   = 0,
    SLEEP_STAGE_REM     = 1,
    SLEEP_STAGE_LIGHT   = 2,
    SLEEP_STAGE_DEEP    = 3,
} SleepStage;

typedef enum {
    ZL_ERROR_NONE = 0,
    ZL_ERROR_UNKNOWN = -1,
    ZL_ERROR_INVALID_PARAMS = -2,
    ZL_ERROR_INVALID_DATA = -3,

    ZL_ERROR_SYSTEM_IS_BUSY = -11,

    ZL_ERROR_SCAN_FAILED = -64,                   //Android
    ZL_ERROR_SCAN_FEATURE_UNSUPPORTED = -65,      //Android
    ZL_ERROR_MAIN_SERVICE_UNSUPPORTED = -66,      //Android

    // BLE device error codes
    ZL_ERROR_BLE_DEVICE_UNREACHABLE = -128,       //Android,Desktop (iOS)
    ZL_ERROR_BLE_DISABLED = -129,                 //Android,Desktop (iOS)
    ZL_ERROR_BLE_UNAVAILABLE = -130,              //Android,Desktop (iOS)

    ZL_ERROR_BLE_DATA_WRITE_FAILURE = -131,       //Desktop

    ZL_ERROR_DEVICE_NOT_CONNECTED = -160,         //Android,iOS     (Desktop)
    ZL_ERROR_DEVICE_UUID_UNAVAILABLE = -196,      //Android,iOS,Desktop

    // ZenLite error codes  
    ZL_ERROR_ZL_EEG_INIT = -1002,
    ZL_ERROR_ZL_IMU_INIT = -1003,
    ZL_ERROR_ZL_PPG_INIT = -1004,
    ZL_ERROR_ZL_BATTERY_VOLTAGE = -1005,
    ZL_ERROR_ZL_BATTERY_TEMPERATURE = -1006,
    ZL_ERROR_ZL_HARDWARE_VERSION = -1007,
    ZL_ERROR_ZL_FLASH_INIT = -1008,
    ZL_ERROR_ZL_BLE_INIT = -1009,
} ZLError;

typedef enum {
    ZL_AFE_SAMPLE_RATE_NONE  = 0,
    ZL_AFE_SAMPLE_RATE_OFF  = 1,
    ZL_AFE_SAMPLE_RATE_128  = 2,
    ZL_AFE_SAMPLE_RATE_256  = 3,
} EEGSampleRate;

typedef enum {
    ZL_IMU_SAMPLE_RATE_NONE = 0,
    ZL_IMU_SAMPLE_RATE_OFF = 1,
    ZL_IMU_SAMPLE_RATE_25 = 2,
    ZL_IMU_SAMPLE_RATE_50 = 3,
    ZL_IMU_SAMPLE_RATE_100 = 4,
    ZL_IMU_SAMPLE_RATE_200 = 5,
    ZL_IMU_SAMPLE_RATE_400 = 6,
    ZL_IMU_SAMPLE_RATE_800 = 7,
} IMUSampleRate;


typedef enum {
    ZL_IMU_MODE_NONE = 0,
    ZL_IMU_MODE_ACC = 1,
    ZL_IMU_MODE_GYRO = 2,
    ZL_IMU_MODE_ACC_GYRO = 3,
    ZL_IMU_MODE_EULER = 4,
} IMUMode;

typedef enum {
    ZL_PPG_SAMPLE_RATE_NONE = 0,
    ZL_PPG_SAMPLE_RATE_OFF = 1,
    ZL_PPG_SAMPLE_RATE_1 = 2,
    ZL_PPG_SAMPLE_RATE_5 = 3,
    ZL_PPG_SAMPLE_RATE_25 = 4,
    ZL_PPG_SAMPLE_RATE_50 = 5,
    ZL_PPG_SAMPLE_RATE_100 = 6,
} PPGReportRate;

typedef enum {
    ZL_PPG_MODE_NONE = 0,
    ZL_PPG_MODE_RAWDATA = 1,
    ZL_PPG_MODE_ALGO = 2,
    ZL_PPG_MODE_SPO2 = 3,
    ZL_PPG_MODE_HR = 4,
    ZL_PPG_MODE_HRV = 5,
} PPGMode;

typedef enum {
    ZL_PPG_REG = 0,
    ZL_PPG_VALUE = 1,
} ZenLitePpgRawSetReg;

typedef enum {
  ZL_CMD_NONE = 0,
  ZL_CMD_PAIR = 1,               // Used when device is in pairing mode
  ZL_CMD_VALIDATE_PAIR_INFO = 2, // Should be sent right after connection established
  ZL_CMD_START = 3,
  ZL_CMD_STOP = 4,
  ZL_CMD_SHUT_DOWN = 5,
  ZL_CMD_ENTER_OTA = 6,
  ZL_CMD_RESET = 7,
  ZL_CMD_SET_DEVICE_NAME = 8,
  ZL_CMD_SET_SLEEP_IDLE_TIME = 9,
  ZL_CMD_GET_SYSTEM_MONITOR = 10,
} ConfigCMD;

typedef enum {
    ZL_EVENT_NONE = 0,
    ZL_EVENT_FALL_ASLEEP = 1,
    //TODO
    ZL_EVENT_WAKE_UP = 2,
    ZL_EVENT_BLINK = 3,
} ZLEvent;

SDK_EXTERN unsigned int zl_gen_msg_id(void);

// 1-1. zl_create_device
SDK_EXTERN ZenLiteDevice * zl_create_device(const char * device_id);

// 1-2. zl_release_device (DEPRECATED:We recommend singleton implementation) 
// SDK_EXTERN int zl_release_device(ZenLiteDevice * device);


// 2. Data Handler
// ==============================================================================
/* call this functions when received any byte data from the devices
 *
 * Note:
 *   This is not a thread safe function
 *
 * @param   device
 * @param   data          data would NOT be free in this function
 * @param   size
 * @return  remain_size   the size of the remaining fragment data
 *          -1            fail
 */
SDK_EXTERN int zl_did_receive_data(ZenLiteDevice * device, const char * data, int size);

// 3. Message Builder
// ==============================================================================
// ZenLite msg pack
SDK_EXTERN int zl_afe_config_pack(unsigned int msg_id, char ** buffer, int sample_rate);
SDK_EXTERN int zl_imu_config_pack(unsigned int msg_id, char ** buffer, int sample_rate, int mode);
SDK_EXTERN int zl_ppg_config_pack(unsigned int msg_id, char ** buffer, int sample_rate, int mode, int raw_set_reg, int raw_set_value);
SDK_EXTERN int zl_sys_cmd_pack(unsigned int msg_id, char ** buffer, int cmd);
SDK_EXTERN int zl_device_name_pack(unsigned int msg_id, char ** buffer, const char *name);
SDK_EXTERN int zl_device_pair_pack(unsigned int msg_id, char ** buffer, bool first, const char *pair_info);
SDK_EXTERN int zl_sleep_idle_time_pack(unsigned int msg_id, char ** buffer, int sec);
SDK_EXTERN int zl_sleep_mode_pack(unsigned int msg_id, char ** buffer, bool enabled);

// Error code to message converters
SDK_EXTERN const char* zl_err_code_to_msg(int err_code);

// 4. Device state getters
SDK_EXTERN ContactState zl_get_contact_state(ZenLiteDevice* device);

// 5. Callbacks
// ==============================================================================
// 5-1. Global Callbacks
typedef void (*LogCB)(const char * msg);
SDK_EXTERN void zl_set_log_callback(LogCB cb);
SDK_EXTERN void zl_set_log_level(LogLevel logLevel);
SDK_EXTERN void zl_log(LogLevel logLevel, const char *format, ...);

typedef float* (*TensorDataCB)(int tensor_type, const float *data, const int len);
SDK_EXTERN void zl_set_tensor_data_callback(TensorDataCB cb);
SDK_EXTERN float* zl_model_predict(int tensor_type, float* predictor_buff);

// 5-2. Device Callbacks
typedef void (*ContactStateChangeCB)(const char * device_id, ContactState state);
SDK_EXTERN int zl_set_contact_state_change_callback(ZenLiteDevice * device, ContactStateChangeCB cb);

typedef void (*SignalQualityWarningCB)(const char * device_id, int quality);
SDK_EXTERN int zl_set_signal_quality_warning_callback(ZenLiteDevice * device, SignalQualityWarningCB cb);

typedef void (*ErrorCB)(const char * device_id, int error);
SDK_EXTERN int zl_set_error_callback(ZenLiteDevice * device, ErrorCB cb);

typedef void (*EEGDataCB)(const char * device_id, EEGData * data);
SDK_EXTERN int zl_set_eeg_data_callback(ZenLiteDevice * device, EEGDataCB cb);

typedef void (*EEGStatsCB)(const char* device_mac, EEGStats * stats);
SDK_EXTERN int zl_set_eeg_stats_callback(ZenLiteDevice * device, EEGStatsCB cb);

typedef void (*IMUDataCB)(const char * device_id, IMUData * data);
SDK_EXTERN int zl_set_imu_data_callback(ZenLiteDevice * device, IMUDataCB cb);

typedef void (*PPGDataCB)(const char * device_id, PPGData * data);
SDK_EXTERN int zl_set_ppg_data_callback(ZenLiteDevice * device, PPGDataCB cb);

typedef void (*DeviceOrientationCB)(const char * device_id, DeviceOrientation orientation);
SDK_EXTERN int zl_set_orientation_change_callback(ZenLiteDevice * device, DeviceOrientationCB cb);

typedef void (*ZLValueCB)(const char * device_id, float value);
SDK_EXTERN int zl_set_attention_callback(ZenLiteDevice * device, ZLValueCB cb);
SDK_EXTERN int zl_set_meditation_callback(ZenLiteDevice * device, ZLValueCB cb);
SDK_EXTERN int zl_set_stress_callback(ZenLiteDevice * device, ZLValueCB cb);
typedef void (*ZLSleepStageCB)(const char * device_id, SleepStage stage, float confidence, float drowsiness);
SDK_EXTERN int zl_set_sleep_stage_callback(ZenLiteDevice * device, ZLSleepStageCB cb);

typedef void (*ZLEventCB)(const char * device_id, int value);
SDK_EXTERN int zl_set_event_callback(ZenLiteDevice * device, ZLEventCB cb);
typedef void (*SleepReportCB)(const char * device_id, SleepReport * data);
SDK_EXTERN int zl_set_sleep_report_callback(ZenLiteDevice * device, SleepReportCB cb);

typedef void (*BlinkCB)(const char * device_id);
SDK_EXTERN int zl_set_blink_callback(ZenLiteDevice * device, BlinkCB cb);

typedef void (*ConfigRespCB)(const char * device_id, unsigned int msg_id, ConfigResp* resp);
SDK_EXTERN int zl_set_afe_config_resp_callback(ZenLiteDevice * device, ConfigRespCB cb);
SDK_EXTERN int zl_set_imu_config_resp_callback(ZenLiteDevice * device, ConfigRespCB cb);
SDK_EXTERN int zl_set_ppg_config_resp_callback(ZenLiteDevice * device, ConfigRespCB cb);
SDK_EXTERN int zl_set_sys_config_resp_callback(ZenLiteDevice * device, ConfigRespCB cb);

typedef void (*SysInfoCB)(const char * device_id, unsigned int msg_id, SysInfoData* sys_info);
SDK_EXTERN int zl_set_sys_info_callback(ZenLiteDevice * device, SysInfoCB cb);

SDK_EXTERN const char* zl_get_sdk_version(void);

// 6. Desktop bluetooth APIs
// ==============================================================================
#if defined(_WIN32) || TARGET_OS_OSX
typedef struct {
    char uuid[40];
    char name[40];
    float rssi;
    unsigned long long address;
    bool in_pairing_mode;
    char battery_level;
} BLEScanResult;

typedef struct {
    char manufacturer[16];
    char model[16];
    char serial[16];
    char hardware[16];
    char firmware[16];
} BLEDeviceInfo;

typedef enum {
    BLE_CONNECTIVITY_CONNECTING    = 0,
    BLE_CONNECTIVITY_CONNECTED     = 1,
    BLE_CONNECTIVITY_DISCONNECTING = 2,
    BLE_CONNECTIVITY_DISCONNECTED  = 3,
} BLEConnectivity;

typedef enum {
    AFE_CHANNEL_NONE = 0,
    AFE_CHANNEL_CH1  = 1,
    AFE_CHANNEL_CH2  = 2,
    AFE_CHANNEL_BOTH = 3,
} AFEChannel;

typedef enum {
    AFE_LEAD_OFF_DISABLED = 0,
    AFE_LEAD_OFF_AC       = 1,
    AFE_LEAD_OFF_DC_6nA   = 2,
    AFE_LEAD_OFF_DC_22nA  = 3,
    AFE_LEAD_OFF_DC_6uA   = 4,
    AFE_LEAD_OFF_DC_22uA  = 5,
} AFELeadOffOption;

typedef void (*FoundDeviceCB)(BLEScanResult *BLEScanResult);
SDK_EXTERN void start_scan(FoundDeviceCB cb);
SDK_EXTERN void stop_scan(void);
SDK_EXTERN ZenLiteDevice* zl_connect_ble(BLEScanResult device_ble_info);
SDK_EXTERN void zl_disconnect_ble(ZenLiteDevice* device);
SDK_EXTERN BLEConnectivity zl_get_ble_connectivity(ZenLiteDevice* device);
SDK_EXTERN const char * zl_get_device_name(ZenLiteDevice* device);
SDK_EXTERN const char * zl_get_manufacturer_name(ZenLiteDevice* device);
SDK_EXTERN const char * zl_get_serial_number(ZenLiteDevice* device);
SDK_EXTERN const char * zl_get_model_number(ZenLiteDevice* device);
SDK_EXTERN const char * zl_get_hardware_revision(ZenLiteDevice* device);
SDK_EXTERN const char * zl_get_firmware_revision(ZenLiteDevice* device);
SDK_EXTERN int zl_get_battery_level(ZenLiteDevice* device);
//TODO on_battery_level_callback

// ZenLite msg
SDK_EXTERN int zl_config_afe(ZenLiteDevice* device, EEGSampleRate sample_rate, ConfigRespCB cb);
SDK_EXTERN int zl_config_imu(ZenLiteDevice* device, IMUSampleRate sample_rate, IMUMode mode, ConfigRespCB cb);
SDK_EXTERN int zl_config_ppg(ZenLiteDevice* device, PPGReportRate sample_rate, PPGMode mode, int raw_set_reg, int raw_set_value, ConfigRespCB cb);
SDK_EXTERN int zl_sys_cmd(ZenLiteDevice* device, ConfigCMD cmd, ConfigRespCB cb);
SDK_EXTERN int zl_pair(ZenLiteDevice* device, bool in_pairing_mode, ConfigRespCB cb);
SDK_EXTERN int zl_set_device_name(ZenLiteDevice* device, const char* name, ConfigRespCB cb);
SDK_EXTERN int zl_set_sleep_idle_time(ZenLiteDevice* device, int sec, ConfigRespCB cb);
SDK_EXTERN int zl_set_sleep_mode(ZenLiteDevice* device, bool enabled, ConfigRespCB cb);
SDK_EXTERN int zl_get_sys_info(ZenLiteDevice* device, ConfigRespCB cb, SysInfoCB info_cb);

// set callback functions (implemented in zenlite_ble.c)
typedef void (*DeviceInfoCB)(const char * device_id, BLEDeviceInfo *info);
SDK_EXTERN int zl_set_device_info_callback(ZenLiteDevice * device, DeviceInfoCB cb);

typedef void (*ConnectivityChangeCB)(const char * device_id, BLEConnectivity connectivity);
SDK_EXTERN int zl_set_connectivity_change_callback(ZenLiteDevice * device, ConnectivityChangeCB cb);


#endif
// ==============================================================================


// 7. Test & experimental functions
// ==============================================================================

SDK_EXTERN int hello(int num);
typedef struct {
    void * bs;
    void * bp;
    void * fft;
} ZLFilter;

// Dev Method
SDK_EXTERN ZLFilter * dev_create_sdk_filter(void);
SDK_EXTERN float dev_filter(ZLFilter* filter, float signal);
SDK_EXTERN float* dev_fft(ZLFilter* filter, float* windowed_signal, int size);
SDK_EXTERN void debug_signal(float * signal);
SDK_EXTERN void dev_analyze_eeg(ZenLiteDevice* device, const float *eeg_data, int size, bool seg_finished);
SDK_EXTERN void dev_set_fall_asleep_threshold(int avg_threshold, int min_threshold);

//CFFI_DEF_END

#ifdef __cplusplus
}
#endif
#endif
