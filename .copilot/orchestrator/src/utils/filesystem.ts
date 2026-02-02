import { promises as fs } from 'fs';
import path from 'path';
import YAML from 'yaml';
import {
    TopicState,
    Session,
    SessionSchema,
    DelegationInfo,
    Config,
    ConfigSchema
} from '../types.js';

// Default paths - can be overridden via env vars
const WORKFLOWS_DIR = process.env.WORKFLOWS_DIR || path.join(process.env.HOME || '~', '.copilot', 'workflows');
const AGENTS_DIR = process.env.AGENTS_DIR || path.join(process.env.HOME || '~', '.copilot', 'agents');
const CONFIG_PATH = process.env.CONFIG_PATH || path.join(process.env.HOME || '~', '.copilot', 'config.json');

// ============================================
// Directory Helpers
// ============================================

export async function ensureDir(dirPath: string): Promise<void> {
    await fs.mkdir(dirPath, { recursive: true });
}

export async function exists(filePath: string): Promise<boolean> {
    try {
        await fs.access(filePath);
        return true;
    } catch {
        return false;
    }
}

// ============================================
// Topic Management
// ============================================

export function getTopicPath(topicName: string): string {
    return path.join(WORKFLOWS_DIR, topicName);
}

export async function listTopics(): Promise<string[]> {
    await ensureDir(WORKFLOWS_DIR);
    const entries = await fs.readdir(WORKFLOWS_DIR, { withFileTypes: true });
    return entries
        .filter(e => e.isDirectory() && !e.name.startsWith('.'))
        .map(e => e.name);
}

export async function loadTopic(topicName: string): Promise<TopicState | null> {
    const topicPath = getTopicPath(topicName);

    if (!await exists(topicPath)) {
        return null;
    }

    const state: TopicState = {
        name: topicName,
        path: topicPath,
        delegations: [],
    };

    // Load plan.md if exists
    const planPath = path.join(topicPath, 'plan.md');
    if (await exists(planPath)) {
        state.plan = await fs.readFile(planPath, 'utf-8');
    }

    // Load task.md if exists
    const taskPath = path.join(topicPath, 'task.md');
    if (await exists(taskPath)) {
        state.task = await fs.readFile(taskPath, 'utf-8');
    }

    // Load .session if exists
    const sessionPath = path.join(topicPath, '.session');
    if (await exists(sessionPath)) {
        const sessionContent = await fs.readFile(sessionPath, 'utf-8');
        const parsed = YAML.parse(sessionContent);
        state.session = SessionSchema.parse(parsed);
    }

    // Load delegations
    const delegationsDir = path.join(topicPath, '.delegations');
    if (await exists(delegationsDir)) {
        state.delegations = await loadDelegations(delegationsDir);
    }

    return state;
}

export async function createTopic(topicName: string, description?: string): Promise<TopicState> {
    const topicPath = getTopicPath(topicName);

    if (await exists(topicPath)) {
        throw new Error(`Topic "${topicName}" already exists`);
    }

    await ensureDir(topicPath);
    await ensureDir(path.join(topicPath, '.delegations'));

    // Create initial plan.md
    const planContent = `# ${topicName}

${description || '_No description provided_'}

## Context
<!-- Add relevant context here -->

## Proposed Changes
<!-- Define what will be changed -->

## Verification Plan
<!-- How to verify the changes work -->
`;

    await fs.writeFile(path.join(topicPath, 'plan.md'), planContent);

    // Create initial task.md
    const taskContent = `# ${topicName} Tasks

## Planning
- [ ] Define scope
- [ ] Create implementation plan

## Execution
- [ ] _Tasks will be added as planning progresses_

## Verification
- [ ] _Verification steps will be added_
`;

    await fs.writeFile(path.join(topicPath, 'task.md'), taskContent);

    return {
        name: topicName,
        path: topicPath,
        plan: planContent,
        task: taskContent,
        delegations: [],
    };
}

export async function saveSession(topicName: string, session: Session): Promise<void> {
    const sessionPath = path.join(getTopicPath(topicName), '.session');
    await fs.writeFile(sessionPath, YAML.stringify(session));
}

