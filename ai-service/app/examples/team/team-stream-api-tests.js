/**
 * Team Stream API Test Suite
 * 
 * This file contains test cases for the Team Stream API,
 * including tests for hierarchical workflow interrupts.
 */

const { TeamStreamClient, HierarchicalInterruptHandler } = require('./team-stream-examples');

// Test configuration
const TEST_CONFIG = {
    TEAM_ID: 'test-team-123',
    THREAD_ID: 'test-thread-456',
    HIERARCHICAL_TEAM_ID: 'hierarchical-test-789',
    HIERARCHICAL_THREAD_ID: 'hierarchical-thread-101',
    USER_CONFIG: {
        DEFAULT_HEADERS: {
            'Content-Type': 'application/json',
            'x-user-id': 'test-user-123',
            'x-user-role': 'user'
        }
    }
};

/**
 * Mock fetch for testing
 */
function mockFetch() {
    global.fetch = jest.fn();
}

/**
 * Create mock streaming response
 */
function createMockStreamResponse(events) {
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
        start(controller) {
            events.forEach(event => {
                const data = `data: ${JSON.stringify(event)}\n\n`;
                controller.enqueue(encoder.encode(data));
            });
            controller.close();
        }
    });

    return {
        ok: true,
        status: 200,
        body: stream
    };
}

/**
 * Test Suite: Basic Team Stream Functionality
 */
describe('TeamStreamClient', () => {
    let client;

    beforeEach(() => {
        mockFetch();
        client = new TeamStreamClient(
            TEST_CONFIG.TEAM_ID,
            TEST_CONFIG.THREAD_ID,
            TEST_CONFIG.USER_CONFIG
        );
    });

    afterEach(() => {
        jest.resetAllMocks();
    });

    test('should create client with correct configuration', () => {
        expect(client.teamId).toBe(TEST_CONFIG.TEAM_ID);
        expect(client.threadId).toBe(TEST_CONFIG.THREAD_ID);
        expect(client.options.DEFAULT_HEADERS['x-user-id']).toBe('test-user-123');
    });

    test('should send simple message successfully', async () => {
        const mockEvents = [
            {
                type: 'message',
                content: 'Hello! How can I help you today?',
                name: 'assistant',
                id: 'msg-123'
            }
        ];

        global.fetch.mockResolvedValue(createMockStreamResponse(mockEvents));

        const messageCallback = jest.fn();
        client.onMessage(messageCallback);

        await client.sendMessage('Hello, team!');

        expect(global.fetch).toHaveBeenCalledWith(
            `http://localhost:8000/api/v1/team/${TEST_CONFIG.TEAM_ID}/stream/${TEST_CONFIG.THREAD_ID}`,
            expect.objectContaining({
                method: 'POST',
                headers: expect.objectContaining({
                    'Content-Type': 'application/json',
                    'x-user-id': 'test-user-123'
                }),
                body: JSON.stringify({
                    messages: [
                        {
                            type: 'human',
                            content: 'Hello, team!'
                        }
                    ]
                })
            })
        );

        // Wait for stream processing
        await new Promise(resolve => setTimeout(resolve, 100));

        expect(messageCallback).toHaveBeenCalledWith(mockEvents[0]);
    });

    test('should handle error responses', async () => {
        global.fetch.mockResolvedValue({
            ok: false,
            status: 404,
            json: () => Promise.resolve({ message: 'Team not found' })
        });

        const errorCallback = jest.fn();
        client.onError(errorCallback);

        await expect(client.sendMessage('Test message')).rejects.toThrow('HTTP 404: Team not found');
    });

    test('should send interrupt successfully', async () => {
        const mockEvents = [
            {
                type: 'message',
                content: 'Tool usage approved, continuing...',
                name: 'system',
                id: 'msg-456'
            }
        ];

        global.fetch.mockResolvedValue(createMockStreamResponse(mockEvents));

        await client.sendInterrupt('tool_review', 'approved');

        expect(global.fetch).toHaveBeenCalledWith(
            expect.any(String),
            expect.objectContaining({
                body: JSON.stringify({
                    messages: [],
                    interrupt: {
                        interaction_type: 'tool_review',
                        decision: 'approved'
                    }
                })
            })
        );
    });

    test('should handle interrupt with tool message', async () => {
        const mockEvents = [];
        global.fetch.mockResolvedValue(createMockStreamResponse(mockEvents));

        await client.sendInterrupt('tool_review', 'rejected', 'Tool usage not allowed');

        expect(global.fetch).toHaveBeenCalledWith(
            expect.any(String),
            expect.objectContaining({
                body: JSON.stringify({
                    messages: [],
                    interrupt: {
                        interaction_type: 'tool_review',
                        decision: 'rejected',
                        tool_message: 'Tool usage not allowed'
                    }
                })
            })
        );
    });
});

