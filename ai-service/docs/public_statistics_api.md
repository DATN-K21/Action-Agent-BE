# Public Statistics API

This documentation provides detailed information about the Statistics API endpoints available in the AI Service. The Statistics API enables users to retrieve statistical data and performance metrics about various entities within the system, including users, connected extensions, threads, and assistants.

## Overview

The Statistics API enables you to:

- Retrieve overview statistics for all main entities in the system
- Get entity counts, averages, and percentage changes over various time periods
- Access ranking statistics to identify top performing entities
- Analyze usage patterns and trends with different date ranges
- Monitor system growth and activity

Statistics provide valuable insights into system usage, user activity, and overall platform health. These metrics can be used for reporting, analysis, and decision-making.

## Base Models

### OverviewStatisticsResponse

Base statistics information for a single entity:

| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Total number of entities |
| `avg_per_day` | float | Average number of entities per day over the selected period |
| `percentage_change` | string | Percentage change in entity count compared to the previous period (formatted with % sign) |

### BaseOverviewStatisticsResponse

Complete overview statistics for all entities:

| Field | Type | Description |
|-------|------|-------------|
| `users` | OverviewStatisticsResponse | User statistics |
| `connected_extensions` | OverviewStatisticsResponse | Connected extensions statistics |
| `threads` | OverviewStatisticsResponse | Thread statistics |
| `assistants` | OverviewStatisticsResponse | Assistants statistics |

### RankingStatisticsResponse

Ranking information for a single entity:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Entity ID |
| `score` | float | Score of the entity based on the statistics |
| `rank` | integer | Rank of the entity based on the statistics |
| `display_info` | object | Additional display information (key-value pairs) |

### BaseRankingEntityStatisticsResponse

Ranking statistics for a specific entity type:

| Field | Type | Description |
|-------|------|-------------|
| `data` | array[RankingStatisticsResponse] | List of ranking statistics for the entity |
| `weights` | object | Weights for the ranking statistics, used for calculating scores |

### BaseRankingStatisticsResponse

Complete ranking statistics for all entities:

| Field | Type | Description |
|-------|------|-------------|
| `users` | BaseRankingEntityStatisticsResponse | User ranking statistics |
| `connected_extensions` | BaseRankingEntityStatisticsResponse | Connected extensions ranking statistics (when available) |

## Date Range Options

The Statistics API supports various date range options for filtering data:

| Value | Description |
|-------|-------------|
| `day` | Current day statistics |
| `yesterday` | Previous day statistics |
| `week` | Current week statistics |
| `month` | Current month statistics |
| `quarter` | Current quarter statistics |
| `year` | Current year statistics |
| `last_7_days` | Statistics for the last 7 days |
| `last_30_days` | Statistics for the last 30 days |
| `all_time` | All-time statistics (default if not specified) |

## Endpoints

### Get Statistics Overview

Retrieves overview statistics for all main entities in the system.

**Endpoint:** `GET /statistics/overview`

**Query Parameters:**
- `period` (optional): Date range for statistics (default: "all_time")
  - Accepted values: "day", "yesterday", "week", "month", "quarter", "year", "last_7_days", "last_30_days", ""

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "users": {
      "total": 153,
      "avg_per_day": 2.8,
      "percentage_change": "12.5%"
    },
    "connected_extensions": {
      "total": 42,
      "avg_per_day": 0.9,
      "percentage_change": "5.0%"
    },
    "threads": {
      "total": 875,
      "avg_per_day": 18.2,
      "percentage_change": "24.7%"
    },
    "assistants": {
      "total": 34,
      "avg_per_day": 0.7,
      "percentage_change": "3.0%"
    }
  }
}
```

### Get Statistics Rankings

Retrieves ranking statistics for users and other entities based on their activity and engagement.

**Endpoint:** `GET /statistics/ranking`

**Query Parameters:**
- `period` (optional): Date range for statistics (default: "all_time")
  - Accepted values: "day", "yesterday", "week", "month", "quarter", "year", "last_7_days", "last_30_days", ""

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "users": {
      "data": [
        {
          "id": "user_abc123",
          "score": 94.5,
          "rank": 1,
          "display_info": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "avatar_url": "https://example.com/avatars/john.png"
          }
        },
        {
          "id": "user_def456",
          "score": 89.2,
          "rank": 2,
          "display_info": {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "avatar_url": "https://example.com/avatars/jane.png"
          }
        },
        {
          "id": "user_ghi789",
          "score": 76.8,
          "rank": 3,
          "display_info": {
            "name": "Alex Johnson",
            "email": "alex@example.com",
            "avatar_url": "https://example.com/avatars/alex.png"
          }
        }
      ],
      "weights": {
        "thread_count": 0.3,
        "message_count": 0.2,
        "upload_count": 0.3,
        "assistant_count": 0.2
      }
    }
  }
}
```

