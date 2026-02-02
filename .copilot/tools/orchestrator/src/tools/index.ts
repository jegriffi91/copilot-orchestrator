import {
    listTopics,
    loadTopic,
    createTopic as createTopicFs,
    saveSession,
    createDelegation,
    loadAgent,
    getAgentPath,
} from '../utils/filesystem.js';
import {
    CreateTopicArgsSchema,
    SwitchTopicArgsSchema,
    DelegateToArgsSchema,
    CheckDelegationsArgsSchema,
    TopicState,
    Session,
    DelegationInfo,
} from '../types.js';

// Track the current active topic
let currentTopic: TopicState | null = null;

// ============================================
// create_topic
// ============================================

export async function createTopic(args: unknown): Promise<{ content: { type: 'text'; text: string }[] }> {
    const parsed = CreateTopicArgsSchema.parse(args);

    const topic = await createTopicFs(parsed.name, parsed.description);
    currentTopic = topic;

    // Create session
    const session: Session = {
        session_id: process.env.COPILOT_SESSION_ID || `local-${Date.now()}`,
        topic: parsed.name,
        created: new Date().toISOString(),
        last_active: new Date().toISOString(),
        coordinator_model: 'premium',
    };
    await saveSession(parsed.name, session);

    return {
        content: [{
            type: 'text',
            text: `✅ Created topic "${parsed.name}"

**Path:** ${topic.path}
**Files created:**
- plan.md (implementation plan scaffold)
- task.md (progress checklist)
- .delegations/ (for agent handoffs)

You are now working on this topic. Use \`switch_topic\` to change topics.`,
        }],
    };
}

// ============================================
// list_topics
// ============================================

export async function listTopicsTool(): Promise<{ content: { type: 'text'; text: string }[] }> {
    const topics = await listTopics();

    if (topics.length === 0) {
        return {
            content: [{
                type: 'text',
                text: 'No topics found. Use `create_topic` to start a new topic.',
            }],
        };
    }

    const topicDetails = await Promise.all(
        topics.map(async (name) => {
            const state = await loadTopic(name);
            const pending = state?.delegations.filter((d: DelegationInfo) => d.status === 'PENDING').length || 0;
            const active = currentTopic?.name === name ? ' ← active' : '';
            return `- **${name}**${active}${pending > 0 ? ` (${pending} pending delegations)` : ''}`;
        })
    );

    return {
        content: [{
            type: 'text',
            text: `## Topics\n\n${topicDetails.join('\n')}`,
        }],
    };
}

// ============================================
// switch_topic
// ============================================

export async function switchTopic(args: unknown): Promise<{ content: { type: 'text'; text: string }[] }> {
    const parsed = SwitchTopicArgsSchema.parse(args);

    const topic = await loadTopic(parsed.name);
    if (!topic) {
        return {
            content: [{
                type: 'text',
                text: `❌ Topic "${parsed.name}" not found. Use \`list_topics\` to see available topics.`,
            }],
        };
    }

    currentTopic = topic;

    // Update session
    const session: Session = {
        session_id: process.env.COPILOT_SESSION_ID || `local-${Date.now()}`,
        topic: parsed.name,
        created: topic.session?.created || new Date().toISOString(),
        last_active: new Date().toISOString(),
        coordinator_model: topic.session?.coordinator_model || 'premium',
    };
    await saveSession(parsed.name, session);

    // Build context summary
    const pendingDelegations = topic.delegations.filter((d: DelegationInfo) => d.status === 'PENDING');
    const completeDelegations = topic.delegations.filter((d: DelegationInfo) => d.status === 'COMPLETE');

    let contextSummary = `# Switched to: ${parsed.name}\n\n`;

    if (topic.plan) {
        // Extract first 500 chars of plan as summary
        const planPreview = topic.plan.slice(0, 500) + (topic.plan.length > 500 ? '...' : '');
        contextSummary += `## Plan Preview\n\`\`\`\n${planPreview}\n\`\`\`\n\n`;
    }

    if (topic.task) {
        // Count task progress
        const completed = (topic.task.match(/\[x\]/g) || []).length;
        const total = (topic.task.match(/\[[ x/]\]/g) || []).length;
        contextSummary += `## Task Progress: ${completed}/${total} complete\n\n`;
    }

    if (pendingDelegations.length > 0) {
        contextSummary += `## Pending Delegations (${pendingDelegations.length})\n`;
        pendingDelegations.forEach((d: DelegationInfo) => {
            contextSummary += `- **${d.agent}**: ${d.task}\n`;
        });
        contextSummary += '\n';
    }

    if (completeDelegations.length > 0) {
        contextSummary += `## Completed Delegations (${completeDelegations.length}) - ready to merge\n`;
        completeDelegations.forEach((d: DelegationInfo) => {
            contextSummary += `- **${d.agent}**: ${d.task}\n`;
        });
    }

    return {
        content: [{
            type: 'text',
            text: contextSummary,
        }],
    };
}

// ============================================
// delegate_to
// ============================================

