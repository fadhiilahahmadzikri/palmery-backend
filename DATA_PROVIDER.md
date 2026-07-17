# Data Provider Strategy

This application supports a switchable data provider architecture via the **Repository Pattern + Dependency Injection**. This allows the application to seamlessly switch between using a PostgreSQL production database and a JSON-based demo dataset without altering the API contracts, endpoint implementations, or frontend code.

## Architecture

The system uses `IHarvestRepository` and `IConfigRepository` interfaces. The concrete implementation injected into the API endpoints depends on the `DATA_PROVIDER` environment variable.

```
       [ FastAPI Route ]
               │
               ▼
 [ Repository Dependency Injector ] (src/api/dependencies.py)
               │
      ├── (Check DATA_PROVIDER) ──┐
      ▼                           ▼
DatabaseRepository         DemoRepository
      │                           │
      ▼                           ▼
  PostgreSQL                  JSON files
```

## How to Switch Providers

To change the data source, modify the `.env` file in the `backend/` directory or set the environment variable directly.

### 1. Production Mode (Default)
Uses the PostgreSQL database.
```env
DATA_PROVIDER=database
```

### 2. Demo Mode
Uses the JSON datasets located in the `backend/demo/` directory.
```env
DATA_PROVIDER=demo
```

**Note:** After changing the `.env` file, restart the FastAPI server for the changes to take effect.

## Generating Demo Data

The demo datasets are not hardcoded. They are generated using a Python script leveraging the `Faker` library.

To regenerate the demo dataset (e.g. 500 realistic harvest records, configs, and tiers):

1. Activate the virtual environment:
   ```bash
   .venv\Scripts\activate
   ```
2. Run the generator script:
   ```bash
   python seed/generate_demo_data.py
   ```

This will populate `backend/demo/harvest.json`, `backend/demo/config.json`, and `backend/demo/tiers.json` with realistic, randomized business data spanning the last 6 months.

## Adding New Providers

Because the architecture relies on standard interfaces, you can easily add new providers in the future (e.g., `CSVDataProvider`, `ExternalApiProvider`) by:
1. Creating a new class implementing the respective interface.
2. Adding a new `DATA_PROVIDER` configuration condition in `src/api/dependencies.py`.
