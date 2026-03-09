-- Update domains for staging environment
-- Run this after restoring the database

BEGIN;

-- Update freshwaterbiodiversity.org to fbis.sta.kartoza.com
UPDATE tenants_domain
SET domain = 'fbis.sta.kartoza.com'
WHERE domain = 'freshwaterbiodiversity.org';

-- Update bims.sanparks.org to sanparks.sta.kartoza.com
UPDATE tenants_domain
SET domain = 'sanparks.sta.kartoza.com'
WHERE domain = 'bims.sanparks.org';

-- Update fada.kartoza.com to fada.sta.kartoza.com
UPDATE tenants_domain
SET domain = 'fada.sta.kartoza.com'
WHERE domain = 'fada.kartoza.com';

-- Update kafue.kartoza.com to kafue.sta.kartoza.com
UPDATE tenants_domain
SET domain = 'kafue.sta.kartoza.com'
WHERE domain = 'kafue.kartoza.com';

-- Update bims.kartoza.com to bims.sta.kartoza.com
UPDATE tenants_domain
SET domain = 'bims.sta.kartoza.com'
WHERE domain = 'bims.kartoza.com';

-- Update fbisafrica.org to fbisafrica.sta.kartoza.com
UPDATE tenants_domain
SET domain = 'fbisafrica.sta.kartoza.com'
WHERE domain = 'fbisafrica.org';

-- Display updated domains
SELECT id, domain, is_primary, tenant_id
FROM tenants_domain
ORDER BY id;

COMMIT;