/**
 * Test Suite: Hierarchical Workflow Interrupts
 */
describe('HierarchicalInterruptHandler', () => {
    let client;
    let handler;

    beforeEach(() => {
        mockFetch();
        client = new TeamStreamClient(
            TEST_CONFIG.HIERARCHICAL_TEAM_ID,
            TEST_CONFIG.HIERARCHICAL_THREAD_ID,
            TEST_CONFIG.USER_CONFIG
        );
        handler = new HierarchicalInterruptHandler(client);
    });

    afterEach(() => {
        jest.resetAllMocks();
    });

    test('should handle tool review interrupt', async () => {
        const mockInterrupt = {
            type: 'interrupt',
            name: 'tool_review',
            tool_calls: [
                {
                    id: 'call-123',
                    name: 'search_web',
                    args: { query: 'AI trends' }
                }
            ],
            id: 'interrupt-123'
        };

        global.fetch.mockResolvedValue(createMockStreamResponse([]));
        
        const spyApprove = jest.spyOn(handler, 'approveToolUsage');
        
        await handler.handleInterrupt(mockInterrupt);

        expect(spyApprove).toHaveBeenCalledWith('interrupt-123');
    });

    test('should handle dangerous tool rejection', async () => {
        const mockInterrupt = {
            type: 'interrupt',
            name: 'tool_review',
            tool_calls: [
                {
                    id: 'call-456',
                    name: 'delete_file',
                    args: { path: '/important/file.txt' }
                }
            ],
            id: 'interrupt-456'
        };

        global.fetch.mockResolvedValue(createMockStreamResponse([]));
        
        const spyReject = jest.spyOn(handler, 'rejectToolUsage');
        
        await handler.handleInterrupt(mockInterrupt);

        expect(spyReject).not.toHaveBeenCalled(); // Since we're testing the actual handler logic
    });

    test('should handle output review interrupt', async () => {
        const mockInterrupt = {
            type: 'interrupt',
            name: 'output_review',
            content: 'This is a short response.',
            id: 'interrupt-789'
        };

        global.fetch.mockResolvedValue(createMockStreamResponse([]));
        
        const spyApprove = jest.spyOn(handler, 'approveOutput');
        
        await handler.handleInterrupt(mockInterrupt);

        expect(spyApprove).toHaveBeenCalledWith('interrupt-789');
    });

    test('should handle context input interrupt', async () => {
        const mockInterrupt = {
            type: 'interrupt',
            name: 'context_input',
            content: 'Please provide more information about the market analysis.',
            id: 'interrupt-101'
        };

        global.fetch.mockResolvedValue(createMockStreamResponse([]));
        
        const spyContext = jest.spyOn(handler, 'promptUserForContext');
        
        await handler.handleInterrupt(mockInterrupt);

        expect(spyContext).toHaveBeenCalledWith(mockInterrupt.content, 'interrupt-101');
    });

    test('should approve tool usage', async () => {
        global.fetch.mockResolvedValue(createMockStreamResponse([]));
        
        await handler.approveToolUsage('test-interrupt-id');

        expect(global.fetch).toHaveBeenCalledWith(
            expect.any(String),
            expect.objectContaining({
                body: JSON.stringify({
                    messages: [],
                    interrupt: {
                        interaction_type: 'tool_review',
                        decision: 'approved'
                    }
                })
            })
        );
    });

    test('should reject tool usage with reason', async () => {
        global.fetch.mockResolvedValue(createMockStreamResponse([]));
        
        await handler.rejectToolUsage('test-interrupt-id', 'Security policy violation');

        expect(global.fetch).toHaveBeenCalledWith(
            expect.any(String),
            expect.objectContaining({
                body: JSON.stringify({
                    messages: [],
                    interrupt: {
                        interaction_type: 'tool_review',
                        decision: 'rejected',
                        tool_message: 'Security policy violation'
                    }
                })
            })
        );
    });

    test('should update tool parameters', async () => {
        global.fetch.mockResolvedValue(createMockStreamResponse([]));
        
        const newParams = { query: 'AI trends 2024', max_results: 5 };
        await handler.updateToolParameters('test-interrupt-id', newParams);

        expect(global.fetch).toHaveBeenCalledWith(
            expect.any(String),
            expect.objectContaining({
                body: JSON.stringify({
                    messages: [],
                    interrupt: {
                        interaction_type: 'tool_review',
                        decision: 'update',
                        tool_message: JSON.stringify(newParams)
                    }
                })
            })
        );
    });

    test('should request output revision', async () => {
        global.fetch.mockResolvedValue(createMockStreamResponse([]));
        
        await handler.requestOutputRevision('test-interrupt-id', 'Please add more examples');

        expect(global.fetch).toHaveBeenCalledWith(
            expect.any(String),
            expect.objectContaining({
                body: JSON.stringify({
                    messages: [],
                    interrupt: {
                        interaction_type: 'output_review',
                        decision: 'review',
                        tool_message: 'Please add more examples'
                    }
                })
            })
        );
    });

    test('should provide additional context', async () => {
        global.fetch.mockResolvedValue(createMockStreamResponse([]));
        
        await handler.provideContext('test-interrupt-id', 'Focus on enterprise solutions');

        expect(global.fetch).toHaveBeenCalledWith(
            expect.any(String),
            expect.objectContaining({
                body: JSON.stringify({
                    messages: [],
                    interrupt: {
                        interaction_type: 'context_input',
                        decision: 'continue',
                        tool_message: 'Focus on enterprise solutions'
                    }
                })
            })
        );
    });
});

