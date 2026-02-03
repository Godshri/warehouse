# Smart Warehouse

## Setup

1. Install dependencies:

```
pip install -r requirements.txt
```

2. Configure PostgreSQL:

```
createdb smart_warehouse
```

Default settings are in `smart_warehouse/settings.py`:

- DB name: `smart_warehouse`
- User: `postgres`
- Password: `postgres`
- Host: `localhost`
- Port: `5432`

3. Run migrations:

```
python manage.py makemigrations
python manage.py migrate
```

4. Create admin user:

```
python manage.py createsuperuser
```

5. Run server:

```
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## API

- `POST /api/token/` -> JWT token
- `GET /api/equipment/`
- `POST /api/operations/issue/`
- `POST /api/operations/return/`
- `POST /api/scan/`
- `GET /api/equipment/{id}/qr/`
- `GET /api/equipment/qr_bulk/`
- `GET /api/reports/?format=csv|xlsx`
- `GET /api/notifications/`
- `POST /api/notifications/mark_all_read/`
- `GET /api/notifications/overdue/`
