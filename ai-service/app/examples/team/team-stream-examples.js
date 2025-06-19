/**
 * Team Stream API JavaScript Examples
 * 
 * This file contains comprehensive examples for integrating with the Team Stream API,
 * including regular messaging and hierarchical workflow interrupt handling.
 */

// Configuration
const API_CONFIG = {
    BASE_URL: 'http://localhost:8000/api/v1/team',
    DEFAULT_HEADERS: {
        'Content-Type': 'application/json',
        'x-user-id': 'your-user-id',
        'x-user-role': 'user'
    },
    TIMEOUT: 30000 // 30 seconds
};

/**
 * Team Stream Client Class
 * Handles streaming communication with AI teams
 */
class TeamStreamClient {
    constructor(teamId, threadId, options = {}) {
        this.teamId = teamId;
        this.threadId = threadId;
        this.options = {
            ...API_CONFIG,
            ...options
        };
        this.eventSource = null;
        this.isConnected = false;
        this.messageQueue = [];
        this.interruptCallback = null;
        this.messageCallback = null;
        this.errorCallback = null;
    }

    /**
     * Send a message to the AI team
     * @param {string} content - The message content
     * @param {string} imgdata - Optional base64 encoded image data
     * @returns {Promise<void>}
     */
    async sendMessage(content, imgdata = null) {
        const payload = {
            messages: [
                {
                    type: 'human',
                    content: content,
                    ...(imgdata && { imgdata })
                }
            ]
        };

        return this._sendRequest(payload);
    }

    /**
     * Send an interrupt response for hierarchical workflow
     * @param {string} interactionType - Type of interaction (tool_review, output_review, context_input)
     * @param {string} decision - User decision (approved, rejected, etc.)
     * @param {string} toolMessage - Optional additional message
     * @returns {Promise<void>}
     */
    async sendInterrupt(interactionType, decision, toolMessage = null) {
        const payload = {
            messages: [],
            interrupt: {
                interaction_type: interactionType,
                decision: decision,
                ...(toolMessage && { tool_message: toolMessage })
            }
        };

        return this._sendRequest(payload);
    }

    /**
     * Internal method to send requests to the stream API
     * @private
     */
    async _sendRequest(payload) {
        const url = `${this.options.BASE_URL}/${this.teamId}/stream/${this.threadId}`;
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: this.options.DEFAULT_HEADERS,
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`HTTP ${response.status}: ${errorData.message || 'Unknown error'}`);
            }

            // Handle streaming response
            await this._handleStreamResponse(response);
            
        } catch (error) {
            console.error('Error sending request:', error);
            if (this.errorCallback) {
                this.errorCallback(error);
            }
            throw error;
        }
    }

    /**
     * Handle streaming response from the API
     * @private
     */
    async _handleStreamResponse(response) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        try {
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            this._handleStreamEvent(data);
                        } catch (e) {
                            console.warn('Failed to parse SSE data:', line);
                        }
                    }
                }
            }
        } finally {
            reader.releaseLock();
        }
    }

    /**
     * Handle individual stream events
     * @private
     */
    _handleStreamEvent(data) {
        switch (data.type) {
            case 'message':
                if (this.messageCallback) {
                    this.messageCallback(data);
                }
                break;
                
            case 'interrupt':
                if (this.interruptCallback) {
                    this.interruptCallback(data);
                }
                break;
                
            case 'error':
                const error = new Error(data.content || 'Stream error');
                if (this.errorCallback) {
                    this.errorCallback(error);
                }
                break;
                
            default:
                console.warn('Unknown stream event type:', data.type);
        }
    }

    /**
     * Set callback for regular messages
     * @param {Function} callback - Function to handle message events
     */
    onMessage(callback) {
        this.messageCallback = callback;
        return this;
    }

    /**
     * Set callback for interrupt events
     * @param {Function} callback - Function to handle interrupt events
     */
    onInterrupt(callback) {
        this.interruptCallback = callback;
        return this;
    }

    /**
     * Set callback for error events
     * @param {Function} callback - Function to handle error events
     */
    onError(callback) {
        this.errorCallback = callback;
        return this;
    }
}

