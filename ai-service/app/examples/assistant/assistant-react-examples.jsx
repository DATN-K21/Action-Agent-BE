/**
 * Assistant API React Examples
 * 
 * This file contains React component examples demonstrating how to use the Assistant API
 * in a React application with proper state management and error handling.
 */

import { useCallback, useEffect, useState } from 'react';

// Custom hook for API requests
const useAssistantAPI = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    const API_BASE_URL = 'http://localhost:8000/api/v1/assistant';
    const USER_ID = localStorage.getItem('userId') || 'default-user';
    const USER_ROLE = localStorage.getItem('userRole') || 'user';
    
    const getHeaders = () => ({
        'Content-Type': 'application/json',
        'x-user-id': USER_ID,
        'x-user-role': USER_ROLE,
    });
    
    const apiRequest = useCallback(async (url, options = {}) => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch(url, {
                headers: getHeaders(),
                ...options
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.message || 'API request failed');
            }
            
            return result;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [USER_ID, USER_ROLE]);
    
    return { apiRequest, loading, error, setError };
};

/**
 * Assistant List Component
 * Displays a list of assistants with pagination
 */
const AssistantList = () => {
    const [assistants, setAssistants] = useState([]);
    const [pagination, setPagination] = useState({
        pageNumber: 1,
        maxPerPage: 10,
        totalPage: 0
    });
    const [filter, setFilter] = useState('');
    
    const { apiRequest, loading, error } = useAssistantAPI();
    
    const fetchAssistants = useCallback(async (page = 1, assistantType = null) => {
        try {
            const queryParams = new URLSearchParams({
                page_number: page.toString(),
                max_per_page: pagination.maxPerPage.toString()
            });
            
            if (assistantType) {
                queryParams.append('assistant_type', assistantType);
            }
            
            const url = `http://localhost:8000/api/v1/assistant/get-all?${queryParams}`;
            const result = await apiRequest(url, { method: 'GET' });
            
            setAssistants(result.data.assistants);
            setPagination({
                pageNumber: result.data.pageNumber,
                maxPerPage: result.data.maxPerPage,
                totalPage: result.data.totalPage
            });
        } catch (err) {
            console.error('Failed to fetch assistants:', err);
        }
    }, [apiRequest, pagination.maxPerPage]);
    
    useEffect(() => {
        fetchAssistants();
    }, [fetchAssistants]);
    
    const handlePageChange = (newPage) => {
        fetchAssistants(newPage, filter || null);
    };
    
    const handleFilterChange = (newFilter) => {
        setFilter(newFilter);
        fetchAssistants(1, newFilter || null);
    };
    
    if (loading) return <div className="loading">Loading assistants...</div>;
    if (error) return <div className="error">Error: {error}</div>;
    
    return (
        <div className="assistant-list">
            <h2>My Assistants</h2>
            
            {/* Filter Controls */}
            <div className="filters">
                <select 
                    value={filter} 
                    onChange={(e) => handleFilterChange(e.target.value)}
                >
                    <option value="">All Assistants</option>
                    <option value="general_assistant">General Assistants</option>
                    <option value="advanced_assistant">Advanced Assistants</option>
                </select>
            </div>
            
            {/* Assistant Cards */}
            <div className="assistant-grid">
                {assistants.map(assistant => (
                    <AssistantCard 
                        key={assistant.id} 
                        assistant={assistant}
                        onUpdate={() => fetchAssistants(pagination.pageNumber, filter || null)}
                    />
                ))}
            </div>
            
            {/* Pagination */}
            <div className="pagination">
                <button 
                    disabled={pagination.pageNumber <= 1}
                    onClick={() => handlePageChange(pagination.pageNumber - 1)}
                >
                    Previous
                </button>
                
                <span>
                    Page {pagination.pageNumber} of {pagination.totalPage}
                </span>
                
                <button 
                    disabled={pagination.pageNumber >= pagination.totalPage}
                    onClick={() => handlePageChange(pagination.pageNumber + 1)}
                >
                    Next
                </button>
            </div>
        </div>
    );
};

