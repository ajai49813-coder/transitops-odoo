/** @odoo-module **/
/**
 * TransitOps Dashboard — OWL 2 Component (Odoo 17)
 * Fetches KPIs and chart data from the backend and renders them.
 */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, useState } from "@odoo/owl";

// Chart.js is loaded via CDN or Odoo's bundled assets.
// We reference the global Chart object.

class TransitOpsDashboard extends Component {
    static template = "transitops.Dashboard";

    setup() {
        this.rpc = useService("rpc");
        this.action = useService("action");

        this.state = useState({
            kpis: {},
            charts: {},
            loading: true,
            error: null,
        });

        onMounted(async () => {
            await this._loadData();
        });
    }

    async _loadData() {
        try {
            const [kpis, charts] = await Promise.all([
                this.rpc("/web/dataset/call_kw", {
                    model: "transit.dashboard",
                    method: "get_kpis",
                    args: [],
                    kwargs: {},
                }),
                this.rpc("/web/dataset/call_kw", {
                    model: "transit.dashboard",
                    method: "get_chart_data",
                    args: [],
                    kwargs: {},
                }),
            ]);
            this.state.kpis = kpis;
            this.state.charts = charts;
            this.state.loading = false;
            // Render charts after DOM update
            setTimeout(() => this._renderCharts(), 50);
        } catch (e) {
            this.state.error = "Failed to load dashboard data.";
            this.state.loading = false;
        }
    }

    _renderCharts() {
        const charts = this.state.charts;
        if (!charts || typeof Chart === "undefined") return;

        this._destroyChart("fuelConsumptionChart");
        this._destroyChart("fuelCostChart");
        this._destroyChart("tripStatusChart");
        this._destroyChart("vehicleUsageChart");
        this._destroyChart("fuelEfficiencyChart");
        this._destroyChart("monthlyTripChart");

        // Fuel Consumption by Month
        const monthlyFuel = charts.monthly_fuel || [];
        this._createChart("fuelConsumptionChart", {
            type: "bar",
            data: {
                labels: monthlyFuel.map((r) => r.month || ""),
                datasets: [{
                    label: "Fuel Consumed (L)",
                    data: monthlyFuel.map((r) => parseFloat(r.liters) || 0),
                    backgroundColor: "rgba(54, 162, 235, 0.7)",
                }],
            },
            options: { responsive: true, plugins: { title: { display: true, text: "Fuel Consumption by Month" } } },
        });

        // Fuel Cost by Month
        this._createChart("fuelCostChart", {
            type: "line",
            data: {
                labels: monthlyFuel.map((r) => r.month || ""),
                datasets: [{
                    label: "Fuel Cost",
                    data: monthlyFuel.map((r) => parseFloat(r.cost) || 0),
                    borderColor: "rgba(255, 99, 132, 1)",
                    backgroundColor: "rgba(255, 99, 132, 0.2)",
                    fill: true,
                }],
            },
            options: { responsive: true, plugins: { title: { display: true, text: "Fuel Cost by Month" } } },
        });

        // Trips by Status
        const statusData = charts.trips_by_status || {};
        const statusLabels = Object.keys(statusData);
        this._createChart("tripStatusChart", {
            type: "doughnut",
            data: {
                labels: statusLabels,
                datasets: [{
                    data: statusLabels.map((k) => statusData[k] || 0),
                    backgroundColor: ["#6c757d", "#0dcaf0", "#ffc107", "#198754", "#dc3545"],
                }],
            },
            options: { responsive: true, plugins: { title: { display: true, text: "Trips by Status" } } },
        });

        // Vehicle Usage
        const vehicleUsage = charts.vehicle_usage || [];
        this._createChart("vehicleUsageChart", {
            type: "bar",
            data: {
                labels: vehicleUsage.map((r) => r.name || ""),
                datasets: [{
                    label: "Trips",
                    data: vehicleUsage.map((r) => parseInt(r.trip_count) || 0),
                    backgroundColor: "rgba(75, 192, 192, 0.7)",
                }],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                plugins: { title: { display: true, text: "Vehicle Usage (Top 10)" } },
            },
        });

        // Fuel Efficiency
        const efficiency = charts.fuel_efficiency || [];
        this._createChart("fuelEfficiencyChart", {
            type: "bar",
            data: {
                labels: efficiency.map((r) => r.name || ""),
                datasets: [{
                    label: "km/L",
                    data: efficiency.map((r) => parseFloat(r.efficiency) || 0),
                    backgroundColor: "rgba(153, 102, 255, 0.7)",
                }],
            },
            options: { responsive: true, plugins: { title: { display: true, text: "Fuel Efficiency (km/L)" } } },
        });

        // Monthly Trip Trend
        const monthlyTrips = charts.monthly_trips || [];
        this._createChart("monthlyTripChart", {
            type: "line",
            data: {
                labels: monthlyTrips.map((r) => r.month || ""),
                datasets: [{
                    label: "Trips",
                    data: monthlyTrips.map((r) => parseInt(r.count) || 0),
                    borderColor: "rgba(255, 159, 64, 1)",
                    backgroundColor: "rgba(255, 159, 64, 0.2)",
                    fill: true,
                }],
            },
            options: { responsive: true, plugins: { title: { display: true, text: "Monthly Trip Trend" } } },
        });
    }

    _chartInstances = {};

    _destroyChart(id) {
        if (this._chartInstances[id]) {
            this._chartInstances[id].destroy();
            delete this._chartInstances[id];
        }
    }

    _createChart(id, config) {
        const canvas = document.getElementById(id);
        if (!canvas) return;
        this._chartInstances[id] = new Chart(canvas.getContext("2d"), config);
    }

    /** Navigate to a model list view */
    openModel(model) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: model,
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
        });
    }

    openAlerts() {
        this.action.doAction("transitops.action_transit_notification");
    }
}

registry.category("actions").add("transitops_dashboard", TransitOpsDashboard);
