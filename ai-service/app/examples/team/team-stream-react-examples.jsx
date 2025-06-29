/**
 * React Team Stream API Integration Examples
 * 
 * This file demonstrates how to integrate the Team Stream API with React applications,
 * including UI components for handling hierarchical workflow interrupts.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Custom Hook for Team Stream API
 */
const useTeamStream = (teamId, threadId, userConfig = {}) => {
    const [messages, setMessages] = useState([]);
    const [currentInterrupt, setCurrentInterrupt] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    
    const config = {
        baseUrl: 'http://localhost:8000/api/v1/team',
        headers: {
            'Content-Type': 'application/json',
            'x-user-id': 'default-user',
            'x-user-role': 'user',
            ...userConfig.headers
        },
        ...userConfig
    };

    /**
     * Send a message to the team
     */
    const sendMessage = useCallback(async (content, imgdata = null) => {
        if (!teamId || !threadId) {
            throw new Error('Team ID and Thread ID are required');
        }

        setIsLoading(true);
        setError(null);

        const payload = {
            messages: [
                {
                    type: 'human',
                    content: content,
                    ...(imgdata && { imgdata })
                }
            ]
        };

        try {
            const response = await fetch(`${config.baseUrl}/${teamId}/stream/${threadId}`, {
                method: 'POST',
                headers: config.headers,
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`HTTP ${response.status}: ${errorData.message || 'Unknown error'}`);
            }

            await handleStreamResponse(response);
            
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setIsLoading(false);
        }
    }, [teamId, threadId, config]);

    /**
     * Send an interrupt response
     */
    const sendInterrupt = useCallback(async (interactionType, decision, toolMessage = null) => {
        setIsLoading(true);
        setError(null);

        const payload = {
            messages: [],
            interrupt: {
                interaction_type: interactionType,
                decision: decision,
                ...(toolMessage && { tool_message: toolMessage })
            }
        };

        try {
            const response = await fetch(`${config.baseUrl}/${teamId}/stream/${threadId}`, {
                method: 'POST',
                headers: config.headers,
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`HTTP ${response.status}: ${errorData.message}`);
            }

            await handleStreamResponse(response);
            setCurrentInterrupt(null); // Clear interrupt after handling
            
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setIsLoading(false);
        }
    }, [teamId, threadId, config]);

    /**
     * Handle streaming response
     */
    const handleStreamResponse = async (response) => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        try {
            setIsConnected(true);
            
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            handleStreamEvent(data);
                        } catch (e) {
                            console.warn('Failed to parse SSE data:', line);
                        }
                    }
                }
            }
        } finally {
            reader.releaseLock();
            setIsConnected(false);
        }
    };

    /**
     * Handle individual stream events
     */
    const handleStreamEvent = (data) => {
        switch (data.type) {
            case 'message':
                setMessages(prev => [...prev, {
                    id: data.id,
                    type: 'ai',
                    content: data.content,
                    name: data.name,
                    timestamp: new Date()
                }]);
                break;
                
            case 'interrupt':
                setCurrentInterrupt(data);
                break;
                
            case 'error':
                setError(data.content || 'Stream error occurred');
                break;
                
            default:
                console.warn('Unknown stream event type:', data.type);
        }
    };

    return {
        messages,
        currentInterrupt,
        isConnected,
        error,
        isLoading,
        sendMessage,
        sendInterrupt,
        clearError: () => setError(null),
        clearMessages: () => setMessages([])
    };
};

/**
 * Tool Review Dialog Component
 */