/**
 * Hierarchical Workflow Interrupt Handler
 * Specialized handler for managing hierarchical workflow interrupts
 */
class HierarchicalInterruptHandler {
    constructor(streamClient) {
        this.streamClient = streamClient;
        this.pendingInterrupts = new Map();
        this.setupDefaultHandlers();
    }

    setupDefaultHandlers() {
        this.streamClient.onInterrupt((interrupt) => {
            this.handleInterrupt(interrupt);
        });
    }

    /**
     * Handle different types of interrupts
     * @param {Object} interrupt - The interrupt event data
     */
    async handleInterrupt(interrupt) {
        const { name: interruptType, tool_calls, content, id } = interrupt;

        switch (interruptType) {
            case 'tool_review':
                await this.handleToolReview(tool_calls, id);
                break;
                
            case 'output_review':
                await this.handleOutputReview(content, id);
                break;
                
            case 'context_input':
                await this.handleContextInput(content, id);
                break;
                
            default:
                console.warn('Unknown interrupt type:', interruptType);
        }
    }

    /**
     * Handle tool review interrupts
     * @param {Array} toolCalls - Array of tool calls to review
     * @param {string} interruptId - Interrupt ID for tracking
     */
    async handleToolReview(toolCalls, interruptId) {
        console.log('Tool Review Required:', toolCalls);
        
        // Store pending interrupt
        this.pendingInterrupts.set(interruptId, {
            type: 'tool_review',
            data: toolCalls
        });

        // Example: Auto-approve safe tools, prompt for others
        const safeTool = this.isSafeTool(toolCalls[0]);
        
        if (safeTool) {
            await this.approveToolUsage(interruptId);
        } else {
            await this.promptUserForToolApproval(toolCalls, interruptId);
        }
    }

    /**
     * Handle output review interrupts
     * @param {string} content - The output content to review
     * @param {string} interruptId - Interrupt ID for tracking
     */
    async handleOutputReview(content, interruptId) {
        console.log('Output Review Required:', content);
        
        this.pendingInterrupts.set(interruptId, {
            type: 'output_review',
            data: content
        });

        // Example: Auto-approve short responses, prompt for longer ones
        if (content.length < 500) {
            await this.approveOutput(interruptId);
        } else {
            await this.promptUserForOutputReview(content, interruptId);
        }
    }

    /**
     * Handle context input requests
     * @param {string} content - The current context
     * @param {string} interruptId - Interrupt ID for tracking
     */
    async handleContextInput(content, interruptId) {
        console.log('Additional Context Requested:', content);
        
        this.pendingInterrupts.set(interruptId, {
            type: 'context_input',
            data: content
        });

        await this.promptUserForContext(content, interruptId);
    }

    /**
     * Check if a tool is considered safe for auto-approval
     * @param {Object} toolCall - The tool call to check
     * @returns {boolean}
     */
    isSafeTool(toolCall) {
        const safeTool = ['search_web', 'get_weather', 'calculate', 'translate'];
        return safeTool.includes(toolCall.name);
    }

    /**
     * Approve tool usage
     * @param {string} interruptId - Interrupt ID
     */
    async approveToolUsage(interruptId) {
        await this.streamClient.sendInterrupt('tool_review', 'approved');
        this.pendingInterrupts.delete(interruptId);
        console.log('Tool usage approved automatically');
    }

    /**
     * Reject tool usage with optional message
     * @param {string} interruptId - Interrupt ID
     * @param {string} reason - Reason for rejection
     */
    async rejectToolUsage(interruptId, reason = null) {
        await this.streamClient.sendInterrupt('tool_review', 'rejected', reason);
        this.pendingInterrupts.delete(interruptId);
        console.log('Tool usage rejected:', reason);
    }

