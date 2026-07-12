# -*- coding: utf-8 -*-
from odoo import models, api
from datetime import date


class TransitDashboard(models.AbstractModel):
    """Dashboard data provider — exposes KPIs to the OWL frontend."""
    _name = 'transit.dashboard'
    _description = 'TransitOps Dashboard'

    @api.model
    def get_kpis(self):
        Vehicle = self.env['transit.vehicle']
        Driver = self.env['transit.driver']
        Trip = self.env['transit.trip']
        Fuel = self.env['transit.fuel']
        Maintenance = self.env['transit.maintenance']
        Notification = self.env['transit.notification']

        total_vehicles = Vehicle.search_count([])
        active_vehicles = Vehicle.search_count([('status', '=', 'active')])
        total_drivers = Driver.search_count([])
        total_trips = Trip.search_count([])
        completed_trips = Trip.search_count([('status', '=', 'completed')])
        ongoing_trips = Trip.search_count([('status', '=', 'ongoing')])

        fuels = Fuel.search([])
        total_fuel = sum(fuels.mapped('quantity_liters'))
        total_fuel_cost = sum(fuels.mapped('total_cost'))

        pending_maintenance = Maintenance.search_count([('status', 'in', ['pending', 'in_progress'])])
        active_alerts = Notification.search_count([('status', '=', 'active')])

        return {
            'total_vehicles': total_vehicles,
            'active_vehicles': active_vehicles,
            'total_drivers': total_drivers,
            'total_trips': total_trips,
            'completed_trips': completed_trips,
            'ongoing_trips': ongoing_trips,
            'total_fuel_consumption': round(total_fuel, 2),
            'total_fuel_cost': round(total_fuel_cost, 2),
            'pending_maintenance': pending_maintenance,
            'active_alerts': active_alerts,
        }

    @api.model
    def get_chart_data(self):
        """Return all chart datasets for the dashboard."""
        monthly_fuel = self.env['transit.fuel.analytics'].get_monthly_fuel()

        Trip = self.env['transit.trip']
        trip_statuses = ['draft', 'scheduled', 'ongoing', 'completed', 'cancelled']
        trips_by_status = {s: Trip.search_count([('status', '=', s)]) for s in trip_statuses}

        self.env.cr.execute("""
            SELECT v.name, COUNT(t.id) AS trip_count
            FROM transit_vehicle v
            LEFT JOIN transit_trip t ON t.vehicle_id = v.id
            GROUP BY v.id, v.name
            ORDER BY trip_count DESC
            LIMIT 10
        """)
        vehicle_usage = self.env.cr.dictfetchall()

        self.env.cr.execute("""
            SELECT TO_CHAR(scheduled_date, 'YYYY-MM') AS month, COUNT(*) AS count
            FROM transit_trip
            WHERE scheduled_date >= (NOW() - INTERVAL '12 months')
            GROUP BY month ORDER BY month
        """)
        monthly_trips = self.env.cr.dictfetchall()

        self.env.cr.execute("""
            SELECT v.name,
                   CASE WHEN SUM(f.quantity_liters) > 0
                        THEN ROUND(CAST(SUM(t.odometer_end - t.odometer_start) AS NUMERIC) /
                                   CAST(SUM(f.quantity_liters) AS NUMERIC), 2)
                        ELSE 0 END AS efficiency
            FROM transit_vehicle v
            JOIN transit_trip t ON t.vehicle_id = v.id AND t.status = 'completed'
                                AND t.odometer_start > 0 AND t.odometer_end > 0
            JOIN transit_fuel f ON f.trip_id = t.id
            GROUP BY v.id, v.name
            ORDER BY efficiency DESC
            LIMIT 10
        """)
        fuel_efficiency = self.env.cr.dictfetchall()

        return {
            'monthly_fuel': monthly_fuel,
            'trips_by_status': trips_by_status,
            'vehicle_usage': vehicle_usage,
            'monthly_trips': monthly_trips,
            'fuel_efficiency': fuel_efficiency,
        }

    @api.model
    def generate_alerts(self):
        """Called by cron — detect and create notifications for expiring items."""
        today = date.today()
        warning_days = 30
        critical_days = 7
        Notif = self.env['transit.notification']

        def _exists(alert_type, vehicle_id=False, driver_id=False):
            domain = [('alert_type', '=', alert_type), ('status', '=', 'active')]
            if vehicle_id:
                domain.append(('vehicle_id', '=', vehicle_id))
            if driver_id:
                domain.append(('driver_id', '=', driver_id))
            return Notif.search_count(domain) > 0

        for v in self.env['transit.vehicle'].search([('insurance_expiry', '!=', False)]):
            days = (v.insurance_expiry - today).days
            if days <= warning_days and not _exists('insurance_expiry', vehicle_id=v.id):
                severity = 'critical' if days <= critical_days else 'warning'
                Notif.create({
                    'title': f'Insurance Expiry: {v.name}',
                    'alert_type': 'insurance_expiry',
                    'vehicle_id': v.id,
                    'severity': severity,
                    'description': f'Insurance expires in {days} days ({v.insurance_expiry}).',
                })

        for v in self.env['transit.vehicle'].search([('registration_expiry', '!=', False)]):
            days = (v.registration_expiry - today).days
            if days <= warning_days and not _exists('vehicle_doc_expiry', vehicle_id=v.id):
                severity = 'critical' if days <= critical_days else 'warning'
                Notif.create({
                    'title': f'Registration Expiry: {v.name}',
                    'alert_type': 'vehicle_doc_expiry',
                    'vehicle_id': v.id,
                    'severity': severity,
                    'description': f'Registration expires in {days} days ({v.registration_expiry}).',
                })

        for d in self.env['transit.driver'].search([('license_expiry', '!=', False)]):
            days = (d.license_expiry - today).days
            if days <= warning_days and not _exists('driver_license_expiry', driver_id=d.id):
                severity = 'critical' if days <= critical_days else 'warning'
                Notif.create({
                    'title': f'License Expiry: {d.name}',
                    'alert_type': 'driver_license_expiry',
                    'driver_id': d.id,
                    'severity': severity,
                    'description': f'Driver license expires in {days} days ({d.license_expiry}).',
                })

        for m in self.env['transit.maintenance'].search([
            ('status', '=', 'pending'),
            ('scheduled_date', '<', today),
        ]):
            if not _exists('maintenance_due', vehicle_id=m.vehicle_id.id):
                Notif.create({
                    'title': f'Maintenance Overdue: {m.vehicle_id.name}',
                    'alert_type': 'maintenance_due',
                    'vehicle_id': m.vehicle_id.id,
                    'severity': 'critical',
                    'description': f'Maintenance "{m.name}" was due on {m.scheduled_date}.',
                })