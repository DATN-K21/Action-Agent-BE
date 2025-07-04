# Public Member API

This documentation provides comprehensive details about the Member API endpoints available in the AI Service. The Member API enables management of team members within assistants, including creating, retrieving, updating, and deleting members with their associated skills and uploads.

## Overview

The Member API enables you to:

- Create new team members with specific roles and configurations
- Retrieve individual members or lists of members from teams
- Update member information, including skills and accessible uploads
- Delete members from teams
- Manage member positioning for UI drag-and-drop functionality
- Configure AI model settings for each member
- Associate skills and uploads with members

Members represent individual AI agents within a team that can have different roles, capabilities, and access to resources.

## Base Models

### MemberBase

Core member information structure:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique member name (1-64 alphanumeric characters, underscores, hyphens only) |
| `backstory` | string | No | Brief backstory of the member (max 1000 characters) |
| `role` | string | No | The role of the member (max 100 characters) |
| `type` | string | Yes | Member type: "leader", "worker", or "freelancer" |
| `position_x` | float | Yes | X coordinate for UI positioning |
| `position_y` | float | Yes | Y coordinate for UI positioning |
| `source` | integer | No | Source identifier for the member |
| `provider` | string | Yes | AI provider (e.g., "openai", "anthropic") |
| `model` | string | Yes | AI model (e.g., "gpt-3.5-turbo", "claude-2") |
| `temperature` | float | Yes | Response temperature (0.0-1.0, default: 0) |
| `interrupt` | boolean | Yes | Whether the member can be interrupted (default: false) |

### CreateMemberRequest

Request structure for creating a new member - inherits all fields from MemberBase.

### UpdateMemberRequest

Request structure for updating a member:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Updated member name |
| `backstory` | string | No | Updated backstory |
| `role` | string | No | Updated role |
| `type` | string | No | Updated member type |
| `team_id` | integer | No | Updated team ID |
| `position_x` | float | No | Updated X coordinate |
| `position_y` | float | No | Updated Y coordinate |
| `skills` | SkillResponse[] | No | List of associated skills |
| `uploads` | UploadResponse[] | No | List of accessible uploads |
| `provider` | string | No | Updated AI provider |
| `model` | string | No | Updated AI model |
| `temperature` | float | No | Updated temperature (0.0-1.0) |
| `interrupt` | boolean | No | Updated interrupt setting |

### MemberResponse

Response structure for member data:

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique member identifier |
| `belongs_to` | integer | Team ID the member belongs to |
| `skills` | SkillResponse[] | List of associated skills |
| `uploads` | UploadResponse[] | List of accessible uploads |
| All MemberBase fields | - | All base member information |

### MembersResponse

Response structure for multiple members:

| Field | Type | Description |
|-------|------|-------------|
| `members` | MemberResponse[] | Array of member objects |
| `count` | integer | Total number of members |

### SkillResponse

Associated skill information:

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique skill identifier |
| `name` | string | Skill name |
| `description` | string | Skill description |
| `display_name` | string | Display name for UI |
| `strategy` | string | Storage strategy ("definition" or "file") |
| `tool_definition` | object | Tool definition configuration |
| `reference_type` | string | Connected service type ("none", "extension", "mcp") |

### UploadResponse

Associated upload information:

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique upload identifier |
| `name` | string | Upload name |
| `description` | string | Upload description |
| `file_type` | string | Type of uploaded file |
| `web_url` | string | Web URL of the upload |
| `status` | string | Upload status |
| `last_modified` | datetime | Last modification timestamp |

## Endpoints

### Get All Members

Retrieves all members from a specific assistant/team.

**Endpoint:** `GET /member/`

**Query Parameters:**
- `assistant_id` (required): The ID of the assistant/team
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 100)