    /**
     * Update tool parameters
     * @param {string} interruptId - Interrupt ID
     * @param {Object} newParams - New tool parameters
     */
    async updateToolParameters(interruptId, newParams) {
        const paramsJson = JSON.stringify(newParams);
        await this.streamClient.sendInterrupt('tool_review', 'update', paramsJson);
        this.pendingInterrupts.delete(interruptId);
        console.log('Tool parameters updated:', newParams);
    }

    /**
     * Approve output
     * @param {string} interruptId - Interrupt ID
     */
    async approveOutput(interruptId) {
        await this.streamClient.sendInterrupt('output_review', 'approved');
        this.pendingInterrupts.delete(interruptId);
        console.log('Output approved');
    }

    /**
     * Request output revision
     * @param {string} interruptId - Interrupt ID
     * @param {string} feedback - Feedback for revision
     */
    async requestOutputRevision(interruptId, feedback) {
        await this.streamClient.sendInterrupt('output_review', 'review', feedback);
        this.pendingInterrupts.delete(interruptId);
        console.log('Output revision requested:', feedback);
    }

    /**
     * Provide additional context
     * @param {string} interruptId - Interrupt ID
     * @param {string} context - Additional context information
     */
    async provideContext(interruptId, context) {
        await this.streamClient.sendInterrupt('context_input', 'continue', context);
        this.pendingInterrupts.delete(interruptId);
        console.log('Additional context provided:', context);
    }

    /**
     * Prompt user for tool approval (to be implemented by UI)
     * @param {Array} toolCalls - Tool calls to review
     * @param {string} interruptId - Interrupt ID
     */
    async promptUserForToolApproval(toolCalls, interruptId) {
        // This would typically show a UI dialog
        console.log('User approval needed for tools:', toolCalls);
        console.log('Use approveToolUsage(), rejectToolUsage(), or updateToolParameters()');
        
        // Example: Auto-approve after 10 seconds for demo
        setTimeout(() => {
            this.approveToolUsage(interruptId);
        }, 10000);
    }

    /**
     * Prompt user for output review (to be implemented by UI)
     * @param {string} content - Content to review
     * @param {string} interruptId - Interrupt ID
     */
    async promptUserForOutputReview(content, interruptId) {
        // This would typically show a UI dialog
        console.log('User review needed for output:', content);
        console.log('Use approveOutput() or requestOutputRevision()');
        
        // Example: Auto-approve after 15 seconds for demo
        setTimeout(() => {
            this.approveOutput(interruptId);
        }, 15000);
    }

    /**
     * Prompt user for additional context (to be implemented by UI)
     * @param {string} content - Current context
     * @param {string} interruptId - Interrupt ID
     */
    async promptUserForContext(content, interruptId) {
        // This would typically show a UI input dialog
        console.log('Additional context needed:', content);
        console.log('Use provideContext() to supply additional information');
        
        // Example: Provide default context after 10 seconds for demo
        setTimeout(() => {
            this.provideContext(interruptId, 'Please provide more specific details and examples.');
        }, 10000);
    }
}

/**
 * Example Usage Functions
 */

/**
 * Basic Chat Example
 * Demonstrates simple message sending and receiving
 */
async function basicChatExample() {
    console.log('🤖 Basic Chat Example');
    
    const client = new TeamStreamClient('team-123', 'thread-456', {
        DEFAULT_HEADERS: {
            ...API_CONFIG.DEFAULT_HEADERS,
            'x-user-id': 'user-123',
            'x-user-role': 'user'
        }
    });

    // Set up message handler
    client.onMessage((message) => {
        console.log(`💬 ${message.name}: ${message.content}`);
    });

    // Set up error handler
    client.onError((error) => {
        console.error('❌ Error:', error.message);
    });

    try {
        // Send a simple message
        await client.sendMessage('Hello! Please analyze the current AI market trends.');
        console.log('✅ Message sent successfully');
        
    } catch (error) {
        console.error('❌ Failed to send message:', error);
    }
}

