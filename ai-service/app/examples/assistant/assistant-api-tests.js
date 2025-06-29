/**
 * Assistant API Testing Examples
 * 
 * This file contains comprehensive test examples for the Assistant API
 * using various testing approaches including unit tests, integration tests,
 * and manual testing scripts.
 */

// For Node.js environments with Jest or similar testing frameworks
const fetch = require('node-fetch'); // npm install node-fetch

// Configuration
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000/api/v1/assistant',
    TEST_USER_ID: 'test-user-123',
    TEST_USER_ROLE: 'user',
    TIMEOUT: 10000 // 10 seconds
};

// Helper function for API requests
const makeAPIRequest = async (url, options = {}) => {
    const headers = {
        'Content-Type': 'application/json',
        'x-user-id': CONFIG.TEST_USER_ID,
        'x-user-role': CONFIG.TEST_USER_ROLE,
        ...options.headers
    };

    const response = await fetch(url, {
        ...options,
        headers
    });

    const result = await response.json();
    
    return {
        status: response.status,
        ok: response.ok,
        data: result
    };
};

/**
 * Jest Test Suite for Assistant API
 */
describe('Assistant API Tests', () => {
    let createdAssistantId = null;
    
    // Setup and teardown
    beforeAll(async () => {
        console.log('Starting Assistant API tests...');
    });
    
    afterAll(async () => {
        // Clean up: delete any created test assistants
        if (createdAssistantId) {
            try {
                await makeAPIRequest(
                    `${CONFIG.API_BASE_URL}/${createdAssistantId}/soft-delete-advanced-assistant`,
                    { method: 'DELETE' }
                );
            } catch (error) {
                console.warn('Failed to clean up test assistant:', error.message);
            }
        }
    });

    /**
     * Test: Get All Assistants
     */
    describe('GET /get-all', () => {
        test('should fetch all assistants successfully', async () => {
            const response = await makeAPIRequest(`${CONFIG.API_BASE_URL}/get-all`);
            
            expect(response.ok).toBe(true);
            expect(response.data.status).toBe(200);
            expect(response.data.data).toHaveProperty('assistants');
            expect(response.data.data).toHaveProperty('pageNumber');
            expect(response.data.data).toHaveProperty('maxPerPage');
            expect(response.data.data).toHaveProperty('totalPage');
            expect(Array.isArray(response.data.data.assistants)).toBe(true);
        });

        test('should handle pagination parameters', async () => {
            const response = await makeAPIRequest(
                `${CONFIG.API_BASE_URL}/get-all?page_number=1&max_per_page=5`
            );
            
            expect(response.ok).toBe(true);
            expect(response.data.data.pageNumber).toBe(1);
            expect(response.data.data.maxPerPage).toBe(5);
        });

        test('should filter by assistant type', async () => {
            const response = await makeAPIRequest(
                `${CONFIG.API_BASE_URL}/get-all?assistant_type=advanced_assistant`
            );
            
            expect(response.ok).toBe(true);
            // All returned assistants should be advanced type
            response.data.data.assistants.forEach(assistant => {
                expect(assistant.assistantType).toBe('advanced_assistant');
            });
        });

        test('should handle invalid pagination parameters', async () => {
            const response = await makeAPIRequest(
                `${CONFIG.API_BASE_URL}/get-all?page_number=0&max_per_page=150`
            );
            
            expect(response.ok).toBe(false);
            expect(response.data.status).toBe(400);
        });
    });

    /**
     * Test: Get or Create General Assistant
     */
    describe('GET /get-or-create-general-assistant', () => {
        test('should get or create general assistant', async () => {
            const response = await makeAPIRequest(
                `${CONFIG.API_BASE_URL}/get-or-create-general-assistant`
            );
            
            expect(response.ok).toBe(true);
            expect([200, 201]).toContain(response.data.status);
            expect(response.data.data).toHaveProperty('id');
            expect(response.data.data).toHaveProperty('assistantType', 'general_assistant');
            expect(response.data.data).toHaveProperty('name');
        });
    });

    /**
     * Test: Create Advanced Assistant
     */
    describe('POST /create', () => {
        test('should create advanced assistant with minimum required fields', async () => {
            const assistantData = {
                name: 'Test Assistant',
                description: 'A test assistant for API testing',
                systemPrompt: 'You are a test assistant.'
            };

            const response = await makeAPIRequest(`${CONFIG.API_BASE_URL}/create`, {
                method: 'POST',
                body: JSON.stringify(assistantData)
            });

            expect(response.ok).toBe(true);
            expect(response.data.status).toBe(201);
            expect(response.data.data).toHaveProperty('id');
            expect(response.data.data.name).toBe(assistantData.name);
            expect(response.data.data.assistantType).toBe('advanced_assistant');
            
            // Store for cleanup
            createdAssistantId = response.data.data.id;
        });

        test('should create advanced assistant with all optional fields', async () => {
            const assistantData = {
                name: 'Full Test Assistant',
                description: 'A comprehensive test assistant with all features',
                systemPrompt: 'You are a comprehensive test assistant with full capabilities.',
                provider: 'openai',
                modelName: 'gpt-4',
                temperature: 0.5,
                askHuman: true,
                interrupt: false,
                supportUnits: ['ragbot', 'searchbot'],
                mcpIds: ['test-mcp-1', 'test-mcp-2'],
                extensionIds: ['test-ext-1']
            };

            const response = await makeAPIRequest(`${CONFIG.API_BASE_URL}/create`, {
                method: 'POST',
                body: JSON.stringify(assistantData)
            });

            expect(response.ok).toBe(true);
            expect(response.data.status).toBe(201);
            expect(response.data.data.provider).toBe(assistantData.provider);
            expect(response.data.data.modelName).toBe(assistantData.modelName);
            expect(response.data.data.temperature).toBe(assistantData.temperature);
            expect(response.data.data.supportUnits).toEqual(assistantData.supportUnits);
        });

        test('should reject invalid assistant data', async () => {
            const invalidData = {
                name: 'AB', // Too short
                description: 'Valid description',
                systemPrompt: 'Valid prompt'
            };

            const response = await makeAPIRequest(`${CONFIG.API_BASE_URL}/create`, {
                method: 'POST',
                body: JSON.stringify(invalidData)
            });

            expect(response.ok).toBe(false);
            expect(response.data.status).toBe(400);
            expect(response.data.message).toContain('name');
        });

        test('should reject missing required fields', async () => {
            const incompleteData = {
                name: 'Test Assistant'
                // Missing description and systemPrompt
            };

            const response = await makeAPIRequest(`${CONFIG.API_BASE_URL}/create`, {
                method: 'POST',
                body: JSON.stringify(incompleteData)
            });

            expect(response.ok).toBe(false);
            expect(response.data.status).toBe(400);
        });
    });

    /**
     * Test: Get Assistant Details
     */
    describe('GET /{assistant_id}/get-detail', () => {
        test('should get assistant details successfully', async () => {
            // First create an assistant to test with
            const createResponse = await makeAPIRequest(`${CONFIG.API_BASE_URL}/create`, {
                method: 'POST',
                body: JSON.stringify({
                    name: 'Detail Test Assistant',
                    description: 'Assistant for testing details endpoint',
                    systemPrompt: 'Test prompt'
                })
            });

            const assistantId = createResponse.data.data.id;

            const response = await makeAPIRequest(
                `${CONFIG.API_BASE_URL}/${assistantId}/get-detail`
            );

            expect(response.ok).toBe(true);
            expect(response.data.status).toBe(200);
            expect(response.data.data.id).toBe(assistantId);
            expect(response.data.data).toHaveProperty('teams');
        });

        test('should return 404 for non-existent assistant', async () => {
            const response = await makeAPIRequest(
                `${CONFIG.API_BASE_URL}/non-existent-id/get-detail`
            );

            expect(response.ok).toBe(false);
            expect(response.data.status).toBe(404);
            expect(response.data.message).toContain('not found');
        });
    });

    /**
     * Test: Update Assistant Configuration
     */
    describe('PATCH /{assistant_id}/update-config', () => {
        let testAssistantId;

        beforeAll(async () => {
            // Create an assistant for update tests
            const response = await makeAPIRequest(`${CONFIG.API_BASE_URL}/create`, {
                method: 'POST',
                body: JSON.stringify({
                    name: 'Update Test Assistant',
                    description: 'Assistant for testing updates',
                    systemPrompt: 'Original prompt'
                })
            });
            testAssistantId = response.data.data.id;
        });

        test('should update assistant configuration', async () => {
            const updateData = {
                systemPrompt: 'Updated system prompt for testing',
                temperature: 0.8,
                askHuman: true
            };

            const response = await makeAPIRequest(
                `${CONFIG.API_BASE_URL}/${testAssistantId}/update-config`,
                {
                    method: 'PATCH',
                    body: JSON.stringify(updateData)
                }
            );

            expect(response.ok).toBe(true);
            expect(response.data.status).toBe(200);
            expect(response.data.data.message).toContain('updated successfully');
        });

        test('should reject invalid configuration values', async () => {
            const invalidUpdate = {
                temperature: 5.0 // Invalid temperature (should be 0-2)
            };

            const response = await makeAPIRequest(
                `${CONFIG.API_BASE_URL}/${testAssistantId}/update-config`,
                {
                    method: 'PATCH',
                    body: JSON.stringify(invalidUpdate)
                }
            );

            expect(response.ok).toBe(false);
            expect(response.data.status).toBe(400);
        });
    });

    /**
     * Test: Delete Assistant
     */
    describe('DELETE /{assistant_id}/soft-delete-advanced-assistant', () => {
        test('should soft delete assistant successfully', async () => {
            // Create an assistant to delete
            const createResponse = await makeAPIRequest(`${CONFIG.API_BASE_URL}/create`, {
                method: 'POST',
                body: JSON.stringify({
                    name: 'Delete Test Assistant',
                    description: 'Assistant for testing deletion',
                    systemPrompt: 'Test prompt'
                })
            });

            const assistantId = createResponse.data.data.id;

            const response = await makeAPIRequest(
                `${CONFIG.API_BASE_URL}/${assistantId}/soft-delete-advanced-assistant`,
                { method: 'DELETE' }
            );

            expect(response.ok).toBe(true);
            expect(response.data.status).toBe(200);
            expect(response.data.data.message).toContain('soft deleted successfully');
        });

        test('should return 404 for non-existent assistant', async () => {
            const response = await makeAPIRequest(
                `${CONFIG.API_BASE_URL}/non-existent-id/soft-delete-advanced-assistant`,
                { method: 'DELETE' }
            );

            expect(response.ok).toBe(false);
            expect(response.data.status).toBe(404);
        });
    });
});