**Headers:**
- `x-user-id` (required): User identifier
- `x-user-role` (required): User role ("admin", "super admin", or user role)

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "members": [
      {
        "id": 1,
        "name": "research_specialist",
        "backstory": "An experienced researcher with expertise in data analysis",
        "role": "Senior Researcher",
        "type": "worker",
        "position_x": 100.0,
        "position_y": 200.0,
        "source": null,
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.7,
        "interrupt": false,
        "belongs_to": 123,
        "skills": [
          {
            "id": 1,
            "name": "web_search",
            "description": "Advanced web search capabilities",
            "display_name": "Web Search",
            "strategy": "definition",
            "tool_definition": {...},
            "reference_type": "extension"
          }
        ],
        "uploads": [
          {
            "id": 1,
            "name": "research_guidelines.pdf",
            "description": "Internal research guidelines document",
            "file_type": "document",
            "web_url": "https://example.com/docs/research_guidelines.pdf",
            "status": "completed",
            "last_modified": "2025-07-01T10:30:00Z"
          }
        ],
        "created_at": "2025-07-01T09:00:00Z",
        "updated_at": "2025-07-01T15:30:00Z"
      }
    ],
    "count": 1
  }
}
```

### Get Member by ID

Retrieves a specific member by their ID.

**Endpoint:** `GET /member/{member_id}`

**Path Parameters:**
- `member_id` (required): The ID of the member to retrieve

**Query Parameters:**
- `assistant_id` (required): The ID of the assistant/team

**Headers:**
- `x-user-id` (required): User identifier
- `x-user-role` (required): User role

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "id": 1,
    "name": "data_analyst",
    "backstory": "Specialized in statistical analysis and data visualization",
    "role": "Data Analyst",
    "type": "worker",
    "position_x": 150.0,
    "position_y": 250.0,
    "source": null,
    "provider": "anthropic",
    "model": "claude-3-sonnet",
    "temperature": 0.3,
    "interrupt": true,
    "belongs_to": 123,
    "skills": [
      {
        "id": 2,
        "name": "data_visualization",
        "description": "Create charts and graphs from data",
        "display_name": "Data Visualization",
        "strategy": "definition",
        "tool_definition": {
          "name": "create_chart",
          "description": "Generate data visualizations",
          "parameters": {
            "type": "object",
            "properties": {
              "data": {"type": "array"},
              "chart_type": {"type": "string"}
            }
          }
        },
        "reference_type": "none"
      }
    ],
    "uploads": [],
    "created_at": "2025-07-01T09:15:00Z",
    "updated_at": "2025-07-01T14:45:00Z"
  }
}
```

### Create Member

Creates a new member in the specified team.

**Endpoint:** `POST /member/`

**Query Parameters:**
- `assistant_id` (required): The ID of the assistant/team

**Headers:**
- `x-user-id` (required): User identifier
- `x-user-role` (required): User role

**Request Body:**

```json
{
  "name": "content_writer",
  "backstory": "Creative writer specializing in technical documentation and marketing content",
  "role": "Content Specialist",
  "type": "freelancer",
  "position_x": 300.0,
  "position_y": 100.0,
  "source": 1,
  "provider": "openai",
  "model": "gpt-4-turbo",
  "temperature": 0.8,
  "interrupt": false
}
```

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "id": 2,
    "name": "content_writer",
    "backstory": "Creative writer specializing in technical documentation and marketing content",
    "role": "Content Specialist",
    "type": "freelancer",
    "position_x": 300.0,
    "position_y": 100.0,
    "source": 1,
    "provider": "openai",
    "model": "gpt-4-turbo",
    "temperature": 0.8,
    "interrupt": false,
    "belongs_to": 123,
    "skills": [],
    "uploads": [],
    "created_at": "2025-07-02T10:00:00Z",
    "updated_at": "2025-07-02T10:00:00Z"
  }
}
```

### Update Member

Updates an existing member's information, including their skills and accessible uploads.

**Endpoint:** `PUT /member/{member_id}`

**Path Parameters:**
- `member_id` (required): The ID of the member to update

**Query Parameters:**
- `assistant_id` (required): The ID of the assistant/team

**Headers:**
- `x-user-id` (required): User identifier
- `x-user-role` (required): User role

**Request Body:**

```json
{
  "name": "senior_content_writer",
  "role": "Senior Content Specialist",
  "temperature": 0.9,
  "skills": [
    {
      "id": 3,
      "name": "content_generation",
      "description": "Generate various types of content"
    },
    {
      "id": 4,
      "name": "seo_optimization",
      "description": "Optimize content for search engines"
    }
  ],
  "uploads": [
    {
      "id": 2,
      "name": "style_guide.pdf",
      "description": "Company writing style guide"
    }
  ]
}
```

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "id": 2,
    "name": "senior_content_writer",
    "backstory": "Creative writer specializing in technical documentation and marketing content",
    "role": "Senior Content Specialist",
    "type": "freelancer",
    "position_x": 300.0,
    "position_y": 100.0,
    "source": 1,
    "provider": "openai",
    "model": "gpt-4-turbo",
    "temperature": 0.9,
    "interrupt": false,
    "belongs_to": 123,
    "skills": [
      {
        "id": 3,
        "name": "content_generation",
        "description": "Generate various types of content",
        "display_name": "Content Generation",
        "strategy": "definition",
        "tool_definition": {...},
        "reference_type": "none"
      },
      {
        "id": 4,
        "name": "seo_optimization",
        "description": "Optimize content for search engines",
        "display_name": "SEO Optimization",
        "strategy": "definition",
        "tool_definition": {...},
        "reference_type": "extension"
      }
    ],
    "uploads": [
      {
        "id": 2,
        "name": "style_guide.pdf",
        "description": "Company writing style guide",
        "file_type": "document",
        "web_url": "https://example.com/docs/style_guide.pdf",
        "status": "completed",
        "last_modified": "2025-07-01T08:00:00Z"
      }
    ],
    "created_at": "2025-07-02T10:00:00Z",
    "updated_at": "2025-07-02T11:30:00Z"
  }
}
```

