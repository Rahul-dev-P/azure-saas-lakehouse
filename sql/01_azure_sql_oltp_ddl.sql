-- Drop tables in reverse FK order if re-initializing
IF OBJECT_ID('dbo.invoices', 'U') IS NOT NULL DROP TABLE dbo.invoices;
IF OBJECT_ID('dbo.subscriptions', 'U') IS NOT NULL DROP TABLE dbo.subscriptions;
IF OBJECT_ID('dbo.users', 'U') IS NOT NULL DROP TABLE dbo.users;
IF OBJECT_ID('dbo.organizations', 'U') IS NOT NULL DROP TABLE dbo.organizations;
IF OBJECT_ID('dbo.plans', 'U') IS NOT NULL DROP TABLE dbo.plans;

-- 1. Plans
CREATE TABLE dbo.plans (
    plan_id INT IDENTITY(1,1) PRIMARY KEY,
    plan_name VARCHAR(50) NOT NULL,
    tier VARCHAR(20) NOT NULL,
    monthly_fee DECIMAL(10, 2) NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

-- 2. Organizations
CREATE TABLE dbo.organizations (
    org_id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    industry VARCHAR(100) NULL,
    country VARCHAR(100) NULL,
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

-- 3. Users
CREATE TABLE dbo.users (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    org_id INT NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NULL,
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_users_org FOREIGN KEY (org_id) REFERENCES dbo.organizations(org_id)
);

-- 4. Subscriptions
CREATE TABLE dbo.subscriptions (
    subscription_id INT IDENTITY(1,1) PRIMARY KEY,
    org_id INT NOT NULL,
    plan_id INT NOT NULL,
    status VARCHAR(30) NOT NULL,
    started_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    cancelled_at DATETIME2 NULL,
    updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_subscriptions_org FOREIGN KEY (org_id) REFERENCES dbo.organizations(org_id),
    CONSTRAINT FK_subscriptions_plan FOREIGN KEY (plan_id) REFERENCES dbo.plans(plan_id)
);

-- 5. Invoices
CREATE TABLE dbo.invoices (
    invoice_id INT IDENTITY(1,1) PRIMARY KEY,
    subscription_id INT NOT NULL,
    amount_due DECIMAL(10, 2) NOT NULL,
    amount_paid DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(30) NOT NULL,
    billing_date DATE NOT NULL,
    paid_at DATETIME2 NULL,
    updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_invoices_sub FOREIGN KEY (subscription_id) REFERENCES dbo.subscriptions(subscription_id)
);