/**
 * Performance Test Suite
 */
describe('Assistant API Performance Tests', () => {
    test('should handle concurrent requests', async () => {
        const concurrentRequests = 10;
        const promises = Array(concurrentRequests).fill().map(() => 
            makeAPIRequest(`${CONFIG.API_BASE_URL}/get-all`)
        );

        const startTime = Date.now();
        const responses = await Promise.all(promises);
        const endTime = Date.now();

        // All requests should succeed
        responses.forEach(response => {
            expect(response.ok).toBe(true);
        });

        // Should complete within reasonable time
        expect(endTime - startTime).toBeLessThan(5000); // 5 seconds
    });

    test('should handle large pagination requests', async () => {
        const response = await makeAPIRequest(
            `${CONFIG.API_BASE_URL}/get-all?page_number=1&max_per_page=100`
        );

        expect(response.ok).toBe(true);
        expect(response.data.data.maxPerPage).toBe(100);
    });
});

/**
 * Integration Test Suite
 * Tests the complete workflow of assistant management
 */
describe('Assistant API Integration Tests', () => {
    test('complete assistant lifecycle', async () => {
        // 1. Create assistant
        const createResponse = await makeAPIRequest(`${CONFIG.API_BASE_URL}/create`, {
            method: 'POST',
            body: JSON.stringify({
                name: 'Lifecycle Test Assistant',
                description: 'Testing complete lifecycle',
                systemPrompt: 'Initial prompt',
                temperature: 0.5
            })
        });

        expect(createResponse.ok).toBe(true);
        const assistantId = createResponse.data.data.id;

        // 2. Get assistant details
        const detailsResponse = await makeAPIRequest(
            `${CONFIG.API_BASE_URL}/${assistantId}/get-detail`
        );

        expect(detailsResponse.ok).toBe(true);
        expect(detailsResponse.data.data.id).toBe(assistantId);

        // 3. Update configuration
        const updateResponse = await makeAPIRequest(
            `${CONFIG.API_BASE_URL}/${assistantId}/update-config`,
            {
                method: 'PATCH',
                body: JSON.stringify({
                    systemPrompt: 'Updated prompt',
                    temperature: 0.7
                })
            }
        );

        expect(updateResponse.ok).toBe(true);

        // 4. Verify update by getting details again
        const updatedDetailsResponse = await makeAPIRequest(
            `${CONFIG.API_BASE_URL}/${assistantId}/get-detail`
        );

        expect(updatedDetailsResponse.ok).toBe(true);
        // Note: API might not immediately reflect config changes in get-detail
        // This depends on implementation

        // 5. Soft delete
        const deleteResponse = await makeAPIRequest(
            `${CONFIG.API_BASE_URL}/${assistantId}/soft-delete-advanced-assistant`,
            { method: 'DELETE' }
        );

        expect(deleteResponse.ok).toBe(true);

        // 6. Verify deletion (should return 404)
        const deletedDetailsResponse = await makeAPIRequest(
            `${CONFIG.API_BASE_URL}/${assistantId}/get-detail`
        );

        expect(deletedDetailsResponse.ok).toBe(false);
        expect(deletedDetailsResponse.data.status).toBe(404);
    });
});