### Delete Member

Soft deletes a member from the team (marks as deleted rather than permanently removing).

**Endpoint:** `DELETE /member/{member_id}`

**Path Parameters:**
- `member_id` (required): The ID of the member to delete

**Query Parameters:**
- `assistant_id` (required): The ID of the assistant/team

**Headers:**
- `x-user-id` (required): User identifier
- `x-user-role` (required): User role

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "message": "Member deleted successfully"
  }
}
```

## Error Handling

All endpoints use standard HTTP status codes and return consistent error responses:

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request (validation errors, duplicate names, protected names) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found (member or assistant not found) |
| 500 | Internal Server Error |

**Error Response Format:**

```json
{
  "status": 400,
  "message": "Member with this name already exists",
  "data": null
}
```

**Common Error Scenarios:**

1. **Duplicate Member Name:**
```json
{
  "status": 400,
  "message": "Member with this name already exists"
}
```

2. **Protected Name:**
```json
{
  "status": 400,
  "message": "Name is a protected name. Choose another name."
}
```

3. **Member Not Found:**
```json
{
  "status": 404,
  "message": "Member not found"
}
```

4. **Insufficient Permissions:**
```json
{
  "status": 403,
  "message": "Not enough permissions"
}
```

5. **Assistant Not Found:**
```json
{
  "status": 404,
  "message": "assistant not found"
}
```

## Validation Rules

### Name Validation
- Must be 1-64 characters long
- Only alphanumeric characters, underscores, and hyphens allowed
- Must be unique within the team
- Cannot be a protected system name

### Temperature Validation
- Must be between 0.0 and 1.0 (inclusive)
- Controls randomness in AI responses

### Type Validation
- Must be one of: "leader", "worker", "freelancer"
- Determines member role in team hierarchy

### Position Validation
- X and Y coordinates must be valid floating-point numbers
- Used for UI positioning in drag-and-drop interfaces

## Examples

### Complete Member Management Workflow

**1. Create a Research Team Leader:**

```bash
curl -X POST "https://your-api-domain/member/?assistant_id=team_123" \
  -H "Content-Type: application/json" \
  -H "x-user-id: user_456" \
  -H "x-user-role: admin" \
  -d '{
    "name": "research_lead",
    "backstory": "Experienced team leader with expertise in AI research coordination",
    "role": "Research Team Lead",
    "type": "leader",
    "position_x": 200.0,
    "position_y": 100.0,
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.5,
    "interrupt": true
  }'
```

**2. Create a Specialized Worker:**

```bash
curl -X POST "https://your-api-domain/member/?assistant_id=team_123" \
  -H "Content-Type: application/json" \
  -H "x-user-id: user_456" \
  -H "x-user-role: admin" \
  -d '{
    "name": "ml_specialist",
    "backstory": "Machine learning expert focused on model development and optimization",
    "role": "ML Engineer",
    "type": "worker",
    "position_x": 100.0,
    "position_y": 300.0,
    "provider": "anthropic",
    "model": "claude-3-opus",
    "temperature": 0.3,
    "interrupt": false
  }'
