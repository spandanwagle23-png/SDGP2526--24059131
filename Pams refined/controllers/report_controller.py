from config.database import DatabaseConnection
from controllers.apartment_controller import ApartmentController
from controllers.payment_controller import PaymentController
from controllers.maintenance_controller import MaintenanceController

class ReportController:
    def __init__(self):
        self.db = DatabaseConnection.get_instance()
        self.apt_ctrl = ApartmentController()
        self.pay_ctrl = PaymentController()
        self.maint_ctrl = MaintenanceController()

    def occupancy_report(self, location=None):
        locations_query = {}
        if location:
            locations_query["city"] = location
        locations = [l["city"] for l in self.db["locations"].find(locations_query)]
        report = []
        for loc in locations:
            stats = self.apt_ctrl.get_occupancy_stats(loc)
            stats["location"] = loc
            rate = (stats["occupied"] / stats["total"] * 100) if stats["total"] > 0 else 0
            stats["occupancy_rate"] = round(rate, 1)
            report.append(stats)
        return report

    def financial_report(self, location=None):
        return self.pay_ctrl.get_financial_summary(location)

    def maintenance_cost_report(self, location=None):
        return self.maint_ctrl.get_maintenance_cost_report(location)

    def get_all_locations(self):
        return [l["city"] for l in self.db["locations"].find({})]
