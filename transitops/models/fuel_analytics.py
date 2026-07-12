# -*- coding: utf-8 -*-
from odoo import models, api
from collections import defaultdict


class FuelAnalytics(models.AbstractModel):
    """Fuel analytics computation — no stored table, pure computed."""
    _name = 'transit.fuel.analytics'
    _description = 'Fuel Analytics'

    @api.model
    def get_summary(self):
        """Return aggregated fuel KPIs."""
        fuels = self.env['transit.fuel'].search([])
        total_liters = sum(fuels.mapped('quantity_liters'))
        total_cost = sum(fuels.mapped('total_cost'))
        avg_cost = total_cost / total_liters if total_liters else 0.0

        # Per-vehicle aggregation
        vehicle_data = defaultdict(lambda: {'liters': 0.0, 'cost': 0.0, 'name': ''})
        for f in fuels:
            vid = f.vehicle_id.id
            vehicle_data[vid]['liters'] += f.quantity_liters
            vehicle_data[vid]['cost'] += f.total_cost
            vehicle_data[vid]['name'] = f.vehicle_id.name or ''

        highest_consuming = max(vehicle_data.values(), key=lambda x: x['liters'], default={})
        most_efficient = self._most_efficient_vehicle()

        return {
            'total_liters': round(total_liters, 2),
            'total_cost': round(total_cost, 2),
            'avg_cost_per_liter': round(avg_cost, 2),
            'highest_consuming_vehicle': highest_consuming.get('name', '-'),
            'most_efficient_vehicle': most_efficient,
            'per_vehicle': [
                {'name': v['name'], 'liters': round(v['liters'], 2), 'cost': round(v['cost'], 2)}
                for v in vehicle_data.values()
            ],
        }

    @api.model
    def _most_efficient_vehicle(self):
        """Vehicle with highest km/L ratio using trip odometer data."""
        trips = self.env['transit.trip'].search([
            ('status', '=', 'completed'),
            ('odometer_start', '>', 0),
            ('odometer_end', '>', 0),
        ])
        efficiency = {}
        for trip in trips:
            vid = trip.vehicle_id.id
            km = max(0, trip.odometer_end - trip.odometer_start)
            fuel_used = sum(trip.fuel_ids.mapped('quantity_liters'))
            if fuel_used > 0:
                efficiency.setdefault(vid, {'km': 0.0, 'fuel': 0.0, 'name': trip.vehicle_id.name or ''})
                efficiency[vid]['km'] += km
                efficiency[vid]['fuel'] += fuel_used
        if not efficiency:
            return '-'
        best = max(efficiency.values(), key=lambda x: x['km'] / x['fuel'] if x['fuel'] else 0)
        return best.get('name', '-')

    @api.model
    def get_monthly_fuel(self):
        """Return monthly fuel consumption and cost for the last 12 months."""
        self.env.cr.execute("""
            SELECT
                TO_CHAR(date, 'YYYY-MM') AS month,
                SUM(quantity_liters) AS liters,
                SUM(total_cost) AS cost
            FROM transit_fuel
            WHERE date >= (CURRENT_DATE - INTERVAL '12 months')
            GROUP BY month
            ORDER BY month
        """)
        rows = self.env.cr.dictfetchall()
        return rows