```

**3. Get All Team Members:**

```bash
curl -X GET "https://your-api-domain/member/?assistant_id=team_123&skip=0&limit=10" \
  -H "x-user-id: user_456" \
  -H "x-user-role: admin"
```

**4. Update Member with Skills and Uploads:**

```bash
curl -X PUT "https://your-api-domain/member/1?assistant_id=team_123" \
  -H "Content-Type: application/json" \
  -H "x-user-id: user_456" \
  -H "x-user-role: admin" \
  -d '{
    "role": "Senior Research Team Lead",
    "temperature": 0.7,
    "skills": [
      {
        "id": 1,
        "name": "project_management",
        "description": "Advanced project management capabilities"
      },
      {
        "id": 2,
        "name": "team_coordination",
        "description": "Team coordination and communication tools"
      }
    ],
    "uploads": [
      {
        "id": 1,
        "name": "research_protocols.pdf",
        "description": "Standard research protocols and procedures"
      }
    ]
  }'
```

**5. Get Specific Member Details:**

```bash
curl -X GET "https://your-api-domain/member/1?assistant_id=team_123" \
  -H "x-user-id: user_456" \
  -H "x-user-role: admin"
```

### Member Types and Use Cases

**Leader Members:**
- Coordinate team activities
- Make strategic decisions
- Higher interrupt capability
- Usually have broader skill sets

```json
{
  "name": "project_coordinator",
  "type": "leader",
  "role": "Project Coordinator",
  "backstory": "Experienced project manager with expertise in cross-functional team leadership",
  "interrupt": true,
  "temperature": 0.6
}
```

**Worker Members:**
- Execute specific tasks
- Specialized in particular domains
- Lower temperature for consistent results
- Focused skill sets

```json
{
  "name": "code_reviewer",
  "type": "worker",
  "role": "Senior Code Reviewer",
  "backstory": "Expert in code quality assurance and best practices",
  "interrupt": false,
  "temperature": 0.2
}
```

**Freelancer Members:**
- Flexible roles
- Temporary assignments
- Higher creativity settings
- Diverse capabilities

```json
{
  "name": "creative_consultant",
  "type": "freelancer",
  "role": "Creative Consultant",
  "backstory": "Creative professional providing innovative solutions and fresh perspectives",
  "interrupt": true,
  "temperature": 0.8
}
```

### Managing Member Skills

**Adding Skills to Members:**

```javascript
// Get available skills first
const skillsResponse = await fetch('/skill/', {
  headers: {
    'x-user-id': 'user_456',
    'x-user-role': 'admin'
  }
});
const skills = await skillsResponse.json();