/**
 * Manual Testing Scripts
 * Functions that can be run manually for testing and debugging
 */

// Function to run all manual tests
const runManualTests = async () => {
    console.log('Starting manual Assistant API tests...\n');

    try {
        await testBasicFunctionality();
        await testErrorHandling();
        await testEdgeCases();
        console.log('\n✅ All manual tests completed successfully!');
    } catch (error) {
        console.error('\n❌ Manual tests failed:', error.message);
    }
};

// Test basic functionality
const testBasicFunctionality = async () => {
    console.log('🧪 Testing basic functionality...');

    // Test getting all assistants
    console.log('  - Getting all assistants...');
    const allAssistants = await makeAPIRequest(`${CONFIG.API_BASE_URL}/get-all`);
    console.log(`    Found ${allAssistants.data.data.assistants.length} assistants`);

    // Test creating an assistant
    console.log('  - Creating test assistant...');
    const newAssistant = await makeAPIRequest(`${CONFIG.API_BASE_URL}/create`, {
        method: 'POST',
        body: JSON.stringify({
            name: 'Manual Test Assistant',
            description: 'Created during manual testing',
            systemPrompt: 'You are a test assistant.'
        })
    });
    console.log(`    Created assistant: ${newAssistant.data.data.id}`);

    // Test getting assistant details
    console.log('  - Getting assistant details...');
    const details = await makeAPIRequest(
        `${CONFIG.API_BASE_URL}/${newAssistant.data.data.id}/get-detail`
    );
    console.log(`    Retrieved details for: ${details.data.data.name}`);

    // Clean up
    console.log('  - Cleaning up test assistant...');
    await makeAPIRequest(
        `${CONFIG.API_BASE_URL}/${newAssistant.data.data.id}/soft-delete-advanced-assistant`,
        { method: 'DELETE' }
    );
    console.log('    Test assistant deleted');
};