/**
 * Assistant Card Component
 * Displays individual assistant information with action buttons
 */
const AssistantCard = ({ assistant, onUpdate }) => {
    const { apiRequest, loading } = useAssistantAPI();
    
    const handleDelete = async () => {
        if (!confirm(`Are you sure you want to delete "${assistant.name}"?`)) {
            return;
        }
        
        try {
            const url = `http://localhost:8000/api/v1/assistant/${assistant.id}/soft-delete-advanced-assistant`;
            await apiRequest(url, { method: 'DELETE' });
            onUpdate(); // Refresh the list
        } catch (err) {
            console.error('Failed to delete assistant:', err);
        }
    };
    
    return (
        <div className="assistant-card">
            <h3>{assistant.name}</h3>
            <p className="type-badge">{assistant.assistantType}</p>
            <p className="description">{assistant.description}</p>
            
            <div className="assistant-details">
                <p><strong>Provider:</strong> {assistant.provider}</p>
                <p><strong>Model:</strong> {assistant.modelName}</p>
                <p><strong>Temperature:</strong> {assistant.temperature}</p>
                <p><strong>Teams:</strong> {assistant.teams?.length || 0}</p>
            </div>
            
            <div className="card-actions">
                <button className="btn-edit">Edit</button>
                <button className="btn-view">View Details</button>
                <button 
                    className="btn-delete" 
                    onClick={handleDelete}
                    disabled={loading}
                >
                    {loading ? 'Deleting...' : 'Delete'}
                </button>
            </div>
        </div>
    );
};

/**
 * Create Assistant Form Component
 * Form for creating new advanced assistants
 */
