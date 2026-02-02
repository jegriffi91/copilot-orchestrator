#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

import {
    createTopic,
    listTopicsTool,
    switchTopic,
    delegateTo,
    checkDelegations,
} from './tools/index.js';

// Create MCP server
const server = new Server(
    {
        name: 'copilot-orchestrator',
        version: '0.1.0',
    },
    {
        capabilities: {
            tools: {},
        },
    }
);

// Tool definitions
const TOOLS = [
    {
        name: 'create_topic',
        description: 'Create a new workflow topic with plan.md and task.md scaffolds. Topics are isolated workspaces for different tasks.',
        inputSchema: {
            type: 'object',
            properties: {
                name: {
                    type: 'string',
                    description: 'Topic name (kebab-case recommended, e.g., "auth-refactor")',
                },
                description: {
                    type: 'string',
                    description: 'Brief description of the topic goal',
                },
            },
            required: ['name'],
        },
    },
    {
        name: 'list_topics',
        description: 'List all workflow topics and their status. Shows active topic, pending delegations, etc.',
        inputSchema: {
            type: 'object',
            properties: {},
        },
    },
    {
        name: 'switch_topic',
        description: 'Switch to a different topic, loading its plan.md and task.md context. Returns a summary of where you left off.',
        inputSchema: {
            type: 'object',
            properties: {
                name: {
                    type: 'string',
                    description: 'Name of the topic to switch to',
                },
            },
            required: ['name'],
        },
    },
    {
        name: 'delegate_to',
        description: 'Delegate a task to a specialist agent (e.g., swift6, testing, docs). Creates a delegation file that the agent will pick up.',
        inputSchema: {
            type: 'object',
            properties: {
                agent: {
                    type: 'string',
                    description: 'Agent name (e.g., "swift6", "testing", "docs")',
                },
                task: {
                    type: 'string',
                    description: 'Natural language task description',
                },
                context: {
                    type: 'object',
                    description: 'Context to provide to the agent',
                    properties: {
                        files: {
                            type: 'array',
                            items: { type: 'string' },
                            description: 'File paths to include as context',
                        },
                        plan_excerpt: {
                            type: 'string',
                            description: 'Relevant section of plan.md',
                        },
                        constraints: {
                            type: 'string',
                            description: 'Specific boundaries or requirements',
                        },
                    },
                },
                model_tier: {
                    type: 'string',
                    enum: ['premium', 'standard', 'cheap'],
                    default: 'cheap',
                    description: 'Model tier for the agent (default: cheap)',
                },
                blocking: {
                    type: 'boolean',
                    default: false,
                    description: 'Wait for result before returning (not yet implemented)',
                },
            },
            required: ['agent', 'task'],
        },
    },
    {
        name: 'check_delegations',
        description: 'Check status of delegated tasks. Shows pending, in-progress, and completed delegations.',
        inputSchema: {
            type: 'object',
            properties: {
                topic: {
                    type: 'string',
                    description: 'Topic to check (defaults to current topic)',
                },
                agent: {
                    type: 'string',
                    description: 'Filter by specific agent',
                },
            },
        },
    },
];

// Handle list_tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return { tools: TOOLS };
});

// Handle call_tool
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
        switch (name) {
            case 'create_topic':
                return await createTopic(args);

            case 'list_topics':
                return await listTopicsTool();

            case 'switch_topic':
                return await switchTopic(args);

            case 'delegate_to':
                return await delegateTo(args);

            case 'check_delegations':
                return await checkDelegations(args);

            default:
                return {
                    content: [{
                        type: 'text',
                        text: `Unknown tool: ${name}`,
                    }],
                    isError: true,
                };
        }
    } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return {
            content: [{
                type: 'text',
                text: `Error: ${message}`,
            }],
            isError: true,
        };
    }
});

// Start server
async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error('Copilot Orchestrator MCP server running on stdio');
}

main().catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
});
