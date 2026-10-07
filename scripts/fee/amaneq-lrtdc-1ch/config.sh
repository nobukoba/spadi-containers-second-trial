#!/usr/bin/env bash
# Channel numbers use the firmware's zero-based numbering (0-127).
AMANEQ_IP="192.168.10.16"
MASK_MAIN_U="ffffffff"
MASK_MAIN_D="ffffffff"
MASK_MZN_U="ffffffff"
# Channel 102 = MZN-D bit (102 - 96) = bit 6. 1 masks, 0 unmasks.
MASK_MZN_D="ffffffbf"