const CreateAssistantForm = ({ onSuccess, onCancel }) => {
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        systemPrompt: '',
        provider: 'openai',
        modelName: 'gpt-4',
        temperature: 0.7,
        askHuman: false,
        interrupt: false,
        supportUnits: [],
        mcpIds: [],
        extensionIds: []
    });
    
    const [errors, setErrors] = useState({});
    const { apiRequest, loading, error } = useAssistantAPI();
    
    const validateForm = () => {
        const newErrors = {};
        
        if (!formData.name || formData.name.length < 3) {
            newErrors.name = 'Name must be at least 3 characters';
        }
        
        if (!formData.description || formData.description.length < 3) {
            newErrors.description = 'Description must be at least 3 characters';
        }
        
        if (!formData.systemPrompt || formData.systemPrompt.length < 3) {
            newErrors.systemPrompt = 'System prompt must be at least 3 characters';
        }
        
        if (formData.temperature < 0 || formData.temperature > 2) {
            newErrors.temperature = 'Temperature must be between 0 and 2';
        }
        
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!validateForm()) {
            return;
        }
        
        try {
            const url = 'http://localhost:8000/api/v1/assistant/create';
            const result = await apiRequest(url, {
                method: 'POST',
                body: JSON.stringify(formData)
            });
            
            onSuccess(result.data);
        } catch (err) {
            console.error('Failed to create assistant:', err);
        }
    };
    
    const handleInputChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
        
        // Clear error for this field
        if (errors[field]) {
            setErrors(prev => ({ ...prev, [field]: '' }));
        }
    };
    
    const handleArrayInputChange = (field, value) => {
        const arrayValue = value.split(',').map(item => item.trim()).filter(Boolean);
        setFormData(prev => ({ ...prev, [field]: arrayValue }));
    };
    
    return (
        <form onSubmit={handleSubmit} className="create-assistant-form">
            <h2>Create Advanced Assistant</h2>
            
            {error && <div className="error-banner">{error}</div>}
            
            <div className="form-group">
                <label htmlFor="name">Name *</label>
                <input
                    id="name"
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    className={errors.name ? 'error' : ''}
                    placeholder="Enter assistant name"
                />
                {errors.name && <span className="error-text">{errors.name}</span>}
            </div>
            
            <div className="form-group">
                <label htmlFor="description">Description *</label>
                <textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    className={errors.description ? 'error' : ''}
                    placeholder="Describe what this assistant does"
                    rows={3}
                />
                {errors.description && <span className="error-text">{errors.description}</span>}
            </div>
            
            <div className="form-group">
                <label htmlFor="systemPrompt">System Prompt *</label>
                <textarea
                    id="systemPrompt"
                    value={formData.systemPrompt}
                    onChange={(e) => handleInputChange('systemPrompt', e.target.value)}
                    className={errors.systemPrompt ? 'error' : ''}
                    placeholder="Enter the system prompt for the assistant"
                    rows={4}
                />
                {errors.systemPrompt && <span className="error-text">{errors.systemPrompt}</span>}
            </div>
            
            <div className="form-row">
                <div className="form-group">
                    <label htmlFor="provider">Provider</label>
                    <select
                        id="provider"
                        value={formData.provider}
                        onChange={(e) => handleInputChange('provider', e.target.value)}
                    >
                        <option value="openai">OpenAI</option>
                        <option value="anthropic">Anthropic</option>
                        <option value="google">Google</option>
                    </select>
                </div>
                
                <div className="form-group">
                    <label htmlFor="modelName">Model Name</label>
                    <input
                        id="modelName"
                        type="text"
                        value={formData.modelName}
                        onChange={(e) => handleInputChange('modelName', e.target.value)}
                        placeholder="e.g., gpt-4, claude-3-sonnet"
                    />
                </div>
            </div>
            
            <div className="form-group">
                <label htmlFor="temperature">Temperature: {formData.temperature}</label>
                <input
                    id="temperature"
                    type="range"
                    min="0"
                    max="2"
                    step="0.1"
                    value={formData.temperature}
                    onChange={(e) => handleInputChange('temperature', parseFloat(e.target.value))}
                />
                <div className="temperature-labels">
                    <span>Focused (0)</span>
                    <span>Balanced (1)</span>
                    <span>Creative (2)</span>
                </div>
                {errors.temperature && <span className="error-text">{errors.temperature}</span>}
            </div>
            
            <div className="form-row">
                <div className="form-group checkbox-group">
                    <label>
                        <input
                            type="checkbox"
                            checked={formData.askHuman}
                            onChange={(e) => handleInputChange('askHuman', e.target.checked)}
                        />
                        Ask human for confirmation
                    </label>
                </div>
                
                <div className="form-group checkbox-group">
                    <label>
                        <input
                            type="checkbox"
                            checked={formData.interrupt}
                            onChange={(e) => handleInputChange('interrupt', e.target.checked)}
                        />
                        Allow interruption
                    </label>
                </div>
            </div>
            
            <div className="form-group">
                <label htmlFor="supportUnits">Support Units</label>
                <div className="checkbox-list">
                    {['ragbot', 'searchbot', 'workflow'].map(unit => (
                        <label key={unit}>
                            <input
                                type="checkbox"
                                checked={formData.supportUnits.includes(unit)}
                                onChange={(e) => {
                                    const updatedUnits = e.target.checked
                                        ? [...formData.supportUnits, unit]
                                        : formData.supportUnits.filter(u => u !== unit);
                                    handleInputChange('supportUnits', updatedUnits);
                                }}
                            />
                            {unit}
                        </label>
                    ))}
                </div>
            </div>
            
            <div className="form-group">
                <label htmlFor="mcpIds">MCP IDs (comma-separated)</label>
                <input
                    id="mcpIds"
                    type="text"
                    value={formData.mcpIds.join(', ')}
                    onChange={(e) => handleArrayInputChange('mcpIds', e.target.value)}
                    placeholder="mcp-id-1, mcp-id-2"
                />
            </div>
            
            <div className="form-group">
                <label htmlFor="extensionIds">Extension IDs (comma-separated)</label>
                <input
                    id="extensionIds"
                    type="text"
                    value={formData.extensionIds.join(', ')}
                    onChange={(e) => handleArrayInputChange('extensionIds', e.target.value)}
                    placeholder="ext-id-1, ext-id-2"
                />
            </div>
            
            <div className="form-actions">
                <button type="button" onClick={onCancel} className="btn-cancel">
                    Cancel
                </button>
                <button type="submit" disabled={loading} className="btn-submit">
                    {loading ? 'Creating...' : 'Create Assistant'}
                </button>
            </div>
        </form>
    );
};