/**
 * Hierarchical Workflow Example
 * Demonstrates interrupt handling for hierarchical workflows
 */
async function hierarchicalWorkflowExample() {
    console.log('🏗️ Hierarchical Workflow Example');
    
    const client = new TeamStreamClient('hierarchical-team-456', 'thread-789', {
        DEFAULT_HEADERS: {
            ...API_CONFIG.DEFAULT_HEADERS,
            'x-user-id': 'user-456',
            'x-user-role': 'user'
        }
    });

    // Set up hierarchical interrupt handler
    const interruptHandler = new HierarchicalInterruptHandler(client);

    // Set up message handler
    client.onMessage((message) => {
        console.log(`🤖 Team Response: ${message.content}`);
    });

    // Set up error handler
    client.onError((error) => {
        console.error('❌ Workflow Error:', error.message);
    });

    try {
        // Send a complex request that might trigger interrupts
        await client.sendMessage(
            'Please research the latest developments in quantum computing and create a comprehensive report with market analysis.'
        );
        console.log('✅ Complex request sent, waiting for team response and potential interrupts...');
        
    } catch (error) {
        console.error('❌ Failed to send request:', error);
    }
}

/**
 * Advanced Interrupt Management Example
 * Demonstrates manual interrupt handling with custom logic
 */
async function advancedInterruptExample() {
    console.log('⚡ Advanced Interrupt Example');
    
    const client = new TeamStreamClient('advanced-team-789', 'thread-101', {
        DEFAULT_HEADERS: {
            ...API_CONFIG.DEFAULT_HEADERS,
            'x-user-id': 'power-user-789',
            'x-user-role': 'admin'
        }
    });

    // Custom interrupt handling with business logic
    client.onInterrupt(async (interrupt) => {
        console.log('🔔 Interrupt received:', interrupt);
        
        switch (interrupt.name) {
            case 'tool_review':
                // Custom tool approval logic
                const toolCall = interrupt.tool_calls[0];
                
                if (toolCall.name === 'send_email') {
                    // Require explicit approval for email sending
                    console.log('📧 Email sending requires approval');
                    console.log('Tool call details:', toolCall);
                    
                    // Simulate user approval after review
                    setTimeout(async () => {
                        await client.sendInterrupt('tool_review', 'approved');
                        console.log('✅ Email sending approved');
                    }, 3000);
                    
                } else if (toolCall.name === 'delete_file') {
                    // Reject dangerous operations
                    await client.sendInterrupt(
                        'tool_review', 
                        'rejected', 
                        'File deletion is not allowed in this context. Please use a safer alternative.'
                    );
                    console.log('❌ File deletion rejected for safety');
                    
                } else {
                    // Auto-approve other tools with parameter validation
                    const updatedParams = validateAndUpdateParams(toolCall.args);
                    
                    if (updatedParams !== toolCall.args) {
                        await client.sendInterrupt('tool_review', 'update', JSON.stringify(updatedParams));
                        console.log('🔧 Tool parameters updated for safety');
                    } else {
                        await client.sendInterrupt('tool_review', 'approved');
                        console.log('✅ Tool approved');
                    }
                }
                break;
                
            case 'output_review':
                // Custom output review logic
                const content = interrupt.content;
                
                if (content.includes('confidential') || content.includes('private')) {
                    await client.sendInterrupt(
                        'output_review', 
                        'review', 
                        'Please remove any confidential information and ensure compliance with privacy policies.'
                    );
                    console.log('🔒 Output flagged for privacy review');
                } else {
                    await client.sendInterrupt('output_review', 'approved');
                    console.log('✅ Output approved');
                }
                break;
                
            case 'context_input':
                // Provide contextual information based on the request
                const contextInfo = getContextualInformation(interrupt.content);
                await client.sendInterrupt('context_input', 'continue', contextInfo);
                console.log('📝 Additional context provided');
                break;
        }
    });

    // Regular message handler
    client.onMessage((message) => {
        console.log(`🎯 ${message.name}: ${message.content}`);
    });

    try {
        await client.sendMessage(
            'Please help me organize my project files and send a status update to the team.'
        );
        console.log('✅ Request sent with advanced interrupt handling active');
        
    } catch (error) {
        console.error('❌ Error in advanced example:', error);
    }
}

