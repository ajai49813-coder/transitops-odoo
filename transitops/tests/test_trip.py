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

        # Create Route Stops
        cls.stop1 = cls.env['transport.route.stop'].create({
            'route_id': cls.route.id,
            'name': 'Stop Alpha-1',
            'sequence': 10,
            'distance_from_start': 10.0,
        })
        cls.stop2 = cls.env['transport.route.stop'].create({
            'route_id': cls.route.id,
            'name': 'Stop Alpha-2',
            'sequence': 20,
            'distance_from_start': 25.0,
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
        # Progress is now computed, let's write to distance completed to test bounds
        with self.assertRaises(ValidationError):
            trip.distance_completed = 100.0  # Would compute progress to > 100% since distance is 0 by default

    def test_04_advanced_features_simulation_and_stats(self):
        """Test movement simulation, computed progress, and vehicle/driver stats calculation."""
        trip = self.env['transport.trip'].create({
            'name': 'Advanced Test Trip',
            'route_id': self.route.id,
            'vehicle_id': self.vehicle.id,
            'driver_id': self.driver.id,
            'distance': 42.5,
        })

        # Check initial computed progress is 0.0 (Scheduled status)
        trip._compute_progress()
        self.assertEqual(trip.progress, 0.0)

        # Start trip
        trip.action_start()
        
        # Test GPS/Movement Simulation
        trip.action_simulate_movement()
        self.assertEqual(trip.tracking_status, 'simulated')
        self.assertNotEqual(trip.current_latitude, 0.0)
        self.assertNotEqual(trip.current_longitude, 0.0)
        self.assertGreater(trip.speed, 0.0)
        self.assertGreater(trip.distance_completed, 0.0)
        self.assertNotEqual(trip.progress, 0.0)

        # Test current stop assignment logic in simulation
        self.assertIsNotNone(trip.current_stop_id)
        
        # Validate Route visualization calculation
        self.route._compute_route_viz()
        self.assertEqual(self.route.total_stops, 2)
        self.assertGreaterEqual(self.route.distance_covered, 0.0)

        # Complete trip
        trip.action_complete()
        self.assertEqual(trip.status, 'completed')
        self.assertEqual(trip.progress, 100.0)

        # Force compute stats for Driver and Vehicle
        self.driver._compute_driver_stats()
        self.vehicle._compute_vehicle_stats()

        # Check Driver performance stats
        self.assertEqual(self.driver.total_trips, 1)
        self.assertEqual(self.driver.completed_trips, 1)
        self.assertEqual(self.driver.average_distance, 42.5)

        # Check Vehicle utilization stats
        self.assertEqual(self.vehicle.total_trips, 1)
        self.assertEqual(self.vehicle.total_distance, 42.5)