// Test error handling
const testErrorHandling = async () => {
    console.log('🔥 Testing error handling...');

    // Test invalid assistant creation
    console.log('  - Testing invalid assistant creation...');
    try {
        await makeAPIRequest(`${CONFIG.API_BASE_URL}/create`, {
            method: 'POST',
            body: JSON.stringify({
                name: 'AB', // Too short
                description: 'Valid description',
                systemPrompt: 'Valid prompt'
            })
        });
        console.log('    ❌ Should have failed but didn\'t');
    } catch (error) {
        console.log('    ✅ Correctly rejected invalid data');
    }

    // Test non-existent assistant
    console.log('  - Testing non-existent assistant retrieval...');
    try {
        await makeAPIRequest(`${CONFIG.API_BASE_URL}/fake-id/get-detail`);
        console.log('    ❌ Should have returned 404 but didn\'t');
    } catch (error) {
        console.log('    ✅ Correctly returned 404 for non-existent assistant');
    }
};

// Test edge cases
const testEdgeCases = async () => {
    console.log('🎯 Testing edge cases...');

    // Test maximum field lengths
    console.log('  - Testing maximum field lengths...');
    const longDescription = 'A'.repeat(5000); // Maximum allowed length
    const longPrompt = 'B'.repeat(5000);

    const maxLengthAssistant = await makeAPIRequest(`${CONFIG.API_BASE_URL}/create`, {
        method: 'POST',
        body: JSON.stringify({
            name: 'Max Length Test Assistant',
            description: longDescription,
            systemPrompt: longPrompt
        })
    });

    if (maxLengthAssistant.ok) {
        console.log('    ✅ Successfully created assistant with maximum field lengths');
        
        // Clean up
        await makeAPIRequest(
            `${CONFIG.API_BASE_URL}/${maxLengthAssistant.data.data.id}/soft-delete-advanced-assistant`,
            { method: 'DELETE' }
        );
    }

    // Test boundary values for temperature
    console.log('  - Testing temperature boundaries...');
    const boundaryTempAssistant = await makeAPIRequest(`${CONFIG.API_BASE_URL}/create`, {
        method: 'POST',
        body: JSON.stringify({
            name: 'Boundary Temp Assistant',
            description: 'Testing temperature boundaries',
            systemPrompt: 'Test prompt',
            temperature: 2.0 // Maximum allowed
        })
    });

    if (boundaryTempAssistant.ok) {
        console.log('    ✅ Successfully created assistant with boundary temperature');
        
        // Clean up
        await makeAPIRequest(
            `${CONFIG.API_BASE_URL}/${boundaryTempAssistant.data.data.id}/soft-delete-advanced-assistant`,
            { method: 'DELETE' }
        );
    }
};