/**
 * Assistant Details Component
 * Shows detailed view of an assistant with edit capabilities
 */
const AssistantDetails = ({ assistantId, onClose }) => {
    const [assistant, setAssistant] = useState(null);
    const [isEditing, setIsEditing] = useState(false);
    const [editData, setEditData] = useState({});
    
    const { apiRequest, loading, error } = useAssistantAPI();
    
    const fetchAssistantDetails = useCallback(async () => {
        try {
            const url = `http://localhost:8000/api/v1/assistant/${assistantId}/get-detail`;
            const result = await apiRequest(url, { method: 'GET' });
            setAssistant(result.data);
            setEditData({
                systemPrompt: result.data.systemPrompt,
                temperature: result.data.temperature,
                askHuman: result.data.askHuman,
                interrupt: result.data.interrupt
            });
        } catch (err) {
            console.error('Failed to fetch assistant details:', err);
        }
    }, [assistantId, apiRequest]);
    
    useEffect(() => {
        fetchAssistantDetails();
    }, [fetchAssistantDetails]);
    
    const handleConfigUpdate = async () => {
        try {
            const url = `http://localhost:8000/api/v1/assistant/${assistantId}/update-config`;
            await apiRequest(url, {
                method: 'PATCH',
                body: JSON.stringify(editData)
            });
            
            setIsEditing(false);
            fetchAssistantDetails(); // Refresh data
        } catch (err) {
            console.error('Failed to update configuration:', err);
        }
    };
    
    if (loading && !assistant) return <div>Loading assistant details...</div>;
    if (error) return <div>Error: {error}</div>;
    if (!assistant) return <div>Assistant not found</div>;
    
    return (
        <div className="assistant-details">
            <div className="details-header">
                <h2>{assistant.name}</h2>
                <button onClick={onClose} className="btn-close">×</button>
            </div>
            
            <div className="details-content">
                <div className="detail-section">
                    <h3>Basic Information</h3>
                    <p><strong>Type:</strong> {assistant.assistantType}</p>
                    <p><strong>Description:</strong> {assistant.description}</p>
                    <p><strong>Provider:</strong> {assistant.provider}</p>
                    <p><strong>Model:</strong> {assistant.modelName}</p>
                    <p><strong>Created:</strong> {new Date(assistant.createdAt).toLocaleDateString()}</p>
                </div>
                
                <div className="detail-section">
                    <h3>Configuration</h3>
                    {isEditing ? (
                        <div className="edit-config">
                            <div className="form-group">
                                <label>System Prompt:</label>
                                <textarea
                                    value={editData.systemPrompt}
                                    onChange={(e) => setEditData(prev => ({
                                        ...prev,
                                        systemPrompt: e.target.value
                                    }))}
                                    rows={4}
                                />
                            </div>
                            
                            <div className="form-group">
                                <label>Temperature: {editData.temperature}</label>
                                <input
                                    type="range"
                                    min="0"
                                    max="2"
                                    step="0.1"
                                    value={editData.temperature}
                                    onChange={(e) => setEditData(prev => ({
                                        ...prev,
                                        temperature: parseFloat(e.target.value)
                                    }))}
                                />
                            </div>
                            
                            <div className="checkbox-group">
                                <label>
                                    <input
                                        type="checkbox"
                                        checked={editData.askHuman}
                                        onChange={(e) => setEditData(prev => ({
                                            ...prev,
                                            askHuman: e.target.checked
                                        }))}
                                    />
                                    Ask human for confirmation
                                </label>
                            </div>
                            
                            <div className="checkbox-group">
                                <label>
                                    <input
                                        type="checkbox"
                                        checked={editData.interrupt}
                                        onChange={(e) => setEditData(prev => ({
                                            ...prev,
                                            interrupt: e.target.checked
                                        }))}
                                    />
                                    Allow interruption
                                </label>
                            </div>
                            
                            <div className="edit-actions">
                                <button onClick={() => setIsEditing(false)} className="btn-cancel">
                                    Cancel
                                </button>
                                <button onClick={handleConfigUpdate} disabled={loading} className="btn-save">
                                    {loading ? 'Saving...' : 'Save Changes'}
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div>
                            <p><strong>System Prompt:</strong> {assistant.systemPrompt}</p>
                            <p><strong>Temperature:</strong> {assistant.temperature}</p>
                            <p><strong>Ask Human:</strong> {assistant.askHuman ? 'Yes' : 'No'}</p>
                            <p><strong>Interrupt:</strong> {assistant.interrupt ? 'Yes' : 'No'}</p>
                            
                            <button onClick={() => setIsEditing(true)} className="btn-edit">
                                Edit Configuration
                            </button>
                        </div>
                    )}
                </div>
                
                <div className="detail-section">
                    <h3>Teams & Units</h3>
                    <p><strong>Main Unit:</strong> {assistant.mainUnit}</p>
                    <p><strong>Support Units:</strong> {assistant.supportUnits?.join(', ') || 'None'}</p>
                    
                    {assistant.teams && assistant.teams.length > 0 && (
                        <div className="teams-list">
                            <h4>Teams:</h4>
                            {assistant.teams.map(team => (
                                <div key={team.id} className="team-item">
                                    <strong>{team.name}</strong> ({team.workflowType})
                                </div>
                            ))}
                        </div>
                    )}
                </div>
                
                {(assistant.mcpIds?.length > 0 || assistant.extensionIds?.length > 0) && (
                    <div className="detail-section">
                        <h3>Connected Services</h3>
                        {assistant.mcpIds?.length > 0 && (
                            <p><strong>MCP IDs:</strong> {assistant.mcpIds.join(', ')}</p>
                        )}
                        {assistant.extensionIds?.length > 0 && (
                            <p><strong>Extension IDs:</strong> {assistant.extensionIds.join(', ')}</p>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

/**
 * Main App Component
 * Demonstrates how to use all the assistant components together
 */
const AssistantApp = () => {
    const [view, setView] = useState('list'); // 'list', 'create', 'details'
    const [selectedAssistantId, setSelectedAssistantId] = useState(null);
    
    const showAssistantDetails = (assistantId) => {
        setSelectedAssistantId(assistantId);
        setView('details');
    };
    
    const handleCreateSuccess = (newAssistant) => {
        console.log('Assistant created successfully:', newAssistant);
        setView('list');
    };
    
    return (
        <div className="assistant-app">
            <header className="app-header">
                <h1>Assistant Manager</h1>
                <nav>
                    <button 
                        onClick={() => setView('list')}
                        className={view === 'list' ? 'active' : ''}
                    >
                        My Assistants
                    </button>
                    <button 
                        onClick={() => setView('create')}
                        className={view === 'create' ? 'active' : ''}
                    >
                        Create Assistant
                    </button>
                </nav>
            </header>
            
            <main className="app-content">
                {view === 'list' && (
                    <AssistantList onSelectAssistant={showAssistantDetails} />
                )}
                
                {view === 'create' && (
                    <CreateAssistantForm
                        onSuccess={handleCreateSuccess}
                        onCancel={() => setView('list')}
                    />
                )}
                
                {view === 'details' && selectedAssistantId && (
                    <AssistantDetails
                        assistantId={selectedAssistantId}
                        onClose={() => setView('list')}
                    />
                )}
            </main>
        </div>
    );
};

export default AssistantApp;
