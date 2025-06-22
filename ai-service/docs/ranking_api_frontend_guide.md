# Ranking API Frontend Integration Guide

## API Endpoint
```
GET /api/v1/statistics/ranking?period={period}
```

## Response Structure

### Top-Level Response
```json
{
  "status": 200,
  "data": {
    "users": [...],
    "connected_extensions": [...]
  },
  "message": "Success"
}
```

### Individual Ranking Item Structure
```json
{
  "id": "user-or-extension-id",
  "name": "Display Name",
  "score": 85.5,
  "rank": 1,
  "entity_type": "user", // or "extension"
  "score_breakdown": {
    "uploads": 45.0,     // For users: upload count * 3
    "threads": 20.0,     // For users: thread count * 2
    "assistants": 20.0,  // For users: assistant count * 4
    "skills": 50.0,      // For extensions: skill count * 5
    "connection_status": 10.0, // For extensions: 10 if successful
    "total": 85.0
  },
  "display_info": {
    // For users:
    "username": "john_doe",
    "email": "john@example.com",
    "upload_count": "15",
    "thread_count": "10",
    "assistant_count": "5",
    
    // For extensions:
    "extension_enum": "slack_integration",
    "connection_status": "success",
    "skill_count": "10"
  }
}
```

## Frontend Table Implementation

### 1. **User Rankings Table**

#### Columns to Display:
```javascript
const userColumns = [
  { key: 'rank', label: '#' },
  { key: 'name', label: 'User Name' },
  { key: 'username', label: 'Username' },
  { key: 'score', label: 'Activity Score' },
  { key: 'uploads', label: 'Uploads' },
  { key: 'threads', label: 'Threads' },
  { key: 'assistants', label: 'Assistants' }
];
```

#### Score Breakdown Display:
- **Total Score**: Display as a badge or colored number
- **Score Components**: Show as a stacked progress bar or tooltip
  - Uploads: Green (high value - 3pts each)
  - Assistants: Blue (highest value - 4pts each)  
  - Threads: Orange (medium value - 2pts each)

#### Example Row Rendering:
```jsx
const UserRankingRow = ({ user }) => (
  <tr>
    <td>#{user.rank}</td>
    <td>
      <div>
        <strong>{user.name}</strong>
        <br />
        <small className="text-muted">{user.display_info.email}</small>
      </div>
    </td>
    <td>{user.display_info.username}</td>
    <td>
      <span className="badge bg-primary">{user.score.toFixed(1)}</span>
      <ScoreBreakdownTooltip breakdown={user.score_breakdown} />
    </td>
    <td>{user.display_info.upload_count}</td>
    <td>{user.display_info.thread_count}</td>
    <td>{user.display_info.assistant_count}</td>
  </tr>
);
```

### 2. **Extension Rankings Table**

#### Columns to Display:
```javascript
const extensionColumns = [
  { key: 'rank', label: '#' },
  { key: 'name', label: 'Extension Name' },
  { key: 'status', label: 'Status' },
  { key: 'score', label: 'Activity Score' },
  { key: 'skills', label: 'Skills Created' }
];
```

#### Status Display:
```jsx
const StatusBadge = ({ status }) => {
  const badgeClass = status === 'success' ? 'bg-success' : 
                    status === 'pending' ? 'bg-warning' : 'bg-danger';
  return <span className={`badge ${badgeClass}`}>{status}</span>;
};
```

### 3. **Score Visualization Components**

#### Score Breakdown Tooltip:
```jsx
const ScoreBreakdownTooltip = ({ breakdown }) => (
  <div className="score-breakdown">
    <small>Score Breakdown:</small>
    {Object.entries(breakdown).map(([key, value]) => (
      key !== 'total' && (
        <div key={key}>
          <span className="score-component">{key}:</span>
          <span className="score-value">{value.toFixed(1)}</span>
        </div>
      )
    ))}
  </div>
);
```

#### Activity Score Progress Bar:
```jsx
const ActivityScoreBar = ({ score, maxScore = 100 }) => {
  const percentage = Math.min((score / maxScore) * 100, 100);
  const getColorClass = (pct) => {
    if (pct >= 80) return 'bg-success';
    if (pct >= 60) return 'bg-info';
    if (pct >= 40) return 'bg-warning';
    return 'bg-danger';
  };
  
  return (
    <div className="progress">
      <div 
        className={`progress-bar ${getColorClass(percentage)}`}
        style={{ width: `${percentage}%` }}
        aria-valuenow={score}
        aria-valuemin="0"
        aria-valuemax={maxScore}
      >
        {score.toFixed(1)}
      </div>
    </div>
  );
};
```

## Activity Scoring Logic (For Frontend Understanding)

### User Activity Score:
- **Uploads**: 3 points each (high engagement indicator)
- **Threads**: 2 points each (conversation starter)
- **Assistants**: 4 points each (advanced feature usage)

### Extension Activity Score:
- **Skills Created**: 5 points each (extension utility)
- **Connection Success**: 10 points (reliability bonus)

### Period Filtering:
- All queries respect the selected time period
- Scores are calculated only for activities within the period
- Available periods: day, yesterday, week, month, quarter, year, last_7_days, last_30_days, all_time

## Usage Examples

### Complete Table Component:
```jsx
const RankingTable = ({ data, type }) => {
  const columns = type === 'users' ? userColumns : extensionColumns;
  
  return (
    <div className="ranking-table">
      <h3>Top 10 Most Active {type === 'users' ? 'Users' : 'Extensions'}</h3>
      <table className="table table-striped">
        <thead>
          <tr>
            {columns.map(col => (
              <th key={col.key}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map(item => (
            type === 'users' ? 
              <UserRankingRow key={item.id} user={item} /> :
              <ExtensionRankingRow key={item.id} extension={item} />
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

### API Integration:
```javascript
const fetchRankingData = async (period = 'all_time') => {
  try {
    const response = await fetch(`/api/v1/statistics/ranking?period=${period}`);
    const result = await response.json();
    
    if (result.status === 200) {
      return {
        users: result.data.users,
        extensions: result.data.connected_extensions
      };
    }
    throw new Error(result.message);
  } catch (error) {
    console.error('Error fetching ranking data:', error);
    throw error;
  }
};
```

## Industry Best Practices Implemented

1. **Composite Scoring**: Multiple activity metrics combined for fair ranking
2. **Transparency**: Score breakdown available for audit/explanation
3. **Flexibility**: Different scoring for different entity types
4. **Time-based Analysis**: Period filtering for trend analysis
5. **Rich Metadata**: Additional display information for context
6. **Pagination**: Limited to top 10 for performance and UX

This implementation follows industry standards used by platforms like GitHub (contribution graphs), Stack Overflow (reputation system), and Slack (activity metrics).