export async function delegateTo(args: unknown): Promise<{ content: { type: 'text'; text: string }[] }> {
    const parsed = DelegateToArgsSchema.parse(args);

    if (!currentTopic) {
        return {
            content: [{
                type: 'text',
                text: '❌ No active topic. Use `create_topic` or `switch_topic` first.',
            }],
        };
    }

    // Check if agent exists
    const agentContent = await loadAgent(parsed.agent);
    const agentPath = getAgentPath(parsed.agent);

    const delegation = await createDelegation(
        currentTopic.name,
        parsed.agent,
        parsed.task,
        parsed.context || {},
        parsed.model_tier
    );

    let response = `## Delegation Created: ${delegation.id}

**Agent:** ${parsed.agent}
**Model Tier:** ${parsed.model_tier}
**Task:** ${parsed.task}

**Delegation file:** \`${currentTopic.path}/.delegations/${delegation.id}.md\`
`;

    if (!agentContent) {
        response += `
> ⚠️ **Warning:** Agent file not found at \`${agentPath}\`
> Create this file to define agent behavior, or the agent will use default behavior.
`;
    }

    response += `
### To execute this delegation:

**Option 1: tmux pane**
\`\`\`bash
tmux split-window -h "gh copilot --agent=${agentPath}"
\`\`\`

**Option 2: Manual**
Open a new terminal and run the agent with the delegation context.

---
The agent should write results to: \`${delegation.id}.result.md\`
`;

    return {
        content: [{
            type: 'text',
            text: response,
        }],
    };
}

// ============================================
// check_delegations
// ============================================

export async function checkDelegations(args: unknown): Promise<{ content: { type: 'text'; text: string }[] }> {
    const parsed = CheckDelegationsArgsSchema.parse(args);

    const topicName = parsed.topic || currentTopic?.name;
    if (!topicName) {
        return {
            content: [{
                type: 'text',
                text: '❌ No active topic and no topic specified.',
            }],
        };
    }

    const topic = await loadTopic(topicName);
    if (!topic) {
        return {
            content: [{
                type: 'text',
                text: `❌ Topic "${topicName}" not found.`,
            }],
        };
    }

    let delegations = topic.delegations;
    if (parsed.agent) {
        delegations = delegations.filter((d: DelegationInfo) => d.agent === parsed.agent);
    }

    if (delegations.length === 0) {
        return {
            content: [{
                type: 'text',
                text: `No delegations found${parsed.agent ? ` for agent "${parsed.agent}"` : ''}.`,
            }],
        };
    }

    const byStatus = {
        PENDING: delegations.filter((d: DelegationInfo) => d.status === 'PENDING'),
        IN_PROGRESS: delegations.filter((d: DelegationInfo) => d.status === 'IN_PROGRESS'),
        COMPLETE: delegations.filter((d: DelegationInfo) => d.status === 'COMPLETE'),
        BLOCKED: delegations.filter((d: DelegationInfo) => d.status === 'BLOCKED'),
    };

    let response = `## Delegations for ${topicName}\n\n`;

    if (byStatus.COMPLETE.length > 0) {
        response += `### ✅ Complete (${byStatus.COMPLETE.length})\n`;
        byStatus.COMPLETE.forEach((d: DelegationInfo) => {
            response += `- **${d.id}**: ${d.task}\n  → Results ready at \`${d.result_path}\`\n`;
        });
        response += '\n';
    }

    if (byStatus.PENDING.length > 0) {
        response += `### ⏳ Pending (${byStatus.PENDING.length})\n`;
        byStatus.PENDING.forEach((d: DelegationInfo) => {
            response += `- **${d.id}**: ${d.task}\n`;
        });
        response += '\n';
    }

    if (byStatus.IN_PROGRESS.length > 0) {
        response += `### 🔄 In Progress (${byStatus.IN_PROGRESS.length})\n`;
        byStatus.IN_PROGRESS.forEach((d: DelegationInfo) => {
            response += `- **${d.id}**: ${d.task}\n`;
        });
        response += '\n';
    }

    if (byStatus.BLOCKED.length > 0) {
        response += `### 🚫 Blocked (${byStatus.BLOCKED.length})\n`;
        byStatus.BLOCKED.forEach((d: DelegationInfo) => {
            response += `- **${d.id}**: ${d.task}\n`;
        });
    }

    return {
        content: [{
            type: 'text',
            text: response,
        }],
    };
}

// ============================================
// Exported tool definitions for MCP
// ============================================

export const toolDefinitions = [
    {
        name: 'create_topic',
        description: 'Create a new workflow topic with plan.md and task.md scaffolds',
        inputSchema: CreateTopicArgsSchema,
    },
    {
        name: 'list_topics',
        description: 'List all workflow topics and their status',
        inputSchema: {},
    },
    {
        name: 'switch_topic',
        description: 'Switch to a different topic, loading its plan and task context',
        inputSchema: SwitchTopicArgsSchema,
    },
    {
        name: 'delegate_to',
        description: 'Delegate a task to a specialist agent (e.g., swift6, testing, docs)',
        inputSchema: DelegateToArgsSchema,
    },
    {
        name: 'check_delegations',
        description: 'Check status of delegated tasks',
        inputSchema: CheckDelegationsArgsSchema,
    },
];