## Error Handling

All endpoints use standard HTTP status codes and return consistent error responses:

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 500 | Internal Server Error |

**Error Response Format:**

```json
{
  "status": 500,
  "message": "Internal server error: Error fetching user statistics",
  "data": null
}
```

**Common Error Scenarios:**

1. **Invalid Period Parameter:**
```json
{
  "status": 400,
  "message": "Invalid period parameter"
}
```

2. **Database Error:**
```json
{
  "status": 500,
  "message": "Internal server error: Error connecting to database"
}
```

## Implementation Details

### Overview Statistics Calculation

Overview statistics are calculated using the following approach:

1. **Total Count**: Count of entities created within the specified time period.
2. **Average Per Day**: Total count divided by the number of days in the period.
3. **Percentage Change**: Comparison with the same metric from the previous equivalent time period.

For the "all_time" period, percentage change is not calculated since there's no meaningful previous period for comparison.

### Ranking Statistics Calculation

User rankings are calculated based on a weighted scoring system that considers various activity metrics:

1. **Thread Creation**: Number of threads created by the user
2. **Message Activity**: Number of messages sent in threads
3. **Upload Activity**: Number of uploads made by the user
4. **Assistant Creation**: Number of assistants created by the user

Each metric is assigned a weight (visible in the response), and the final score is calculated as a weighted sum of normalized values.

## Examples

### Get Statistics Overview for Last 7 Days

**Request:**

```bash
curl -X GET "https://your-api-domain/statistics/overview?period=last_7_days" \
  -H "Content-Type: application/json"
```

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "users": {
      "total": 24,
      "avg_per_day": 3.4,
      "percentage_change": "20.0%"
    },
    "connected_extensions": {
      "total": 8,
      "avg_per_day": 1.1,
      "percentage_change": "33.3%"
    },
    "threads": {
      "total": 156,
      "avg_per_day": 22.3,
      "percentage_change": "18.2%"
    },
    "assistants": {
      "total": 6,
      "avg_per_day": 0.9,
      "percentage_change": "50.0%"
    }
  }
}
```

### Get Monthly Rankings

**Request:**

```bash
curl -X GET "https://your-api-domain/statistics/ranking?period=month" \
  -H "Content-Type: application/json"
```

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "users": {
      "data": [
        {
          "id": "user_xyz789",
          "score": 92.1,
          "rank": 1,
          "display_info": {
            "name": "Sarah Williams",
            "email": "sarah.w@example.com",
            "avatar_url": "https://example.com/avatars/sarah.png"
          }
        },
        {
          "id": "user_pqr456",
          "score": 85.6,
          "rank": 2,
          "display_info": {
            "name": "Michael Brown",
            "email": "michael.b@example.com",
            "avatar_url": "https://example.com/avatars/michael.png"
          }
        },
        {
          "id": "user_lmn123",
          "score": 73.9,
          "rank": 3,
          "display_info": {
            "name": "Emily Davis",
            "email": "emily.d@example.com",
            "avatar_url": "https://example.com/avatars/emily.png"
          }
        }
      ],
      "weights": {
        "thread_count": 0.3,
        "message_count": 0.2,
        "upload_count": 0.3,
        "assistant_count": 0.2
      }
    }
  }
}
```

## Best Practices

1. **Efficient Period Selection**: Choose the appropriate date range to minimize data processing and improve response times.

2. **Caching Results**: For frequent requests, consider caching results, especially for longer time periods like "all_time" that change less frequently.

3. **Error Handling**: Implement proper error handling to manage issues like database connectivity problems or invalid parameters.

4. **Using Overview with Rankings**: Combine overview statistics with ranking data to get a complete picture of system usage and identify top contributors.

## Integration Examples

### JavaScript Integration Example

