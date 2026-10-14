import os
import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy import create_engine, text


fake = Faker()
Faker.seed(42)
random.seed(42)

SQL_SERVER = "sqlserver-saas-dev.database.windows.net"      # e.g. "sqlserver-saas-dev-XXXX.database.windows.net"
SQL_DB = "sqldb-saas-dev"
SQL_USER = "sqladmin"
SQL_PASSWORD = "PASSWORD"  # Replace with your actual password or use environment variables for security

# Using ODBC Driver 18 with encryption enabled for Azure SQL
CONNECTION_URI = (
    f"mssql+pymssql://{SQL_USER}:{SQL_PASSWORD}@{SQL_SERVER}:1433/{SQL_DB}"
)

engine = create_engine(CONNECTION_URI)

def seed_azure_sql(num_orgs=300, num_users=2500, num_invoices=6000):
    # ------------------------------------------------------------------ #
    # Clean up any previous partial/full seed runs and reset identity seeds
    # so org_id / sub_id references are always consistent.
    # ------------------------------------------------------------------ #
    with engine.begin() as conn:
        print("Cleaning up existing data...")
        conn.execute(text("DELETE FROM dbo.invoices"))
        conn.execute(text("DELETE FROM dbo.subscriptions"))
        conn.execute(text("DELETE FROM dbo.users"))
        conn.execute(text("DELETE FROM dbo.organizations"))
        conn.execute(text("DELETE FROM dbo.plans"))
        # Reseed IDENTITY columns so IDs always start at 1
        conn.execute(text("DBCC CHECKIDENT ('dbo.invoices',       RESEED, 0)"))
        conn.execute(text("DBCC CHECKIDENT ('dbo.subscriptions',  RESEED, 0)"))
        conn.execute(text("DBCC CHECKIDENT ('dbo.users',          RESEED, 0)"))
        conn.execute(text("DBCC CHECKIDENT ('dbo.organizations',  RESEED, 0)"))
        conn.execute(text("DBCC CHECKIDENT ('dbo.plans',          RESEED, 0)"))

    with engine.begin() as conn:
        print("Seeding plans...")
        plans_data = [
            {"plan_name": "Free Tier", "tier": "starter", "monthly_fee": 0.00},
            {"plan_name": "Pro Annual", "tier": "pro", "monthly_fee": 49.00},
            {"plan_name": "Pro Monthly", "tier": "pro", "monthly_fee": 59.00},
            {"plan_name": "Enterprise Scale", "tier": "enterprise", "monthly_fee": 299.00},
            {"plan_name": "Enterprise Custom", "tier": "enterprise", "monthly_fee": 999.00},
        ]
        for p in plans_data:
            conn.execute(
                text("INSERT INTO dbo.plans (plan_name, tier, monthly_fee) VALUES (:plan_name, :tier, :monthly_fee)"),
                p
            )

        print(f"Seeding {num_orgs} organizations...")
        industries = ["Fintech", "Healthcare", "SaaS", "E-commerce", "Logistics", "EdTech"]
        country_variants = [
            ("US", "USA", "United States"),
            ("CA", "CAN", "Canada"),
            ("GB", "GBR", "United Kingdom"),
            ("DE", "DEU", "Germany"),
            ("IN", "IND", "India")
        ]
        orgs = []
        for _ in range(num_orgs):
            name = fake.company()
            if random.random() < 0.15:
                name = f"  {name}  "  # Whitespace flaw
            
            country = random.choice(random.choice(country_variants))  # Format inconsistency
            industry = random.choice(industries) if random.random() > 0.08 else None  # Null flaw
            is_active = 1 if random.random() > 0.08 else 0  # Soft delete
            created_at = fake.date_time_between(start_date="-2y", end_date="-6m")
            
            orgs.append({
                "name": name,
                "industry": industry,
                "country": country,
                "is_active": is_active,
                "created_at": created_at,
                "updated_at": created_at
            })
        conn.execute(
            text("""
                INSERT INTO dbo.organizations (name, industry, country, is_active, created_at, updated_at) 
                VALUES (:name, :industry, :country, :is_active, :created_at, :updated_at)
            """),
            orgs
        )

        # Fetch actual inserted org IDs (safe against identity gaps)
        org_ids = [row[0] for row in conn.execute(text("SELECT org_id FROM dbo.organizations")).fetchall()]

        print(f"Seeding {num_users} users...")
        roles = ["Admin", "Member", "Viewer", "Billing Manager"]
        users = []
        for _ in range(num_users):
            email = fake.unique.email()
            rand_val = random.random()
            if rand_val < 0.15:
                email = email.upper()  # Uppercase flaw
            elif rand_val < 0.18:
                email = email.replace("@", "_at_")  # Malformed email flaw

            created_at = fake.date_time_between(start_date="-6m", end_date="now")
            users.append({
                "org_id": random.choice(org_ids),
                "email": email,
                "role": random.choice(roles),
                "is_active": 1 if random.random() > 0.12 else 0,
                "created_at": created_at,
                "updated_at": created_at
            })
        conn.execute(
            text("""
                INSERT INTO dbo.users (org_id, email, role, is_active, created_at, updated_at) 
                VALUES (:org_id, :email, :role, :is_active, :created_at, :updated_at)
            """),
            users
        )

        print("Seeding subscriptions...")
        # Fetch actual plan IDs from DB
        plan_ids = [row[0] for row in conn.execute(text("SELECT plan_id FROM dbo.plans")).fetchall()]
        subscriptions = []
        for org_id in org_ids:
            sub_count = random.choice([1, 1, 2])
            for _ in range(sub_count):
                status = random.choices(["active", "cancelled", "past_due"], weights=[0.8, 0.15, 0.05])[0]
                started_at = fake.date_time_between(start_date="-18m", end_date="-2m")
                cancelled_at = started_at + timedelta(days=random.randint(30, 90)) if status == "cancelled" else None
                updated_at = cancelled_at if cancelled_at else started_at
                subscriptions.append({
                    "org_id": org_id,
                    "plan_id": random.choice(plan_ids),
                    "status": status,
                    "started_at": started_at,
                    "cancelled_at": cancelled_at,
                    "updated_at": updated_at
                })
        conn.execute(
            text("""
                INSERT INTO dbo.subscriptions (org_id, plan_id, status, started_at, cancelled_at, updated_at) 
                VALUES (:org_id, :plan_id, :status, :started_at, :cancelled_at, :updated_at)
            """),
            subscriptions
        )

        # Fetch actual inserted subscription IDs
        sub_ids = [row[0] for row in conn.execute(text("SELECT subscription_id FROM dbo.subscriptions")).fetchall()]

        total_subs = len(sub_ids)
        print(f"Seeding invoices ({total_subs} subscriptions → variable invoices)...")
        invoices = []
        for sub_id in sub_ids:
            for _ in range(random.randint(1, 4)):
                amount = random.choice([0.00, 49.00, 59.00, 299.00, 999.00])
                status = random.choices(["paid", "failed"], weights=[0.9, 0.1])[0]
                billing_date = fake.date_between(start_date="-1y", end_date="today")
                paid_at = datetime.combine(billing_date, datetime.min.time()) + timedelta(hours=random.randint(1, 48)) if status == "paid" else None
                
                paid_amt = amount if status == "paid" else 0.00
                if status == "paid" and random.random() < 0.03:
                    paid_amt = amount + 25.00  # Overpayment anomaly

                updated_at = paid_at if paid_at else datetime.combine(billing_date, datetime.min.time())
                invoices.append({
                    "subscription_id": sub_id,
                    "amount_due": amount,
                    "amount_paid": paid_amt,
                    "status": status,
                    "billing_date": billing_date,
                    "paid_at": paid_at,
                    "updated_at": updated_at
                })
        conn.execute(
            text("""
                INSERT INTO dbo.invoices (subscription_id, amount_due, amount_paid, status, billing_date, paid_at, updated_at) 
                VALUES (:subscription_id, :amount_due, :amount_paid, :status, :billing_date, :paid_at, :updated_at)
            """),
            invoices
        )

    print("Azure SQL database seeded successfully.")

if __name__ == "__main__":
    seed_azure_sql()