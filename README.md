# Posudba opreme (backend)

Web aplikacija za posudbu fakultetske opreme. Ovaj repozitorij sadrži backend (`api/`) i prazno mjesto za frontend (`web/`, 2. dio projekta).

## Tehnologije

FastAPI, Pydantic, SQLAlchemy 2.0, Alembic, PostgreSQL, JWT (PyJWT), bcrypt, pytest, freezegun.

## Uloge

- `student`: vidi opremu, posuđuje je, te vidi i mijenja samo svoje posudbe.
- `admin`: upravlja opremom i vidi sve posudbe.

## Poslovna pravila

- Student može imati najviše 3 aktivne posudbe (`loan_limit_reached`).
- Posuđena oprema ne može se ponovno posuditi dok se ne vrati (`equipment_unavailable`).
- Rok posudbe je 14 dana.
- Posudba se može produljiti jednom, za 7 dana (`already_extended`), i to samo prije isteka roka (`loan_overdue`).
- Vraćena posudba ne može se ponovno vratiti ni produljiti (`already_returned`).
- Tuđa posudba za studenta ne postoji: odgovor je 404 `loan_not_found`.

## Pokretanje

Potrebni su Python 3 i Docker.

1. Baza:

```
docker run --name posudba-db -e POSTGRES_PASSWORD=lozinka -p 5432:5432 -d postgres:16
docker exec posudba-db psql -U postgres -c "CREATE DATABASE posudba;"
```

2. Konfiguracija (u mapi `api`):

```
cp .env.example .env
```

U `.env` upiši lozinku baze i novi tajni ključ (`python -c "import secrets; print(secrets.token_hex(32))"`).

3. Okruženje i paketi:

```
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

4. Migracije i početni podaci (skriptu je sigurno pokrenuti više puta):

```
alembic upgrade head
python -m app.seed
```

Početni korisnici: `admin` / `admin123`, `student1` / `student123`, `student2` / `student123`.

5. Server:

```
uvicorn app.main:app --reload
```

Dokumentacija: http://127.0.0.1:8000/docs

## Testovi

```
docker exec posudba-db psql -U postgres -c "CREATE DATABASE posudba_test;"
python -m pytest -q
```

Testovi koriste zasebnu bazu `posudba_test`. Pravila vezana uz vrijeme testirana su zamrznutim vremenom (freezegun).

## Krajnje točke

| Metoda | Putanja | Tko |
|---|---|---|
| POST | /auth/login | svi |
| POST | /auth/refresh | svi (s refresh tokenom) |
| GET | /auth/me | prijavljeni |
| GET | /equipment | prijavljeni (limit, offset) |
| GET | /equipment/{id} | prijavljeni |
| POST | /equipment | admin |
| PATCH | /equipment/{id} | admin |
| DELETE | /equipment/{id} | admin |
| POST | /loans | prijavljeni |
| GET | /loans | prijavljeni (limit, offset, active); student vidi svoje, admin sve |
| GET | /loans/{id} | vlasnik ili admin |
| POST | /loans/{id}/return | vlasnik ili admin |
| POST | /loans/{id}/extend | vlasnik ili admin |

## Format pogrešaka

Sve pogreške imaju oblik `{"code": "...", "message": "..."}`. Kriva lozinka i nepostojeće korisničko ime vraćaju isti odgovor (401 `invalid_credentials`).