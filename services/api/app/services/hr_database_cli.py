from app.core.config import get_settings
from app.services.hr_database_service import HRDatabaseService


def main() -> None:
    service = HRDatabaseService(get_settings())
    service.ensure_database(force_reset=True)
    print(f"Seeded HR database at {service.database_path}")


if __name__ == "__main__":
    main()
