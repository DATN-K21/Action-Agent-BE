/**
 * Assistant API JavaScript Examples
 * 
 * This file contains practical JavaScript examples for all Assistant API endpoints.
 * These examples use the Fetch API and can be adapted for use in web applications,
 * Node.js, or other JavaScript environments.
 */

// Base configuration
const API_BASE_URL = 'http://localhost:8000/api/v1/assistant';
const USER_ID = 'your-user-id'; // Replace with actual user ID
const USER_ROLE = 'user'; // Replace with actual user role

// Common headers for all requests
const getHeaders = (additionalHeaders = {}) => ({
    'Content-Type': 'application/json',
    'x-user-id': USER_ID,
    'x-user-role': USER_ROLE,
    ...additionalHeaders
});

// Utility function for making API requests
const apiRequest = async (url, options = {}) => {
    try {
        const response = await fetch(url, {
            headers: getHeaders(options.headers),
            ...options
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(`API Error: ${result.message || 'Unknown error'}`);
        }
        
        return result;
    } catch (error) {
        console.error('API Request failed:', error);
        throw error;
    }
};

/**
 * 1. Get All Assistants
 * Retrieve a paginated list of assistants for the authenticated user
 */
const getAllAssistants = async (options = {}) => {
    const { assistantType = null, pageNumber = 1, maxPerPage = 10 } = options;
    
    const queryParams = new URLSearchParams({
        page_number: pageNumber.toString(),
        max_per_page: maxPerPage.toString()
    });
    
    if (assistantType) {
        queryParams.append('assistant_type', assistantType);
    }
    
    const url = `${API_BASE_URL}/get-all?${queryParams}`;
    
    return await apiRequest(url, { method: 'GET' });
};

// Example usage
const exampleGetAllAssistants = async () => {
    try {
        // Get all assistants
        const allAssistants = await getAllAssistants();
        console.log('All assistants:', allAssistants);
        
        // Get only advanced assistants
        const advancedAssistants = await getAllAssistants({
            assistantType: 'advanced_assistant',
            pageNumber: 1,
            maxPerPage: 20
        });
        console.log('Advanced assistants:', advancedAssistants);
        
    } catch (error) {
        console.error('Failed to get assistants:', error);
    }
};

/**
 * 2. Get or Create General Assistant
 * Get existing general assistant or create a new one if it doesn't exist
 */
const getOrCreateGeneralAssistant = async () => {
    const url = `${API_BASE_URL}/get-or-create-general-assistant`;
    
    return await apiRequest(url, { method: 'GET' });
};

// Example usage
const exampleGetOrCreateGeneralAssistant = async () => {
    try {
        const generalAssistant = await getOrCreateGeneralAssistant();
        console.log('General assistant:', generalAssistant);
        
        // The API will return existing assistant or create a new one
        if (generalAssistant.status === 200) {
            console.log('Existing general assistant found');
        } else if (generalAssistant.status === 201) {
            console.log('New general assistant created');
        }
        
    } catch (error) {
        console.error('Failed to get or create general assistant:', error);
    }
};

/**
 * 3. Create Advanced Assistant
 * Create a new advanced assistant with custom configuration
 */
const createAdvancedAssistant = async (assistantData) => {
    const url = `${API_BASE_URL}/create`;
    
    return await apiRequest(url, {
        method: 'POST',
        body: JSON.stringify(assistantData)
    });
};

// Example usage
const exampleCreateAdvancedAssistant = async () => {
    try {
        // Basic research assistant
        const researchAssistant = await createAdvancedAssistant({
            name: 'Research Assistant',
            description: 'An advanced assistant for research and analysis tasks',
            systemPrompt: 'You are a research assistant specialized in finding and analyzing information. Always provide well-sourced and accurate information.',
            provider: 'openai',
            modelName: 'gpt-4',
            temperature: 0.3,
            askHuman: true,
            interrupt: false,
            supportUnits: ['ragbot', 'searchbot']
        });
        console.log('Research assistant created:', researchAssistant);
        
        // Assistant with extensions and MCPs
        const productivityAssistant = await createAdvancedAssistant({
            name: 'Productivity Assistant',
            description: 'A comprehensive assistant for productivity tasks with tool access',
            systemPrompt: 'You are a productivity assistant with access to various tools. Help users manage their tasks, schedule, and workflow efficiently.',
            provider: 'anthropic',
            modelName: 'claude-3-sonnet',
            temperature: 0.5,
            askHuman: true,
            interrupt: false,
            supportUnits: ['ragbot', 'searchbot'],
            mcpIds: ['mcp-calendar-id', 'mcp-email-id'],
            extensionIds: ['ext-notion-id', 'ext-slack-id']
        });
        console.log('Productivity assistant created:', productivityAssistant);
        
        // Minimal assistant (only required fields)
        const minimalAssistant = await createAdvancedAssistant({
            name: 'Simple Assistant',
            description: 'A simple assistant for basic tasks',
            systemPrompt: 'You are a helpful assistant.'
        });
        console.log('Minimal assistant created:', minimalAssistant);
        
    } catch (error) {
        console.error('Failed to create advanced assistant:', error);
    }
};

/**
 * 4. Get Assistant Details
 * Retrieve detailed information about a specific assistant
 */
const getAssistantDetails = async (assistantId) => {
    const url = `${API_BASE_URL}/${assistantId}/get-detail`;
    
    return await apiRequest(url, { method: 'GET' });
};

// Example usage
const exampleGetAssistantDetails = async () => {
    try {
        const assistantId = 'your-assistant-id'; // Replace with actual assistant ID
        const assistantDetails = await getAssistantDetails(assistantId);
        console.log('Assistant details:', assistantDetails);
        
        // Access specific properties
        const assistant = assistantDetails.data;
        console.log('Assistant name:', assistant.name);
        console.log('Assistant type:', assistant.assistantType);
        console.log('Teams:', assistant.teams);
        
    } catch (error) {
        console.error('Failed to get assistant details:', error);
    }
};

/**
 * 5. Update Advanced Assistant
 * Update an existing advanced assistant's information
 */
const updateAdvancedAssistant = async (assistantId, updateData) => {
    const url = `${API_BASE_URL}/${assistantId}/update-advanced-assistant`;
    
    return await apiRequest(url, {
        method: 'PATCH',
        body: JSON.stringify(updateData)
    });
};

// Example usage
const exampleUpdateAdvancedAssistant = async () => {
    try {
        const assistantId = 'your-assistant-id'; // Replace with actual assistant ID
        
        // Partial update - only update specific fields
        const partialUpdate = await updateAdvancedAssistant(assistantId, {
            name: 'Updated Research Assistant',
            temperature: 0.5,
            askHuman: false
        });
        console.log('Partial update result:', partialUpdate);
        
        // Update support units and connected services
        const serviceUpdate = await updateAdvancedAssistant(assistantId, {
            supportUnits: ['ragbot', 'searchbot', 'workflow'],
            mcpIds: ['new-mcp-id-1', 'new-mcp-id-2'],
            extensionIds: ['new-ext-id-1']
        });
        console.log('Service update result:', serviceUpdate);
        
        // Complete update
        const completeUpdate = await updateAdvancedAssistant(assistantId, {
            name: 'Completely Updated Assistant',
            description: 'Updated description with new capabilities',
            systemPrompt: 'You are an updated assistant with enhanced capabilities.',
            provider: 'openai',
            modelName: 'gpt-4-turbo',
            temperature: 0.7,
            askHuman: true,
            interrupt: false,
            supportUnits: ['ragbot', 'searchbot'],
            mcpIds: ['mcp-1', 'mcp-2'],
            extensionIds: ['ext-1', 'ext-2']
        });
        console.log('Complete update result:', completeUpdate);
        
    } catch (error) {
        console.error('Failed to update advanced assistant:', error);
    }
};

/**
 * 6. Update Assistant Configuration
 * Update only the configuration settings without affecting connected services
 */
const updateAssistantConfig = async (assistantId, configData) => {
    const url = `${API_BASE_URL}/${assistantId}/update-config`;
    
    return await apiRequest(url, {
        method: 'PATCH',
        body: JSON.stringify(configData)
    });
};

// Example usage
const exampleUpdateAssistantConfig = async () => {
    try {
        const assistantId = 'your-assistant-id'; // Replace with actual assistant ID
        
        // Update model configuration
        const modelConfigUpdate = await updateAssistantConfig(assistantId, {
            provider: 'anthropic',
            modelName: 'claude-3-opus',
            temperature: 0.2
        });
        console.log('Model config update result:', modelConfigUpdate);
        
        // Update behavior settings
        const behaviorUpdate = await updateAssistantConfig(assistantId, {
            systemPrompt: 'You are an assistant optimized for accuracy and detailed responses.',
            askHuman: true,
            interrupt: false
        });
        console.log('Behavior update result:', behaviorUpdate);
        
        // Update only system prompt
        const promptUpdate = await updateAssistantConfig(assistantId, {
            systemPrompt: 'Updated system prompt for better performance and accuracy.'
        });
        console.log('Prompt update result:', promptUpdate);
        
    } catch (error) {
        console.error('Failed to update assistant configuration:', error);
    }
};

/**
 * 7. Soft Delete Assistant
 * Mark an assistant as deleted without permanently removing it
 */
const softDeleteAssistant = async (assistantId) => {
    const url = `${API_BASE_URL}/${assistantId}/soft-delete-advanced-assistant`;
    
    return await apiRequest(url, { method: 'DELETE' });
};

// Example usage
const exampleSoftDeleteAssistant = async () => {
    try {
        const assistantId = 'your-assistant-id'; // Replace with actual assistant ID
        const deleteResult = await softDeleteAssistant(assistantId);
        console.log('Soft delete result:', deleteResult);
        
        if (deleteResult.status === 200) {
            console.log('Assistant successfully soft deleted');
        }
        
    } catch (error) {
        console.error('Failed to soft delete assistant:', error);
    }
};

/**
 * 8. Hard Delete Assistant
 * Permanently delete an assistant and all related data
 */
const hardDeleteAssistant = async (assistantId) => {
    const url = `${API_BASE_URL}/${USER_ID}/${assistantId}/hard-delete-advanced-assistant`;
    
    return await apiRequest(url, { method: 'DELETE' });
};

// Example usage
const exampleHardDeleteAssistant = async () => {
    try {
        const assistantId = 'your-assistant-id'; // Replace with actual assistant ID
        
        // Confirm deletion (in a real app, you'd show a confirmation dialog)
        const confirmDelete = confirm('Are you sure you want to permanently delete this assistant? This action cannot be undone.');
        
        if (confirmDelete) {
            const deleteResult = await hardDeleteAssistant(assistantId);
            console.log('Hard delete result:', deleteResult);
            
            if (deleteResult.status === 200) {
                console.log('Assistant permanently deleted');
            }
        }
        
    } catch (error) {
        console.error('Failed to hard delete assistant:', error);
    }
};

/**
 * Complete Workflow Example
 * Demonstrates a complete workflow of creating, updating, and managing assistants
 */
const completeWorkflowExample = async () => {
    try {
        console.log('Starting complete workflow example...');
        
        // 1. Get all existing assistants
        console.log('1. Getting all assistants...');
        const allAssistants = await getAllAssistants();
        console.log(`Found ${allAssistants.data.assistants.length} assistants`);
        
        // 2. Get or create general assistant
        console.log('2. Getting or creating general assistant...');
        const generalAssistant = await getOrCreateGeneralAssistant();
        console.log('General assistant:', generalAssistant.data.name);
        
        // 3. Create a new advanced assistant
        console.log('3. Creating new advanced assistant...');
        const newAssistant = await createAdvancedAssistant({
            name: 'Workflow Test Assistant',
            description: 'A test assistant for workflow demonstration',
            systemPrompt: 'You are a test assistant created for workflow demonstration.',
            provider: 'openai',
            modelName: 'gpt-4',
            temperature: 0.5,
            askHuman: false,
            supportUnits: ['ragbot']
        });
        
        const assistantId = newAssistant.data.id;
        console.log('Created assistant with ID:', assistantId);
        
        // 4. Get the created assistant's details
        console.log('4. Getting assistant details...');
        const assistantDetails = await getAssistantDetails(assistantId);
        console.log('Assistant details retrieved:', assistantDetails.data.name);
        
        // 5. Update the assistant configuration
        console.log('5. Updating assistant configuration...');
        await updateAssistantConfig(assistantId, {
            systemPrompt: 'Updated system prompt for the test assistant.',
            temperature: 0.7
        });
        console.log('Configuration updated successfully');
        
        // 6. Update the assistant with new features
        console.log('6. Updating assistant with new features...');
        await updateAdvancedAssistant(assistantId, {
            name: 'Updated Workflow Test Assistant',
            supportUnits: ['ragbot', 'searchbot']
        });
        console.log('Assistant updated with new features');
        
        // 7. Soft delete the assistant (for testing - in real use you might not want to delete immediately)
        console.log('7. Soft deleting assistant...');
        await softDeleteAssistant(assistantId);
        console.log('Assistant soft deleted successfully');
        
        console.log('Workflow completed successfully!');
        
    } catch (error) {
        console.error('Workflow failed:', error);
    }
};

/**
 * Error Handling Examples
 * Demonstrates proper error handling for various scenarios
 */
const errorHandlingExamples = async () => {
    try {
        // Example 1: Handling validation errors
        try {
            await createAdvancedAssistant({
                name: 'AB', // Too short - will trigger validation error
                description: 'Valid description',
                systemPrompt: 'Valid system prompt'
            });
        } catch (error) {
            console.log('Validation error caught:', error.message);
        }
        
        // Example 2: Handling not found errors
        try {
            await getAssistantDetails('non-existent-id');
        } catch (error) {
            console.log('Not found error caught:', error.message);
        }
        
        // Example 3: Handling network errors with retry logic
        const retryRequest = async (requestFn, maxRetries = 3) => {
            for (let attempt = 1; attempt <= maxRetries; attempt++) {
                try {
                    return await requestFn();
                } catch (error) {
                    console.log(`Attempt ${attempt} failed:`, error.message);
                    
                    if (attempt === maxRetries) {
                        throw error;
                    }
                    
                    // Wait before retrying (exponential backoff)
                    await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
                }
            }
        };
        
        const assistantsWithRetry = await retryRequest(() => getAllAssistants());
        console.log('Request succeeded with retry:', assistantsWithRetry.status);
        
    } catch (error) {
        console.error('Error handling example failed:', error);
    }
};

// Export functions for use in other modules (Node.js)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getAllAssistants,
        getOrCreateGeneralAssistant,
        createAdvancedAssistant,
        getAssistantDetails,
        updateAdvancedAssistant,
        updateAssistantConfig,
        softDeleteAssistant,
        hardDeleteAssistant,
        completeWorkflowExample,
        errorHandlingExamples
    };
}

// Example usage (uncomment to run)
// completeWorkflowExample();
// errorHandlingExamples();