/**
 * Load Testing Script
 */
const runLoadTest = async (concurrentUsers = 10, requestsPerUser = 5) => {
    console.log(`🚀 Running load test with ${concurrentUsers} concurrent users, ${requestsPerUser} requests each...`);

    const userPromises = Array(concurrentUsers).fill().map(async (_, userIndex) => {
        const userRequests = [];
        
        for (let i = 0; i < requestsPerUser; i++) {
            userRequests.push(
                makeAPIRequest(`${CONFIG.API_BASE_URL}/get-all?page_number=${i + 1}`)
            );
        }
        
        try {
            const results = await Promise.all(userRequests);
            return {
                userId: userIndex,
                successCount: results.filter(r => r.ok).length,
                totalRequests: requestsPerUser
            };
        } catch (error) {
            return {
                userId: userIndex,
                successCount: 0,
                totalRequests: requestsPerUser,
                error: error.message
            };
        }
    });

    const startTime = Date.now();
    const results = await Promise.all(userPromises);
    const endTime = Date.now();

    const totalRequests = concurrentUsers * requestsPerUser;
    const successfulRequests = results.reduce((sum, r) => sum + r.successCount, 0);
    const averageResponseTime = (endTime - startTime) / totalRequests;

    console.log('\n📊 Load Test Results:');
    console.log(`  Total requests: ${totalRequests}`);
    console.log(`  Successful requests: ${successfulRequests}`);
    console.log(`  Failed requests: ${totalRequests - successfulRequests}`);
    console.log(`  Success rate: ${((successfulRequests / totalRequests) * 100).toFixed(2)}%`);
    console.log(`  Total time: ${endTime - startTime}ms`);
    console.log(`  Average response time: ${averageResponseTime.toFixed(2)}ms`);
};

// Export functions for use in test runners
module.exports = {
    makeAPIRequest,
    runManualTests,
    testBasicFunctionality,
    testErrorHandling,
    testEdgeCases,
    runLoadTest,
    CONFIG
};

// If running this file directly, run manual tests
if (require.main === module) {
    runManualTests();
}
