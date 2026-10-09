"""
Tests unitarios para el modelo y resolución de canales de Write-Blocker (Sprint R08.2.1).
"""

import pytest
from datetime import datetime, timezone
from agente_forense.hardware.write_blockers import (
    WriteBlockerChannel, WriteBlockerAttachment, RelationStatus, WriteBlockerTopologySummary
)
from agente_forense.hardware.models import DiskSnapshot, ForensicDiskClassification, ClassifiedDisk


def test_write_blocker_channel_creation():
    channel = WriteBlockerChannel(
        blocker_id="BLOCKER-TABLEAU-01",
        display_name="Tableau T34589is",
        operator_label="BLOQUEADOR_1",
        manufacturer="Tableau",
        model="T34589is",
        serial_number="34cc0e0084305900",
        pnp_device_id="SBP2\\TABLEAU&T34589IS&LUN0&REV15\\000ECC3400593084",
        bus="1394"
    )

    assert channel.blocker_id == "BLOCKER-TABLEAU-01"
    assert channel.bus == "1394"
    assert channel.os_visible is True


def test_write_blocker_attachment_relation():
    attachment = WriteBlockerAttachment(
        blocker_id="BLOCKER-TABLEAU-01",
        disk_number=7,
        physical_drive="\\\\.\\PHYSICALDRIVE7",
        friendly_name="USB DISK 3.0",
        disk_serial="34cc0e0084305900",
        size_bytes=16000000000,
        is_read_only=True,
        is_system=False,
        is_boot=False,
        relation_status=RelationStatus.CONFIRMED
    )

    assert attachment.relation_status == RelationStatus.CONFIRMED
    assert attachment.physical_drive == "\\\\.\\PHYSICALDRIVE7"
    assert attachment.is_read_only is True


def test_write_blocker_topology_summary():
    channel = WriteBlockerChannel(
        blocker_id="BLOCKER-GENERIC-02",
        display_name="Generic Write Blocker",
        operator_label="BLOQUEADOR_2",
        bus="USB"
    )

    attachment = WriteBlockerAttachment(
        blocker_id="BLOCKER-GENERIC-02",
        disk_number=6,
        physical_drive="\\\\.\\PHYSICALDRIVE6",
        friendly_name="Generic Flash Disk",
        is_read_only=True,
        relation_status=RelationStatus.CONFIRMED
    )

    summary = WriteBlockerTopologySummary(
        channels=[channel],
        attachments=[attachment],
        unresolved_disks=[]
    )

    assert len(summary.channels) == 1
    assert len(summary.attachments) == 1
    assert summary.attachments[0].blocker_id == "BLOCKER-GENERIC-02"