// Update member with selected skills
const updateResponse = await fetch('/member/1?assistant_id=team_123', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'x-user-id': 'user_456',
    'x-user-role': 'admin'
  },
  body: JSON.stringify({
    skills: [
      { id: 1, name: 'web_search' },
      { id: 3, name: 'data_analysis' },
      { id: 5, name: 'report_generation' }
    ]
  })
});
```

### Managing Member Uploads

**Providing Document Access:**

```javascript
// Update member with accessible documents
await fetch('/member/2?assistant_id=team_123', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'x-user-id': 'user_456',
    'x-user-role': 'admin'
  },
  body: JSON.stringify({
    uploads: [
      {
        id: 1,
        name: 'api_documentation.pdf',
        description: 'Complete API reference documentation'
      },
      {
        id: 3,
        name: 'coding_standards.md',
        description: 'Team coding standards and guidelines'
      }
    ]
  })
});
```

## Advanced Features

### Drag-and-Drop Positioning

Members support UI positioning for visual team management:

```json
{
  "position_x": 150.0,
  "position_y": 250.0
}
```

Use these coordinates to:
- Create visual team hierarchies
- Show workflow relationships
- Enable drag-and-drop interfaces
- Maintain consistent UI layouts

### AI Model Configuration

Each member can use different AI providers and models:

```json
{
  "provider": "openai",
  "model": "gpt-4-turbo",
  "temperature": 0.7
}
```

**Supported Providers:**
- `openai`: GPT models
- `anthropic`: Claude models
- `local`: Local model deployments

**Temperature Guidelines:**
- `0.0-0.3`: Consistent, factual responses
- `0.4-0.6`: Balanced creativity and consistency
- `0.7-1.0`: Creative, varied responses

### Permission Management

Access control is based on user roles:

| User Role | Permissions |
|-----------|-------------|
| `super admin` | Full access to all members across all teams |
| `admin` | Full access to all members across all teams |
| Team Owner | Full access to members in owned teams only |
| Regular User | Read-only access to members in accessible teams |

## Performance Considerations

1. **Pagination**: Use `skip` and `limit` parameters for large teams
2. **Selective Updates**: Only include changed fields in update requests
3. **Skill Management**: Batch skill assignments when possible
4. **Upload Access**: Limit upload associations to necessary documents
5. **Query Optimization**: Filter by assistant_id to improve performance

## Security Notes

1. **Name Validation**: Prevents injection attacks through strict naming rules
2. **Permission Checks**: All operations verify user permissions
3. **Soft Deletion**: Members are marked as deleted rather than permanently removed
4. **Access Control**: Skills and uploads are validated for accessibility
5. **Input Sanitization**: All inputs are validated and sanitized

## Integration Patterns

### Team Management Dashboard

```javascript
class TeamMemberManager {
  constructor(apiClient, teamId) {
    this.api = apiClient;
    this.teamId = teamId;
  }
  
  async loadTeamMembers() {
    const response = await this.api.get(`/member/?assistant_id=${this.teamId}`);
    return response.data.members;
  }
  
  async createMember(memberData) {
    return await this.api.post(`/member/?assistant_id=${this.teamId}`, memberData);
  }
  
  async updateMemberPosition(memberId, x, y) {
    return await this.api.put(`/member/${memberId}?assistant_id=${this.teamId}`, {
      position_x: x,
      position_y: y
    });
  }
  
  async assignSkillsToMember(memberId, skillIds) {
    const skills = skillIds.map(id => ({ id }));
    return await this.api.put(`/member/${memberId}?assistant_id=${this.teamId}`, {
      skills
    });
  }
}
```

### Member Workflow Coordination

```python
class MemberCoordinator:
    def __init__(self, api_client, team_id):
        self.api = api_client
        self.team_id = team_id
    
    async def create_research_team(self):
        # Create team leader
        leader = await self.api.post(f"/member/?assistant_id={self.team_id}", {
            "name": "research_leader",
            "type": "leader",
            "role": "Research Coordinator",
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.5,
            "interrupt": True,
            "position_x": 200.0,
            "position_y": 100.0
        })
        
        # Create specialized workers
        specialists = []
        for i, specialty in enumerate(["data_analysis", "literature_review", "report_writing"]):
            specialist = await self.api.post(f"/member/?assistant_id={self.team_id}", {
                "name": f"{specialty}_specialist",
                "type": "worker",
                "role": f"{specialty.replace('_', ' ').title()} Specialist",
                "provider": "anthropic",
                "model": "claude-3-sonnet",
                "temperature": 0.3,
                "interrupt": False,
                "position_x": 100.0 + (i * 150),
                "position_y": 300.0
            })
            specialists.append(specialist)
        
        return leader, specialists
```

## Troubleshooting

### Common Issues

1. **Name Conflicts**: Ensure member names are unique within the team
2. **Permission Errors**: Verify user has appropriate role for the operation
3. **Invalid Skills**: Check that skill IDs exist and are accessible
4. **Upload Access**: Ensure uploads are available to the team
5. **Model Configuration**: Verify provider and model combinations are valid

### Debug Checklist

1. **Check User Headers**: Ensure `x-user-id` and `x-user-role` are set
2. **Verify Team Access**: Confirm user has access to the specified team
3. **Validate Input**: Check all required fields are provided
4. **Review Permissions**: Ensure user role allows the requested operation
5. **Monitor Logs**: Check server logs for detailed error information

This comprehensive API documentation provides developers with all the information needed to effectively manage team members through the Member API endpoints.
