# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from odoo import fields
from datetime import timedelta

class TestTransportTrip(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a partner for the driver
        cls.driver = cls.env['res.partner'].create({
            'name': 'Test Driver Partner',
            'email': 'driver@transitops.test',
        })
        
        # Create a vehicle brand
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'Transit Brand',
        })
        
        # Create a vehicle model
        cls.vehicle_model = cls.env['fleet.vehicle.model'].create({
            'name': 'Transit Bus Model',
            'brand_id': cls.brand.id,
        })

        # Create a vehicle
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.vehicle_model.id,
            'license_plate': 'TOPS-9999',
        })

        # Create a route
        cls.route = cls.env['transport.route'].create({
            'route_id': 'RT-TEST-100',
            'name': 'Test Route Route',
            'source': 'Station Alpha',
            'destination': 'Station Omega',
            'total_distance': 42.5,
            'estimated_travel_time': 1.5,
        })

    def test_01_trip_creation_and_defaults(self):
        """Test default values, onchange trigger, and sequence assignment."""
        trip = self.env['transport.trip'].create({
            'name': 'New Trip',
            'route_id': self.route.id,
            'vehicle_id': self.vehicle.id,
            'driver_id': self.driver.id,
        })
        # Check sequence generation
        self.assertNotEqual(trip.trip_id, '/')
        self.assertTrue(trip.trip_id.startswith('TRIP/'))
        
        # Manually trigger onchange to test defaults from route
        trip._onchange_route_id()
        self.assertEqual(trip.start_location, 'Station Alpha')
        self.assertEqual(trip.end_location, 'Station Omega')
        self.assertEqual(trip.distance, 42.5)

    def test_02_workflow_state_transitions(self):
        """Test trip lifecycle transition buttons and constraints."""
        trip = self.env['transport.trip'].create({
            'name': 'Lifecycle Trip',
            'route_id': self.route.id,
            'vehicle_id': self.vehicle.id,
            'driver_id': self.driver.id,
        })
        self.assertEqual(trip.status, 'scheduled')

        # Try to complete scheduled trip directly (should raise UserError)
        with self.assertRaises(UserError):
            trip.action_complete()

        # Start trip
        trip.action_start()
        self.assertEqual(trip.status, 'in_progress')
        self.assertTrue(trip.departure_time)

        # Complete trip
        trip.action_complete()
        self.assertEqual(trip.status, 'completed')
        self.assertEqual(trip.progress, 100.0)
        self.assertTrue(trip.actual_arrival_time)

        # Reset to scheduled
        trip.action_reset()
        self.assertEqual(trip.status, 'scheduled')
        self.assertFalse(trip.actual_arrival_time)
        self.assertEqual(trip.progress, 0.0)

    def test_03_validation_constraints(self):
        """Test model validations and constraints."""
        now = fields.Datetime.now()

        # 1. Expected Arrival must be after Departure Time
        with self.assertRaises(ValidationError):
            self.env['transport.trip'].create({
                'name': 'Invalid Times Trip',
                'route_id': self.route.id,
                'vehicle_id': self.vehicle.id,
                'driver_id': self.driver.id,
                'departure_time': now + timedelta(hours=2),
                'expected_arrival_time': now,
            })

        # 2. Progress must remain between 0 and 100
        trip = self.env['transport.trip'].create({
            'name': 'Progress Trip',
            'route_id': self.route.id,
            'vehicle_id': self.vehicle.id,
            'driver_id': self.driver.id,
        })
        with self.assertRaises(ValidationError):
            trip.progress = 120.0

        with self.assertRaises(ValidationError):
            trip.progress = -10.0

        # 3. Completed trips must have actual arrival
        with self.assertRaises(ValidationError):
            trip.write({
                'status': 'completed',
                'actual_arrival_time': False,
            })