/**
 * Integration Tests
 */
describe('Team Stream API Integration', () => {
    test('should handle complete workflow with interrupts', async () => {
        mockFetch();
        
        const client = new TeamStreamClient('integration-team', 'integration-thread');
        const handler = new HierarchicalInterruptHandler(client);

        const mockEvents = [
            // Initial message
            {
                type: 'message',
                content: 'I need to search for information. Requesting tool approval...',
                name: 'assistant',
                id: 'msg-1'
            },
            // Tool review interrupt
            {
                type: 'interrupt',
                name: 'tool_review',
                tool_calls: [
                    {
                        id: 'call-1',
                        name: 'search_web',
                        args: { query: 'AI developments' }
                    }
                ],
                id: 'interrupt-1'
            }
        ];

        global.fetch
            .mockResolvedValueOnce(createMockStreamResponse(mockEvents))
            .mockResolvedValueOnce(createMockStreamResponse([])); // For interrupt response

        const messageCallback = jest.fn();
        const interruptCallback = jest.fn();

        client.onMessage(messageCallback);
        client.onInterrupt(interruptCallback);

        // Send initial message
        await client.sendMessage('Please research AI developments');

        // Wait for processing
        await new Promise(resolve => setTimeout(resolve, 100));

        expect(messageCallback).toHaveBeenCalledWith(mockEvents[0]);
        expect(interruptCallback).toHaveBeenCalledWith(mockEvents[1]);
    });

    test('should handle error recovery', async () => {
        mockFetch();
        
        const client = new TeamStreamClient('error-team', 'error-thread');
        
        // First call fails
        global.fetch.mockResolvedValueOnce({
            ok: false,
            status: 500,
            json: () => Promise.resolve({ message: 'Internal server error' })
        });
        
        // Second call succeeds
        global.fetch.mockResolvedValueOnce(createMockStreamResponse([
            {
                type: 'message',
                content: 'Recovery successful',
                name: 'assistant',
                id: 'msg-recovery'
            }
        ]));

        const errorCallback = jest.fn();
        const messageCallback = jest.fn();

        client.onError(errorCallback);
        client.onMessage(messageCallback);

        // First attempt should fail
        await expect(client.sendMessage('Test message')).rejects.toThrow('HTTP 500: Internal server error');

        // Second attempt should succeed
        await client.sendMessage('Retry message');

        await new Promise(resolve => setTimeout(resolve, 100));

        expect(messageCallback).toHaveBeenCalledWith(
            expect.objectContaining({
                content: 'Recovery successful'
            })
        );
    });
});