// ============================================
// Delegation Management
// ============================================

async function loadDelegations(delegationsDir: string): Promise<DelegationInfo[]> {
    const entries = await fs.readdir(delegationsDir);
    const delegations: DelegationInfo[] = [];

    for (const entry of entries) {
        if (entry.endsWith('.md') && !entry.endsWith('.result.md')) {
            const content = await fs.readFile(path.join(delegationsDir, entry), 'utf-8');
            const info = parseDelegationFile(entry, content);
            if (info) {
                // Check for result file
                const resultPath = path.join(delegationsDir, entry.replace('.md', '.result.md'));
                if (await exists(resultPath)) {
                    info.result_path = resultPath;
                    info.status = 'COMPLETE';
                }
                delegations.push(info);
            }
        }
    }

    return delegations;
}

function parseDelegationFile(filename: string, content: string): DelegationInfo | null {
    // Parse filename format: <agent>-<timestamp>.md
    const match = filename.match(/^(.+)-(\d+)\.md$/);
    if (!match) return null;

    const [, agent, timestamp] = match;

    // Parse YAML frontmatter if present
    const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
    let metadata: Record<string, unknown> = {};
    if (frontmatterMatch) {
        metadata = YAML.parse(frontmatterMatch[1]);
    }

    return {
        id: `${agent}-${timestamp}`,
        agent,
        task: (metadata.task as string) || 'Unknown task',
        context: (metadata.context as DelegationInfo['context']) || {},
        model_tier: (metadata.model_tier as DelegationInfo['model_tier']) || 'cheap',
        status: (metadata.status as DelegationInfo['status']) || 'PENDING',
        created: new Date(parseInt(timestamp)).toISOString(),
    };
}

export async function createDelegation(
    topicName: string,
    agent: string,
    task: string,
    context: DelegationInfo['context'],
    modelTier: DelegationInfo['model_tier']
): Promise<DelegationInfo> {
    const timestamp = Date.now();
    const id = `${agent}-${timestamp}`;
    const filename = `${id}.md`;

    const delegationsDir = path.join(getTopicPath(topicName), '.delegations');
    await ensureDir(delegationsDir);

    const content = `---
status: PENDING
task: "${task}"
agent: ${agent}
model_tier: ${modelTier}
created: ${new Date(timestamp).toISOString()}
context:
${context.files ? `  files:\n${context.files.map((f: string) => `    - ${f}`).join('\n')}` : ''}
${context.plan_excerpt ? `  plan_excerpt: |\n    ${context.plan_excerpt.split('\n').join('\n    ')}` : ''}
${context.constraints ? `  constraints: "${context.constraints}"` : ''}
---

# Delegation: ${task}

## Agent: ${agent}
## Model Tier: ${modelTier}

## Task Description
${task}

## Context
${context.plan_excerpt ? `### Plan Excerpt\n${context.plan_excerpt}\n` : ''}
${context.files?.length ? `### Files\n${context.files.map((f: string) => `- \`${f}\``).join('\n')}\n` : ''}
${context.constraints ? `### Constraints\n${context.constraints}\n` : ''}

---
_Write results to: ${id}.result.md_
`;

    await fs.writeFile(path.join(delegationsDir, filename), content);

    return {
        id,
        agent,
        task,
        context,
        model_tier: modelTier,
        status: 'PENDING',
        created: new Date(timestamp).toISOString(),
    };
}

// ============================================
// Config Management
// ============================================

export async function loadConfig(): Promise<Config> {
    if (!await exists(CONFIG_PATH)) {
        return {};
    }

    const content = await fs.readFile(CONFIG_PATH, 'utf-8');
    const parsed = JSON.parse(content);
    return ConfigSchema.parse(parsed);
}

// ============================================
// Agent Helpers
// ============================================

export function getAgentPath(agentName: string): string {
    return path.join(AGENTS_DIR, `${agentName}.agent.md`);
}

export async function loadAgent(agentName: string): Promise<string | null> {
    const agentPath = getAgentPath(agentName);
    if (!await exists(agentPath)) {
        return null;
    }
    return fs.readFile(agentPath, 'utf-8');
}
