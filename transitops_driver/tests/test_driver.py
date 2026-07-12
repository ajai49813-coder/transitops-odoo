# -*- coding: utf-8 -*-
"""Unit tests for the Transit Driver model."""

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class TestTransitDriver(TransactionCase):
    """Test suite for 'transit.driver' model business logic and constraints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test vehicles
        cls.vehicle_1 = cls.env['transit.vehicle'].create({
            'brand': 'toyota',
            'model_name': 'Hiace',
            'license_plate': 'TEST-001',
            'active': True,
        })
        cls.vehicle_2 = cls.env['transit.vehicle'].create({
            'brand': 'ford',
            'model_name': 'Transit',
            'license_plate': 'TEST-002',
            'active': True,
        })

    def test_01_driver_id_generation(self):
        """Test that Driver ID is automatically generated with sequence (DRVxxxx)."""
        driver = self.env['transit.driver'].create({
            'name': 'John Doe',
            'license_number': 'LIC-100',
        })
        self.assertTrue(driver.driver_id)
        self.assertNotEqual(driver.driver_id, 'New')
        self.assertTrue(driver.driver_id.startswith('DRV'))

    def test_02_license_uniqueness(self):
        """Test that duplicate license numbers raise ValidationError."""
        self.env['transit.driver'].create({
            'name': 'Driver A',
            'license_number': 'LIC-DUP-123',
        })
        with self.assertRaises(ValidationError):
            self.env['transit.driver'].create({
                'name': 'Driver B',
                'license_number': 'LIC-DUP-123',
            })

    def test_03_license_status_expiry(self):
        """Test the computed license status (Active, Warning, Expired)."""
        today = date.today()

        # 1. Active license (expires in 45 days)
        driver_active = self.env['transit.driver'].create({
            'name': 'Driver Active',
            'license_expiry_date': today + timedelta(days=45),
            'license_number': 'LIC-ACTIVE',
        })
        self.assertEqual(driver_active.license_status, 'active')
        self.assertFalse(driver_active.license_expiry_warning)

        # 2. Expiring soon license (expires in 15 days)
        driver_warning = self.env['transit.driver'].create({
            'name': 'Driver Warning',
            'license_expiry_date': today + timedelta(days=15),
            'license_number': 'LIC-WARN',
        })
        self.assertEqual(driver_warning.license_status, 'active')
        self.assertTrue(driver_warning.license_expiry_warning)

        # 3. Expired license (expired yesterday)
        driver_expired = self.env['transit.driver'].create({
            'name': 'Driver Expired',
            'license_expiry_date': today - timedelta(days=1),
            'license_number': 'LIC-EXPIRED',
        })
        self.assertEqual(driver_expired.license_status, 'expired')
        self.assertFalse(driver_expired.license_expiry_warning)

    def test_04_vehicle_assignment_restrictions(self):
        """Test that vehicles cannot be assigned to suspended or expired license drivers."""
        today = date.today()

        # 1. Suspended driver
        driver_suspended = self.env['transit.driver'].create({
            'name': 'Suspended Driver',
            'driver_status': 'suspended',
            'license_number': 'LIC-SUSPEND',
        })
        with self.assertRaises(ValidationError):
            driver_suspended.vehicle_id = self.vehicle_1.id

        # 2. Expired license driver
        driver_expired = self.env['transit.driver'].create({
            'name': 'Expired Driver',
            'license_expiry_date': today - timedelta(days=5),
            'license_number': 'LIC-EXP-ASSIGN',
        })
        with self.assertRaises(ValidationError):
            driver_expired.vehicle_id = self.vehicle_1.id

    def test_05_single_vehicle_assignment(self):
        """Test that a vehicle cannot be assigned to more than one active driver."""
        driver_1 = self.env['transit.driver'].create({
            'name': 'Driver One',
            'license_number': 'LIC-ONE',
            'vehicle_id': self.vehicle_1.id,
        })
        # Try to assign the same vehicle_1 to driver_2
        with self.assertRaises(ValidationError):
            self.env['transit.driver'].create({
                'name': 'Driver Two',
                'license_number': 'LIC-TWO',
                'vehicle_id': self.vehicle_1.id,
            })
