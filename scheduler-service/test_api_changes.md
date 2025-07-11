# Test API Changes for Enhanced Job Filtering

## Changes Made

### 1. Updated JobService.get_jobs()
- Added `assistant_id` and `team_id` parameters
- Both parameters are optional (Optional[str])
- If provided, jobs will be filtered by these values
- If empty/None, no filtering is applied for these fields

### 2. Updated API Endpoint list_jobs()
- Added `assistant_id` and `team_id` query parameters
- Both are optional Query parameters
- Updated documentation to reflect new filtering options

## API Usage Examples

### List all jobs for a user
```
GET /api/v1/jobs/
Headers:
  x_user_id: user123
  x_user_role: member
```

### List jobs filtered by assistant_id
```
GET /api/v1/jobs/?assistant_id=assistant-456
Headers:
  x_user_id: user123
  x_user_role: member
```

### List jobs filtered by team_id
```
GET /api/v1/jobs/?team_id=team-789
Headers:
  x_user_id: user123
  x_user_role: member
```

### List jobs filtered by both assistant_id and team_id
```
GET /api/v1/jobs/?assistant_id=assistant-456&team_id=team-789
Headers:
  x_user_id: user123
  x_user_role: member
```

### List jobs with pagination and all filters
```
GET /api/v1/jobs/?skip=0&limit=10&status=pending&job_type=recurring&assistant_id=assistant-456&team_id=team-789
Headers:
  x_user_id: user123
  x_user_role: member
```

## Behavior

- If `assistant_id` is provided, only jobs with that assistant_id will be returned
- If `team_id` is provided, only jobs with that team_id will be returned
- If both are provided, jobs must match both criteria
- If neither is provided, all jobs for the user are returned (existing behavior)
- Admin and super admin users can see all jobs regardless of created_by filter
- Regular users can only see their own jobs (jobs where created_by = x_user_id)

## Database Queries

The service now generates SQL queries like:
```sql
SELECT * FROM scheduled_jobs 
WHERE is_deleted = false 
  AND created_by = 'user123'  -- Only for non-admin users
  AND assistant_id = 'assistant-456'  -- If provided
  AND team_id = 'team-789'  -- If provided
  AND status = 'pending'  -- If provided
  AND job_type = 'recurring'  -- If provided
ORDER BY created_at DESC
LIMIT 10 OFFSET 0;
```