/**
 * Utility Functions
 */

/**
 * Validate and update tool parameters for safety
 * @param {Object} params - Original tool parameters
 * @returns {Object} - Validated/updated parameters
 */
function validateAndUpdateParams(params) {
    const updatedParams = { ...params };
    
    // Example validation rules
    if (params.max_results && params.max_results > 100) {
        updatedParams.max_results = 100; // Limit to prevent abuse
    }
    
    if (params.query && typeof params.query === 'string') {
        // Sanitize query parameters
        updatedParams.query = params.query.replace(/[<>\"']/g, '');
    }
    
    return updatedParams;
}

/**
 * Get contextual information based on the request
 * @param {string} context - Current context
 * @returns {string} - Additional context information
 */
function getContextualInformation(context) {
    // Example context provision based on keywords
    if (context.includes('market analysis')) {
        return 'Please focus on the last 12 months of data and include competitor analysis. Use reputable sources like industry reports and financial publications.';
    } else if (context.includes('technical')) {
        return 'Provide technical details suitable for a development team audience. Include code examples and implementation considerations.';
    } else {
        return 'Please provide comprehensive information with clear explanations and relevant examples.';
    }
}

/**
 * Error Recovery Example
 * Demonstrates robust error handling and recovery
 */
async function errorRecoveryExample() {
    console.log('🛡️ Error Recovery Example');
    
    const client = new TeamStreamClient('test-team', 'test-thread');
    
    let retryCount = 0;
    const maxRetries = 3;
    
    client.onError(async (error) => {
        console.error(`❌ Error (attempt ${retryCount + 1}):`, error.message);
        
        if (retryCount < maxRetries) {
            retryCount++;
            console.log(`🔄 Retrying in ${retryCount * 2} seconds...`);
            
            setTimeout(async () => {
                try {
                    await client.sendMessage('Retry message after error');
                } catch (retryError) {
                    console.error('❌ Retry failed:', retryError);
                }
            }, retryCount * 2000);
        } else {
            console.error('❌ Max retries exceeded, giving up');
        }
    });
    
    // Simulate error scenario
    try {
        await client.sendMessage('This might cause an error');
    } catch (error) {
        console.log('Initial error handled by error callback');
    }
}

/**
 * Export classes and functions for use in other modules
 */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        TeamStreamClient,
        HierarchicalInterruptHandler,
        basicChatExample,
        hierarchicalWorkflowExample,
        advancedInterruptExample,
        errorRecoveryExample
    };
}

/**
 * Run examples if this file is executed directly
 */
if (typeof window === 'undefined' && require.main === module) {
    console.log('🚀 Running Team Stream API Examples\n');
    
    // Run examples sequentially
    (async () => {
        try {
            await basicChatExample();
            console.log('\n' + '='.repeat(50) + '\n');
            
            await hierarchicalWorkflowExample();
            console.log('\n' + '='.repeat(50) + '\n');
            
            await advancedInterruptExample();
            console.log('\n' + '='.repeat(50) + '\n');
            
            await errorRecoveryExample();
            
        } catch (error) {
            console.error('Example execution failed:', error);
        }
    })();
}

// Browser compatibility
if (typeof window !== 'undefined') {
    window.TeamStreamAPI = {
        TeamStreamClient,
        HierarchicalInterruptHandler,
        basicChatExample,
        hierarchicalWorkflowExample,
        advancedInterruptExample,
        errorRecoveryExample
    };
}