```javascript
// Function to fetch statistics overview
async function fetchStatisticsOverview(period = 'all_time') {
  try {
    const response = await fetch(`https://your-api-domain/statistics/overview?period=${period}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (data.status === 200) {
      return data.data;
    } else {
      console.error(`Error: ${data.message}`);
      return null;
    }
  } catch (error) {
    console.error('Failed to fetch statistics:', error);
    return null;
  }
}

// Function to fetch ranking statistics
async function fetchRankingStatistics(period = 'all_time') {
  try {
    const response = await fetch(`https://your-api-domain/statistics/ranking?period=${period}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (data.status === 200) {
      return data.data;
    } else {
      console.error(`Error: ${data.message}`);
      return null;
    }
  } catch (error) {
    console.error('Failed to fetch rankings:', error);
    return null;
  }
}

// Example usage
async function displayDashboardStatistics() {
  // Get last 30 days statistics
  const overview = await fetchStatisticsOverview('last_30_days');
  if (overview) {
    console.log(`Total Users: ${overview.users.total}`);
    console.log(`User Growth: ${overview.users.percentage_change}`);
    console.log(`Total Threads: ${overview.threads.total}`);
    console.log(`Thread Activity: ${overview.threads.avg_per_day} per day`);
  }
  
  // Get user rankings
  const rankings = await fetchRankingStatistics('last_30_days');
  if (rankings && rankings.users) {
    console.log('Top Users:');
    rankings.users.data.forEach(user => {
      console.log(`${user.rank}. ${user.display_info.name} - Score: ${user.score}`);
    });
  }
}
```

### Python Integration Example

```python
import requests

def fetch_statistics_overview(period='all_time'):
    """Fetch overview statistics from the API."""
    try:
        response = requests.get(
            f"https://your-api-domain/statistics/overview",
            params={"period": period}
        )
        response_data = response.json()
        
        if response_data["status"] == 200:
            return response_data["data"]
        else:
            print(f"Error: {response_data['message']}")
            return None
    except Exception as e:
        print(f"Failed to fetch statistics: {e}")
        return None

def fetch_ranking_statistics(period='all_time'):
    """Fetch ranking statistics from the API."""
    try:
        response = requests.get(
            f"https://your-api-domain/statistics/ranking",
            params={"period": period}
        )
        response_data = response.json()
        
        if response_data["status"] == 200:
            return response_data["data"]
        else:
            print(f"Error: {response_data['message']}")
            return None
    except Exception as e:
        print(f"Failed to fetch rankings: {e}")
        return None

# Example usage
def generate_weekly_report():
    # Get statistics for the last week
    weekly_stats = fetch_statistics_overview('week')
    if weekly_stats:
        print("=== Weekly Statistics Report ===")
        print(f"New Users: {weekly_stats['users']['total']} ({weekly_stats['users']['percentage_change']} change)")
        print(f"New Extensions: {weekly_stats['connected_extensions']['total']}")
        print(f"New Threads: {weekly_stats['threads']['total']}")
        print(f"New Assistants: {weekly_stats['assistants']['total']}")
        
    # Get top users of the week
    weekly_rankings = fetch_ranking_statistics('week')
    if weekly_rankings:
        print("\n=== Top Users This Week ===")
        for user in weekly_rankings['users']['data'][:5]:  # Top 5 users
            print(f"{user['rank']}. {user['display_info'].get('name', user['id'])} - Score: {user['score']}")
```

## Performance Considerations

1. **Database Indexing**: The Statistics API benefits from proper indexing on the `created_at` and `is_deleted` fields for all entity tables to optimize date range queries.

2. **Data Volume**: For large datasets, consider limiting the time ranges available for querying or implementing pagination for ranking results.

3. **Concurrent Requests**: The API is designed to handle multiple concurrent requests efficiently.

4. **Background Processing**: For systems with high data volume, consider pre-calculating statistics periodically in a background process and serving cached results.

## Security Notes

1. **Data Privacy**: All statistics are aggregated and do not expose sensitive user information. 

2. **Access Control**: Depending on implementation, you may want to restrict certain statistics to administrative users only.

3. **Rate Limiting**: Consider implementing rate limiting to prevent abuse of the statistics endpoints.

This comprehensive API documentation provides developers with all the information needed to effectively work with the Statistics API endpoints.