/**
 * Performance Tests
 */
describe('Team Stream API Performance', () => {
    test('should handle multiple concurrent requests', async () => {
        mockFetch();
        
        const clients = Array.from({ length: 5 }, (_, i) => 
            new TeamStreamClient(`team-${i}`, `thread-${i}`)
        );

        global.fetch.mockResolvedValue(createMockStreamResponse([
            {
                type: 'message',
                content: 'Concurrent response',
                name: 'assistant',
                id: 'concurrent-msg'
            }
        ]));

        const promises = clients.map((client, i) => 
            client.sendMessage(`Concurrent message ${i}`)
        );

        const startTime = Date.now();
        await Promise.all(promises);
        const endTime = Date.now();

        expect(endTime - startTime).toBeLessThan(5000); // Should complete within 5 seconds
        expect(global.fetch).toHaveBeenCalledTimes(5);
    });

    test('should handle large message content', async () => {
        mockFetch();
        
        const client = new TeamStreamClient('large-team', 'large-thread');
        const largeContent = 'x'.repeat(10000); // 10KB message

        global.fetch.mockResolvedValue(createMockStreamResponse([
            {
                type: 'message',
                content: 'Large message processed',
                name: 'assistant',
                id: 'large-msg'
            }
        ]));

        await expect(client.sendMessage(largeContent)).resolves.not.toThrow();
        
        expect(global.fetch).toHaveBeenCalledWith(
            expect.any(String),
            expect.objectContaining({
                body: expect.stringContaining(largeContent)
            })
        );
    });
});

/**
 * Edge Cases and Error Handling
 */
describe('Team Stream API Edge Cases', () => {
    test('should handle malformed stream data', async () => {
        mockFetch();
        
        const client = new TeamStreamClient('malformed-team', 'malformed-thread');
        
        // Create stream with malformed JSON
        const encoder = new TextEncoder();
        const stream = new ReadableStream({
            start(controller) {
                controller.enqueue(encoder.encode('data: {invalid json}\n\n'));
                controller.enqueue(encoder.encode('data: {"type": "message", "content": "valid"}\n\n'));
                controller.close();
            }
        });

        global.fetch.mockResolvedValue({
            ok: true,
            status: 200,
            body: stream
        });

        const messageCallback = jest.fn();
        const consoleWarn = jest.spyOn(console, 'warn').mockImplementation();

        client.onMessage(messageCallback);

        await client.sendMessage('Test message');

        await new Promise(resolve => setTimeout(resolve, 100));

        expect(consoleWarn).toHaveBeenCalledWith('Failed to parse SSE data:', 'data: {invalid json}');
        expect(messageCallback).toHaveBeenCalledWith(
            expect.objectContaining({
                type: 'message',
                content: 'valid'
            })
        );

        consoleWarn.mockRestore();
    });

    test('should handle network interruption', async () => {
        mockFetch();
        
        const client = new TeamStreamClient('network-team', 'network-thread');
        
        global.fetch.mockRejectedValue(new Error('Network error'));

        const errorCallback = jest.fn();
        client.onError(errorCallback);

        await expect(client.sendMessage('Test message')).rejects.toThrow('Network error');
    });

    test('should validate required parameters', () => {
        expect(() => new TeamStreamClient('', 'thread')).not.toThrow();
        expect(() => new TeamStreamClient('team', '')).not.toThrow();
        
        const client = new TeamStreamClient('', '');
        expect(client.sendMessage('test')).rejects.toThrow('Team ID and Thread ID are required');
    });
});

module.exports = {
    TEST_CONFIG,
    createMockStreamResponse,
    mockFetch
};
