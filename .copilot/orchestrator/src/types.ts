import { z } from 'zod';

// ============================================
// Topic & Session Types
// ============================================

export const SessionSchema = z.object({
    session_id: z.string(),
    topic: z.string(),
    created: z.string().datetime(),
    last_active: z.string().datetime(),
    coordinator_model: z.enum(['premium', 'standard', 'cheap']).default('premium'),
});

export type Session = z.infer<typeof SessionSchema>;

export interface TopicState {
    name: string;
    path: string;
    plan?: string;      // Contents of plan.md
    task?: string;      // Contents of task.md
    session?: Session;
    delegations: DelegationInfo[];
}

// ============================================
// Delegation Types
// ============================================

export const DelegationStatusSchema = z.enum(['PENDING', 'IN_PROGRESS', 'COMPLETE', 'BLOCKED']);

export const DelegationContextSchema = z.object({
    files: z.array(z.string()).optional(),
    plan_excerpt: z.string().optional(),
    constraints: z.string().optional(),
});

export type DelegationContext = z.infer<typeof DelegationContextSchema>;

export interface DelegationInfo {
    id: string;
    agent: string;
    task: string;
    context: DelegationContext;
    model_tier: 'premium' | 'standard' | 'cheap';
    status: z.infer<typeof DelegationStatusSchema>;
    created: string;
    result_path?: string;
}

// ============================================
// MCP Tool Argument Schemas
// ============================================

export const CreateTopicArgsSchema = z.object({
    name: z.string().describe('Topic name (kebab-case recommended, e.g., "auth-refactor")'),
    description: z.string().optional().describe('Brief description of the topic goal'),
});

export const SwitchTopicArgsSchema = z.object({
    name: z.string().describe('Name of the topic to switch to'),
});

export const DelegateToArgsSchema = z.object({
    agent: z.string().describe('Agent name (e.g., "swift6", "testing", "docs")'),
    task: z.string().describe('Natural language task description'),
    context: DelegationContextSchema.optional().describe('Context to provide to the agent'),
    model_tier: z.enum(['premium', 'standard', 'cheap']).default('cheap').describe('Model tier for the agent'),
    blocking: z.boolean().default(false).describe('Wait for result before returning'),
});

export const CheckDelegationsArgsSchema = z.object({
    topic: z.string().optional().describe('Topic to check (defaults to current topic)'),
    agent: z.string().optional().describe('Filter by specific agent'),
});

export const MergeResultsArgsSchema = z.object({
    delegation_id: z.string().describe('ID of the delegation to merge'),
});

export const ArchiveTopicArgsSchema = z.object({
    name: z.string().describe('Topic to archive'),
});

// ============================================
// Config Types
// ============================================

export const ModelTiersSchema = z.object({
    premium: z.string().default('o1-preview'),
    standard: z.string().default('gpt-4o'),
    cheap: z.string().default('gpt-4o-mini'),
});

export const ConfigSchema = z.object({
    model_tiers: ModelTiersSchema.optional(),
    defaults: z.object({
        coordinator: z.enum(['premium', 'standard', 'cheap']).default('premium'),
        specialist: z.enum(['premium', 'standard', 'cheap']).default('cheap'),
    }).optional(),
});

export type Config = z.infer<typeof ConfigSchema>;