const ToolReviewDialog = ({ interrupt, onApprove, onReject, onUpdate, onClose }) => {
    const [isUpdating, setIsUpdating] = useState(false);
    const [updatedParams, setUpdatedParams] = useState('');
    const [rejectReason, setRejectReason] = useState('');

    if (!interrupt || interrupt.name !== 'tool_review') return null;

    const toolCall = interrupt.tool_calls?.[0];
    if (!toolCall) return null;

    const handleUpdate = () => {
        try {
            const params = JSON.parse(updatedParams);
            onUpdate(params);
            setIsUpdating(false);
        } catch (e) {
            alert('Invalid JSON format for parameters');
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
                <h2 className="text-xl font-bold mb-4">🔧 Tool Usage Review</h2>
                
                <div className="mb-4">
                    <h3 className="font-semibold mb-2">Tool Details:</h3>
                    <div className="bg-gray-100 p-3 rounded">
                        <p><strong>Tool:</strong> {toolCall.name}</p>
                        <p><strong>Parameters:</strong></p>
                        <pre className="mt-2 text-sm overflow-x-auto">
                            {JSON.stringify(toolCall.args, null, 2)}
                        </pre>
                    </div>
                </div>

                {!isUpdating && (
                    <div className="flex flex-wrap gap-2 mb-4">
                        <button
                            onClick={onApprove}
                            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                        >
                            ✅ Approve
                        </button>
                        
                        <button
                            onClick={() => setIsUpdating(true)}
                            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                        >
                            🔧 Update Parameters
                        </button>
                        
                        <button
                            onClick={() => {
                                const reason = window.prompt('Reason for rejection (optional):');
                                onReject(reason);
                            }}
                            className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                        >
                            ❌ Reject
                        </button>
                        
                        <button
                            onClick={onClose}
                            className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
                        >
                            Cancel
                        </button>
                    </div>
                )}

                {isUpdating && (
                    <div className="mb-4">
                        <h3 className="font-semibold mb-2">Update Parameters:</h3>
                        <textarea
                            value={updatedParams}
                            onChange={(e) => setUpdatedParams(e.target.value)}
                            placeholder={JSON.stringify(toolCall.args, null, 2)}
                            className="w-full h-32 p-2 border rounded font-mono text-sm"
                        />
                        <div className="flex gap-2 mt-2">
                            <button
                                onClick={handleUpdate}
                                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                            >
                                Apply Updates
                            </button>
                            <button
                                onClick={() => setIsUpdating(false)}
                                className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

/**
 * Output Review Dialog Component
 */
const OutputReviewDialog = ({ interrupt, onApprove, onRequestRevision, onClose }) => {
    const [feedback, setFeedback] = useState('');

    if (!interrupt || interrupt.name !== 'output_review') return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
                <h2 className="text-xl font-bold mb-4">📝 Output Review</h2>
                
                <div className="mb-4">
                    <h3 className="font-semibold mb-2">AI Output:</h3>
                    <div className="bg-gray-100 p-3 rounded max-h-60 overflow-y-auto">
                        <pre className="whitespace-pre-wrap text-sm">{interrupt.content}</pre>
                    </div>
                </div>

                <div className="mb-4">
                    <label className="block font-semibold mb-2">Feedback (optional):</label>
                    <textarea
                        value={feedback}
                        onChange={(e) => setFeedback(e.target.value)}
                        placeholder="Enter feedback for revision..."
                        className="w-full h-24 p-2 border rounded"
                    />
                </div>

                <div className="flex gap-2">
                    <button
                        onClick={onApprove}
                        className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                    >
                        ✅ Approve Output
                    </button>
                    
                    <button
                        onClick={() => onRequestRevision(feedback)}
                        className="bg-orange-500 text-white px-4 py-2 rounded hover:bg-orange-600"
                    >
                        🔄 Request Revision
                    </button>
                    
                    <button
                        onClick={onClose}
                        className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
                    >
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    );
};

/**
 * Context Input Dialog Component
 */
const ContextInputDialog = ({ interrupt, onProvideContext, onClose }) => {
    const [context, setContext] = useState('');

    if (!interrupt || interrupt.name !== 'context_input') return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-lg w-full">
                <h2 className="text-xl font-bold mb-4">💭 Additional Context Required</h2>
                
                <div className="mb-4">
                    <p className="text-gray-700 mb-2">{interrupt.content}</p>
                </div>

                <div className="mb-4">
                    <label className="block font-semibold mb-2">Additional Information:</label>
                    <textarea
                        value={context}
                        onChange={(e) => setContext(e.target.value)}
                        placeholder="Provide additional context or information..."
                        className="w-full h-24 p-2 border rounded"
                        autoFocus
                    />
                </div>

                <div className="flex gap-2">
                    <button
                        onClick={() => onProvideContext(context)}
                        disabled={!context.trim()}
                        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:bg-gray-300"
                    >
                        📤 Provide Context
                    </button>
                    
                    <button
                        onClick={onClose}
                        className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
                    >
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    );
};

/**
 * Main Chat Interface Component
 */
const TeamChatInterface = ({ teamId, threadId, userConfig }) => {
    const [inputMessage, setInputMessage] = useState('');
    const [showInterruptDialog, setShowInterruptDialog] = useState(false);
    const messagesEndRef = useRef(null);

    const {
        messages,
        currentInterrupt,
        isConnected,
        error,
        isLoading,
        sendMessage,
        sendInterrupt,
        clearError
    } = useTeamStream(teamId, threadId, userConfig);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Show interrupt dialog when interrupt is received
    useEffect(() => {
        if (currentInterrupt) {
            setShowInterruptDialog(true);
        }
    }, [currentInterrupt]);

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!inputMessage.trim() || isLoading) return;

        const messageToSend = inputMessage;
        setInputMessage('');

        // Add user message to UI immediately
        const userMessage = {
            id: Date.now().toString(),
            type: 'human',
            content: messageToSend,
            timestamp: new Date()
        };

        try {
            await sendMessage(messageToSend);
        } catch (err) {
            console.error('Failed to send message:', err);
        }
    };

    const handleInterruptApprove = async () => {
        try {
            await sendInterrupt(currentInterrupt.name, 'approved');
            setShowInterruptDialog(false);
        } catch (err) {
            console.error('Failed to approve:', err);
        }
    };

    const handleInterruptReject = async (reason) => {
        try {
            await sendInterrupt(currentInterrupt.name, 'rejected', reason);
            setShowInterruptDialog(false);
        } catch (err) {
            console.error('Failed to reject:', err);
        }
    };

    const handleInterruptUpdate = async (params) => {
        try {
            await sendInterrupt(currentInterrupt.name, 'update', JSON.stringify(params));
            setShowInterruptDialog(false);
        } catch (err) {
            console.error('Failed to update:', err);
        }
    };

    const handleOutputRevision = async (feedback) => {
        try {
            await sendInterrupt(currentInterrupt.name, 'review', feedback);
            setShowInterruptDialog(false);
        } catch (err) {
            console.error('Failed to request revision:', err);
        }
    };

    const handleProvideContext = async (context) => {
        try {
            await sendInterrupt(currentInterrupt.name, 'continue', context);
            setShowInterruptDialog(false);
        } catch (err) {
            console.error('Failed to provide context:', err);
        }
    };

    return (
        <div className="flex flex-col h-full max-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white border-b p-4 flex items-center justify-between">
                <div>
                    <h1 className="text-lg font-semibold">Team Chat</h1>
                    <p className="text-sm text-gray-600">
                        Team: {teamId} | Thread: {threadId}
                        {isConnected && <span className="ml-2 text-green-500">● Connected</span>}
                        {isLoading && <span className="ml-2 text-blue-500">● Processing...</span>}
                    </p>
                </div>
                
                {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-3 py-2 rounded flex items-center">
                        <span className="mr-2">❌ {error}</span>
                        <button 
                            onClick={clearError}
                            className="text-red-500 hover:text-red-700"
                        >
                            ✕
                        </button>
                    </div>
                )}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`flex ${message.type === 'human' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div
                            className={`max-w-[70%] rounded-lg p-3 ${
                                message.type === 'human'
                                    ? 'bg-blue-500 text-white'
                                    : 'bg-white border shadow-sm'
                            }`}
                        >
                            {message.name && message.type === 'ai' && (
                                <div className="text-xs text-gray-500 mb-1 font-semibold">
                                    {message.name}
                                </div>
                            )}
                            <div className="whitespace-pre-wrap">{message.content}</div>
                            <div className={`text-xs mt-1 ${
                                message.type === 'human' ? 'text-blue-100' : 'text-gray-400'
                            }`}>
                                {message.timestamp?.toLocaleTimeString()}
                            </div>
                        </div>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSendMessage} className="bg-white border-t p-4">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        placeholder="Type your message..."
                        className="flex-1 border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={!inputMessage.trim() || isLoading}
                        className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-300"
                    >
                        {isLoading ? '⏳' : '📤'}
                    </button>
                </div>
            </form>

            {/* Interrupt Dialogs */}
            {showInterruptDialog && (
                <>
                    <ToolReviewDialog
                        interrupt={currentInterrupt}
                        onApprove={handleInterruptApprove}
                        onReject={handleInterruptReject}
                        onUpdate={handleInterruptUpdate}
                        onClose={() => setShowInterruptDialog(false)}
                    />
                    
                    <OutputReviewDialog
                        interrupt={currentInterrupt}
                        onApprove={handleInterruptApprove}
                        onRequestRevision={handleOutputRevision}
                        onClose={() => setShowInterruptDialog(false)}
                    />
                    
                    <ContextInputDialog
                        interrupt={currentInterrupt}
                        onProvideContext={handleProvideContext}
                        onClose={() => setShowInterruptDialog(false)}
                    />
                </>
            )}
        </div>
    );
};

/**
 * Example App Component
 */
const TeamStreamApp = () => {
    const [teamId, setTeamId] = useState('demo-team-123');
    const [threadId, setThreadId] = useState('demo-thread-456');
    const [userId, setUserId] = useState('demo-user-789');
    const [userRole, setUserRole] = useState('user');

    const userConfig = {
        headers: {
            'x-user-id': userId,
            'x-user-role': userRole
        }
    };

    return (
        <div className="h-screen flex flex-col">
            {/* Configuration Header */}
            <div className="bg-gray-100 p-4 border-b">
                <h1 className="text-xl font-bold mb-2">Team Stream API Demo</h1>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    <div>
                        <label className="block text-xs font-semibold mb-1">Team ID</label>
                        <input
                            type="text"
                            value={teamId}
                            onChange={(e) => setTeamId(e.target.value)}
                            className="w-full text-xs p-1 border rounded"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-semibold mb-1">Thread ID</label>
                        <input
                            type="text"
                            value={threadId}
                            onChange={(e) => setThreadId(e.target.value)}
                            className="w-full text-xs p-1 border rounded"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-semibold mb-1">User ID</label>
                        <input
                            type="text"
                            value={userId}
                            onChange={(e) => setUserId(e.target.value)}
                            className="w-full text-xs p-1 border rounded"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-semibold mb-1">User Role</label>
                        <select
                            value={userRole}
                            onChange={(e) => setUserRole(e.target.value)}
                            className="w-full text-xs p-1 border rounded"
                        >
                            <option value="user">User</option>
                            <option value="admin">Admin</option>
                            <option value="super admin">Super Admin</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Chat Interface */}
            <div className="flex-1">
                <TeamChatInterface
                    teamId={teamId}
                    threadId={threadId}
                    userConfig={userConfig}
                />
            </div>
        </div>
    );
};

export {
    ContextInputDialog, OutputReviewDialog, TeamChatInterface, TeamStreamApp, ToolReviewDialog, useTeamStream
};

export default TeamStreamApp;
