from lib.constants import FlashInfo, internal_path, ecu_control_module_identifier
from .simos18 import base_addresses_s18, block_lengths_s18
from .simosshared import (
    block_identifiers_simos,
    block_checksums_simos,
    box_code_location_simos,
    software_version_location_simos,
    block_transfer_sizes_simos,
)


# Simos 16.11 Flash Info

block_names_frf_s16 = {
    1: "FD_01DATA",
    2: "FD_02DATA",
    3: "FD_03DATA",
    4: "FD_04DATA",
    5: "FD_05DATA",
}

s16_key = bytes.fromhex("0ACFFB51 3E95644A 396A4132 5235D9A9")
s16_iv = bytes.fromhex("01D13742 6B6B536F B3333F69 1B366D34")

sa2_script_s16 = bytes.fromhex(
    "680393712EAB7C4A059314062012496803870112201282824A0584FD073A5D494C"
)

s16_binfile_offsets = {
    0: 0x0,  # SBOOT
    1: 0x200000,  # CBOOT
    2: 0x20000,  # ASW1
    3: 0x100000,  # ASW2
    4: 0x2C0000,  # ASW3
    5: 0x220000,  # CAL
}

s16_binfile_size = 4194304

s16_project_name = "SG1"

s16_flash_info = FlashInfo(
    base_addresses_s18,
    block_lengths_s18,
    sa2_script_s16,
    s16_key,
    s16_iv,
    None,
    block_names_frf_s16,
    None,
    None,
    None,
    block_identifiers_simos,
    block_checksums_simos,
    ecu_control_module_identifier,
    software_version_location_simos,
    box_code_location_simos,
    block_transfer_sizes_simos,
    s16_binfile_offsets,
    s16_binfile_size,
    s16_project_name,
)